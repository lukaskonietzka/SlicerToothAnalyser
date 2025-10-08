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
import vtk

import slicer
from MRMLCorePython import vtkMRMLLabelMapVolumeNode
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin, getNode
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    Choice, parameterPack
)

from slicer import vtkMRMLScalarVolumeNode
from ToothAnalyserLib.SampleData.ToothCrownMicroCT import registerToothCrownMicroCT

# load images for Help and Acknowledgement section
scriptDir = os.path.dirname(__file__)
projectRoot = os.path.abspath(os.path.join(scriptDir, ".."))
relativePathLogo = os.path.join(projectRoot, "Screenshots", "logo.png")
relativePathTHA = os.path.join(projectRoot, "Screenshots", "logoTHA.png")
relativePathLMU = os.path.join(projectRoot, "Screenshots", "logoLMU.svg")

# Pfad zur Moduldatei (ToothAnalyser.py)
module_dir = os.path.dirname(__file__)

# Pfad zum Library-Ordner (ToothAnalyserLib)
lib_path = os.path.join(module_dir, 'ToothAnalyserLib')

# Falls noch nicht im sys.path, hinzufügen
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)


# ----- Tooth Analyser meta information ----- #
class ToothAnalyser(ScriptedLoadableModule):
    """ This Class holds all meta information about this module
    and add the connection to the 3D Slicer core application.
    As a child class of "ScriptedLoadableModule" all methods from
    this class can be used."""

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("Tooth Analyser")
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Segmentation")]
        self.parent.dependencies = []
        self.parent.contributors = ["Lukas Konietzka (THA)", "Simon Hofmann (THA)", "Prof. Dr. Peter Rösch (THA)", "Dr. Elias Walter (LMU)"]
        self.parent.helpText = _(f"""
            <img src="{relativePathLogo}" width="200">
            <br>
            <br>
            Tooth Analyser is an ongoing development effort for a 3D Slicer extension (SEM)
            designed for micro-computed tomography (microCT) scans of teeth. It provides
            specialized preprocessing, segmentation, and analysis features tailored for
            the analysis of tooth anatomy and pathology.
            <br>
            <br>
            If you need more information
            check out the <a href="https://github.com/lukaskonietzka/SlicerToothAnalyser/tree/dev">module documentation</a>.
        """)
        self.parent.acknowledgementText = _(f"""
            Developed in collaboration between the *Department of Computer Science* at
            the Technical University of Augsburg and the *Department of Conservative
            Dentistry and Periodontology* at the LMU Hospital, Munich. Tooth Analyser
            facilitates advanced dental research through automated and semi-automate
            workflows.
            <br>
            <br>
            <img src="{relativePathTHA}" width="100">
            <img src="{relativePathLMU}" width="100">
        """)
        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerToothCrownMicroCT)


# ----- Tooth Analyser Parameter Node ----- #
@parameterPack
class AnatomicalParameters:
    """
    The parameters needed by the section
    Anatomical Segmentation
    """
    selectedAnatomicalAlgo: Annotated[str, Choice(["Otsu", "Renyi"])] = "Otsu"
    calcMidSurface: bool

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
class ToothAnalyserParameterNode:
    """
    All parameters needed by module
    separated in: analytical, anatomical, batch
    """
    anatomical: AnatomicalParameters
    currentImage: vtkMRMLScalarVolumeNode
    segmentation: Annotated[str, Choice(["Anatomical Segmentation", "Caries Segmentation"])] = "Anatomical Segmentation"
    batch: Batch
    isBatch: bool
    isPreProcessing: bool
    status: str = ""


# ----- Tooth Analyser widget class ----- #
class ToothAnalyserWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
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
        self.logic = ToothAnalyserLogic()

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
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/ToothAnalyser.ui"))
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
        self.ui.progressBar.setVisible(False)
        self.ui.status.setVisible(False)
        self.ui.status.enabled = False
        self._param.anatomical.selectedAnatomicalAlgo = "Otsu"

    def setParameterNode(self, inputParameterNode: Optional[ToothAnalyserParameterNode]) -> None:
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

            # attach an observer to the parameters in the Tooth Analyser widget
            self.addObserver(self._param, vtk.vtkCommand.ModifiedEvent,self.observerParameters)
            self.observerParameters()

    def observerParameters(self, caller=None, event=None) -> None:
        """
        This is an event function connected to the parameters in the widget.
        Called everytime a Tooth Analyser parameter changes.
        call up everything that is to be updated here if the parameters in the ui change
        @param caller:
        @param event. the event that triggered the funktion (ModifiedEvent)
        """
        self.handleApplyButton()
        self.handleSegmentation()
        self.handleBatchCollapsible()
        self.handlePreProcessingCollapsible()

    def handlePreProcessingCollapsible(self):
        """
        This methode shows the preprocessing collapsible
        depending on the preprocessing checkbox
        """
        if self._param.isPreProcessing:
            self.ui.preProcessingCollapsible.setVisible(True)
        elif not self._param.isPreProcessing:
            self.ui.preProcessingCollapsible.setVisible(False)

    def handleBatchCollapsible(self):
        """
        This methode shows the batch processing collapsible
        depending on the batch processing checkbox
        """
        if self._param.isBatch:
            self.ui.batchCollapsible.setVisible(True)
        elif not self._param.isBatch:
            self.ui.batchCollapsible.setVisible(False)

    def handleApplyButton(self):
        """
        Enable the "Apply Anatomical" Button, if an image is
        loaded to the scene.
        """
        if not self._param.currentImage:
            self.ui.apply.enabled = False
        elif self.ui.status.isVisible():
            self.ui.apply.enabled = False
        else:
            self.ui.apply.enabled = True

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
        slicer.app.processEvents()

        self.ui.progressBar.enabled = isVisible

        self.ui.apply.enabled = not isVisible
        self.ui.applyBatch.enabled = not isVisible

        self.ui.status.setVisible(isVisible)
        self.ui.progressBar.setVisible(isVisible)
        self.ui.progressBar.enabled = isVisible

        self.handleApplyButton()

        slicer.app.processEvents()

    def handleSegmentation(self):
        if self._param.segmentation == "Anatomical Segmentation":
            self.ui.anatomicaCollapsible.setVisible(True)
            self.ui.cariesCollapsible.setVisible(False)
        else:
            self.ui.anatomicaCollapsible.setVisible(False)
            self.ui.cariesCollapsible.setVisible(True)

    def handleProgressBarRange(self) -> None:
        """
        This Methode sets the maximum for the progress Bar
        depending on the medial surfaces
        """
        maxWithMedialSurface = 12
        maxWithoutMedialSurface = 10

        if self._param.anatomical.calcMidSurface:
            self.ui.progressBar.maximum = maxWithMedialSurface
        else:
            self.ui.progressBar.maximum = maxWithoutMedialSurface


    def handleOnApply(self):
        """
        This methode is called when the apply button is pressed
        """
        self._param.status = "start anatomical segmentation..."
        self.handleProgressBarRange()
        self.activateComputingMode(True)
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            if self._param.isBatch:
                self.logic.setSelectedAlgorithm(self._param.segmentation)
                self.logic.getSelectedAlgorithm().executeAsBatch(param=self._param, progressBar=self.ui.progressBar)
            else:
                self.logic.setSelectedAlgorithm(self._param.segmentation)
                self.logic.getSelectedAlgorithm().execute(param=self._param, progressBar=self.ui.progressBar)
        self.activateComputingMode(False)


# ----- Tooth Analyser logic interface ----- #
class ToothAnalyserLogic(ScriptedLoadableModuleLogic):
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
        if cls not in ToothAnalyserLogic._algorithm:
            ToothAnalyserLogic._algorithm.append(cls)

    def __str__(self):
        """Standardwert, falls eine Kindklasse __str__ nicht überschreibt."""
        return "Unbekannter Algorithmus"

    def __repr__(self):
        return f"{self.__class__.__name__}()"

    def getAlgorithmsByName(self):
        """Gibt die Namen zurück, die durch __str__ in den Kindklassen definiert wurden."""
        return [subclass().__str__() for subclass in self._algorithm]

    def getAlgorithms(self):
        """Gibt die verfügbaren Algorithmus-Klassen zurück."""
        return [subclass for subclass in self._algorithm]

    def setSelectedAlgorithm(self, currentAlgorithmName):
        """Setzt den aktuellen Algorithmus basierend auf dem Namen."""
        for algorithm in self.getAlgorithms():
            instance = algorithm()  # Instanz erstellen
            if instance.__str__() == currentAlgorithmName:  # __str__-Namen vergleichen
                self._selectedAlgorithm = instance  # Instanz speichern
                break

    def getSelectedAlgorithm(self):
        """Gibt den aktuell ausgewählten Algorithmus zurück."""
        return self._selectedAlgorithm

    def getParameterNode(self) -> ToothAnalyserParameterNode:
        """
        Getter methode for the ParameterNode needed in the logic class
        return: The ParameterNode from this module
        """
        return ToothAnalyserParameterNode(super().getParameterNode())

    def preprocessing(self) -> None:
        """Implement your preprocessing here"""
        pass

    def postprocessing(self) -> None:
        """Implement your postprocessing here"""
        pass

    def execute(self, param: ToothAnalyserParameterNode, progressBar) -> None:
        """Abstract method"""
        raise NotImplementedError("Please implement the execute() methode in one of the child classes")

    def executeAsBatch(self, param: ToothAnalyserParameterNode, progressBar) -> None:
        """Abstract method"""
        raise NotImplementedError("Please implement the executeAsBatch() methode in one of the child classes")


# ----- Tooth Analyser section anatomical segmentation ----- #
class AnatomicalSegmentationLogic(ToothAnalyserLogic):
    """
    this class contains all the logic needed to visualise
    the anatomical segmentation
    """
    _anatomicalSegmentationName: str = "_AnatomicalSegmentation_"
    _midSurfaceName: str = "_MedialSurface_"
    _segmentNames: list[str] = ["Dentin", "Enamel"]
    _fileTypes: tuple[str] = (".ISQ", ".mhd", ".nrrd", "nii")

    def __str__(self):
        return "Anatomical Segmentation"


    def error(self, msg: str) -> None:
        slicer.util.errorDisplay(msg)

    def warning(self, msg: str) -> None:
        slicer.util.warningDisplay(msg)

    def collectFiles(self, path: str, suffix: tuple) -> list:
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
        if os.path.exists(path):
            files = sorted([f for f in os.listdir(path) if f.endswith(suffix)])
        return files

    def createSegmentation(self, labelMapNode: vtkMRMLLabelMapVolumeNode,
                           deleteLabelMapNode: bool,
                           currentImageName: str) -> None:
        """
        Generates a segmentationNode from a given labelNode.
        After generation the segmentationNode will get some properties
        @param labelMapNode: The labelNode to be segmented
        @param deleteLabelMapNode: Decides whether the given labelNode should be deleted after segmentation
        @param currentImageName: the name of the segmented image, so give the segmentation a unique name
        @example:
            cls.createSegmentation(labelImageNode, True, currentImageName)
        """
        try:
            # create segmentation
            seg = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
            slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(labelMapNode, seg)
            seg.CreateClosedSurfaceRepresentation()

            # set properties for segmentation
            seg.SetName(currentImageName + self._anatomicalSegmentationName)
            default_names = self._segmentNames

            # set properties for segmentation
            num_segments = seg.GetSegmentation().GetNumberOfSegments()
            for i in range(num_segments):
                if i < len(default_names):
                    segment_name = default_names[i]
                    if segment_name == "Enamel":
                        seg.GetSegmentation().GetNthSegment(i).SetColor(0.435, 0.722, 0.824)
                    if segment_name == "Dentin":
                        seg.GetSegmentation().GetNthSegment(i).SetColor(1.0, 1.0, 0.8)
                else:
                    segment_name = f"Segment {i + 1}"
                seg.GetSegmentation().GetNthSegment(i).SetName(segment_name)

            # delete the given labelNode
            if deleteLabelMapNode:
                slicer.mrmlScene.RemoveNode(labelMapNode)
        except Exception as e:
            self.error(f"Error while creating the segmentation! {e}")


    def createMedialSurface(self, midSurfaceDentinLabelMapNode: vtkMRMLLabelMapVolumeNode,
                            midSurfaceEnamelLabelMapNode: vtkMRMLLabelMapVolumeNode,
                            currentImageName: str,
                            deleteLabelMapNodes: bool) -> None:
        """
        This method creates a segmentation for the given medial surface
        @param midSurfaceDentinLabelMapNode: the dentin label map image to be segmented
        @param midSurfaceEnamelLabelMapNode: the enamel label map image to be segmented
        @param deleteLabelMapNodes: True if labeImage should be deleted after segmentation
        @param currentImageName: the name of the segmented image, so give the segmentation a unique name
        @example:
            currentImageName = 'P01A-C0005278'
            cls.createMedialSurface(dentinMidSurfaceNode, enamelMidSurfaceNode, True, currentImageName)
        """
        try:
            # create dentin medial surface segmentation
            segDentin = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
            slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(midSurfaceDentinLabelMapNode, segDentin)
            segDentin.SetName("MedialSurface_source")

            if segDentin.GetSegmentation().GetNumberOfSegments() > 0:
                segDentin.GetSegmentation().GetNthSegment(0).SetName(self._segmentNames[0])
                segDentin.GetSegmentation().GetNthSegment(0).SetColor(1.0, 0.0, 0.0)
                slicer.mrmlScene.RemoveNode(midSurfaceDentinLabelMapNode)

            # create enamel medial surface segmentation
            segEnamel = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
            slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(midSurfaceEnamelLabelMapNode, segEnamel)
            print("Midname: " + currentImageName)
            segEnamel.SetName(currentImageName + self._midSurfaceName)

            if segEnamel.GetSegmentation().GetNumberOfSegments() > 0:
                segEnamel.GetSegmentation().GetNthSegment(0).SetName(self._segmentNames[1])
                segEnamel.GetSegmentation().GetNthSegment(0).SetColor(0.0, 1.0, 0.0)
                slicer.mrmlScene.RemoveNode(midSurfaceEnamelLabelMapNode)

            # copy all segments from dentin to enamel and delete dentin
            for i in range(segDentin.GetSegmentation().GetNumberOfSegments()):
                source_segment = segDentin.GetSegmentation().GetNthSegment(i)
                segment_id = segDentin.GetSegmentation().GetSegmentIdBySegment(source_segment)
                segEnamel.GetSegmentation().CopySegmentFromSegmentation(segDentin.GetSegmentation(), segment_id, True)
            slicer.mrmlScene.RemoveNode(getNode("MedialSurface_source"))

            if deleteLabelMapNodes:
                slicer.mrmlScene.RemoveNode(midSurfaceEnamelLabelMapNode)
                slicer.mrmlScene.RemoveNode(midSurfaceDentinLabelMapNode)
        except Exception as e:
            self.error(f"Error while creating the medial surfaces! {e}")

    def clearScene(self) -> None:
        """
        Deletes all nodes from the scene, that where generated
        by the algorithm.
        @param currentImageName: the image to be segmented
        @return: None
        @example:
            imgNode = 'P01A-C0005278.ISQ'
            cls.clearScene(imgNode)
        """
        try:
            anatomicalSegmentation = getNode("*" + self._anatomicalSegmentationName)
            slicer.mrmlScene.RemoveNode(anatomicalSegmentation)

            midSurface = getNode("*" + self._midSurfaceName)
            slicer.mrmlScene.RemoveNode(midSurface)
        except:
            pass

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
        except:
            pass

    def createDirectory(self, path: str, directoryName: str) -> str:
        """
        Creates a directory with the given name in the given path if
        there is no directory with this name.
        :param path: The path where the directory needs to be added
        :param directoryName: The name of the new directory
        :return targetDirectory: The absolut path to the created directory
        """
        targetDirectory = path + directoryName + "/"
        try:
            os.makedirs(targetDirectory, exist_ok=True)
        except Exception as e:
            self.error(f"Error while creating directory: {e}")
        return targetDirectory

    def createTemporaryStorageNode(self, param):
        """

        @param param:
        @return:
        """
        tempPath = slicer.app.temporaryPath
        print("temp pfad: ", tempPath)
        fileName = (param.currentImage.GetName() + ".nrrd")
        filePath = os.path.join(tempPath, fileName)
        storageNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLVolumeArchetypeStorageNode")
        storageNode.SetFileName(filePath)
        param.currentImage.SetAndObserveStorageNodeID(storageNode.GetID())
        storageNode.WriteData(param.currentImage)

    def createLabelMapNode(self, itkImage, labelMapName: str) -> any:
        """

        @param itkImage:
        @param labelMapName:
        @return:
        """
        return sitkUtils.PushVolumeToSlicer(itkImage, None, labelMapName, "vtkMRMLLabelMapVolumeNode")

    def runSegmentationPipeline(self, param: ToothAnalyserParameterNode, progressBar) -> dict:
        """

        @param param:
        @param progressBar:
        @return:
        """
        from ToothAnalyserLib.AnatomicalSegmentation.Segmentation import calcSegmentationGen

        segmentationType = param.anatomical.selectedAnatomicalAlgo.lower()

        try:
            sourcePath = param.currentImage.GetStorageNode().GetFullNameFromFileName()
        except Exception:
            self.createTemporaryStorageNode(param)
            sourcePath = param.currentImage.GetStorageNode().GetFullNameFromFileName()

        param.status = "Start der Verarbeitung..."
        slicer.app.processEvents()

        segmentationStep = calcSegmentationGen(
            sourcePath=sourcePath,
            selectedAlgorithm=param.anatomical.selectedAnatomicalAlgo,
            calcMedialSurfaces=param.anatomical.calcMidSurface)

        while True:
            result = next(segmentationStep)

            if isinstance(result, dict):
                print("Fertig!")
                toothDict = result
                break
            else:
                progressBar.value = result
                slicer.app.processEvents()

        # Ergebnisse extrahieren
        results = {
            "segmentationType": segmentationType,
            "enamelMidSurface": toothDict.get(f"enamel_{segmentationType}_{segmentationType}_midsurface"),
            "dentinMidSurface": toothDict.get(f"dentin_{segmentationType}_{segmentationType}_midsurface"),
            "labelImage": toothDict.get(f"segmentation_{segmentationType}_{segmentationType}_labels"),
            "imageName": toothDict.get("name", param.currentImage.GetName())
        }

        return results

    def loadResultsToScene(self, results: dict, param: ToothAnalyserParameterNode) -> None:
        """

        @param results:
        @param param:
        @return:
        """
        self.clearScene()

        labelNode = self.createLabelMapNode(results["labelImage"], "tempLabel")
        self.createSegmentation(
            labelMapNode=labelNode,
            deleteLabelMapNode=True,
            currentImageName=results["imageName"])

        if results["enamelMidSurface"] or results["dentinMidSurface"]:
            dentinNode = self.createLabelMapNode(results["dentinMidSurface"], "tempDentin")
            enamelNode = self.createLabelMapNode(results["enamelMidSurface"], "tempEnamel")
            self.createMedialSurface(
                midSurfaceDentinLabelMapNode=dentinNode,
                midSurfaceEnamelLabelMapNode=enamelNode,
                currentImageName=results["imageName"],
                deleteLabelMapNodes=True)

    def execute(self, param: ToothAnalyserParameterNode, progressBar) -> None:
        """

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
        print(f"Verarbeitung abgeschlossen in: {duration // 60:.0f} Minuten und {duration % 60:.0f} Sekunden")

    def executeAsBatch(self, param: ToothAnalyserParameterNode, progressBar) -> None:
        """
        This method starts the pipeline to compute all files in batch process
        @param param: all parameters from the user interface (UI)
        @return: None
        @example:
            AnatomicalSegmentationLogic.executeAsBatch(param=self._param)
        """
        from ToothAnalyserLib.AnatomicalSegmentation.Segmentation import parseName, writeToothDict, calcSegmentationGen

        # create local variables for all parameters
        if not os.path.isdir(param.batch.sourcePath):
            slicer.util.errorDisplay("The given source path is not an directory.")
            return
        if not os.path.isdir(param.batch.targetPath):
            slicer.util.errorDisplay("The given target path is not an directory.")
            return
        sourcePath = param.batch.sourcePath
        targetPath = param.batch.targetPath
        segmentationType = param.anatomical.selectedAnatomicalAlgo
        fileType = param.batch.fileType
        files = self.collectFiles(sourcePath, self._fileTypes)
        numOfFiles = len(files)
        param.status = "detecting " + str(numOfFiles) + "files"

        # Create result directory
        targetDirectory = self.createDirectory(
            path=targetPath,
            directoryName=self._anatomicalSegmentationName + segmentationType)

        # Delete the old segmentation to keep order
        self.clearDirectory(targetDirectory)

        for file in files:
            fileName = parseName(file)
            fullFilePath = sourcePath + "/" + file

            # create directory for each File to be calculated
            targetFileDirectory = self.createDirectory(
                path=targetDirectory,
                directoryName=fileName)

            segmentationStep = calcSegmentationGen(
                sourcePath=sourcePath,
                selectedAlgorithm=param.anatomical.selectedAnatomicalAlgo,
                calcMedialSurfaces=param.anatomical.calcMidSurface)

            while True:
                result = next(segmentationStep)

                if isinstance(result, dict):
                    print("Fertig!")
                    toothDict = result
                    break
                else:
                    progressBar.value = result
                    slicer.app.processEvents()

            writeToothDict(
                tooth=toothDict,
                path=targetFileDirectory,
                calcMidSurface=param.anatomical.calcMidSurface,
                fileType=param.batch.fileType)
            toothDictName = toothDict['name']


class CariesSegmentation(ToothAnalyserLogic):
    def __str__(self):
        """
        This methode provides the visible name in the
        section Segmentation
        @return:
        """
        return "Caries Segmentation"

    def execute(self, param: ToothAnalyserParameterNode, progressBar):
        self.preprocessing()
        print("execute Caries Segmentation ...")
        self.postprocessing()

    def executeAsBatch(self, param: ToothAnalyserParameterNode, progressBar):
        self.preprocessing()
        print("execute Caries Segmentation as Batch ...")
        self.postprocessing()



# ----- Tooth Analyser Tests ----- #
class ToothAnalyserTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()
        self.loadSampleData()

    def loadSampleData(self):
        import SampleData
        self.delayDisplay("loading sample data. This will take some minutes...")
        return SampleData.downloadSample('ToothCrownMicroCT')

    def getSampleDataAsITK(self):
        node = slicer.util.getFirstNodeByName("ToothCrownMicroCT")
        self.delayDisplay("Setting up test suit...")
        return sitkUtils.PullVolumeFromSlicer(node)

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.testValidateBatchSettingsOneEnabled()
        self.testValidateBatchSettingsOneDisabled()
        self.testParsName()
        self.testParseType()
        self.testCast8UInt()
        self.testPixelType()
        #self.testSmoothImage() # takes a lot of time
        self.testIsSmoothed()

    def testCreateDirectory(self):
        path = "/data/test/"
        directoryName = "new_folder"
        expectedDirectory = "/data/test/new_folder/"
        anatomicalSeg = AnatomicalSegmentationLogic()
        result = anatomicalSeg.createDirectory(path, directoryName)

        self.assertEqual(result, expectedDirectory)
        self.delayDisplay("Test 2 passed")

    def testValidateBatchSettingsOneEnabled(self):
        from unittest.mock import MagicMock

        self.mockedClass = MagicMock()
        params = {
            "option1": False,
            "option2": True,
            "option3": False
        }
        result = self.mockedClass.validateBatchSettings(params)

        self.assertTrue(result)
        self.delayDisplay("Test 3 passed")

    def testValidateBatchSettingsOneDisabled(self):
        from unittest.mock import MagicMock

        self.mockedClass = MagicMock()
        params = {
            "option1": False,
            "option2": False,
            "option3": False
        }
        result = self.mockedClass.validateBatchSettings(params)

        self.assertTrue(result)
        self.delayDisplay("Test 4 passed")

    def testParsName(self):
        from ToothAnalyserLib.AnatomicalSegmentation.Segmentation import parseName

        path = "/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ"
        expectation = "P01A-C0005278"
        result = parseName(path)
        self.assertEqual(result, expectation)

        path = "/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ"
        expectation = "P01A-C0005278.ISQ"
        result = parseName(path)
        self.assertNotEqual(result, expectation)

        self.delayDisplay("Test 5 passed")

    def testParseType(self):
        from ToothAnalyserLib.AnatomicalSegmentation.Segmentation import parseTyp

        path = "/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ"
        expectation = "isq"
        result = parseTyp(path)
        self.assertEqual(expectation, result)

        path = "/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ"
        expectation = "ISQ"
        result = parseTyp(path)
        self.assertNotEqual(expectation, result)

        self.delayDisplay("Test 6 passed")

    def testCast8UInt(self):
        from ToothAnalyserLib.AnatomicalSegmentation.Segmentation import cast8UInt

        sampleData = self.getSampleDataAsITK()
        beforeCast = sampleData.GetPixelID()
        imageCast = cast8UInt(sampleData)
        afterCast = imageCast.GetPixelID()

        self.assertNotEqual(beforeCast, afterCast)
        self.delayDisplay("Test 7 passed")

    def testPixelType(self):
        from ToothAnalyserLib.AnatomicalSegmentation.Segmentation import pixelType

        sampleDate = self.getSampleDataAsITK()
        expectation = sampleDate.GetPixelIDTypeAsString()
        result = pixelType(sampleDate)

        self.assertEqual(expectation, result)
        self.delayDisplay("Test 8 passed")

    def testSmoothImage(self):
        from ToothAnalyserLib.AnatomicalSegmentation.Segmentation import smoothImage
        import numpy as np
        import SimpleITK as sitk

        sampleData = self.getSampleDataAsITK()
        self.delayDisplay("filtering image...")
        sampleDataFiltered = smoothImage(sampleData)

        sampleData_std_dev = np.std(sitk.GetArrayFromImage(sampleData))
        sampleDataFiltered_std_dev = np.std(sitk.GetArrayFromImage(sampleDataFiltered))

        self.assertTrue(sampleDataFiltered_std_dev < sampleData_std_dev)
        self.delayDisplay("Test 9 passed")

    def testIsSmoothed(self):
        from ToothAnalyserLib.AnatomicalSegmentation.Segmentation import isSmoothed

        sampleDate = self.getSampleDataAsITK()
        result = isSmoothed(sampleDate)

        self.assertFalse(result)
        self.delayDisplay("Test 10 passed")