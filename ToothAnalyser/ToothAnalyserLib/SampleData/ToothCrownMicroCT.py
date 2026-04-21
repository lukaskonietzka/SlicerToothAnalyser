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
    Register the raw Tooth Crown MicroCT sample dataset in 3D Slicer.

    The sample is hosted in a GitHub release to keep the extension
    repository lightweight and fast to clone.
    """

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # fist sample CT -> ToothCrownMicroCT
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        category="General",
        sampleName="ToothCrownMicroCTRaw",
        thumbnailFileName=os.path.join(iconsPath, "SampleData.png"),
        # path to sample image
        uris="https://github.com/lukaskonietzka/SlicerToothAnalyser/releases/download/v1.0.0/P01A-C0005278.nii.gz",
        fileNames="P01A-C0005278.nii.gz",
        checksums=None,
        nodeNames="ToothCrownMicroCTRaw",
    )

def registerToothCrownMicroCT8Bit():
    """
    Register the 8-bit Tooth Crown MicroCT sample dataset in 3D Slicer.

    The sample is hosted in a GitHub release to keep the extension
    repository lightweight and fast to clone.
    """

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # fist sample CT -> ToothCrownMicroCT
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        category="General",
        sampleName="ToothCrownMicroCT",
        thumbnailFileName=os.path.join(iconsPath, "SampleData.png"),
        # path to sample image
        uris="https://github.com/lukaskonietzka/SlicerToothAnalyser/releases/download/v1.0.0/Z_149_C0005709_bm4_20.nii",
        fileNames="Z_149_C0005709_bm4_20.nii",
        checksums=None,
        nodeNames="ToothCrownMicroCT",
    )
