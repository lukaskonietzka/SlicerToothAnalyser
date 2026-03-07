"""
ToothAnalyserLib.Algorithm.utils
=================================

This module provides general standard functions and decorators that may be useful for all algorithms.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY.


Author
-------
Lukas Konietzka, lukas.konietzka@tha.de
"""



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

        print(f"{func.__name__}: Done {minutes}:{seconds:02d} minutes")
        return result

    return wrapper


def createSTL(labelImage, outputDirectory: str, fileName: str = "segmentation") -> str:
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

    clean = vtk.vtkCleanPolyData()
    clean.SetInputConnection(surface.GetOutputPort())
    clean.Update()

    writer = vtk.vtkSTLWriter()
    writer.SetFileName(stlPath)
    writer.SetFileTypeToBinary()
    writer.SetInputConnection(clean.GetOutputPort())
    writer.Write()

    return stlPath
