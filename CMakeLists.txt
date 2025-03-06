cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(SlicerToothAnalyser)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://www.slicer.org/wiki/Documentation/Nightly/Extensions/SlicerToothAnalyser")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_CONTRIBUTORS "Lukas Konietzka (Technical University of Applied Sciences), Simon Hofmann (Technical University of Applied Sciences), Dr. Elias Walter (LMU), Prof. Dr. Peter Roesch (Technical University of Applied Sciences)")
set(EXTENSION_DESCRIPTION "This extension provides specialized preprocessing, segmentation, and analysis features tailored for the analysis of tooth anatomy and pathology starting from microCT.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/lukaskonietzka/SlicerToothAnalyser/main/SlicerToothAnalyser.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/lukaskonietzka/SlicerToothAnalyser/main/Screenshots/fullView.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(ToothAnalyser)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
