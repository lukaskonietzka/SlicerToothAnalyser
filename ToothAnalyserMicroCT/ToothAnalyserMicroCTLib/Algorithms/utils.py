"""
ToothAnalyserMicroCTLib.Algorithm.utils
=================================

This module provides general standard functions and decorators that may be useful for all algorithms.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY.


Author
-------
Lukas Konietzka, lukas.konietzka@tha.de
"""

import logging



def measure_time(func):
    """
    This function is a decorator to measure the
    runtime of a method
    @param func:
    @return:
    """
    import time
    import functools
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        stop = time.time()

        elapsed = stop - start
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        logging.info("%s: Done %d:%02d minutes", func.__name__, minutes, seconds)
        return result

    return wrapper


def createSTL(
    labelImage,
    outputDirectory: str,
    fileName: str = "segmentation",
    printMode: bool = True
) -> str:
    """
    Create an STL mesh from a SimpleITK label image.

    Foreground is defined as label values > 0 and exported as a single mesh.
    Returns the absolute path to the written STL file.
    """
    import os
    import numpy as np
    import SimpleITK as sitk
    import vtk
    from vtkmodules.util import numpy_support


    if labelImage is None:
        raise ValueError("labelImage must not be None.")

    os.makedirs(outputDirectory, exist_ok=True)
    stlPath = os.path.abspath(os.path.join(outputDirectory, f"{fileName}.stl"))

    binaryImage = sitk.Cast(labelImage > 0, sitk.sitkUInt8)
    # Add a zero border to avoid clipped/open surfaces at volume boundaries.
    binaryImage = sitk.ConstantPad(binaryImage, [1, 1, 1], [1, 1, 1], 0)
    array = sitk.GetArrayFromImage(binaryImage)
    if int(array.max()) == 0:
        raise ValueError("Label image contains no foreground voxels (> 0).")

    depth, height, width = array.shape
    vtkImage = vtk.vtkImageData()
    vtkImage.SetDimensions(width, height, depth)
    vtkImage.SetSpacing(binaryImage.GetSpacing())
    vtkImage.SetOrigin(binaryImage.GetOrigin())

    vtkScalars = numpy_support.numpy_to_vtk(
        np.ascontiguousarray(array).ravel(order="C"),
        deep=True,
        array_type=vtk.VTK_UNSIGNED_CHAR
    )
    vtkImage.GetPointData().SetScalars(vtkScalars)

    surface = vtk.vtkDiscreteMarchingCubes()
    surface.SetInputData(vtkImage)
    surface.SetValue(0, 1)
    surface.Update()

    polyData = surface.GetOutput()
    if polyData is None or polyData.GetNumberOfPoints() == 0 or polyData.GetNumberOfCells() == 0:
        raise ValueError("Surface extraction failed (empty mesh).")

    def repairPolyData(inputPolyData, holeSize: float, enablePrintMode: bool):
        triangle = vtk.vtkTriangleFilter()
        triangle.SetInputData(inputPolyData)
        triangle.PassVertsOff()
        triangle.PassLinesOff()
        triangle.Update()

        clean = vtk.vtkCleanPolyData()
        clean.SetInputConnection(triangle.GetOutputPort())
        clean.Update()

        connectivity = vtk.vtkPolyDataConnectivityFilter()
        connectivity.SetInputConnection(clean.GetOutputPort())
        connectivity.SetExtractionModeToLargestRegion()
        connectivity.Update()

        fillHoles = vtk.vtkFillHolesFilter()
        fillHoles.SetInputConnection(connectivity.GetOutputPort())
        fillHoles.SetHoleSize(holeSize)
        fillHoles.Update()

        processingOutputPort = fillHoles.GetOutputPort()

        if enablePrintMode:
            # Print mode: smooth staircase artifacts from voxels.
            smooth = vtk.vtkWindowedSincPolyDataFilter()
            smooth.SetInputConnection(processingOutputPort)
            smooth.SetNumberOfIterations(20)
            smooth.SetPassBand(0.08)
            smooth.BoundarySmoothingOff()
            smooth.FeatureEdgeSmoothingOff()
            smooth.NonManifoldSmoothingOn()
            smooth.NormalizeCoordinatesOn()
            smooth.Update()
            processingOutputPort = smooth.GetOutputPort()

            # Print mode: reduce triangle count while preserving topology.
            decimate = vtk.vtkDecimatePro()
            decimate.SetInputConnection(processingOutputPort)
            decimate.SetTargetReduction(0.15)
            decimate.PreserveTopologyOn()
            decimate.SplittingOff()
            decimate.BoundaryVertexDeletionOff()
            decimate.Update()
            processingOutputPort = decimate.GetOutputPort()

        normals = vtk.vtkPolyDataNormals()
        normals.SetInputConnection(processingOutputPort)
        normals.ConsistencyOn()
        normals.AutoOrientNormalsOn()
        normals.SplittingOff()
        normals.ComputeCellNormalsOn()
        normals.ComputePointNormalsOn()
        normals.Update()

        finalClean = vtk.vtkCleanPolyData()
        finalClean.SetInputConnection(normals.GetOutputPort())
        finalClean.Update()
        return finalClean.GetOutput()

    def validatePolyData(inputPolyData) -> list[str]:
        warnings = []
        if inputPolyData is None or inputPolyData.GetNumberOfCells() == 0:
            return ["Mesh has no polygons after repair."]

        featureEdges = vtk.vtkFeatureEdges()
        featureEdges.SetInputData(inputPolyData)
        featureEdges.BoundaryEdgesOn()
        featureEdges.NonManifoldEdgesOn()
        featureEdges.ManifoldEdgesOff()
        featureEdges.FeatureEdgesOff()
        featureEdges.Update()
        problematicEdgeCount = featureEdges.GetOutput().GetNumberOfCells()
        if problematicEdgeCount > 0:
            warnings.append(
                f"Mesh is not watertight or contains non-manifold edges ({problematicEdgeCount} problematic edges)."
            )

        connectivity = vtk.vtkPolyDataConnectivityFilter()
        connectivity.SetInputData(inputPolyData)
        connectivity.SetExtractionModeToAllRegions()
        connectivity.Update()
        regionCount = connectivity.GetNumberOfExtractedRegions()
        if regionCount > 1:
            warnings.append(f"Mesh contains {regionCount} disconnected components.")

        bounds = inputPolyData.GetBounds()
        extents = (bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4])
        if any(extent <= 0 for extent in extents):
            warnings.append("Mesh bounds are degenerate (zero thickness in at least one axis).")

        return warnings

    repaired = repairPolyData(polyData, holeSize=100.0, enablePrintMode=printMode)
    issues = validatePolyData(repaired)
    if issues:
        repaired = repairPolyData(repaired, holeSize=10000.0, enablePrintMode=printMode)
        issues = validatePolyData(repaired)
    if issues:
        raise ValueError(
            "STL validation failed after repair: " + "; ".join(issues)
        )

    writer = vtk.vtkSTLWriter()
    writer.SetFileName(stlPath)
    writer.SetFileTypeToBinary()
    writer.SetInputData(repaired)
    writer.Write()

    return stlPath


def validateSTL(stlPath: str) -> list[str]:
    """
    Perform lightweight printability checks on an STL file.

    Returns a list of warning strings. Empty list means no issues detected.
    """
    import os
    import vtk

    warnings = []
    if not os.path.exists(stlPath):
        return [f"STL file was not written: {stlPath}"]
    if os.path.getsize(stlPath) == 0:
        return [f"STL file is empty: {stlPath}"]

    reader = vtk.vtkSTLReader()
    reader.SetFileName(stlPath)
    reader.Update()
    polyData = reader.GetOutput()

    if polyData is None or polyData.GetNumberOfPoints() == 0 or polyData.GetNumberOfCells() == 0:
        return ["STL has no valid geometry (0 points or 0 cells)."]

    featureEdges = vtk.vtkFeatureEdges()
    featureEdges.SetInputData(polyData)
    featureEdges.BoundaryEdgesOn()
    featureEdges.NonManifoldEdgesOn()
    featureEdges.ManifoldEdgesOff()
    featureEdges.FeatureEdgesOff()
    featureEdges.Update()
    problematicEdgeCount = featureEdges.GetOutput().GetNumberOfCells()
    if problematicEdgeCount > 0:
        warnings.append(
            f"Mesh is not watertight or contains non-manifold edges ({problematicEdgeCount} problematic edges)."
        )

    connectivity = vtk.vtkPolyDataConnectivityFilter()
    connectivity.SetInputData(polyData)
    connectivity.SetExtractionModeToAllRegions()
    connectivity.Update()
    regionCount = connectivity.GetNumberOfExtractedRegions()
    if regionCount > 1:
        warnings.append(f"Mesh contains {regionCount} disconnected components.")

    bounds = polyData.GetBounds()
    extents = (bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4])
    if any(extent <= 0 for extent in extents):
        warnings.append("Mesh bounds are degenerate (zero thickness in at least one axis).")

    return warnings
