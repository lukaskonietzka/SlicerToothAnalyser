"""
Author:    Peter Rösch, peter.roesch@tha.de

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY
--------------------------------------------------------------------

This package contains all the logic required to
calculate an anatomical segmentation of one or more tooth µCTs
"""

import argparse
import os
from typing import TextIO

import numba
import numpy as np
import SimpleITK as sitk

from .filtering import downsample_2_numba


def _get_label_set(arr: np.ndarray, background_label: int = 0) -> set[int]:
    """
    Get the label set from an input array.

    Args:
        arr (np.ndarra): Input array
        background_label (int): Background label, defaults is 0

    Returns:
        set[int]: The set of unique labels extracted from
        the input array
    """
    label_array = np.unique(arr.reshape(-1))
    return set(label_array) - set((background_label,))


@numba.njit(parallel=True)
def _label_stats_numba(
    arr1: np.ndarray,
    arr2: np.ndarray,
    label_array: np.ndarray,
):
    intersection_array = np.zeros(
        shape=(label_array.shape[0]), dtype=np.uint64
    )
    union_array = np.zeros(shape=(label_array.shape[0]), dtype=np.uint64)

    arr1 = arr1.reshape(-1)
    arr2 = arr2.reshape(-1)

    max_index = label_array.shape[0]
    for l in numba.prange(max_index):  # pylint: disable=not-an-iterable
        label = label_array[l]
        for i in range(arr1.shape[0]):
            if arr1[i] == label:
                union_array[l] += 1
            if arr2[i] == label:
                if arr1[i] == arr2[i]:
                    intersection_array[l] += 1
                else:
                    union_array[l] += 1

    result_array = np.zeros(
        shape=2 * (1 + label_array.shape[0]), dtype=np.float32
    )
    # overall iou and dice
    iou_all = intersection_array.sum() / union_array.sum()
    dice_all = 2 * iou_all / (1 + iou_all)
    result_array[0] = iou_all
    result_array[1] = dice_all
    for i in range(intersection_array.shape[0]):
        iou = intersection_array[i] / union_array[i]
        dice = 2 * iou / (1 + iou)
        result_array[2 + 2 * i] = iou
        result_array[2 + 2 * i + 1] = dice
    return result_array


def store_segmentation_metrics(
    arr1: np.array,
    arr2: np.array,
    pattern: str,
    out_file: TextIO,
    background_label: int = 0,
) -> None:
    """
    Calculate segmentation metrics betwen two arrays and write the
    results to a file.

    Args:
        arr1_nd (np.ndarray): First array
        arr2_nd (np.ndarray): Scond array
        pattern (str): The pattern to use for writing the results.
        out_file (TextIO): The file object to write the results to.
        background_label (int): Background label, default is 0.

    Returns:
        None: This function does not return anything.
    """

    labels_1 = _get_label_set(arr1, background_label=background_label)
    labels_2 = _get_label_set(arr2, background_label=background_label)
    common_labels = []
    #
    # exclude labels which are present in one image only
    for label_tuple, arr, im_name in (
        ((labels_1, labels_2), arr1, "first image"),
        ((labels_2, labels_1), arr2, "second image"),
    ):
        for l in label_tuple[0]:
            if l not in label_tuple[1]:
                print(f"Warning: ignoring label {l} in {im_name}")
                arr[arr == l] = background_label
            else:
                if l not in common_labels:
                    common_labels.append(l)
    common_label_array = np.array(common_labels, dtype=np.uint8)
    dice_array = _label_stats_numba(arr1, arr2, common_label_array)
    out_file.write(f"{pattern} {dice_array[0]} {dice_array[1]} ")
    # Coefficients for individual labels
    for i, label in enumerate(common_labels):
        if label != background_label:
            out_file.write(f"{label} ")
            out_file.write(f"{dice_array[2*i+2]} ")
            out_file.write(f"{dice_array[2*i+3]} ")
    out_file.write("\n")


def _process_image_pair(
    im1_name: str, im2_name: str, pattern: str, out_file: TextIO
):
    im1 = sitk.ReadImage(im1_name)
    im2 = sitk.ReadImage(im2_name)
    im1_basename = os.path.basename(im1_name)
    im2_basename = os.path.basename(im2_name)
    # check geometry
    if (
        im1.GetOrigin() != im2.GetOrigin()
    ) or im1.GetDirection() != im2.GetDirection():
        raise ValueError(
            f"{im1_basename} / {im2_basename}: Geometry mismatach"
        )
    else:
        arr1 = sitk.GetArrayFromImage(im1).astype(np.uint8)
        arr2 = sitk.GetArrayFromImage(im2).astype(np.uint8)
        # downsample if required
        if arr1.shape != arr2.shape:
            arr1_half_shape = tuple(s // 2 for s in arr1.shape)
            im1_spacing = im1.GetSpacing()
            im1_double_spacing = tuple(s * 2 for s in im1_spacing)
            arr2_half_shape = tuple(s // 2 for s in arr2.shape)
            im2_spacing = im2.GetSpacing()
            im2_double_spacing = tuple(s * 2 for s in im2_spacing)
            if arr1.shape == arr2_half_shape and np.allclose(
                im1_spacing, im2_double_spacing
            ):
                print(f"Downsampling image {im2_basename} by factor 2")
                arr2 = downsample_2_numba(arr2, use_median=True)
            elif arr2.shape == arr1_half_shape and np.allclose(
                im2_spacing, im1_double_spacing
            ):
                print(f"Downsampling image {im1_basename} by factor 2")
                arr1 = downsample_2_numba(arr1, use_median=True)
            else:
                raise ValueError("Incompatible image sizes or spacings")
        store_segmentation_metrics(arr1, arr2, pattern, out_file)


def create_segmentation_metrics_file(
    list_file_name: str, output_file_name: str
) -> None:
    """
    Creates a segmentation metrics file by reading a list file and
    storing the segmentation metrics for each image pair.

    Args:
        list_file_name (str): The name of the list file containing the
            image pair information.
        output_file_name (str): The name of the output file to store the
            segmentation metrics.

    Returns:
        None
    """
    with open(output_file_name, "w", encoding="utf8") as out_file:
        out_file.write("# pattern iou_mean dice_mean ")
        out_file.write("label_i iou_i dice_i ...\n")
        with open(list_file_name, "r", encoding="utf8") as list_file:
            for line in list_file:
                line = line.strip()
                if len(line) > 0 and line[0] != "#":
                    im1_name, im2_name, pattern = line.split()
                    _process_image_pair(im1_name, im2_name, pattern, out_file)


def metrics_main():
    """
    Calculate segmentation metrics for a set of files.

    Args:
        list_file_name (str): The name of a file containing the image list.
        output_file_name (str): The name of the output file.

    Returns:
        None
    """
    parser = argparse.ArgumentParser(
        description="Calculate segmentation metrics for a set of files",
        epilog="Uses SimpleITK for image I/O",
    )
    parser.add_argument(
        "list_file_name",
        type=str,
        help="Name of a file containing the image list",
    )
    parser.add_argument(
        "output_file_name",
        type=str,
        help="Name of a the output file",
    )

    args = parser.parse_args()

    create_segmentation_metrics_file(
        list_file_name=args.list_file_name,
        output_file_name=args.output_file_name,
    )
