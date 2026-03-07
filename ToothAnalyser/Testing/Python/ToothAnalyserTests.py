"""Regression tests for the ToothAnalyser scripted module.

This file keeps test implementation separate from ``ToothAnalyser.py`` while
preserving Slicer's Reload-and-Test integration through a wrapper class.
"""

import os
import slicer


class ToothAnalyserTestMixin:
    """Mixin containing module-level regression tests for ToothAnalyser.py."""

    def setUp(self):
        """Reset scene state before each test run."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Entry point used by Slicer's Reload-and-Test button."""
        testMethods = [
            "testAlgorithmSelection",
            "testSetSelectedAlgorithmUnknownName",
            "testLogicRepresentation",
            "testCariesSegmentationName",
            "testValidateBatchSettings",
            "testObserverParametersTriggersHandlers",
            "testHandlePreProcessingCollapsible",
            "testHandleBatchCollapsible",
            "testHandleSegmentation",
            "testHandleProgressBarRange",
            "testSafeRemoveNode",
            "testClearSceneRemovesMatchingNodes",
            "testCollectFilesFiltersSupportedExtensions",
            "testCreateAndClearDirectory",
            "testExecuteAsBatchInvalidSourcePath",
            "testExecuteAsBatchInvalidTargetPath",
            "testExecuteAsBatchNoSupportedFiles",
        ]

        self.delayDisplay(f"Starting ToothAnalyser tests ({len(testMethods)} cases)...", 200)
        for methodName in testMethods:
            self.setUp()
            getattr(self, methodName)()
            self.delayDisplay(f"Passed: {methodName}", 100)
        self.delayDisplay("All ToothAnalyser tests passed.", 300)

    class _UiFlag:
        """Minimal UI element stub with visibility/enabled state."""

        def __init__(self, visible=False, enabled=True):
            self._visible = visible
            self.enabled = enabled
            self.maximum = 0
            self.value = 0

        def setVisible(self, value: bool):
            self._visible = value

        def isVisible(self):
            return self._visible

    def _createWidgetStub(self):
        """Create a lightweight widget-like object for UI logic tests."""
        from types import SimpleNamespace

        ui = SimpleNamespace(
            apply=self._UiFlag(visible=True, enabled=True),
            status=self._UiFlag(visible=False, enabled=False),
            preProcessingCollapsible=self._UiFlag(visible=False),
            batchCollapsible=self._UiFlag(visible=False),
            anatomicaCollapsible=self._UiFlag(visible=False),
            cariesCollapsible=self._UiFlag(visible=False),
            progressBar=self._UiFlag(visible=False, enabled=False),
        )

        param = SimpleNamespace(
            isPreProcessing=False,
            isBatch=False,
            currentImage=None,
            segmentation="Anatomical Segmentation",
            anatomical=SimpleNamespace(calcMidSurface=True),
        )

        widget = SimpleNamespace(ui=ui, _param=param)
        widget.handleApplyButton = lambda: None
        return widget

    def testAlgorithmSelection(self):
        """Test algorithm discovery and name-based selection."""
        logic = self.ToothAnalyserLogic()
        algorithmNames = logic.getAlgorithmsByName()

        self.assertIn("Anatomical Segmentation", algorithmNames)
        self.assertIn("Caries Segmentation", algorithmNames)

        logic.setSelectedAlgorithm("Anatomical Segmentation")
        self.assertIsInstance(logic.getSelectedAlgorithm(), self.AnatomicalSegmentationLogic)

    def testSetSelectedAlgorithmUnknownName(self):
        """Test that unknown algorithm names do not overwrite current selection."""
        logic = self.ToothAnalyserLogic()
        logic.setSelectedAlgorithm("Anatomical Segmentation")
        before = logic.getSelectedAlgorithm()
        logic.setSelectedAlgorithm("This Algorithm Does Not Exist")
        self.assertIs(logic.getSelectedAlgorithm(), before)

    def testLogicRepresentation(self):
        """Test default text representation for base logic class."""
        logic = self.ToothAnalyserLogic()
        self.assertEqual(str(logic), "Unbekannter Algorithmus")
        self.assertIn("ToothAnalyserLogic", repr(logic))

    def testCariesSegmentationName(self):
        """Test display name for the caries logic implementation."""
        logic = self.CariesSegmentation()
        self.assertEqual(str(logic), "Caries Segmentation")

    def testValidateBatchSettings(self):
        """Test batch settings validation with valid and invalid combinations."""
        self.assertTrue(self.ToothAnalyserWidget.validateBatchSettings(None, {"a": True, "b": False}))
        self.assertFalse(self.ToothAnalyserWidget.validateBatchSettings(None, {"a": False, "b": False}))
        self.assertFalse(self.ToothAnalyserWidget.validateBatchSettings(None, {"a": True, "b": True}))
        self.assertTrue(self.ToothAnalyserWidget.validateBatchSettings(None, {"a": True, "label": "x"}))

    def testObserverParametersTriggersHandlers(self):
        """Test that parameter observer triggers all UI update handlers."""
        from unittest.mock import MagicMock
        from types import SimpleNamespace

        widget = SimpleNamespace(
            handleApplyButton=MagicMock(),
            handleSegmentation=MagicMock(),
            handleBatchCollapsible=MagicMock(),
            handlePreProcessingCollapsible=MagicMock(),
        )

        self.ToothAnalyserWidget.observerParameters(widget)

        widget.handleApplyButton.assert_called_once()
        widget.handleSegmentation.assert_called_once()
        widget.handleBatchCollapsible.assert_called_once()
        widget.handlePreProcessingCollapsible.assert_called_once()

    def testHandlePreProcessingCollapsible(self):
        """Test pre-processing collapsible visibility handling."""
        widget = self._createWidgetStub()
        widget._param.isPreProcessing = True
        self.ToothAnalyserWidget.handlePreProcessingCollapsible(widget)
        self.assertTrue(widget.ui.preProcessingCollapsible.isVisible())

        widget._param.isPreProcessing = False
        self.ToothAnalyserWidget.handlePreProcessingCollapsible(widget)
        self.assertFalse(widget.ui.preProcessingCollapsible.isVisible())

    def testHandleBatchCollapsible(self):
        """Test batch collapsible visibility handling."""
        widget = self._createWidgetStub()
        widget._param.isBatch = True
        self.ToothAnalyserWidget.handleBatchCollapsible(widget)
        self.assertTrue(widget.ui.batchCollapsible.isVisible())

        widget._param.isBatch = False
        self.ToothAnalyserWidget.handleBatchCollapsible(widget)
        self.assertFalse(widget.ui.batchCollapsible.isVisible())

    def testHandleSegmentation(self):
        """Test segmentation panel switching."""
        widget = self._createWidgetStub()
        widget._param.segmentation = "Anatomical Segmentation"
        self.ToothAnalyserWidget.handleSegmentation(widget)
        self.assertTrue(widget.ui.anatomicaCollapsible.isVisible())
        self.assertFalse(widget.ui.cariesCollapsible.isVisible())

        widget._param.segmentation = "Caries Segmentation"
        self.ToothAnalyserWidget.handleSegmentation(widget)
        self.assertFalse(widget.ui.anatomicaCollapsible.isVisible())
        self.assertTrue(widget.ui.cariesCollapsible.isVisible())

    def testHandleProgressBarRange(self):
        """Test progress bar range setup for with/without medial surfaces."""
        widget = self._createWidgetStub()
        widget._param.anatomical.calcMidSurface = True
        self.ToothAnalyserWidget.handleProgressBarRange(widget)
        self.assertEqual(widget.ui.progressBar.maximum, 13)

        widget._param.anatomical.calcMidSurface = False
        self.ToothAnalyserWidget.handleProgressBarRange(widget)
        self.assertEqual(widget.ui.progressBar.maximum, 11)

    def testSafeRemoveNode(self):
        """Test _safeRemoveNode removes nodes only when they are in a scene."""
        logic = self.AnatomicalSegmentationLogic()

        realNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        realNodeId = realNode.GetID()
        logic._safeRemoveNode(realNode)
        self.assertIsNone(slicer.mrmlScene.GetNodeByID(realNodeId))

        # No-op cases should not raise exceptions.
        logic._safeRemoveNode(realNode)
        logic._safeRemoveNode(None)

    def testClearSceneRemovesMatchingNodes(self):
        """Test clearScene queries all generated node groups and removes returned nodes."""
        from types import SimpleNamespace
        from unittest.mock import patch

        logic = self.AnatomicalSegmentationLogic()
        anatomicalNode = SimpleNamespace(GetScene=lambda: True)
        midsurfaceNode = SimpleNamespace(GetScene=lambda: True)

        with patch("slicer.util.getNodes") as getNodes, patch.object(logic, "_safeRemoveNode") as safeRemove:
            getNodes.side_effect = [{"a": anatomicalNode}, {"m": midsurfaceNode}, {}]
            logic.clearScene()
            self.assertEqual(getNodes.call_count, 3)
            self.assertEqual(safeRemove.call_count, 2)

    def testCollectFilesFiltersSupportedExtensions(self):
        """Test that batch input collection only returns supported files."""
        import tempfile

        anatomicalSeg = self.AnatomicalSegmentationLogic()
        with tempfile.TemporaryDirectory() as tmpdir:
            supported = ["a.ISQ", "b.mhd", "c.nrrd", "d.nii", "e.NII"]
            unsupported = ["f.txt", "g", "h.raw"]
            for name in supported + unsupported:
                with open(os.path.join(tmpdir, name), "w", encoding="utf8"):
                    pass

            os.makedirs(os.path.join(tmpdir, "nested.nii"), exist_ok=True)

            files = anatomicalSeg.collectFiles(tmpdir, anatomicalSeg._fileTypes)

            self.assertEqual(files, sorted(supported))

    def testCreateAndClearDirectory(self):
        """Test batch result directory creation and cleanup."""
        import tempfile

        anatomicalSeg = self.AnatomicalSegmentationLogic()
        with tempfile.TemporaryDirectory() as tmpdir:
            resultPath = anatomicalSeg.createDirectory(tmpdir, "results")
            self.assertTrue(os.path.isdir(resultPath))

            with open(os.path.join(resultPath, "result_1.nrrd"), "w", encoding="utf8"):
                pass
            os.makedirs(os.path.join(resultPath, "nested"), exist_ok=True)
            with open(os.path.join(resultPath, "nested", "result_2.nrrd"), "w", encoding="utf8"):
                pass

            anatomicalSeg.clearDirectory(resultPath)
            self.assertEqual(os.listdir(resultPath), [])

    def testExecuteAsBatchInvalidSourcePath(self):
        """Test executeAsBatch error handling for invalid source path."""
        from types import SimpleNamespace
        from unittest.mock import patch
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            param = SimpleNamespace(
                batch=SimpleNamespace(sourcePath=os.path.join(tmpdir, "missing"), targetPath=tmpdir, fileType=".nrrd"),
                anatomical=SimpleNamespace(selectedAnatomicalAlgo="Otsu", calcMidSurface=True),
                pre=SimpleNamespace(compress=False),
            )
            progressBar = self._UiFlag()
            logic = self.AnatomicalSegmentationLogic()
            with patch("slicer.util.errorDisplay") as errorDisplay:
                logic.executeAsBatch(param, progressBar)
                errorDisplay.assert_called_once()

    def testExecuteAsBatchInvalidTargetPath(self):
        """Test executeAsBatch error handling for invalid target path."""
        from types import SimpleNamespace
        from unittest.mock import patch
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            sourceDir = os.path.join(tmpdir, "source")
            os.makedirs(sourceDir, exist_ok=True)
            param = SimpleNamespace(
                batch=SimpleNamespace(sourcePath=sourceDir, targetPath=os.path.join(tmpdir, "missing"), fileType=".nrrd"),
                anatomical=SimpleNamespace(selectedAnatomicalAlgo="Otsu", calcMidSurface=True),
                pre=SimpleNamespace(compress=False),
            )
            progressBar = self._UiFlag()
            logic = self.AnatomicalSegmentationLogic()
            with patch("slicer.util.errorDisplay") as errorDisplay:
                logic.executeAsBatch(param, progressBar)
                errorDisplay.assert_called_once()

    def testExecuteAsBatchNoSupportedFiles(self):
        """Test executeAsBatch warning when no supported files are found."""
        from types import SimpleNamespace
        from unittest.mock import patch
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            sourceDir = os.path.join(tmpdir, "source")
            targetDir = os.path.join(tmpdir, "target")
            os.makedirs(sourceDir, exist_ok=True)
            os.makedirs(targetDir, exist_ok=True)
            with open(os.path.join(sourceDir, "ignore.txt"), "w", encoding="utf8"):
                pass
            param = SimpleNamespace(
                batch=SimpleNamespace(sourcePath=sourceDir, targetPath=targetDir, fileType=".nrrd"),
                anatomical=SimpleNamespace(selectedAnatomicalAlgo="Otsu", calcMidSurface=True),
                pre=SimpleNamespace(compress=False),
            )
            progressBar = self._UiFlag()
            logic = self.AnatomicalSegmentationLogic()
            with patch.object(logic, "warning") as warning:
                logic.executeAsBatch(param, progressBar)
                warning.assert_called_once()
