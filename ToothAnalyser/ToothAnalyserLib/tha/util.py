"""
ToothAnalyserLib.tha.util
=========================

This module provides various utility functions for handling, converting,
and visualizing µCT image data used in the ToothAnalyser framework.

It includes tools for matching corresponding image files between directories,
reading and converting Scanco ISQ image files to MetaImage (MHD) or other formats,
and comparing intensity profiles across multiple 3D images.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY.

Example Usage
-------------
In Python:
    import ToothAnalyserLib.tha.util as util
    util.convert_isq("sample.isq", "sample.nii.gz")
    util.corresponding_files_to_file("dirA", "dirB", r"(\d+)", ".bak", "pairs.txt")

From the command line:
    $ python -m ToothAnalyserLib.tha.util convert_isq_main sample.isq sample.nii.gz

Author
-------
Peter Rösch, peter.roesch@tha.de
Lukas Konietzka, lukas.konietzka@tha.de
"""


import argparse
from collections.abc import Sequence
from collections import OrderedDict
import os
from pathlib import Path
import re
import sys
from tempfile import TemporaryDirectory

import SimpleITK as sitk
import numpy as np
import matplotlib.pyplot as plt


def corresponding_files_to_file(
    dir_1_name: str,
    dir_2_name: str,
    regular_expression: str,
    excluded_suffix: str,
    out_file_name: str,
) -> None:
    """
    Generates a list of corresponding files in two directories
    based on a regular expression pattern.

    Args:
        dir_1_name (str): The name of the first directory.
        dir_2_name (str): The name of the second directory.
        regular_expression (str): The regular expression pattern
            used to match file names.
        excluded_suffix (str): The suffix to be excluded from the
            file names.
        out_file_name (str): The name of the output file.

    Returns:
        None
    """
    pattern = re.compile(regular_expression)
    file_name_list_1 = []
    file_name_list_2 = []
    for dir_name, file_name_list in (
        (dir_1_name, file_name_list_1),
        (dir_2_name, file_name_list_2),
    ):
        for entry in Path(dir_name).iterdir():
            if entry.is_file():
                file_name = entry.name
                matches = pattern.findall(file_name)
                if len(matches) == 1:
                    if (suffix_len := len(excluded_suffix)) > 0 and file_name[
                        -suffix_len:
                    ] != excluded_suffix:
                        file_name_list.append((entry.resolve(), matches[0]))
        file_name_list.sort(key=lambda entry: entry[1])

    with open(out_file_name, mode="w", encoding="utf8") as out_file:
        out_file.write("# call arguments:\n")
        out_file.write(f"#     {dir_1_name = }\n")
        out_file.write(f"#     {dir_2_name = }\n")
        out_file.write(f"#     {regular_expression = }\n")
        out_file.write(f"#     {excluded_suffix = }\n#\n")
        out_file.write("# format:\n")
        out_file.write("#     file_name_1 file_name_2 matched_expression\n#\n")
        for name_1, key_1 in file_name_list_1:
            for name_2, key_2 in file_name_list_2:
                if key_1 == key_2:
                    out_file.write(f"{name_1} {name_2} {key_1}\n")
                    break


def corresponding_files_main():
    """
    Collect corresponding file names from two directories using
    Python regular expressions.

    Args:
        dir_1_name (str): Name of the first directory containing files.
        dir_2_name (str): Name of the second directory containing files.
        regular_expression (str): Regular expression pattern to match file names.
        excluded_suffix (str): Suffix to exclude files ending with.
        out_file_name (str): Output file name.
            Output Format: file_name_1 file_name_2 matched_expression

    Returns:
        None
    """
    parser = argparse.ArgumentParser(
        description="Collect corresponding file names from two directories",
        epilog="Uses Python regular expressions",
    )
    parser.add_argument(
        "dir_1_name",
        type=str,
        help="Name of first directory containing files",
    )
    parser.add_argument(
        "dir_2_name",
        type=str,
        help="Name of second directory containing files",
    )
    parser.add_argument(
        "regular_expression",
        type=str,
        help="regular expression (Don't forget to put it in quotes)",
    )
    parser.add_argument(
        "excluded_suffix",
        type=str,
        help="exclude files ending with this suffix",
    )
    parser.add_argument(
        "out_file_name",
        type=str,
        help=(
            "Output file name."
            + " Format: file_name_1 file_name_2 matched_expression"
        ),
    )

    args = parser.parse_args()
    corresponding_files_to_file(
        args.dir_1_name,
        args.dir_2_name,
        args.regular_expression,
        args.excluded_suffix,
        args.out_file_name,
    )


def _array_profiles(
    image: sitk.Image, centre_pos: Sequence[int]
) -> Sequence[tuple[np.ndarray, np.ndarray]]:
    image_spacing = image.GetSpacing()[::-1]
    image_size = image.GetSize()[::-1]
    grey_array = sitk.GetArrayFromImage(image)
    profiles = []
    for i in range(grey_array.ndim):
        horizontal_values = np.linspace(
            start=0, stop=image_size[i] * image_spacing[i], num=image_size[i]
        )
        slc = []
        for k in range(grey_array.ndim):
            if k != i:
                slc.append(slice(centre_pos[k], centre_pos[k] + 1))
            else:
                slc.append(slice(0, image_size[k]))
        vertical_values = grey_array[tuple(slc)].reshape(-1)
        profiles.append((horizontal_values, vertical_values))
    return profiles[::-1]


def _plot_profiles(
    profiles: Sequence[tuple[np.ndarray, np.ndarray]],
    labels: Sequence[str],
    styles: Sequence[str],
    title: str,
    axes_names: Sequence[str],
) -> None:
    plots = []
    figures = []
    for _ in range(len(axes_names)):
        fig = plt.figure()
        figures.append(fig)
        plots.append(fig.add_subplot(111))
    for i, profile in enumerate(profiles):
        for k, name in enumerate(axes_names):
            (pts,) = plots[k].plot(profile[k][0], profile[k][1], styles[i])
            pts.set_label(labels[i])
            plots[k].set_xlabel("Position / mm")
            plots[k].set_ylabel("Grey Value")
            plots[k].set_title(f"{title}, {name} direction")
            plots[k].legend()
    if "ipykernel" not in sys.modules:
        for fig in figures:
            fig.show()


def profile_comparison(
    image_names: Sequence[str],
    centre_pos_xyz: Sequence[int],
    styles: list[str],
    title: str,
    labels: list[str] = None,
) -> None:
    """
    Support comparison of images by plotting grey value profiles.

    Args:
        image_names: List containing file names of images to be compared.
        centre_pos_xyz: Point in voxel coordinates where all profiles meet.
        styles: list of plot styles, e.g ['r.', 'b-']
        title: Plot title
        labels: List of plot labels. Default is None in which case
            the image names are used as labels.
    """
    profiles = []
    if labels is None:
        label_list = []
    else:
        if len(labels) != len(image_names):
            raise ValueError("Lengths of image name and label list must agree")
        else:
            label_list = labels
    image_size = None
    image_spacing = None
    for image_name in image_names:
        image = sitk.ReadImage(image_name)
        if image_size is None:
            image_size = image.GetSize()
        elif image.GetSize() != image_size:
            raise ValueError("Image sizes must agree")
        if image_spacing is None:
            image_spacing = image.GetSpacing()
        elif image.GetSpacing() != image_spacing:
            raise ValueError("Image spacings must agree")
        if labels is None:
            label_list.append(os.path.basename(image_name))
        profiles.append(_array_profiles(image, centre_pos_xyz[::-1]))
    _plot_profiles(profiles, labels, styles, title, ("x", "y", "z"))


# positions of relevant parameters in ISQ header. Numbers correspond
# to indices in a np.int32 array.
# Source: http://www.scanco.ch/en/support/customer-login/\
#                           faq-customers/faq-customers-general.html
__ISQ_OFFSETS_INT_4 = {
    "dimx_p": 11,
    "dimy_p": 12,
    "dimz_p": 13,
    "dimx_um": 14,
    "dimy_um": 15,
    "dimz_um": 16,
    "slice_thickness": 17,
    "slice_increment_um": 18,
    "slice_1_pos_um": 19,
    "min_data_value": 20,
    "max_data_value": 21,
    "mu_scaling": 22,
    "energy": 42,
    "intensity": 43,
    "data_offset": -1,
}

# Default values for mhd file parameters
__MHD_DEFAULTS = OrderedDict(
    [
        ("ObjectType", "Image"),
        ("NDims", "3"),
        ("BinaryData", "True"),
        ("BinaryDataByteOrderMSB", "False"),
        ("CompressedData", "False"),
        ("TransformMatrix", "1 0 0 0 1 0 0 0 1"),
        ("Offset", "0 0 0"),
        ("CenterOfRotation", "0 0 0"),
        ("AnatomicalOrientation", "RAI"),
        ("ElementSpacing", "1 1 1"),
        ("DimSize", "1 1 1"),
        ("HeaderSize", "-1"),
        ("ElementType", "MET_SHORT"),
    ]
)


def _read_isq_param(
    in_file_name: str,
) -> tuple[OrderedDict, int, tuple[int, int]]:
    """
    Read parameters from ISQ file into OrderedDict

    Args:
        in_file_name (str): Input file name including suffix
    Returns:
        tuple of
            OrderedDict containing parameters in mhd style,
            offset of ISQ file data part in bytes
            grey value range (tuple)
    """
    param = __MHD_DEFAULTS.copy()
    isq_header = np.fromfile(in_file_name, np.int32, 128)
    # swap bytes if required
    if sys.byteorder == "big":
        isq_header = isq_header.byteswap()
    dim_p_str = ""
    element_spacing_str = ""
    # load image dimensions and calculate element spacing
    for i in range(3):
        dim_p = isq_header[__ISQ_OFFSETS_INT_4["dimx_p"] + i]
        dim_um = isq_header[__ISQ_OFFSETS_INT_4["dimx_um"] + i]
        dim_p_str += str(dim_p) + " "
        element_spacing_mm = dim_um / dim_p / 1000.0
        element_spacing_str += str(element_spacing_mm) + " "
    # get grey value range for windowing
    grey_min = isq_header[__ISQ_OFFSETS_INT_4["min_data_value"]]
    grey_max = isq_header[__ISQ_OFFSETS_INT_4["max_data_value"]]
    # set mhd parameters
    param["DimSize"] = dim_p_str[:-1]
    param["ElementSpacing"] = element_spacing_str[:-1]
    param["ElementType"] = "MET_SHORT"
    param["HeaderSize"] = "-1"
    param["ISQ_slice_thickness_um"] = str(
        isq_header[__ISQ_OFFSETS_INT_4["slice_thickness"]]
    )
    param["ISQ_slice_increment_um"] = str(
        isq_header[__ISQ_OFFSETS_INT_4["slice_increment_um"]]
    )
    param["ISQ_slice_1_pos_um"] = str(
        isq_header[__ISQ_OFFSETS_INT_4["slice_1_pos_um"]]
    )
    param["ISQ_min_data_value"] = str(grey_min)
    param["ISQ_max_data_value"] = str(grey_max)
    param["ISQ_mu_scaling"] = str(
        isq_header[__ISQ_OFFSETS_INT_4["mu_scaling"]]
    )
    param["ISQ_energy_V"] = str(isq_header[__ISQ_OFFSETS_INT_4["energy"]])
    param["ISQ_intensity_muA"] = str(
        isq_header[__ISQ_OFFSETS_INT_4["intensity"]]
    )
    param["ElementDataFile"] = os.path.basename(in_file_name)
    # calculate offset for grey value loading
    offset = (isq_header[__ISQ_OFFSETS_INT_4["data_offset"]] + 1) * 512
    grey_range = (grey_min, grey_max)
    return param, offset, grey_range


def isq_to_mhd(isq_file_name: str, mhd_file_name: str) -> None:
    """
    Convert ISQ file into meta image file
    ARGS:
        isq_file_name (str): full path name of isq image file
        mhd_file_name (str): name of mhd file to be written
    """
    mhd_param, _, _ = _read_isq_param(isq_file_name)
    if os.sep in mhd_file_name:
        mhd_param["ElementDataFile"] = os.path.abspath(isq_file_name)
    else:
        mhd_param["ElementDataFile"] = isq_file_name
    with open(mhd_file_name, "w", encoding="utf8") as out_file:
        for i in mhd_param.items():
            out_file.write(i[0] + " = " + i[1] + "\n")


def isq_to_mhd_main():
    """
    Convert ISQ to mhd image file.

    Args:
        isq_file_name (str): full path name of isq image file
        mhd_file_name (str): name of mhd file to be written
    """
    parser = argparse.ArgumentParser(
        description="Convert ISQ file to meta image format",
        epilog="The mhd file uses raw data of the original ISQ file.",
    )
    parser.add_argument(
        "isq_file_name",
        type=str,
        help="Name of input ISQ file",
    )
    parser.add_argument(
        "mhd_file_name",
        type=str,
        help="Name of output mhd file",
    )

    args = parser.parse_args()
    isq_to_mhd(
        args.isq_file_name,
        args.mhd_file_name,
    )


def convert_isq(
    isq_file_name: str, out_file_name: str, convert_to_uint8: bool = True
) -> None:
    """
    Convert ISQ file to other image file formats.

    Args:
        isq_file_name (str): Name of ISQ file to be converted.
        out_file_name (str): Output file name. The format is
            deduced from the file suffix.
        convert_to_uint8 (bool): Rescale and convert image to uint8
    """
    with TemporaryDirectory() as tmp_dir_name:
        mhd_file_name = os.path.join(tmp_dir_name, "tmp.mhd")
        isq_to_mhd(isq_file_name, mhd_file_name)
        im = sitk.ReadImage(mhd_file_name)
        if convert_to_uint8:
            im = sitk.RescaleIntensity(im, 0, 255)
            im = sitk.Cast(im, sitk.sitkUInt8)
        sitk.WriteImage(im, out_file_name)


def convert_isq_main():
    """
    Convert ISQ file to other image file formats.

    Args:
        isq_file_name (str): Name of ISQ file to be converted.
        out_file_name (str): Output file name. The format is
            deduced from the file suffix.
        convert_to_uint8 (bool): Rescale and convert image to uint8
    """
    parser = argparse.ArgumentParser(
        description="Convert ISQ file to other image formats.",
        epilog="Uses SimpleITK for Image I/O, rescaling and casting.",
    )
    parser.add_argument(
        "isq_file_name",
        type=str,
        help="Name of input ISQ file",
    )
    parser.add_argument(
        "out_file_name",
        type=str,
        help="Name of output file. The format is determined by the suffix.",
    )
    parser.add_argument(
        "--convert_to_uint8",
        help="Rescale and convert ISQ image to 8 bit unsigned int pixel type",
        action="store_true",
    )

    args = parser.parse_args()
    convert_isq(
        args.isq_file_name,
        args.out_file_name,
        args.convert_to_uint8,
    )
