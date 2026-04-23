"""
Author:    Lukas Konietzka, lukas.konietzka@tha.de

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY
--------------------------------------------------------------------

This module contains all the logic related to the 3D Slicer core system
"""

import logging
import os
import sys
import shutil
import time

from typing import Annotated, Optional

import sitkUtils
import vtkSegmentationCorePython as vtkSegCore
import vtk

import slicer
from MRMLCorePython import vtkMRMLLabelMapVolumeNode
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    Choice, parameterPack
)

from slicer import vtkMRMLScalarVolumeNode
from ToothAnalyserMicroCTLib.SampleData.ToothCrownMicroCT import registerToothCrownMicroCT8Bit

# load images for Help and Acknowledgement section
scriptDir = os.path.dirname(__file__)
projectRoot = os.path.abspath(os.path.join(scriptDir, ".."))
relativePathLogo = os.path.join(projectRoot, "Screenshots", "logo.png")
relativePathTHA = os.path.join(projectRoot, "Screenshots", "logoTHA.png")
relativePathLMU = os.path.join(projectRoot, "Screenshots", "logoLMU.svg")

# path to main module (ToothAnalyserMicroCT.py)
module_dir = os.path.dirname(__file__)

# path to library folder (ToothAnalyserMicroCTLib)
lib_path = os.path.join(module_dir, 'ToothAnalyserMicroCTLib')
test_path = os.path.join(module_dir, 'Testing', 'Python')

if lib_path not in sys.path:
    sys.path.insert(0, lib_path)
if test_path not in sys.path:
    sys.path.insert(0, test_path)


# ----- ToothAnalyserMicroCT meta information ----- #
class ToothAnalyserMicroCT(ScriptedLoadableModule):
    """ This Class holds all meta information about this module
    and add the connection to the 3D Slicer core application.
    As a child class of "ScriptedLoadableModule" all methods from
    this class can be used."""
    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("ToothAnalyserMicroCT")
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Segmentation")]
        self.parent.dependencies = []
        self.parent.contributors = ["Lukas Konietzka", "Dr. Elias Walter (Department of Conservative Dentistry, Periodontology and Digital Dentistry at the LMU Hospital, Munich)", "Simon Hofmann", "Prof. Dr. Peter Rösch (Technical University of Augsburg)"]
        self.parent.helpText = _(f"""
            <img src="{relativePathLogo}" width="200">
            <br>
            <br>
            ToothAnalyserMicroCT is an ongoing development effort for a 3D Slicer extension (SEM)
            designed for micro-computed tomography (microCT) scans of teeth. It provides
            specialized preprocessing, segmentation, and analysis features tailored for
            the analysis of tooth anatomy and pathology.
            <br>
            <br>
            If you need more information
            check out the <a href="https://github.com/lukaskonietzka/SlicerToothAnalyser">module documentation</a>.
        """)
        self.parent.acknowledgementText = _(f"""
            Developed in collaboration between the *Department of Computer Science* at
            the Technical University of Augsburg and the *Department of Conservative
            Dentistry and Periodontology* at the LMU Hospital, Munich. ToothAnalyserMicroCT
            facilitates advanced dental research through automated and semi-automate
            workflows.
            <br>
            <br>
            <img src="{relativePathTHA}" width="100">
            <img src="{relativePathLMU}" width="100">
        """)
        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerToothCrownMicroCT8Bit)


# ----- ToothAnalyserMicroCT Parameter Node ----- #
@parameterPack
class PreProcessing:
    """
    The Parameter needed by the section
    Pre Processing
    """
    compress: bool

@parameterPack
class AnatomicalParameters:
    """
    The parameters needed by the section
    Anatomical Segmentation
    """
    calcMidSurface: bool
    createMesh: bool

@parameterPack
class Batch:
    """
    The parameters needed by the section
    Batch Processing
    """
    sourcePath: str
    targetPath: str
    fileType: Annotated[str, Choice([".nrrd", ".nii", ".mhd"])] = ".nrrd"

@parameterNodeWrapper
class ToothAnalyserMicroCTParameterNode:
    """
    All parameters needed by module
    separated in: analytical, anatomical, batch
    """
    pre: PreProcessing
    anatomical: AnatomicalParameters
    currentImage: vtkMRMLScalarVolumeNode
    segmentation: Annotated[str, Choice(["Anatomical Segmentation"])] = "Anatomical Segmentation"
    batch: Batch
    isBatch: bool
    status: str = ""


# ----- ToothAnalyserMicroCT widget class ----- #
class ToothAnalyserMicroCTWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """
    This class include all the frontend logic
    Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """
    def __init__(self, parent=None) -> None:
        """
        Called when the user opens the module the first
        time and the widget is initialized
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._param = None
        self._parameterNodeGuiTag = None
        self._isComputing = False

    def setup(self) -> None:
        """
        Called when the user opens the module the first time and the widget is initialized.
        This Method creates an ui from the .ui file, set the scene in MRML widgets, instantiate
        the logic class, connect the observers and the static elements and initialize the
        ParameterNode.
        """
        ScriptedLoadableModuleWidget.setup(self)

        # create the ui widget from the QT ui-file
        uiWidget = self.createUI()

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = ToothAnalyserMicroCTLogic()

        # Add scene Connections
        self.connectObservers()
        self.connectStaticUiElements()

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def connectStaticUiElements(self) -> None:
        """
        This method connects all static ui elements that has no specific parameter
        More elements can be added.
        """
        self.ui.apply.connect("clicked(bool)", self.handleOnApply)
        self.ui.rdoSingle.connect("toggled(bool)", self.onBatchModeChanged)
        self.ui.rdoBatch.connect("toggled(bool)", self.onBatchModeChanged)

    def connectObservers(self) -> None:
        """
        These connections ensure that we update
        parameter node when scene is closed
        """
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

    def createUI(self) -> any:
        """
        Loads widget form .ui file (created by Qt Designer)
        .ui file is located in ./Resources/UI
        Additional widgets can be instantiated manually and added to self.layout
        return: the created ui as a widget
        """
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/ToothAnalyserMicroCT.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)
        return uiWidget

    def cleanup(self) -> None:
        """
        EVENT FUNCTION
        Called when the application closes and
        the module widget is destroyed.
        """
        self.removeObservers()

    def enter(self) -> None:
        """
        EVENT FUNCTION
        Called each time the user opens this module
        Make sure parameter node exists and observed
        """
        self.initializeParameterNode()

    def exit(self) -> None:
        """
        EVENT FUNCTION
        Called each time the user opens a different module.
        """
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._param:
            self._param.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._param, vtk.vtkCommand.ModifiedEvent, self.observerParameters)

    def onSceneStartClose(self, caller, event) -> None:
        """
        EVENT FUNCTION
        Called just before the scene is closed.
        :param: caller
        :param: event
        """
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """
        EVENT FUNCTION
        Called just after the scene is closed.
        param: caller
        param: event
        """
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """
        Ensure parameter node exists and observed.
        Parameter node stores all user choices in parameter values, node selections, etc.
        so that when the scene is saved and reloaded, these settings are restored.
        """
        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._param.currentImage:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._param.currentImage = firstVolumeNode

        # default settings for the parameters
        self.ui.calcMidSurface.checked = True
        self.ui.createMesh.checked = True
        self.ui.progressBar.setVisible(False)
        self.ui.status.setVisible(False)
        self.ui.status.enabled = False

    def setParameterNode(self, inputParameterNode: Optional[ToothAnalyserMicroCTParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        Note: Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each.
        @param inputParameterNode:  The ParameterNode from the module
        """
        if self._param:
            self._param.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._param, vtk.vtkCommand.ModifiedEvent, self.observerParameters)
        self._param = inputParameterNode
        if self._param:
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._param.connectGui(self.ui)

            # attach an observer to the parameters in the ToothAnalyserMicroCT widget
            self.addObserver(self._param, vtk.vtkCommand.ModifiedEvent,self.observerParameters)
            self.observerParameters()

    def observerParameters(self, caller=None, event=None) -> None:
        """
        This is an event function connected to the parameters in the widget.
        Called everytime a ToothAnalyserMicroCT parameter changes.
        call up everything that is to be updated here if the parameters in the ui change
        @param caller:
        @param event. the event that triggered the funktion (ModifiedEvent)
        """
        self.syncBatchModeUi()
        self.handleApplyButton()
        self.handleSegmentation()
        self.handleBatchCollapsible()

    def syncBatchModeUi(self) -> None:
        """
        Keep the radio buttons in sync with the parameter node.
        """
        if not self._param:
            return
        self.ui.rdoBatch.checked = bool(self._param.isBatch)
        self.ui.rdoSingle.checked = not self._param.isBatch

    def onBatchModeChanged(self, _checked=None) -> None:
        """
        Update parameter node when the batch mode radios change.
        """
        if not self._param:
            return
        self._param.isBatch = bool(self.ui.rdoBatch.checked)

    def handleBatchCollapsible(self):
        """
        Toggle input parameter visibility depending on batch mode.
        """
        if self._param.isBatch:
            self.ui.label_3.setVisible(False)
            self.ui.currentImage.setVisible(False)
            self.ui.currentImage.enabled = False
            self.ui.label_4.setVisible(True)
            self.ui.sourcePath.setVisible(True)
            self.ui.label_5.setVisible(True)
            self.ui.targetPath.setVisible(True)
            self.ui.label_7.setVisible(True)
            self.ui.fileType.setVisible(True)
            self.ui.sourcePath.enabled = True
            self.ui.targetPath.enabled = True
            self.ui.fileType.enabled = True
        else:
            self.ui.label_3.setVisible(True)
            self.ui.currentImage.setVisible(True)
            self.ui.currentImage.enabled = True
            self.ui.label_4.setVisible(False)
            self.ui.sourcePath.setVisible(False)
            self.ui.label_5.setVisible(False)
            self.ui.targetPath.setVisible(False)
            self.ui.label_7.setVisible(False)
            self.ui.fileType.setVisible(False)
            self.ui.sourcePath.enabled = False
            self.ui.targetPath.enabled = False
            self.ui.fileType.enabled = False

    def handleApplyButton(self):
        """
        Enable the apply button when either batch mode is enabled
        or an image is loaded, unless processing is currently active.
        """
        if self._isComputing:
            self.ui.apply.enabled = False
            self.ui.apply.text = "Applying..."
            return

        if self._param.isBatch or self._param.currentImage:
            self.ui.apply.enabled = True
            self.ui.apply.text = "Apply"
            if self._param.isBatch:
                self.ui.apply.text = "Apply Batch"
        else:
            self.ui.apply.enabled = False
            self.ui.apply.text = "Apply"

    def validateBatchSettings(self, paramsToCheck: dict) -> bool:
        """
        The method checks if exactly one batch setting checkbox is enabled.
        @param paramsToCheck: A dictionary with the checkboxes to be checked
        @return: True, if there is exactly one enabled checkbox
        """
        return sum(value for value in paramsToCheck.values() if isinstance(value, bool)) == 1

    def activateComputingMode(self, isVisible: bool) -> None:
        """
        This method sets the Ui to calculation mode so that
        no unwanted user input can occur
        @param isVisible: computing mode ist activated when TRUE
        """
        self._isComputing = isVisible
        slicer.app.processEvents()

        self.ui.progressBar.enabled = isVisible
        self.ui.progressBar.setVisible(isVisible)
        self.ui.progressBar.enabled = isVisible

        self.handleApplyButton()

        slicer.app.processEvents()

    def handleSegmentation(self):
        if self._param.segmentation == "Anatomical Segmentation":
            self.ui.cariesCollapsible.setVisible(False)
        else:
            self.ui.cariesCollapsible.setVisible(True)

    def handleProgressBarRange(self) -> None:
        """
        This Methode sets the maximum for the progress Bar
        depending on the medial surfaces
        """
        maxWithMedialSurface = 13
        maxWithoutMedialSurface = 11

        if self._param.anatomical.calcMidSurface:
            self.ui.progressBar.maximum = maxWithMedialSurface
        else:
            self.ui.progressBar.maximum = maxWithoutMedialSurface


    def handleOnApply(self):
        """
        This methode is called when the apply button is pressed
        """
        self.handleProgressBarRange()
        self.activateComputingMode(True)
        try:
            with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
                self.logic.setSelectedAlgorithm(self._param.segmentation)
                selectedAlgorithm = self.logic.getSelectedAlgorithm()
                if not selectedAlgorithm:
                    raise RuntimeError(f"Unsupported segmentation algorithm '{self._param.segmentation}'.")

                if self._param.isBatch:
                    selectedAlgorithm.executeAsBatch(param=self._param, progressBar=self.ui.progressBar)
                else:
                    selectedAlgorithm.execute(param=self._param, progressBar=self.ui.progressBar)
        finally:
            self.activateComputingMode(False)


# ----- ToothAnalyserMicroCT logic interface ----- #
class ToothAnalyserMicroCTLogic(ScriptedLoadableModuleLogic):
    """ This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """
    _algorithm = []

    def __init__(self) -> None:
        """ Called when the logic class is instantiated.
        Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)
        self._selectedAlgorithm = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls not in ToothAnalyserMicroCTLogic._algorithm:
            ToothAnalyserMicroCTLogic._algorithm.append(cls)

    def __str__(self):
        """Return the default algorithm label if subclasses do not override ``__str__``."""
        return "Unbekannter Algorithmus"

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def getAlgorithmsByName(self):
        """Return algorithm names as exposed by each subclass ``__str__`` implementation."""
        return [subclass().__str__() for subclass in self._algorithm]

    def getAlgorithms(self):
        """Return all registered algorithm classes."""
        return [subclass for subclass in self._algorithm]

    def setSelectedAlgorithm(self, currentAlgorithmName):
        """Set the active algorithm instance by display name."""
        self._selectedAlgorithm = None
        for algorithm in self.getAlgorithms():
            instance = algorithm()
            if instance.__str__() == currentAlgorithmName:
                self._selectedAlgorithm = instance
                break

    def getSelectedAlgorithm(self):
        """Return the currently selected algorithm instance."""
        return self._selectedAlgorithm

    def getParameterNode(self) -> ToothAnalyserMicroCTParameterNode:
        """
        Return the module-specific wrapped parameter node.
        """
        return ToothAnalyserMicroCTParameterNode(super().getParameterNode())

    def preprocessing(self) -> None:
        """Implement your preprocessing here"""
        pass

    def postprocessing(self) -> None:
        """Implement your postprocessing here"""
        pass

    def error(self, msg: str) -> None:
        slicer.util.errorDisplay(msg)

    def warning(self, msg: str) -> None:
        slicer.util.warningDisplay(msg)

    def execute(self, param: ToothAnalyserMicroCTParameterNode, progressBar) -> None:
        """Abstract method"""
        raise NotImplementedError("Please implement the execute() methode in one of the child classes")

    def executeAsBatch(self, param: ToothAnalyserMicroCTParameterNode, progressBar) -> None:
        """Abstract method"""
        raise NotImplementedError("Please implement the executeAsBatch() methode in one of the child classes")


# ----- ToothAnalyserMicroCT section anatomical segmentation ----- #
class AnatomicalSegmentationLogic(ToothAnalyserMicroCTLogic):
    """
    this class contains all the logic needed to visualise
    the anatomical segmentation
    """
    _anatomicalSegmentationName: str = "_AnatomicalSegmentation"
    _midSurfaceName: str = "_MedialSurface"
    _stlModelName: str = "_Mesh"
    _segmentNames: list[str] = ["Dentin", "Enamel"]
    _fileTypes: tuple[str] = (".ISQ", ".mhd", ".nrrd", ".nii")

    def __str__(self):
        return "Anatomical Segmentation"

    def collectFiles(self, path: str, suffix: tuple[str, ...]) -> list[str]:
        """
        Loads all data with the given suffix from the given path
        @param path: the path to the directory where the files are located
        @param suffix: only files with this format are loaded
        @return: the collected files in a python list
        @example:
            path = '/data/MicroCT/Original_ISQ/'
            suffix = ('.mhd', '.nrrd', '.nii')
            files = cls.collectFiles(path, suffix)
            files -> [file1, file2, ...]
        """
        files = []
        if os.path.isdir(path):
            normalizedSuffix = tuple(
                s.lower() if s.startswith(".") else f".{s.lower()}" for s in suffix
            )
            files = sorted([
                f for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))
                and os.path.splitext(f)[1].lower() in normalizedSuffix
            ])
        return files

    def _safeRemoveNode(self, node):
        """Remove node only if it still exists in the scene."""
        if node and node.GetScene():
            slicer.mrmlScene.RemoveNode(node)

    def createSegmentation(self, labelMapNode: vtkMRMLLabelMapVolumeNode,
                           deleteLabelMapNode: bool,
                           currentImageName: str):
        """
        Generates a segmentationNode from a given labelNode.
        After generation the segmentationNode will get some properties
        """
        try:
            # create segmentation
            seg = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
            slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(labelMapNode, seg)
            seg.CreateClosedSurfaceRepresentation()

            # set properties for segmentation
            seg.SetName(currentImageName + self._anatomicalSegmentationName)
            default_names = self._segmentNames

            segmentation = seg.GetSegmentation()
            num_segments = segmentation.GetNumberOfSegments()

            for i in range(num_segments):
                segment = segmentation.GetNthSegment(i)

                if i < len(default_names):
                    segment_name = default_names[i]

                    if segment_name == "Enamel":
                        segment.SetColor(0.435, 0.722, 0.824)

                    if segment_name == "Dentin":
                        segment.SetColor(1.0, 1.0, 0.8)
                else:
                    segment_name = f"Segment {i + 1}"

                segment.SetName(segment_name)

            # delete the given labelNode
            if deleteLabelMapNode:
                self._safeRemoveNode(labelMapNode)

            return seg

        except Exception as e:
            self.error(f"Error while creating the segmentation! {e}")
            return None

    def createSTLModelsInScene(self, segmentationNode, currentImageName: str) -> None:
        """
        Create STL-ready model nodes from the segmentation and store them in the Slicer scene.
        """
        try:
            if not segmentationNode:
                return

            modelNodesBefore = {
                slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLModelNode").GetID()
                for i in range(slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLModelNode"))
            }

            segmentationNode.CreateClosedSurfaceRepresentation()
            shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
            folderItemId = shNode.CreateFolderItem(
                shNode.GetSceneItemID(),
                currentImageName + self._stlModelName
            )
            slicer.modules.segmentations.logic().ExportAllSegmentsToModels(segmentationNode, folderItemId)

            modelCount = slicer.mrmlScene.GetNumberOfNodesByClass("vtkMRMLModelNode")
            for i in range(modelCount):
                modelNode = slicer.mrmlScene.GetNthNodeByClass(i, "vtkMRMLModelNode")
                if modelNode.GetID() not in modelNodesBefore:
                    modelNode.SetName(f"{currentImageName}_{modelNode.GetName()}{self._stlModelName}")
        except Exception as e:
            logging.exception("Failed to create STL model nodes for '%s'", currentImageName)
            self.warning(f"Could not create STL models in scene for '{currentImageName}': {e}")

    def createMedialSurface(self, midSurfaceDentinLabelMapNode: vtkMRMLLabelMapVolumeNode,
                            midSurfaceEnamelLabelMapNode: vtkMRMLLabelMapVolumeNode,
                            currentImageName: str,
                            deleteLabelMapNodes: bool) -> None:
        """
        This method creates a segmentation for the given medial surface
        """
        try:
            # create dentin medial surface segmentation
            segDentin = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
            slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(
                midSurfaceDentinLabelMapNode, segDentin)
            segDentin.SetName("MedialSurface_source")

            dentinSegmentation = segDentin.GetSegmentation()

            if dentinSegmentation.GetNumberOfSegments() > 0:
                segment = dentinSegmentation.GetNthSegment(0)
                segment.SetName(self._segmentNames[0])
                segment.SetColor(1.0, 0.0, 0.0)
                if deleteLabelMapNodes:
                    self._safeRemoveNode(midSurfaceDentinLabelMapNode)

            # create enamel medial surface segmentation
            segEnamel = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
            slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(
                midSurfaceEnamelLabelMapNode, segEnamel)
            segEnamel.SetName(currentImageName + self._midSurfaceName)

            enamelSegmentation = segEnamel.GetSegmentation()

            if enamelSegmentation.GetNumberOfSegments() > 0:
                segment = enamelSegmentation.GetNthSegment(0)
                segment.SetName(self._segmentNames[1])
                segment.SetColor(0.0, 1.0, 0.0)
                if deleteLabelMapNodes:
                    self._safeRemoveNode(midSurfaceEnamelLabelMapNode)

            # copy all segments from dentin to enamel (FIX: clone segments -> no ID conflicts)
            for i in range(dentinSegmentation.GetNumberOfSegments()):
                sourceSegment = dentinSegmentation.GetNthSegment(i)

                # clone segment
                newSegment = vtkSegCore.vtkSegment()
                newSegment.DeepCopy(sourceSegment)

                # generate guaranteed unique ID in target
                newSegmentId = enamelSegmentation.GenerateUniqueSegmentID(
                    sourceSegment.GetName()
                )
                enamelSegmentation.AddSegment(newSegment, newSegmentId)

            # remove dentin helper segmentation
            try:
                node = slicer.util.getFirstNodeByName("MedialSurface_source")
                self._safeRemoveNode(node)
            except Exception as e:
                logging.exception("Failed to remove helper node 'MedialSurface_source'")
                self.warning(f"Could not remove temporary medial-surface helper node: {e}")

            if deleteLabelMapNodes:
                self._safeRemoveNode(midSurfaceEnamelLabelMapNode)
                self._safeRemoveNode(midSurfaceDentinLabelMapNode)

        except Exception as e:
            self.error(f"Error while creating the medial surfaces! {e}")

    def clearScene(self) -> None:
        """
        Deletes all nodes from the scene that were generated by the algorithm.
        """
        try:
            for node in slicer.util.getNodes("*" + self._anatomicalSegmentationName).values():
                self._safeRemoveNode(node)
            for node in slicer.util.getNodes("*" + self._midSurfaceName).values():
                self._safeRemoveNode(node)
            for node in slicer.util.getNodes("*" + self._stlModelName).values():
                self._safeRemoveNode(node)
        except Exception as e:
            logging.exception("Failed to clear generated scene nodes")
            self.warning(f"Could not fully clear generated scene nodes: {e}")

    def clearDirectory(self, path: str) -> None:
        """
        Delete all files in the given directory
        @param path: path to the directory to be cleaned
        @example:
            path = "/data/MicroCT/Original_ISQ/Results"
            cls.clearDirectory(path)
        """

        if not os.path.exists(path):
            slicer.util.errorDisplay("The given directory for the batch process does not exists")
            return

        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
        except Exception as e:
            logging.exception("Failed to clear batch target directory '%s'", path)
            self.error(f"Could not clear batch target directory '{path}': {e}")

    def createDirectory(self, path: str, directoryName: str) -> str:
        """
        Creates a directory with the given name in the given path if
        there is no directory with this name.
        :param path: The path where the directory needs to be added
        :param directoryName: The name of the new directory
        :return targetDirectory: The absolut path to the created directory
        """
        targetDirectory = os.path.join(path, directoryName) + os.sep
        try:
            os.makedirs(targetDirectory, exist_ok=True)
        except Exception as e:
            self.error(f"Error while creating directory: {e}")
        return targetDirectory

    def createTemporaryStorageNode(self, param):
        """
        This methode creates a storage node, to cache the sample data

        @param param:
        @return:
        """
        tempPath = slicer.app.temporaryPath
        fileName = (param.currentImage.GetName() + ".nrrd")
        filePath = os.path.join(tempPath, fileName)
        storageNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLVolumeArchetypeStorageNode")
        storageNode.SetFileName(filePath)
        param.currentImage.SetAndObserveStorageNodeID(storageNode.GetID())
        storageNode.WriteData(param.currentImage)

    def createLabelMapNode(self, itkImage, labelMapName: str) -> any:
        """
        This methode creates a Slicer labelMapNode starting from itk

        @param itkImage:
        @param labelMapName:
        @return:
        """
        return sitkUtils.PushVolumeToSlicer(itkImage, None, labelMapName, "vtkMRMLLabelMapVolumeNode")

    def createVolume(self, img):
        """
        This method creates a Slicer volume starting form an itk

        @param img:
        @return:
        """
        return sitkUtils.PushVolumeToSlicer(img)

    def runSegmentationPipeline(
            self,
            param: ToothAnalyserMicroCTParameterNode,
            progressBar,
            sourcePath: Optional[str] = None) -> dict:
        """
        This methode executes the segmentation pipeline and provide the
        results in a dictionary

        @param param:
        @param progressBar:
        @return:
        """
        from ToothAnalyserMicroCTLib.Algorithms.Anatomical import calcSegmentationGen

        segmentationType = "otsu"

        if sourcePath is None:
            try:
                sourcePath = param.currentImage.GetStorageNode().GetFullNameFromFileName()
            except Exception:
                self.createTemporaryStorageNode(param)
                sourcePath = param.currentImage.GetStorageNode().GetFullNameFromFileName()

        slicer.app.processEvents()

        segmentationStep = calcSegmentationGen(
            sourcePath=sourcePath,
            selectedAlgorithm="Otsu",
            calcMedialSurfaces=param.anatomical.calcMidSurface,
            compress=param.pre.compress)

        while True:
            result = next(segmentationStep)

            if isinstance(result, dict):
                toothDict = result
                break
            else:
                progressBar.value = result
                slicer.app.processEvents()

        # provide results in dict
        results = {
            "segmentationType": segmentationType,
            "enamelMidSurface": toothDict.get(f"enamel_{segmentationType}_{segmentationType}_midsurface"),
            "dentinMidSurface": toothDict.get(f"dentin_{segmentationType}_{segmentationType}_midsurface"),
            "labelImage": toothDict.get(f"segmentation_{segmentationType}_{segmentationType}_labels"),
            "imageName": toothDict.get("name", os.path.basename(sourcePath)),
            "image": toothDict.get("img"),
            "toothDict": toothDict
        }
        return results

    def loadResultsToScene(self, results: dict, param: ToothAnalyserMicroCTParameterNode) -> None:
        """
        This methode takes the results from the segmentation pipeline and
        load it to the Slicer scene.

        @param results:
        @param param:
        @return:
        """
        self.clearScene()

        labelNode = self.createLabelMapNode(results["labelImage"], "tempLabel")
        segmentationNode = self.createSegmentation(
            labelMapNode=labelNode,
            deleteLabelMapNode=True,
            currentImageName=results["imageName"])
        if param.anatomical.createMesh:
            self.createSTLModelsInScene(segmentationNode, results["imageName"])

        if results["enamelMidSurface"] and results["dentinMidSurface"]:
            dentinNode = self.createLabelMapNode(results["dentinMidSurface"], "tempDentin")
            enamelNode = self.createLabelMapNode(results["enamelMidSurface"], "tempEnamel")
            self.createMedialSurface(
                midSurfaceDentinLabelMapNode=dentinNode,
                midSurfaceEnamelLabelMapNode=enamelNode,
                currentImageName=results["imageName"],
                deleteLabelMapNodes=True)

        if param.pre.compress and param.currentImage:
            import SimpleITK as sitk

            oldNode = param.currentImage
            compressedImage = results["image"]
            if compressedImage.GetPixelID() != sitk.sitkUInt8:
                compressedImage = sitk.Cast(compressedImage, sitk.sitkUInt8)

            compressedNode = sitkUtils.PushVolumeToSlicer(
                compressedImage,
                None,
                f"{results['imageName']}_Comp",
                "vtkMRMLScalarVolumeNode"
            )
            param.currentImage = compressedNode
            self._safeRemoveNode(oldNode)

    def execute(self, param: ToothAnalyserMicroCTParameterNode, progressBar) -> None:
        """
        Execute the algorithm by clicking the "apply" Button.
        @param param:
        @param progressBar:
        @return:
        """
        start = time.time()

        # calculate Segmentation
        segmentationResults = self.runSegmentationPipeline(param, progressBar)

        # load the segmentation th the slicer scene
        self.loadResultsToScene(segmentationResults, param)

        duration = time.time() - start
        logging.info("Verarbeitung abgeschlossen in: %.0f Minuten und %.0f Sekunden",duration // 60, duration % 60)

    def executeAsBatch(self, param: ToothAnalyserMicroCTParameterNode, progressBar) -> None:
        """
        This method starts the pipeline to compute all files in batch process
        @param param: all parameters from the user interface (UI)
        @param progressBar
        @return: None
        @example:
            AnatomicalSegmentationLogic.executeAsBatch(param=self._param)
        """
        from ToothAnalyserMicroCTLib.Algorithms.Anatomical import writeToothDict
        from ToothAnalyserMicroCTLib.Algorithms.utils import createSTL

        # create local variables for all parameters
        if not os.path.isdir(param.batch.sourcePath):
            slicer.util.errorDisplay("The given source path is not an directory.")
            return
        if not os.path.isdir(param.batch.targetPath):
            slicer.util.errorDisplay("The given target path is not an directory.")
            return
        sourcePath = param.batch.sourcePath
        targetPath = param.batch.targetPath
        segmentationType = "Otsu"
        files = self.collectFiles(sourcePath, self._fileTypes)
        if not files:
            self.warning("No supported input files found in source directory.")
            return

        # Create result directory
        targetDirectory = self.createDirectory(
            path=targetPath,
            directoryName=self._anatomicalSegmentationName + segmentationType)

        # Delete the old segmentation to keep order
        self.clearDirectory(targetDirectory)

        for file in files:
            fullFilePath = os.path.join(sourcePath, file)

            try:
                segmentationResults = self.runSegmentationPipeline(
                    param=param,
                    progressBar=progressBar,
                    sourcePath=fullFilePath)
                toothDict = segmentationResults["toothDict"]

                # create directory for each File to be calculated
                targetFileDirectory = self.createDirectory(
                    path=targetDirectory,
                    directoryName=segmentationResults["imageName"])

                writeToothDict(
                    tooth=toothDict,
                    path=targetFileDirectory,
                    calcMidSurface=param.anatomical.calcMidSurface,
                    fileType=param.batch.fileType)

                if param.anatomical.createMesh:
                    stlFileName = (
                        f"{segmentationResults['imageName']}_"
                        f"{segmentationResults['segmentationType']}_segmentation"
                    )
                    createSTL(
                        labelImage=segmentationResults["labelImage"],
                        outputDirectory=targetFileDirectory,
                        fileName=stlFileName,
                        printMode=True
                    )
            except Exception as e:
                logging.exception("Batch processing failed for '%s'", fullFilePath)
                self.warning(f"Skipping '{file}': {e}")
                continue


class PathologicalSegmentation(ToothAnalyserMicroCTLogic):
    """Placeholder implementation for pathological segmentation workflows."""
    def __str__(self):
        """
        Return the visible algorithm name in the segmentation selector.
        """
        return "Pathological Segmentation"

    def execute(self, param: ToothAnalyserMicroCTParameterNode, progressBar):
        self.preprocessing()
        print("Coming up soon, execute Pathological Segmentation ...")
        self.postprocessing()

    def executeAsBatch(self, param: ToothAnalyserMicroCTParameterNode, progressBar):
        self.preprocessing()
        print("Coming up soon, execute Pathological Segmentation as Batch ...")
        self.postprocessing()


# ----- ToothAnalyserMicroCT Tests ----- #
from Testing.Python.ToothAnalyserMicroCTTests import ToothAnalyserMicroCTTestMixin

class ToothAnalyserMicroCTTest(ToothAnalyserMicroCTTestMixin, ScriptedLoadableModuleTest):
    """Wrapper class so Slicer's Reload-and-Test discovers module tests."""

    ToothAnalyserMicroCTLogic = ToothAnalyserMicroCTLogic
    ToothAnalyserMicroCTWidget = ToothAnalyserMicroCTWidget
    AnatomicalSegmentationLogic = AnatomicalSegmentationLogic
    PathologicalSegmentation = PathologicalSegmentation
