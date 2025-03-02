import logging
import os

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

# load images for Help and Acknowledgement
scriptDir = os.path.dirname(__file__)
projectRoot = os.path.abspath(os.path.join(scriptDir, ".."))
relativePathLogo = os.path.join(projectRoot, "Screenshots", "logo.png")
relativePathTHA = os.path.join(projectRoot, "Screenshots", "logoTHA.png")
relativePathLMU = os.path.join(projectRoot, "Screenshots", "logoLMU.svg")


##################################################
# Tooth Analyser
##################################################
class ToothAnalyser(ScriptedLoadableModule):
    """ This Class holds all meta information about this module
    and add the connection to the 3D Slicer core application.
    As a child class of "ScriptedLoadableModule" all methods from
    this class can be used."""

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("Tooth Analyser")
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Segmentation")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
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
        slicer.app.connect("startupCompleted()", registerSampleData)


##################################################
# Register sample data for the module tests
##################################################
def registerSampleData():
    """
    This Methode provides sample Data for the module tests
    To ensure that the source code repository remains small
    (can be downloaded and installed quickly) it is recommended to
    store data sets that are larger than a few MB in a GitHub release.
    """
    import SampleData
    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # fist sample CT -> ToothAnalyser1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        category="ToothAnalyser",
        sampleName="ToothAnalyser1",
        thumbnailFileName=os.path.join(iconsPath, "ToothAnalyser1.png"),
        # path to sample image
        uris="https://github.com/lukaskonietzka/ToothAnalyserSampleData/releases/download/v1.0.0/P01A-C0005278.nii.gz",
        fileNames="P01A-C0005278.nii.gz",
        checksums=None,
        nodeNames="ToothAnalyser1",
    )


##################################################
# Tooth Analyser Parameter Node
##################################################
@parameterPack
class AnalyticalParameters:
    """
    The parameters needed by the section
    Analytics
    """
    currentAnalyticalVolume: vtkMRMLScalarVolumeNode
    showHistogram: bool
    useAnalyticForBatch: bool

@parameterPack
class AnatomicalParameters:
    """
    The parameters needed by the section
    Anatomical Segmentation
    """
    currentAnatomicalVolume: vtkMRMLScalarVolumeNode
    selectedAnatomicalAlgo: Annotated[str, Choice(["Otsu", "Renyi"])] = "Otsu"
    calcMidSurface: bool
    useAnatomicalForBatch: bool

@parameterPack
class Batch:
    """
    The parameters needed by the section
    Batch Processy ing
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
    analytical: AnalyticalParameters
    anatomical: AnatomicalParameters
    batch: Batch
    status: str = ""


##################################################
# Tooth Analyser Widget
##################################################
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
        self.ui.applyAnalytics.connect("clicked(bool)", self.onApplyAnalyticsButton)
        self.ui.applyAnatomical.connect("clicked(bool)", self.onApplyAnatomicalButton)
        self.ui.applyBatch.connect("clicked(bool)", self.onApplyBatchButton)

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
        if not self._param.anatomical.currentAnatomicalVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._param.anatomical.currentAnatomicalVolume = firstVolumeNode

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._param.analytical.currentAnalyticalVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._param.analytical.currentAnalyticalVolume = firstVolumeNode

        # default settings for the parameters
        self.ui.showHistogram.checked = True
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
        self.handleApplyBatchButton()
        self.handleApplyAnalyticsButton()
        self.handleApplyAnatomicalButton()

    def handleApplyBatchButton(self):
        """
        This methode check if there is exactly one
        enabled checkbox for the batch process.
        """
        if not self.validateBatchSettings(
            paramsToCheck={
                "analytics": self._param.analytical.useAnalyticForBatch,
                "anatomical": self._param.anatomical.useAnatomicalForBatch})\
            or not self._param.batch.sourcePath or not self._param.batch.targetPath:
                self.ui.applyBatch.enabled = False
        elif self.ui.status.isVisible():
            self.ui.applyBatch.enabled = False
        else:
            self.ui.applyBatch.enabled = True

    def handleApplyAnalyticsButton(self):
        """
        Enable the "Apply Analytical" Button, if an image is
        loaded to the scene.
        """
        if not self._param.analytical.currentAnalyticalVolume:
            self.ui.applyAnalytics.enabled = False
        elif self.ui.status.isVisible():
            self.ui.applyAnalytics.enabled = False
        else:
            self.ui.applyAnalytics.enabled = True

    def handleApplyAnatomicalButton(self):
        """
        Enable the "Apply Anatomical" Button, if an image is
        loaded to the scene.
        """
        if not self._param.anatomical.currentAnatomicalVolume:
            self.ui.applyAnatomical.enabled = False
        elif self.ui.status.isVisible():
            self.ui.applyAnatomical.enabled = False
        else:
            self.ui.applyAnatomical.enabled = True

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

        self.ui.applyAnalytics.enabled = not isVisible
        self.ui.applyAnatomical.enabled = not isVisible
        self.ui.applyBatch.enabled = not isVisible

        self.ui.status.setVisible(isVisible)
        self.ui.progressBar.setVisible(isVisible)
        self.ui.progressBar.enabled = isVisible

        #self.handleApplyBatchButton()
        self.handleApplyAnalyticsButton()
        self.handleApplyAnatomicalButton()

        slicer.app.processEvents()

    def onApplyAnalyticsButton(self) -> None:
        """
        Run the analytical processing in an error display
        when user clicks "Apply Analytics" Button.
        """
        self._param.status = "start analytics..."
        self.activateComputingMode(True)
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            Analytics.execute(self._param)
        self.activateComputingMode(False)

    def onApplyAnatomicalButton(self) -> None:
        """
        Run the anatomical segmentation processing in an error display
        when user clicks "Apply Analytics" Button.
        """
        self._param.status = "start anatomical segmentation..."
        self.activateComputingMode(True)
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            slicer.util.warningDisplay("""The anatomical segmentation may take up to 17 minutes, depending on the image and your local machine.""")
            try:
                AnatomicalSegmentationLogic.execute(param=self._param)
            except:
                slicer.util.errorDisplay("""An error occurred while processing the image. Please note
                    that this module is specifically designed for CT scans of teeth."""
                )
            print("anatomical")
        self.activateComputingMode(False)

    def onApplyBatchButton(self) -> None:
        """
        Run the batch processing in an error display
        when user clicks "Apply Batch" button.
        """
        self.activateComputingMode(True)
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            if self._param.analytical.useAnalyticForBatch:
                Analytics.executeAsBatch(param=self._param)
                self.activateComputingMode(False)
            elif self._param.anatomical.useAnatomicalForBatch:
                slicer.util.warningDisplay("""The Batch processing of the anatomical segmentation may take a lot of resources on your local machine.""")
                AnatomicalSegmentationLogic.executeAsBatch(param=self._param)
        self.activateComputingMode(False)


##################################################
# Tooth Analyser Logic
##################################################
class ToothAnalyserLogic(ScriptedLoadableModuleLogic):
    """ This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """ Called when the logic class is instantiated.
        Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self) -> ToothAnalyserParameterNode:
        """
        Getter methode for the ParameterNode needed in the logic class
        return: The ParameterNode from this module
        """
        return ToothAnalyserParameterNode(super().getParameterNode())

    def preProcessing(self) -> None:
        """Implement your pre processing here"""
        pass

    def postProcessing(self) -> None:
        """Implement your post processing here"""
        pass

    def execute(self, param: ToothAnalyserParameterNode) -> None:
        """Abstract method"""
        raise NotImplementedError("Please implement the execute() methode in one of the child classes")

    def executeAsBatch(self, param: ToothAnalyserParameterNode) -> None:
        """Abstract method"""
        raise NotImplementedError("Please implement the executeAsBatch() methode in one of the child classes")


###########################################
#     Tooth Analyser section Analytics     #
###########################################
class Analytics(ToothAnalyserLogic):
    """
    this class contains all the logic needed to visualise
    the analytics
    """

    @classmethod
    def _showHistogram(cls, image: vtkMRMLScalarVolumeNode) -> None:
        """
        This Methode creates a histogram from the current selected Volume
        @param image: the image for which a histogram is required
        """
        import numpy as np
        from collections import namedtuple

        AxisFitting = namedtuple('AxisFitting', ['x', 'y'])
        axes = AxisFitting(x="Intensity", y="Frequency")

        # create histogram data
        imageData = slicer.util.arrayFromVolume(image)
        histogram = np.histogram(imageData, bins= 200)

        # create plot
        chartNode = slicer.util.plot(
            narray=histogram,
            xColumnIndex=1,
            columnNames=[axes.x, axes.y],
            title=image.GetName() + "_Histogram")

        # set properties for chartNode
        chartNode.SetTitle("Histogram of Image: " + image.GetName())
        chartNode.SetYAxisTitle(axes.y)
        chartNode.SetXAxisTitle(axes.x)
        chartNode.SetLegendVisibility(True)
        chartNode.SetYAxisRange(0, 100)
        chartNode.SetXAxisRange(0, 100)
        # set properties for  plot series
        plotSeries = getNode("*PlotSeries*")
        plotSeries.SetName(axes.y)

    @classmethod
    def execute(cls, param: ToothAnalyserParameterNode) -> None:
        """
        This method is an abstract method form the parent class
        ToothAnalyserLogic. It is implementing the algorithm
        for the analytics
        """
        if param.analytical.showHistogram:
            param.status = "calculate histogram"
            cls._showHistogram(param.analytical.currentAnalyticalVolume)

    @classmethod
    def executeAsBatch(cls, param: ToothAnalyserParameterNode) -> None:
        print("Analytics as Batch")
        print(type(param.batch.fileType))


##################################################
# Tooth Analyser section Anatomical Segmentation
##################################################
class AnatomicalSegmentationLogic(ToothAnalyserLogic):
    """
    this class contains all the logic needed to visualise
    the anatomical segmentation
    """
    _anatomicalSegmentationName: str = "_AnatomicalSegmentation_"
    _midSurfaceName: str = "_MedialSurface_"
    _segmentNames: list[str] = ["Dentin", "Enamel"]
    _fileTypes: tuple[str] = (".ISQ", ".mhd", ".nrrd", "nii")

    @classmethod
    def collectFiles(cls, path: str, suffix: tuple) -> list:
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

    @classmethod
    def createSegmentation(cls, labelMapNode: vtkMRMLLabelMapVolumeNode,
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
        # create segmentation
        seg = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
        slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(labelMapNode, seg)
        seg.CreateClosedSurfaceRepresentation()

        # set properties for segmentation
        seg.SetName(currentImageName + cls._anatomicalSegmentationName)
        default_names = cls._segmentNames

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

    @classmethod
    def createMedialSurface(cls, midSurfaceDentinLabelMapNode: vtkMRMLLabelMapVolumeNode,
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
        # create dentin medial surface segmentation
        segDentin = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
        slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(midSurfaceDentinLabelMapNode, segDentin)
        segDentin.SetName("MedialSurface_source")

        if segDentin.GetSegmentation().GetNumberOfSegments() > 0:
            segDentin.GetSegmentation().GetNthSegment(0).SetName(cls._segmentNames[0])
            segDentin.GetSegmentation().GetNthSegment(0).SetColor(1.0, 0.0, 0.0)
            slicer.mrmlScene.RemoveNode(midSurfaceDentinLabelMapNode)

        # create enamel medial surface segmentation
        segEnamel = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
        slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(midSurfaceEnamelLabelMapNode, segEnamel)
        print("Midname: " + currentImageName)
        segEnamel.SetName(currentImageName + cls._midSurfaceName)

        if segEnamel.GetSegmentation().GetNumberOfSegments() > 0:
            segEnamel.GetSegmentation().GetNthSegment(0).SetName(cls._segmentNames[1])
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

    @classmethod
    def clearScene(cls, currentImageName: str) -> None:
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
            anatomicalSegmentation = getNode("*" + cls._anatomicalSegmentationName)
            slicer.mrmlScene.RemoveNode(anatomicalSegmentation)

            midSurface = getNode("*" + cls._midSurfaceName)
            slicer.mrmlScene.RemoveNode(midSurface)
        except:
            pass

    @classmethod
    def clearDirectory(cls, path: str) -> None:
        """
        Delete all files in the given directory
        @param path: path to the directory to be cleaned
        @example:
            path = "/data/MicroCT/Original_ISQ/Results"
            cls.clearDirectory(path)
        """
        import shutil
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
            print(f"Error while cleaning directory '{path}': {e}")
            slicer.util.errorDisplay("Error while cleaning directory")

    @classmethod
    def createDirectory(cls, path: str, directoryName: str) -> str:
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
            print(f"Error while creating directory: {e}")
        return targetDirectory

    @classmethod
    def createTemporaryStorageNode(cls, param):
        tempPath = slicer.app.temporaryPath
        print("temp pfad: ", tempPath)
        fileName = param.anatomical.currentAnatomicalVolume.GetName() + ".nrrd"
        filePath = os.path.join(tempPath, fileName)
        storageNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLVolumeArchetypeStorageNode")
        storageNode.SetFileName(filePath)
        param.anatomical.currentAnatomicalVolume.SetAndObserveStorageNodeID(storageNode.GetID())
        storageNode.WriteData(param.anatomical.currentAnatomicalVolume)

    @classmethod
    def createLabelMapNode(cls, itkImage, labelMapName: str) -> any:
        return sitkUtils.PushVolumeToSlicer(itkImage, None, labelMapName, "vtkMRMLLabelMapVolumeNode")

    @classmethod
    def calcPipeline(cls, sourcePath: str, calcMidSurface: bool, param: ToothAnalyserParameterNode) -> dict:
        """
        This method forms the complete pipeline for the calculation of smoothing,
        labels and medial surfaces. It is very large but therefore the clearest
        @param sourcePath: the path to the file that should be entered in the pipeline
        @param calcMidSurface: the path to the directory where the generated images are saved in the file system
        @param param: parameters from the UI
        @return: the full created tooth dictionary with all images
        @example:
            path = '/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ'
            targetPath = '/data/MicroCT/Original_ISQ/anatomicalSegmentationOtsu/'
            tooth_dict = pipe_full_dict_selection(path, param)
        """

        from ToothAnalyserLib.AnatomicalSegmentation.Segmentation import (
            loadImage, isSmoothed, smoothImage, imageMask, smoothImageMask, enamelSelect, enamelSmoothSelect,
            enamelLayering, enamelPreparation, enamelFilling, additionalEnamelFilling, dentinLayers,
            segmentationLabels, enamelMidSurface, dentinMidSurface)

        # 1. load and filter image
        img, name = loadImage(sourcePath)
        print("type: ", img.GetPixelIDTypeAsString())
        param.status = "loading image " + name + "..."
        slicer.app.processEvents()

        if isSmoothed(img):
            img_smooth = img
        else:
            param.status = "smoothing image..."
            slicer.app.processEvents()
            img_smooth = smoothImage(img)

        # 2. extract the tooth from the background
        param.status = "extracting tooth from background..."
        slicer.app.processEvents()
        tooth, tooth_masked = imageMask(img, img_smooth)
        tooth_smooth_masked = smoothImageMask(img_smooth, tooth)
        # 3. select enamel area
        param.status = "extracting enamel segment from tooth..."
        slicer.app.processEvents()
        enamel_select = enamelSelect(param.anatomical.selectedAnatomicalAlgo, tooth_masked)
        enamel_smooth_select = enamelSmoothSelect(param.anatomical.selectedAnatomicalAlgo, tooth_smooth_masked)

        # 4. stack the enamels
        param.status = "creating enamel segment..."
        slicer.app.processEvents()
        enamel_layers = enamelLayering(enamel_select, enamel_smooth_select)

        # 5. Prepare the enamel
        param.status = "smoothing enamel segment..."
        slicer.app.processEvents()
        enamel_layers_extended_smooth_2 = enamelPreparation(enamel_layers)

        # 6. Filling of small structures within the tooth
        param.status = "filling structures on enamel segment..."
        slicer.app.processEvents()
        contour_extended, enamel_layers_extended_smooth_3 = enamelFilling(enamel_layers_extended_smooth_2, tooth)

        # 7. Filling of small structures within the tooth, important with many datasets
        param.status = "filling structures on enamel segment..."
        slicer.app.processEvents()
        enamel_layers = additionalEnamelFilling(enamel_layers, enamel_layers_extended_smooth_3)

        # 8. generate dentin segment
        param.status = "extracting dentin segment from tooth..."
        slicer.app.processEvents()
        dentin_layers = dentinLayers(contour_extended, enamel_layers, tooth)

        # 9. generate label file for segmentation
        param.status = "creating segmentation labels..."
        slicer.app.processEvents()
        segmentation_labels = segmentationLabels(dentin_layers, enamel_layers)

        # 10. generating medial surface for enamel and dentin if needed
        if calcMidSurface:
            param.status = "creating medial surfaces enamel..."
            slicer.app.processEvents()
            enamel_midsurface = enamelMidSurface(enamel_layers)
            param.status = "creating medial surfaces dentin..."
            slicer.app.processEvents()
            dentin_midsurface = dentinMidSurface(dentin_layers)
        else:
            enamel_midsurface = None
            dentin_midsurface = None

        # 11. generate tooth dictionary to store all generated data sets local
        filt_1 = param.anatomical.selectedAnatomicalAlgo.lower()
        filt_2 = param.anatomical.selectedAnatomicalAlgo.lower()

        enamel_key = 'enamel_' + filt_1
        enamel_smooth_key = 'enamel_smooth_' + filt_2
        enamel_layers_key = 'enamel_' + filt_1 + '_' + filt_2 + '_layers'
        dentin_layers_key = 'dentin_' + filt_1 + '_' + filt_2 + '_layers'
        segmentation_labels_key = 'segmentation_' + filt_1 + '_' + filt_2 + '_labels'
        enamel_midsurface_key = 'enamel_' + filt_1 + '_' + filt_2 + '_midsurface'
        dentin_midsurface_key = 'dentin_' + filt_1 + '_' + filt_2 + '_midsurface'

        tooth_dict = {
            'path': sourcePath,
            'name': name,
            'img': img,
            'img_smooth': img_smooth,
            'tooth': tooth,
            enamel_key: enamel_select,
            enamel_smooth_key: enamel_smooth_select,
            enamel_layers_key: enamel_layers,
            dentin_layers_key: dentin_layers,
            segmentation_labels_key: segmentation_labels,
            enamel_midsurface_key: enamel_midsurface,
            dentin_midsurface_key: dentin_midsurface
        }
        return tooth_dict

    @classmethod
    def execute(cls, param: ToothAnalyserParameterNode) -> None:
        """
        This methode starts the pipeline to compute the output
        of one file and load it into the slicer scene
        @param param: all parameter from the user interface (UI)
        @return: None
        @example:
            AnatomicalSegmentationLogic.execute(param=self._param)
        """
        import time

        start = time.time()
        logging.info("Processing started")

        segmentationType = param.anatomical.selectedAnatomicalAlgo
        currentImageNameWithTyp = param.anatomical.currentAnatomicalVolume.GetName()
        try:
            sourcePath = param.anatomical.currentAnatomicalVolume.GetStorageNode().GetFullNameFromFileName()
        except:
            cls.createTemporaryStorageNode(param)
            sourcePath = param.anatomical.currentAnatomicalVolume.GetStorageNode().GetFullNameFromFileName()

        param.status = "start processing..."
        slicer.app.processEvents()

        #Calculate Anatomical Segmentation by executing pipeline
        toothDict = cls.calcPipeline(
            sourcePath=sourcePath, #path to file
            calcMidSurface=param.anatomical.calcMidSurface,
            param=param,)

        # extract itk images from the calculated tooth dictionary
        segmentationType = segmentationType.lower()
        enamelMidSurfaceITK = toothDict["enamel_" + segmentationType + "_" + segmentationType + "_midsurface"]
        dentinMidSurfaceITK = toothDict["dentin_" + segmentationType + "_" + segmentationType + "_midsurface"]
        labelImageITK = toothDict["segmentation_" + segmentationType + "_" + segmentationType + "_labels"]
        currentImageName = toothDict["name"]

        # Delete unused nodes from the scene
        cls.clearScene(currentImageName=currentImageNameWithTyp)

        try:
            # try to create the segmentation based on the label image
            cls.createSegmentation(
                labelMapNode=cls.createLabelMapNode(labelImageITK, "tempLabel"),
                deleteLabelMapNode=True,
                currentImageName=currentImageName)

            # try to create medial surfaces if there were calculated
            if enamelMidSurfaceITK is not None or dentinMidSurfaceITK is not None:
                cls.createMedialSurface(
                    midSurfaceDentinLabelMapNode=cls.createLabelMapNode(dentinMidSurfaceITK, "tempDentin"),
                    midSurfaceEnamelLabelMapNode=cls.createLabelMapNode(enamelMidSurfaceITK, "tempEnamel"),
                    currentImageName=currentImageName,
                    deleteLabelMapNodes=True)
        except:
            slicer.util.errorDisplay("""An error occurred while processing the image.
                Please note that this module is specifically designed for CT scans of teeth."""
            )

        stop = time.time()
        print("Processing completed in: ", f" {(stop - start) // 60:.0f} minutes and {(stop - start) % 60:.0f} seconds")


    @classmethod
    def executeAsBatch(cls, param: ToothAnalyserParameterNode) -> None:
        """
        This method starts the pipeline to compute all files in an batch process
        @param param: all parameters from the user interface (UI)
        @return: None
        @example:
            AnatomicalSegmentationLogic.executeAsBatch(param=self._param)
        """
        from ToothAnalyserLib.AnatomicalSegmentation.Segmentation import parseName, writeToothDict

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
        files = cls.collectFiles(sourcePath, cls._fileTypes)
        numOfFiles = len(files)
        param.status = "detecting " + str(numOfFiles) + "files"

        # Create result directory
        targetDirectory = cls.createDirectory(
            path=targetPath,
            directoryName=cls._anatomicalSegmentationName + segmentationType)

        # Delete the old segmentation to keep order
        cls.clearDirectory(targetDirectory)

        for file in files:
            fileName = parseName(file)
            fullFilePath = sourcePath + "/" + file
            # create directory for each File to be calculated
            targetFileDirectory = cls.createDirectory(
                path=targetDirectory,
                directoryName=fileName)

            toothDict = cls.calcPipeline(
                sourcePath=fullFilePath,
                calcMidSurface=param.anatomical.calcMidSurface,
                param=param)
            writeToothDict(tooth=toothDict,
                           path=targetFileDirectory,
                           calcMidSurface=param.anatomical.calcMidSurface,
                           fileType=param.batch.fileType)
            toothDictName = toothDict['name']


##################################################
# Tooth Analyser Tests
##################################################
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
        return SampleData.downloadSample('ToothAnalyser1')

    def getSampleDataAsITK(self):
        node = slicer.util.getFirstNodeByName("ToothAnalyser1")
        self.delayDisplay("Setting up test suit...")
        return sitkUtils.PullVolumeFromSlicer(node)

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.testHandleApplyAnalyticsButton()
        self.testCreateDirectory()
        self.testValidateBatchSettingsOneEnabled()
        self.testValidateBatchSettingsOneDisabled()
        self.testParsName()
        self.testParseType()
        self.testCast8UInt()
        self.testPixelType()
        self.testSmoothImage()
        self.testIsSmoothed()

    def testHandleApplyAnalyticsButton(self):
        """
        Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """
        from unittest.mock import MagicMock

        self.mockedClass = MagicMock()
        self.mockedClass.ui.applyAnalytics = MagicMock()
        self.mockedClass._param.analytical = MagicMock()

        self.mockedClass._param.analytical.currentAnalyticalVolume = None
        self.mockedClass.handleApplyAnalyticsButton()
        self.mockedClass.ui.applyAnalytics.enabled = False
        self.mockedClass._param.analytical.currentAnalyticalVolume = "SomeVolume"
        self.mockedClass.handleApplyAnalyticsButton()
        self.mockedClass.ui.applyAnalytics.enabled = True

        self.delayDisplay("Test 1 passed")

    def testCreateDirectory(self):

        path = "/data/test/"
        directoryName = "new_folder"
        expectedDirectory = "/data/test/new_folder/"
        result = AnatomicalSegmentationLogic.createDirectory(path, directoryName)

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
        import sitkUtils

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


