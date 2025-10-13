"""
ToothAnalyserLib.SampleData.ToothCrownMicroCT
=================================

This module provides a function to register sample Data in
3D Slicer.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY.

Example Usage
-------------

Author
-------
Lukas Konietzka, lukas.konietzka@tha.de
"""


import SampleData
import os

def registerToothCrownMicroCT():
    """
    This Methode provides sample Data for the module tests
    To ensure that the source code repository remains small
    (can be downloaded and installed quickly) it is recommended to
    store data sets that are larger than a few MB in a GitHub release.
    """

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # fist sample CT -> ToothCrownMicroCT
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        category="General",
        sampleName="ToothCrownMicroCT",
        thumbnailFileName=os.path.join(iconsPath, "SampleData.png"),
        # path to sample image
        uris="https://github.com/lukaskonietzka/ToothAnalyserSampleData/releases/download/v1.0.0/P01A-C0005278.nii.gz",
        fileNames="P01A-C0005278.nii.gz",
        checksums=None,
        nodeNames="ToothCrownMicroCT",
    )