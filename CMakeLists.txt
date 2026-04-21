cmake_minimum_required(VERSION 3.16.3...3.19.7 FATAL_ERROR)

project(ToothAnalyser)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/lukaskonietzka/SlicerToothAnalyser")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_CONTRIBUTORS "Lukas Konietzka, Dr. Elias Walter (Department of Conservative Dentistry, Periodontology and Digital Dentistry at the LMU Hospital, Munich), Simon Hofmann, Prof. Dr. Peter Roesch (Technical University of Augsburg)")
set(EXTENSION_DESCRIPTION "This extension provides specialized preprocessing, segmentation, and analysis features tailored for the analysis of tooth anatomy and pathology starting from microCT.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/lukaskonietzka/SlicerToothAnalyser/main/SlicerToothAnalyser.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/lukaskonietzka/SlicerToothAnalyser/main/Screenshots/fullView.png")
set(EXTENSION_DEPENDS "Numba") # Specified as a list or "NA" if no dependencies

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
