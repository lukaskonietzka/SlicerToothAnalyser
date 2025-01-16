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
# ToothAnalyser
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
        # Category and sample name displayed in Sample Data module
        category="ToothAnalyser",
        sampleName="ToothAnalyser1",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, "ToothAnalyser1.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="ToothAnalyser1.nrrd",
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        # This node name will be used when the data set is loaded
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
# ToothAnalyserParameterNode
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
    showMidSurfaceAs3D: bool
    useAnatomicalForBatch: bool

@parameterPack
class Batch:
    """
    The parameters needed by the section
    Batch Processing
    """
    sourcePath: str
    targetPath: str

@parameterNodeWrapper
class ToothAnalyserParameterNode:
    """
    All parameters needed by module
    separated in: analytical, anatomical, batch
    """
    analytical: AnalyticalParameters
    anatomical: AnatomicalParameters
    batch: Batch


##################################################
# ToothAnalyserWidget
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

    def onApplyAnalyticsButton(self) -> None:
        """
        Run the analytical processing in an error display
        when user clicks "Apply Analytics" Button.
        """
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            Analytics.execute(self._param)

    def onApplyAnatomicalButton(self) -> None:
        """
        Run the anatomical segmentation processing in an error display
        when user clicks "Apply Analytics" Button.
        """
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            AnatomicalSegmentationLogic.setSelectedAlgorithm(self._param.anatomical.selectedAnatomicalAlgo)
            AnatomicalSegmentationLogic.getSelectedAlgorithm().execute(param=self._param)

    def onApplyBatchButton(self) -> None:
        """
        Run the batch processing in an error display
        when user clicks "Apply Batch" button.
        """
        with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
            if self._param.analytical.useAnalyticForBatch:
                Analytics.executeAsBatch(param=self._param)
            elif self._param.anatomical.useAnatomicalForBatch:
                AnatomicalSegmentationLogic.setSelectedAlgorithm(self._param.anatomical.selectedAnatomicalAlgo)
                AnatomicalSegmentationLogic.getSelectedAlgorithm().executeAsBatch(param=self._param)


##################################################
# ToothAnalyserLogic
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

    def monitorProgress(self, estimatedRuntimeInSec: int) -> None:
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
            labelText="Please wait until the algorithm is ready.",
            windowTitle="Executing algorithm"
        )
        try:
            start_time = time.time()
            elapsed_time = 0
            while elapsed_time < estimatedRuntimeInSec:
                elapsed_time = time.time() - start_time
                progress_value = int((elapsed_time / estimatedRuntimeInSec) * 100)
                progressDialog.setValue(progress_value)
                slicer.app.processEvents()  # GUI-Update sicherstellen
                time.sleep(0.5)
            progressDialog.setValue(100)
            slicer.app.processEvents()
        finally:
            progressDialog.close()

    @classmethod
    def deleteFromScene(cls, currentVolume) -> None:
        """
        Deletes the given Volume from the MRML-Scene if there is anything to delete
        param: currentVolume xtkMRMLNodeVolume: The Volume to be deleted
        return None
        """
        try:
            volumeNode = slicer.util.getNode(currentVolume.GetName())
            slicer.mrmlScene.RemoveNode(volumeNode)
            logging.info(f"The volumen '{volumeNode.GetName()}' was successful deleted .")
        except slicer.util.MRMLNodeNotFoundException:
            logging.error("The volume was not found .")




###########################################
#     ToothAnalyser section Analytics     #
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


##################################################
# ToothAnalyser section Anatomical Segmentation
##################################################
class AnatomicalSegmentationLogic(ToothAnalyserLogic):
    _availableAlgorithms = []
    _selectedAlgorithm = None
    _anatomicalSegmentationName = "Anatomical-Segmentationbla"
    _midSurfaceName = "Medial-Surfacedada"

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls not in AnatomicalSegmentationLogic._availableAlgorithms:
            AnatomicalSegmentationLogic._availableAlgorithms.append(cls)

    @classmethod
    def getAlgorithmsByName(cls) -> list[str]:
        """
        Collects all subclasses names of the class "ToothAnalyserLogic" in a list
        param: None
        return: algorithms: A list out of names from all available algorithms
        """
        return [subclass.__name__ for subclass in cls._availableAlgorithms]

    @classmethod
    def getAvailableAlgorithms(cls) -> list[any]:
        """
        Collects all subclasses in a list. Type must be any,
        because we do not know which subclasses will be added
        param: None
        return: algorithms: A list out of objects from all available algorithms
        """
        return [subclass for subclass in cls._availableAlgorithms]

    @classmethod
    def setSelectedAlgorithm(cls, currentAlgorithmName: str) -> None:
        """
        This methode set the current algorithms as selected,
        if it is an available algorithm.
        param: currentAlgorithmName: The algorithm that should be selected
        return: None
        """
        for algorithm in cls.getAvailableAlgorithms():
            if algorithm.__name__ == currentAlgorithmName:
                cls._selectedAlgorithm = algorithm
                break

    @classmethod
    def getSelectedAlgorithm(cls):
        """
        Getter for the field selectedAlgorithm
        param: None
        return: _selectedAlgorithms: The algorithm that is selected
        """
        return cls._selectedAlgorithm

    @classmethod
    def preProcessing(cls) -> None:
        """
        Method for defining preconditions for an algorithm
        param: None
        return: None
        """
        print("Vor jedem Algorihmus")

    @classmethod
    def postProcessing(cls) -> None:
        """
        Method for defining post conditions for an algorithm
        param: None
        return: None
        """
        print("Nach jedem Algorithmus")

    @classmethod
    def getDirectoryForFile(cls, file_path: str) -> str:
        """"""
        folder_path = os.path.dirname(file_path)
        if not folder_path:
            folder_path = os.getcwd()

        return folder_path

    @classmethod
    def loadFromDirectory(cls, path: str, suffix: tuple[str]) -> None:
        """
        Loads all data with the given suffix from the given path
        param: path (str): path to the files
        param; suffix (tuple[str]): Only files with this format are loaded
        return: fileCount (int): The number of images that have been loaded
        """
        import os

        if not os.path.exists(path):
            logging.error(f"Folder {path} dont exists.")
            return

        # Collect all files that ends with the given suffix
        files = sorted([f for f in os.listdir(path) if f.lower().endswith(suffix)])
        if not files:
            logging.error(f"No File with the given suffix in the  {path}.")
            return

        # load files from the given path as labelmap or scalenode
        for file in files:
            file_path = os.path.join(path, file)
            try:
                if "midsurface" in file.lower():
                    slicer.util.loadVolume(file_path, properties={"labelmap": True, "show": True})
                    continue
                if "label" in file.lower():
                    slicer.util.loadVolume(file_path, properties={"labelmap": True, "show": False})
                    continue
                else:
                    pass
            except Exception as e:
                logging.error(f"Error while loading {file_path}: {e}")

    @classmethod
    def createSegmentation(cls, labelImage: vtkMRMLLabelMapVolumeNode, deleteLabelImage: bool=False) -> None:
        """
        Generates a segmentationNode from a given labelNode.
        After generation the segmentationNode will get some properties
        param: The labelNode to be segmented
        param: Decides whether the given labelNode should be deleted after segmentation
        return: None
        """
        # create segmentation
        seg = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
        slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(labelImage, seg)
        seg.CreateClosedSurfaceRepresentation()

        # set properties for segmentation
        seg.SetName(cls._anatomicalSegmentationName)
        #seg.GetSegmentation().GetNthSegment(0).SetName("Dentin")
        #seg.GetSegmentation().GetNthSegment(1).SetName("Enamel")
        default_names = ["Dentin", "Schmelz"]

        # set properties for segmentation
        num_segments = seg.GetSegmentation().GetNumberOfSegments()
        for i in range(num_segments):
            if i < len(default_names):
                # Benenne die ersten Segmente mit den vordefinierten Namen
                segment_name = default_names[i]
            else:
                # Generiere generische Namen für die übrigen Segmente
                segment_name = f"Segment {i + 1}"

            # Setze den Namen des Segments
            seg.GetSegmentation().GetNthSegment(i).SetName(segment_name)

        # delete the given labelNode
        if deleteLabelImage:
            slicer.mrmlScene.RemoveNode(labelImage)

    @classmethod
    def createMedialSurface(cls, midSurfaceDentin: vtkMRMLLabelMapVolumeNode, midSurfaceEnamel: vtkMRMLLabelMapVolumeNode, show3D: bool) -> None:
        # create dentin medial surface segmentation
        print("show 3D: ", show3D)
        segDentin = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
        slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(midSurfaceDentin, segDentin)
        segDentin.SetName("MedialSurface_source")

        if segDentin.GetSegmentation().GetNumberOfSegments() > 0:
            segDentin.GetSegmentation().GetNthSegment(0).SetName("Dentin")
            slicer.mrmlScene.RemoveNode(midSurfaceDentin)
            if show3D:
                print("create 3D dentin")
                segDentin.CreateClosedSurfaceRepresentation()

        # create enamel medial surface segmentation
        segEnamel = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
        slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(midSurfaceEnamel, segEnamel)
        segEnamel.SetName(cls._midSurfaceName)

        if segEnamel.GetSegmentation().GetNumberOfSegments() > 0:
            segEnamel.GetSegmentation().GetNthSegment(0).SetName("Enamel")
            slicer.mrmlScene.RemoveNode(midSurfaceEnamel)
            if show3D:
                print("create 3D enamel")
                segEnamel.CreateClosedSurfaceRepresentation()

        # copy all segments from dentin to enamel and delete dentin
        for i in range(segDentin.GetSegmentation().GetNumberOfSegments()):
            source_segment = segDentin.GetSegmentation().GetNthSegment(i)
            segment_id = segDentin.GetSegmentation().GetSegmentIdBySegment(source_segment)
            segEnamel.GetSegmentation().CopySegmentFromSegmentation(segDentin.GetSegmentation(), segment_id, True)
        slicer.mrmlScene.RemoveNode(getNode("MedialSurface_source"))

    @classmethod
    def createFolder(cls, item: str, folderName: str) -> None:
        shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
        SceneID = shNode.GetSceneItemID()
        folderNum = shNode.CreateFolderItem(SceneID, folderName)

        nodes = slicer.mrmlScene.GetNodes()
        for node in nodes:
            if item in node.GetName().lower():
                shNode.CreateItem(folderNum, node)

    @classmethod
    def clearScene(cls, currentImageName) -> None:
        """
        Deletes all nodes from the scene, that where generated
        by the algorithm
        """

        try:
            currentImage = getNode(currentImageName)
            slicer.mrmlScene.RemoveNode(currentImage)

            anatomicalSegmentation = getNode(cls._anatomicalSegmentationName)
            slicer.mrmlScene.RemoveNode(anatomicalSegmentation)

            midSurface = getNode(cls._midSurfaceName)
            slicer.mrmlScene.RemoveNode(midSurface)
        except:
            pass

        # slicer.mrmlScene.Clear()

    @classmethod
    def countFiles(cls, path: str, suffix: tuple[str]) -> int:
        """
        This methode counts all Files in a given directory with the given ending
        param: path (str): path to the files
        param; suffix (tuple[str]): Only files with this format are loaded
        return: fileCount (int): The number of images that have been loaded
        Example: fileCount = countFiles(param.sourcePath, ('.mhd', '.isq'))
        """
        import os
        return len(sorted([f for f in os.listdir(path) if f.lower().endswith(suffix)]))

    @classmethod
    def isValidPath(cls, path: str) -> bool:
        """
        This method checks whether the given string is a path to a folder
        This should work for all common operating systems
        param: path (str): value to check for a path
        return: isValidPath (bool): Returns True if the given string is a path to a folder
        """
        import re
        # Regex for directory on several operating systems
        pattern = r'^(?:[a-zA-Z]:\\|/)?(?:[\w\s.-]+(?:\\|/))*$'
        return bool(re.fullmatch(pattern, path))

    @classmethod
    def clearDirectory(cls, path: str) -> None:
        """
        Delete all files in the given directory
        :param path: path to the directory, that has to be cleared
        """
        if not os.path.isdir(path):
            raise ValueError(f"The given '{path}' is not an directory.")
        try:
            for file in os.listdir(path):
                file_path = os.path.join(path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        except Exception as e:
            print(f"Error while clearing directory: {e}")

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


##################################################
# Anatomical Segmentation Strategies
##################################################
class Otsu(AnatomicalSegmentationLogic):
    """
    This class is a possible strategy for the
    Anatomical Segmentation that can selected via
    the parameter "Algorithm" in the UI
    """

    @classmethod
    def execute(cls, param: ToothAnalyserParameterNode) -> None:
        """
        This method is an abstract method form the parent class
        ToothAnalyserLogic. It is implementing the current strategy
        as a single procedure.
        """
        super().preProcessing()
        import time
        from ToothAnalyserLib.AnatomicalSegmentation.Segmentation import calcAnatomicalSegmentation

        start = time.time()
        logging.info("Processing started")

        # Create result directory
        targetDirectory = super().createDirectory(
            path=super().getDirectoryForFile(param.anatomical.currentAnatomicalVolume.GetStorageNode().GetFullNameFromFileName()),
            directoryName="/anatomicalSegmentationOtsu/"
        )

        # Delete the old segmentation to keep order
        super().clearDirectory(targetDirectory)

        #Calculate Anatomical Segmentation
        mockDirectory = "/Users/lukas/Documents/THA/7.Semester/Abschlussarbeit/Beispieldatensaetze/Mock/"
        calcAnatomicalSegmentation(
            sourcePath=param.anatomical.currentAnatomicalVolume.GetStorageNode().GetFullNameFromFileName(),
            targetPath=targetDirectory,
            segmentationType="Otsu"
        )

        # Delete all nodes form scene
        super().clearScene(param.anatomical.currentAnatomicalVolume.GetName())

        # Load and create the calculated Segmentation
        super().loadFromDirectory(path=targetDirectory,suffix='.mhd')
        super().createSegmentation(labelImage=getNode("*label*"), deleteLabelImage=True)
        super().createMedialSurface(
            midSurfaceDentin=getNode("*dentin*midsurface*"),
            midSurfaceEnamel=getNode("*enamel*midsurface*"),
            show3D=param.anatomical.showMidSurfaceAs3D
       )

        # Time tracking
        stop = time.time()
        print("Processing completed in: ",  f" {(stop-start) // 60:.0f} minutes and {(stop - start) % 60:.0f} seconds")
        print()

    @classmethod
    def executeAsBatch(cls, param: ToothAnalyserParameterNode) -> None:
        """
        This method is an abstract method form the parent class
        ToothAnalyserLogic. It is implementing the current strategy
        as a single procedure.
        """
        super().preProcessing()
        print("execute Anatomical Segmentation with Otsu as Batch ...")
        super().postProcessing()
        print()



class Renyi(AnatomicalSegmentationLogic):
    """
    This class is a possible strategy for the
    Anatomical Segmentation that can selected via
    the parameter "Algorithm" in the UI
    """

    @classmethod
    def execute(cls, param: ToothAnalyserParameterNode):
        """
        This method is an abstract method form the parent class
        ToothAnalyserLogic. It is implementing the current strategy
        as a single procedure.
        """
        super().preProcessing()

        import time
        from ToothAnalyserLib.AnatomicalSegmentation.Segmentation import calcAnatomicalSegmentation

        # Time Tracking
        start = time.time()
        logging.info("Processing started")

        # Create result directory eventuell nach Segmentation auslagern
        targetDirectory = super().createDirectory(
            path=super().getDirectoryForFile(
                param.anatomical.currentAnatomicalVolume.GetStorageNode().GetFullNameFromFileName()),
            directoryName="/anatomicalSegmentationRenyi/"
        )

        # Delete the old segmentation to keep order
        super().clearDirectory(targetDirectory)

        # Calculate Anatomical Segmentation
        # mockDirectory = "/Users/lukas/Documents/THA/7.Semester/Abschlussarbeit/Beispieldatensaetze/Orginale/anatomicalSegmentation/"
        calcAnatomicalSegmentation(
            sourcePath=param.anatomical.currentAnatomicalVolume.GetStorageNode().GetFullNameFromFileName(),
            targetPath=targetDirectory,
            segmentationType="Renyi"
        )

        # Delete all nodes from scene
        super().clearScene(param.anatomical.currentAnatomicalVolume.GetName())

        # Load and create the calculated Segmentation to the Slicer scene
        super().loadFromDirectory(path=targetDirectory, suffix='.mhd')
        super().createSegmentation(labelImage=getNode("*label*"), deleteLabelImage=True)
        super().createMedialSurface(
            midSurfaceDentin=getNode("*dentin*midsurface*"),
            midSurfaceEnamel=getNode("*enamel*midsurface*"),
            show3D=param.anatomical.showMidSurfaceAs3D
        )

        # Time tracking
        stop = time.time()
        logging.info(f"Processing completed in {stop - start:.2f} seconds")
        print(f"Processing completed in {(stop - start) / 60:.2f} minutes")
        print()

        super().postProcessing()
        print()

    @classmethod
    def executeAsBatch(cls, param: ToothAnalyserParameterNode):
        """
        This method is an abstract method form the parent class
        ToothAnalyserLogic. It is implementing the current strategy
        as a single procedure.
        """
        super().preProcessing()
        print("execute Anatomical Segmentation with Renyi as Batch ...")
        super().postProcessing()
        print()



##################################################
# ToothAnalyserTests
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
        self.testValidateBatchSettings()

    def testValidateBatchSettings(self):
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

        self.delayDisplay("Starting the test")

        self.delayDisplay("Test passed")

