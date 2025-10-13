"""
ToothAnalyserLib.tha.filtering
==============================
This module provides a set of image processing utilities for 3D medical and dental image analysis,
implemented using SimpleITK, NumPy, and Numba for high-performance computation.

The functions in this module support label manipulation, spatial downsampling, and several filtering
methods commonly used for volumetric image preprocessing and noise reduction.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY

Example Usage
-------------
In Python:
    import ToothAnalyserLib.tha.filtering as filtering
    filtering.replace_labels(image, old_labels=(1, 2), new_labels=(10, 20))
    filtering.downsample_2("input.nii.gz", "output.nii.gz", use_median=True)

From the command line:
    $ python -m ToothAnalyserLib.tha.filtering downsample_2_main input.nii.gz output.nii.gz --use_median

Authors
-------
- Peter Rösch, peter.roesch@tha.de
- Lukas Konietzka, lukas.konietzka@tha.de
"""

import argparse

import numpy as np
import SimpleITK as sitk
import slicer
from typing import Union

try:
    import numba
except ModuleNotFoundError:
    if slicer.util.confirmOkCancelDisplay(
            "This module requires the 'numba' Python package. Click OK to install it now."):
        slicer.util.pip_install("numba")


@numba.njit(parallel=True)
def _replace_label_numba_uint8(
    im_array: np.ndarray, old_gval: np.uint8, new_gval: np.uint8
) -> None:
    """
    A Numba-optimized function that replaces a specific value with another
    value in a NumPy array.

    Parameters:
        im_array (np.ndarray): Input NumPy array.
        old_gval (np.uint8): The old value to be replaced.
        new_gval (np.uint8): The new value to replace the old value with.
    """
    im_array_1d = im_array.reshape((-1,))
    i_max = im_array_1d.shape[0]
    for i in numba.prange(i_max):  # pylint: disable=not-an-iterable
        if im_array_1d[i] == old_gval:
            im_array_1d[i] = new_gval


def replace_labels(
    in_im: sitk.Image, old_labels: tuple[int], new_labels: tuple[int]
) -> sitk.Image:
    """
    Replaces specified labels in an input image with new labels.

    Args:
        in_im (sitk.Image): The input image.
        old_labels (tuple[int]): The labels to be replaced.
        new_labels (tuple[int]): The new labels to replace the old labels with.

    Returns:
        sitk.Image: The output image with the specified labels replaced.
    """
    in_np_data = sitk.GetArrayFromImage(in_im)
    for old, new in zip(old_labels, new_labels):
        _replace_label_numba_uint8(in_np_data, old, new)
    out_im = sitk.GetImageFromArray(in_np_data)
    out_im.SetSpacing(in_im.GetSpacing())
    out_im.SetOrigin(in_im.GetOrigin())
    out_im.SetDirection(in_im.GetDirection())
    return out_im


@numba.njit(parallel=True)
def downsample_2_numba(
    in_array: np.ndarray, use_median: bool = False
) -> np.ndarray:
    """
    Downsamples a 3D array using the mean filter. Numba is used to speed
    up and to parallelise the calculations.

    Args:
    in_array (ndarray): The input 3D array to be downsampled.
    use_median (bool): Use median value if true. otherwise use mean.


    Returns:
        out_array (ndarray): The output 3D array where the downsampled
            values are stored.
    """
    out_shape = (
        in_array.shape[0] // 2,
        in_array.shape[1] // 2,
        in_array.shape[2] // 2,
    )
    out_array = np.zeros(shape=out_shape, dtype=in_array.dtype)
    out_maxvalue = np.iinfo(out_array.dtype).max
    z_max = out_array.shape[0]
    for out_z in numba.prange(z_max):  # pylint: disable=not-an-iterable
        z = out_z * 2
        for out_y in range(out_array.shape[1]):
            y = out_y * 2
            for out_x in range(out_array.shape[2]):
                x = out_x * 2
                if use_median:
                    out_array[out_z, out_y, out_x] = np.median(
                        np.array(
                            (
                                in_array[z, y, x],
                                in_array[z, y, x + 1],
                                in_array[z, y + 1, x],
                                in_array[z, y + 1, x + 1],
                                in_array[z + 1, y, x],
                                in_array[z + 1, y, x + 1],
                                in_array[z + 1, y + 1, x],
                                in_array[z + 1, y + 1, x + 1],
                                # make sure that median is called with an odd
                                # number of arguments, otherwise mean values
                                # will be generated
                                out_maxvalue,
                            ),
                            dtype=out_array.dtype,
                        )
                    )
                else:
                    out_array[out_z, out_y, out_x] = np.mean(
                        np.array(
                            (
                                in_array[z, y, x],
                                in_array[z, y, x + 1],
                                in_array[z, y + 1, x],
                                in_array[z, y + 1, x + 1],
                                in_array[z + 1, y, x],
                                in_array[z + 1, y, x + 1],
                                in_array[z + 1, y + 1, x],
                                in_array[z + 1, y + 1, x + 1],
                            ),
                            dtype=out_array.dtype,
                        )
                    )
    return out_array


def downsample_2(
    in_file_name: str,
    out_file_name: str,
    use_median: bool = False,
    adapt_origin: bool = True,
    convert_to_uint8: bool = False,
) -> None:
    """
    Downsample an image by a factor of 2 by applying either averaging or
    median filtering to the voxels of the input image.

    Args:
        in_file_name (str): Name of the input image to read.
        out_file_name (str): Name of the output image to write.
        use_median (bool): Apply median filtering. Default is False
            (apply  grey value averaging).
        adapt_origin (bool): Adapt origin of output image to new resolution.
            Default ist True (perform origin adaption).
        convert_to_uint8: Rescale grey values to 0..255 and cast to uint8.
    """
    in_im = sitk.ReadImage(in_file_name)
    in_im_array = sitk.GetArrayFromImage(in_im)
    out_im_array = downsample_2_numba(in_im_array, use_median)
    out_im = sitk.GetImageFromArray(out_im_array)
    out_im.SetDirection(in_im.GetDirection())
    in_spacing = in_im.GetSpacing()
    out_spacing = tuple([s * 2 for s in in_spacing])
    out_im.SetSpacing(out_spacing)
    if adapt_origin:
        out_origin = in_im.TransformContinuousIndexToPhysicalPoint(
            (0.5, 0.5, 0.5)
        )
    else:
        out_origin = in_im.GetOrigin()
    out_im.SetOrigin(out_origin)
    if out_im.GetPixelID() != sitk.sitkUInt8 and convert_to_uint8:
        if not use_median:
            out_im = sitk.RescaleIntensity(out_im, 0, 255)
        out_im = sitk.Cast(out_im, sitk.sitkUInt8)
    sitk.WriteImage(out_im, out_file_name)


def downsample_2_main():
    """
    Downsample an image by a factor of 2 by applying either averaging or
    median filtering to the voxels of the input image.

    Args:
        in_file_name (str): Name of the input image to read.
        out_file_name (str): Name of the output image to write.
        use_median (bool): Apply median filtering. Default is False
            (apply  grey value averaging).
        adapt_origin (bool): Adapt origin of output image to new resolution.
            Default ist True (perform origin adaption).
        convert_to_uint8: Rescale grey values to 0..255 and cast to uint8.
    """
    parser = argparse.ArgumentParser(
        description="Downsample imgage by a factor of 2",
        epilog="Uses the SimpleITK package for image I/O, scaling and resampling",
    )
    parser.add_argument(
        "in_file_name",
        type=str,
        help="Name of the image file to be downsampled",
    )
    parser.add_argument(
        "out_file_name",
        type=str,
        help="Name of the output image file",
    )
    parser.add_argument(
        "--use_median",
        help="Use median rather than averaging. Recommended for label images.",
        action="store_true",
    )
    parser.add_argument(
        "--keep_origin",
        help="Do not adapt the origin to the lower resolution",
        action="store_true",
    )
    parser.add_argument(
        "--convert_to_uint8",
        help="Rescale and convert voxxels to 8 bit unsigned int",
        action="store_true",
    )
    args = parser.parse_args()
    downsample_2(
        args.in_file_name,
        args.out_file_name,
        args.use_median,
        not args.keep_origin,
        args.convert_to_uint8,
    )


def bilateral_filter(
    in_file_name: str,
    out_file_name: str,
    domain_sigma: Union[int, float],
    range_sigma: Union[int, float],
    nr_of_samples: int,
) -> None:
    """
    Apply a bilateral filter to an image.

    Args:
        in_file_name (str): The path to the input image file.
        out_file_name (str): The path to save the filtered image.
        domain_sigma (int | float): The sigma value for the spatial domain.
        range_sigma (int | float): The sigma value for the intensity range domain.
        nr_of_samples (int): The number of samples for the range domain.

    Returns:
        None
    """
    in_im = sitk.ReadImage(in_file_name)
    result_im = sitk.Bilateral(
        in_im,
        domainSigma=domain_sigma,
        rangeSigma=range_sigma,
        numberOfRangeGaussianSamples=nr_of_samples,
    )
    sitk.WriteImage(result_im, out_file_name)


def bilateral_main():
    """
    Perform 3D bilateral filtering.

    This function takes in the name of the input image file, the name of
    the output image file, the domain sigma value (in the same unit as the
    image spacing), the range sigma value (in grey level units), and the number
    of samples (voxels) as arguments. It uses the SimpleITK package to perform
    the bilateral filtering operation.

    Args:
        in_file_name (str): Name of input image file.
        out_file_name (str): Name of output image file.
        domain_sigma (float): Domain sigma value (in the same unit as the
            image spacing).
        range_sigma (float): Range sigma value (in grey level units).
        nr_of_samples (int): Number of samples (voxels).

    Returns:
    - None
    """
    parser = argparse.ArgumentParser(
        description="Perform 3D bilateral filtering",
        epilog="Uses the SimpleITK package",
    )
    parser.add_argument(
        "in_file_name",
        type=str,
        help="Name of input image file",
    )
    parser.add_argument(
        "out_file_name",
        type=str,
        help="Name of output image file",
    )
    parser.add_argument(
        "domain_sigma",
        type=float,
        help="Domain sigma value (same unit as image spacing)",
    )
    parser.add_argument(
        "range_sigma",
        type=float,
        help="Range sigma value (grey level units)",
    )
    parser.add_argument(
        "nr_of_samples",
        type=int,
        help="Number of samples (voxels)",
    )
    args = parser.parse_args()
    bilateral_filter(
        args.in_file_name,
        args.out_file_name,
        args.domain_sigma,
        args.range_sigma,
        args.nr_of_samples,
    )


def bm4d_filter(
    in_file_name: str, out_file_name: str, sigma_psd: Union[int, float]
) -> None:
    """
    Apply bm4d filtering to an image,
    https://pypi.org/project/bm4d

    Args:
        in_file_name (str): The path to the input image file.
        out_file_name (str): The path to save the filtered image.
        sigma_psd (int | float): White noise sigma value.

    Returns:
        None
    """
    in_im = sitk.ReadImage(in_file_name)
    in_array = sitk.GetArrayFromImage(in_im)
    in_min = in_array.min()
    in_max = in_array.max()
    in_range = in_max - in_min
    result_array = bm4d(in_array, sigma_psd)
    result_min = result_array.min()
    result_max = result_array.max()
    result_range = result_max - result_min
    result_array = (result_array.astype(np.float64) - result_min) / (
        result_range
    ) * in_range + in_min
    result_array = result_array.astype(in_array.dtype)
    result_im = sitk.GetImageFromArray(result_array)
    result_im.SetSpacing(in_im.GetSpacing())
    result_im.SetOrigin(in_im.GetOrigin())
    result_im.SetDirection(in_im.GetDirection())
    sitk.WriteImage(result_im, out_file_name)


def bm4d_main():
    """
    Perform 3D bm4d filtering.

    This function takes in the name of the input image file, the name of
    the output image file and the white noise sigma value (in grey level units).
    It uses the bm4d package to perform the filtering.

    Args:
        in_file_name (str): Name of input image file.
        out_file_name (str): Name of output image file.
        sigma_psd (float): White noise sigma.

    Returns:
    - None
    """
    parser = argparse.ArgumentParser(
        description="Perform 3D bm4d filtering",
        epilog="Uses the bm4d python package, https://pypi.org/project/bm4d",
    )
    parser.add_argument(
        "in_file_name",
        type=str,
        help="Name of input image file",
    )
    parser.add_argument(
        "out_file_name",
        type=str,
        help="Name of output image file",
    )
    parser.add_argument(
        "sigma_psd",
        type=float,
        help="White noise sigma",
    )
    args = parser.parse_args()
    bm4d_filter(
        args.in_file_name,
        args.out_file_name,
        args.sigma_psd,
    )
