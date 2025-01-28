import logging
import os

from typing import Annotated, Optional

import vtk

import slicer
from MRMLCorePython import vtkMRMLLabelMapVolumeNode
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin, getNode, getNodes
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    Choice, parameterPack
)

from slicer import vtkMRMLScalarVolumeNode


##################################################
# Tooth Analyser Meta data
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
        self.parent.contributors = ["Lukas Konietzka (THA)", "Simon Hoffmann (THA)", "Prof. Dr. Peter Rösch (THA)"]
        self.parent.helpText = _("""This is an example of scripted loadable module bundled in an extension. See more
        information in <a href="https://github.com/organization/projectname#ToothAnalyser">module documentation</a>.""")
        self.parent.acknowledgementText = _("""This module was developed for the dental caries research of the Dental
        Clinic at the LMU in Munich. The development is a collaboration between the LMU and the THA""")

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


##################################################
# Register sample data for the module tests
##################################################
def registerSampleData():
    """Add data sets to Sample Data module."""
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # ToothAnalyser1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Kategorie und Name der Beispiel-Daten
        category="ToothAnalyser",
        sampleName="ToothAnalyser1",
        # Thumbnail-Bild
        thumbnailFileName=os.path.join(iconsPath, "ToothAnalyser1.png"),
        # Download-URL und Ziel-Dateiname
        uris="https://github.com/lukaskonietzka/ToothAnalyserSampleData/releases/download/v1.0.0/P01A-C0005278.nii.gz",
        fileNames="P01A-C0005278.nii.gz",  # Der heruntergeladene Dateiname
        # Überprüfungs-Hash (SHA256-Checksumme)
        checksums=None,
        # Der Name des Nodes, der beim Laden der Daten verwendet wird
        nodeNames="ToothAnalyser1",
    )

    # ToothAnalyser2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="ToothAnalyser",
        sampleName="ToothAnalyser2",
        thumbnailFileName=os.path.join(iconsPath, "ToothAnalyser2.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="ToothAnalyser2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="ToothAnalyser2",
    )


##################################################
# Tooth Analyser Configuration
##################################################

class ToothAnalyserConfig:
    anatomicalSegmentationName: str = "_AnatomicalSegmentation_"
    medialSurfaceName: str = "_MedialSurface_"
    segmentNames: list[str] = ["Dentin", "Enamel"]
    fileTyps: tuple[str] = (".ISQ", ".mhd", ".nrrd")
    mockDirectory: str = "/Users/lukas/Documents/THA/7.Semester/Abschlussarbeit/Beispieldatensaetze/Mock/"




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
    sourcePath: str = "/Users/lukas/Documents/THA/7.Semester/Abschlussarbeit/Beispieldatensaetze/Orginale/"
    targetPath: str =  "/Users/lukas/Documents/THA/7.Semester/Abschlussarbeit/Beispieldatensaetze/Ergebnisse/"
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
    status: str = "Test"


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
        Example: buttons
        """
        self.ui.applyAnalytics.connect("clicked(bool)", self.onApplyAnalyticsButton)
        self.ui.applyAnatomical.connect("clicked(bool)", self.onApplyAnatomicalButton)
        self.ui.applyBatch.connect("clicked(bool)", self.onApplyBatchButton)
        # self.ui.selectedAlgorithm.addItems(ToothAnalyserLogic.getAlgorithmsByName())
        # self.ui.selectedAlgorithm.currentText = ToothAnalyserLogic.getAlgorithmsByName()[0]

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
        Called when the application closes and
        the module widget is destroyed.
        """
        self.removeObservers()

    def enter(self) -> None:
        """
        Called each time the user opens this module
        Make sure parameter node exists and observed
        """
        self.initializeParameterNode()

    def exit(self) -> None:
        """
        Called each time the user opens a different module.
        """
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._param:
            self._param.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            self.removeObserver(self._param, vtk.vtkCommand.ModifiedEvent, self._uiObserver)

    def onSceneStartClose(self, caller, event) -> None:
        """
        Called just before the scene is closed.
        :param: caller
        :param: event
        """
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """
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

        # select medial surfaces by default
        self.ui.calcMidSurface.checked = True
        self.ui.executing.setVisible(False)
        self.ui.progressBar.setVisible(False)

    def setParameterNode(self, inputParameterNode: Optional[ToothAnalyserParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        Note: Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each.
        param:  The ParameterNode from the module
        """
        if self._param:
            self._param.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._param, vtk.vtkCommand.ModifiedEvent, self._uiObserver)
        self._param = inputParameterNode
        if self._param:
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._param.connectGui(self.ui)
            self.addObserver(self._param, vtk.vtkCommand.ModifiedEvent, self._uiObserver)
            self._uiObserver()

    def _uiObserver(self, caller=None, event=None) -> None:
        """
        This is an event function.
        Called everytime when the UI changes.
        :param:  caller
        :param:  event
        """
        self.handleApplyBatchButton()
        self.handleApplyAnalyticsButton()
        self.handleApplyAnatomicalButton()

    def handleApplyBatchButton(self):
        """
        This methode check if there is exactly one
        enabled checkbox.
        """
        if self.validateBatchSettings(
            paramsToCheck={
                "analytics": self._param.analytical.useAnalyticForBatch,
                "anatomical": self._param.anatomical.useAnatomicalForBatch})\
            and self._param.batch.sourcePath and self._param.batch.targetPath:
                self.ui.applyBatch.enabled = True
        else:
            self.ui.applyBatch.enabled = False

    def handleApplyAnalyticsButton(self):
        """
        Enable the "Apply Analytical" Button, if an image is
        loaded to the scene.
        """
        if not self._param.analytical.currentAnalyticalVolume:
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
        else:
            self.ui.applyAnatomical.enabled = True

    def validateBatchSettings(self, paramsToCheck: dict) -> bool:
        """
        The method checks if exactly one batch setting checkbox is enabled.
        :param: A dictionary with the checkboxes to be checked
        :return: True, if there is exactly one enabled checkbox
        """
        return sum(value for value in paramsToCheck.values() if isinstance(value, bool)) == 1

    def showProgressBar(self, isVisible: bool) -> None:
        # Sichtbarkeit des Labels umschalten

        self.ui.executing.setVisible(isVisible)
        self.ui.progressBar.setVisible(isVisible)
        slicer.app.processEvents()

    def onApplyAnalyticsButton(self) -> None:
        """
        Run the analytical processing in an error display
        when user clicks "Apply Analytics" Button.
        """
        self.showProgressBar(True)
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            import hashlib
            print(hashlib.sha256(open("P01A-C0005278.nii.gz", "rb").read()).hexdigest())
            Analytics.execute(self._param)
        self.showProgressBar(False)

    def onApplyAnatomicalButton(self) -> None:
        """
        Run the anatomical segmentation processing in an error display
        when user clicks "Apply Analytics" Button.
        """
        self.showProgressBar(True)
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            AnatomicalSegmentationLogic.execute(param=self._param)
        self.showProgressBar(False)
    def onApplyBatchButton(self) -> None:
        """
        Run the batch processing in an error display
        when user clicks "Apply Batch" button.
        """
        self.showProgressBar(True)
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            if self._param.analytical.useAnalyticForBatch:
                Analytics.executeAsBatch(param=self._param)
            elif self._param.anatomical.useAnatomicalForBatch:
                AnatomicalSegmentationLogic.executeAsBatch(param=self._param)
        self.showProgressBar(False)


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
    _availableTypes = [".nrrd", ".mhd", "nii"]

    def __init__(self) -> None:
        """ Called when the logic class is instantiated.
        Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self) -> ToothAnalyserParameterNode:
        """
        Getter methode for the ParameterNode needed
        in the logic class
        param: None
        return: The ParameterNode from this module
        """
        return ToothAnalyserParameterNode(super().getParameterNode())

    def preProcessing(self) -> None:
        """Abstract method"""
        raise NotImplementedError("Please implement the preProcessing() methode in one of the child classes")

    def postProcessing(self) -> None:
        """Abstract method"""
        raise NotImplementedError("Please implement the postProcessing() methode in one of the child classes")

    def execute(self, param: ToothAnalyserParameterNode) -> None:
        """Abstract method"""
        raise NotImplementedError("Please implement the execute() methode in one of the child classes")

    def executeAsBatch(self, param: ToothAnalyserParameterNode) -> None:
        """Abstract method"""
        raise NotImplementedError("Please implement the executeAsBatch() methode in one of the child classes")

    @classmethod
    def monitorProgress(cls, estimatedRuntimeInSec: int, stop) -> None:
        """
        Monitors the progress of the running algorithm
        based on the estimated runtime.
        param: algorithm_runtime_seconds (int): Estimated runtime of the algorithm.
        return: None
        """
        import time

        # create a dialog with a progress bar
        progressDialog = slicer.util.createProgressDialog(
            value=0,
            maximum=100,
            labelText="The anatomical segmentation of the CT takes approx. 17 minutes, depending on the parameters. Please wait while the algorithm is running.",
            windowTitle="Executing algorithm..."
        )
        print("stop event: ", stop.is_set())
        try:
            start_time = time.time()
            elapsed_time = 0
            while elapsed_time < estimatedRuntimeInSec and not progressDialog.wasCanceled and not stop.is_set():
                elapsed_time = time.time() - start_time
                progress_value = int((elapsed_time / estimatedRuntimeInSec) * 100)
                progressDialog.setValue(progress_value)
                slicer.app.processEvents()  # GUI-Update sicherstellen
                time.sleep(0.5)

            stop.set()
            progressDialog.setValue(100)
            slicer.app.processEvents()
        finally:
            progressDialog.close()




###########################################
#     Tooth Analyser section Analytics     #
###########################################
class Analytics(ToothAnalyserLogic):

    @classmethod
    def preProcessing(cls):
        print("Vor jedem analytischen Verfahren")

    @classmethod
    def postProcessing(cls):
        print("Nach jedem analytischen Verfahren")

    @classmethod
    def showHistogram(cls, image: vtkMRMLScalarVolumeNode) -> None:
        """
        This Methode creates a histogram from the current selected Volume
        param: param: The parameters from the ui
        param: title: The title for the histogram
        param: xTitle: The title for the x-axes in the histogram
        param: yTitle: The title for the y-axes in the histogram
        return: None
        """
        import numpy as np
        from collections import namedtuple

        AxisFitting = namedtuple('AxisFitting', ['x', 'y'])
        axes = AxisFitting(x="Intensity", y="Frequency")

        # create histogram data
        imageData = slicer.util.arrayFromVolume(image)
        histogram = np.histogram(imageData, bins=50)

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
        chartNode.SetYAxisRange(0, 4e5)
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
            cls.showHistogram(param.analytical.currentAnalyticalVolume)

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
    _anatomicalSegmentationName = ToothAnalyserConfig.anatomicalSegmentationName
    _midSurfaceName = ToothAnalyserConfig.medialSurfaceName
    _segmentNames = ToothAnalyserConfig.segmentNames
    _fileTypes = ToothAnalyserConfig.fileTyps

    @classmethod
    def preProcessing(cls) -> None:
        """
        Method for defining preconditions for an algorithm
        """
        print("Before each algorithm")

    @classmethod
    def postProcessing(cls) -> None:
        """
        Method for defining post conditions for an algorithm
        """
        print("After each algorithm")

    @classmethod
    def getDirectoryForFile(cls, filePath: str) -> str:
        """
        This method returns the directory in which a given
        file is located.
        @param filePath: the full path to the file
        @return: the full path to the directory where the file is located
        @example:
            filePath = '/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ'
            directoryPath = cls.getDirectoryForFile(filePath)
            directoryPath -> '/data/MicroCT/Original_ISQ/'
        """
        folder_path = os.path.dirname(filePath)
        if not folder_path:
            folder_path = os.getcwd()

        return folder_path

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
    def createSegmentation(cls, labelImage: vtkMRMLLabelMapVolumeNode, deleteLabelImage: bool, currentImageName: str) -> None:
        """
        Generates a segmentationNode from a given labelNode.
        After generation the segmentationNode will get some properties
        @param labelImage: The labelNode to be segmented
        @param deleteLabelImage: Decides whether the given labelNode should be deleted after segmentation
        @param currentImageName: the name of the segmented image, so give the segmentation a unique name
        @example:
            cls.createSegmentation(labelImageNode, True, currentImageName)
        """
        # create segmentation
        seg = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
        slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(labelImage, seg)
        seg.CreateClosedSurfaceRepresentation()

        # set properties for segmentation
        print("SegName: ", currentImageName)
        seg.SetName(currentImageName + cls._anatomicalSegmentationName)
        default_names = cls._segmentNames

        # set properties for segmentation
        num_segments = seg.GetSegmentation().GetNumberOfSegments()
        for i in range(num_segments):
            if i < len(default_names):
                segment_name = default_names[i]
                if segment_name == "Enamel":
                    seg.GetSegmentation().GetNthSegment(i).SetColor(1.0, 1.0, 0.6)
            else:
                segment_name = f"Segment {i + 1}"
            seg.GetSegmentation().GetNthSegment(i).SetName(segment_name)

        # delete the given labelNode
        if deleteLabelImage:
            slicer.mrmlScene.RemoveNode(labelImage)

    @classmethod
    def createMedialSurface(cls, midSurfaceDentin: vtkMRMLLabelMapVolumeNode,
                            midSurfaceEnamel: vtkMRMLLabelMapVolumeNode,
                            currentImageName: str) -> None:
        """
        This method creates a segmentation for the given medial surface
        @param midSurfaceDentin: the dentin label map image to be segmented
        @param midSurfaceEnamel: the enamel label map image to be segmented
        @param show3D: true if a 3D model is to be created
        @param currentImageName: the name of the segmented image, so give the segmentation a unique name
        @example:
            currentImageName = 'P01A-C0005278'
            cls.createMedialSurface(dentinMidSurfaceNode, enamelMidSurfaceNode, True, currentImageName)
        """
        # create dentin medial surface segmentation
        segDentin = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
        slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(midSurfaceDentin, segDentin)
        segDentin.SetName("MedialSurface_source")

        if segDentin.GetSegmentation().GetNumberOfSegments() > 0:
            segDentin.GetSegmentation().GetNthSegment(0).SetName(cls._segmentNames[0])
            segDentin.GetSegmentation().GetNthSegment(0).SetColor(1.0, 0.0, 0.0)
            slicer.mrmlScene.RemoveNode(midSurfaceDentin)

        # create enamel medial surface segmentation
        segEnamel = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
        slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(midSurfaceEnamel, segEnamel)
        print("Midname: " + currentImageName)
        segEnamel.SetName(currentImageName + cls._midSurfaceName)

        if segEnamel.GetSegmentation().GetNumberOfSegments() > 0:
            segEnamel.GetSegmentation().GetNthSegment(0).SetName(cls._segmentNames[1])
            segEnamel.GetSegmentation().GetNthSegment(0).SetColor(0.0, 1.0, 0.0)
            slicer.mrmlScene.RemoveNode(midSurfaceEnamel)

        # copy all segments from dentin to enamel and delete dentin
        for i in range(segDentin.GetSegmentation().GetNumberOfSegments()):
            source_segment = segDentin.GetSegmentation().GetNthSegment(i)
            segment_id = segDentin.GetSegmentation().GetSegmentIdBySegment(source_segment)
            segEnamel.GetSegmentation().CopySegmentFromSegmentation(segDentin.GetSegmentation(), segment_id, True)
        slicer.mrmlScene.RemoveNode(getNode("MedialSurface_source"))

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
            currentImage = getNode(currentImageName)
            slicer.mrmlScene.RemoveNode(currentImage)

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
            print(f"Das Verzeichnis '{path}' existiert nicht.")
            return

        if not os.path.isdir(path):
            print(f"Der Pfad '{path}' ist kein Verzeichnis.")
            return

        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
        except Exception as e:
            print(f"Fehler beim Leeren des Ordners '{path}': {e}")

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
    def convertIntoVTK(cls, itkImage):
        """
        This methode converts an itk image into a vtk image
        by using the numpy array of an image. Then a vtk image
        object will be created.
        @param: the itk image to be converted
        @return: the converted vtk image
        @example:
            vtkImage = cls.convertIntoVTK(itkImage)
        """
        import SimpleITK as sitk
        import numpy as np

        # convert the itk image into numpy array
        array_data = sitk.GetArrayFromImage(itkImage) # numpy array (z, y, x)
        array_data_c = np.ascontiguousarray(array_data, dtype=np.uint8)
        # convert the numpy array into a vtk image
        vtk_array = vtk.util.numpy_support.numpy_to_vtk(array_data_c.ravel(), deep=True, array_type=vtk.VTK_UNSIGNED_CHAR)
        # create an vtk image object
        vtk_image = vtk.vtkImageData()
        vtk_image.SetDimensions(array_data.shape[2], array_data.shape[1], array_data.shape[0]) # (x, y, z)
        vtk_image.SetSpacing(itkImage.GetSpacing())  # ITK-Spacings
        vtk_image.SetOrigin(itkImage.GetOrigin())  # ITK-Origin
        vtk_image.GetPointData().SetScalars(vtk_array)
        return vtk_image

    @classmethod
    def createLabelNode(cls, itkImage, vtk_image):
        """
        This methode creates a label map node based
        on an itk image and a vtk image
        @param itkImage: the itk image for the calculation
        @param vtk_image: the vtk image to load the label node
        @return: the created label image
        @example:
            vtkImage = cls.convertIntoVTK(itkImage)
            labelMapNode = cls.createLabelNode(itkImage, vtkImage)
        """
        labelmap_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode", "Test")
        labelmap_node.SetAndObserveImageData(vtk_image)
        labelmap_node.SetSpacing(itkImage.GetSpacing())
        labelmap_node.SetOrigin(itkImage.GetOrigin())
        return labelmap_node

    @classmethod
    def itkToLabelNode(cls, itkImage):
        """
        Convert an itk image into a label map node to open
        it in the slicer scene.
        @param itkImage: the itk image to be converted into a vtk image
        @example:
            labelImageNode = cls.itkToLabelNode(labelImageITK)
        """
        # convert the itk image in an label node
        vtkImage = cls.convertIntoVTK(itkImage)
        labelmap_node = cls.createLabelNode(itkImage, vtkImage)
        labelmap_node.CreateDefaultDisplayNodes()
        app_logic = slicer.app.applicationLogic()
        selection_node = app_logic.GetSelectionNode()

        # set the label nod as current node
        selection_node.SetReferenceActiveLabelVolumeID(labelmap_node.GetID())
        app_logic.PropagateVolumeSelection(0)

        # redraw the views
        layout_manager = slicer.app.layoutManager()
        for slice_view in ['Red', 'Green', 'Yellow']:
            slice_widget = layout_manager.sliceWidget(slice_view)
            slice_widget.sliceLogic().FitSliceToAll()
        return labelmap_node

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
        from ToothAnalyserLib.AnatomicalSegmentation.Segmentation import parseName, calcPipeline

        start = time.time()
        logging.info("Processing started")

        segmentationType = param.anatomical.selectedAnatomicalAlgo
        currentImageNameWithTyp = param.anatomical.currentAnatomicalVolume.GetName()
        sourcePath = param.anatomical.currentAnatomicalVolume.GetStorageNode().GetFullNameFromFileName()

        #Calculate Anatomical Segmentation by executing pipeline
        toothDict = calcPipeline(
            sourcePath=sourcePath, #path to file
            calcMidSurface=param.anatomical.calcMidSurface,
            filter_selection_1=segmentationType,
            filter_selection_2=segmentationType,
        )

        # extract itk images from the calculated tooth dictionary
        segmentationType = segmentationType.lower()
        enamelMidSurfaceITK = toothDict["enamel_" + segmentationType + "_" + segmentationType + "_midsurface"]
        dentinMidSurfaceITK = toothDict["dentin_" + segmentationType + "_" + segmentationType + "_midsurface"]
        labelImageITK = toothDict["segmentation_" + segmentationType + "_" + segmentationType + "_labels"]

        # Delete unused nodes from the scene
        cls.clearScene(currentImageName=currentImageNameWithTyp)

        try:
            # try to create the segmentation based on the label image
            currentImageName = toothDict["name"]
            labelImageNode = cls.itkToLabelNode(labelImageITK)
            cls.createSegmentation(
                labelImage=labelImageNode,
                deleteLabelImage=True,
                currentImageName=currentImageName
            )
            # try to create medial surfaces if there were calculated
            if enamelMidSurfaceITK is not None or dentinMidSurfaceITK is not None:
                enamelMidSurfaceNode = cls.itkToLabelNode(enamelMidSurfaceITK)
                dentinMidSurfaceNode = cls.itkToLabelNode(dentinMidSurfaceITK)
                cls.createMedialSurface(
                    midSurfaceDentin=dentinMidSurfaceNode,
                    midSurfaceEnamel=enamelMidSurfaceNode,
                    currentImageName=currentImageName)
            else:
                pass
        except:
            pass

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
        from ToothAnalyserLib.AnatomicalSegmentation.Segmentation import calcPipelineAsBatch, parseName

        # create local variables for all parameters
        sourcePath = param.batch.sourcePath
        targetPath = param.batch.targetPath
        segmentationType = param.anatomical.selectedAnatomicalAlgo
        fileType = param.batch.fileType
        files = cls.collectFiles(sourcePath, cls._fileTypes)

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
            calcPipelineAsBatch(
                sourcePath=fullFilePath,
                targetPath=targetFileDirectory,
                segmentationType=segmentationType,
                calcMidSurface=param.anatomical.calcMidSurface,
                fileType=fileType)


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

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.testHandleApplyAnalyticsButton()
        self.testGetDirectoryForFile()
        self.testGetDirectoryForEmptyPath()
        self.testCreateDirectory()
        self.testValidateBatchSettingsOneEnabled()
        self.testValidateBatchSettingsOneDisabled()
        self.testParsName()
        self.testParseType()
        self.testSampleData()

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

    def testGetDirectoryForFile(self):

        filePath = "/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ"
        expectedDirectory = "/data/MicroCT/Original_ISQ"
        result = AnatomicalSegmentationLogic.getDirectoryForFile(filePath)

        self.assertEqual(result, expectedDirectory)
        self.delayDisplay("Test 2 passed")

    def testGetDirectoryForEmptyPath(self):

        filePath = ""
        expectedDirectory = os.getcwd()
        result = AnatomicalSegmentationLogic.getDirectoryForFile(filePath)

        self.assertEqual(result, expectedDirectory)
        self.delayDisplay("Test 3 passed")

    def testCreateDirectory(self):

        path = "/data/test/"
        directoryName = "new_folder"
        expectedDirectory = "/data/test/new_folder/"
        result = AnatomicalSegmentationLogic.createDirectory(path, directoryName)

        self.assertEqual(result, expectedDirectory)
        self.delayDisplay("Test 4 passed")

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
        self.delayDisplay("Test 5 passed")

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
        self.delayDisplay("Test 6 passed")

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

        self.delayDisplay("Test 7 passed")

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

        self.delayDisplay("Test 8 passed")

    def testSampleData(self):
        import SampleData
        node1 = SampleData.downloadSample('ToothAnalyser1')

        self.assertIsNotNone(node1, "ToothAnalyser1 konnte nicht geladen werden.")