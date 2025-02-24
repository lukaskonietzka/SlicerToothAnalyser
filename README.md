![Screenshot of the application](Screenshots/logo.png)

This 3D Slicer extension is designed for dental research, specifically to support studies at the  
*Poliklinik für Zahnerhaltung und Parodontologie* at LMU Munich.

With this extension, you can apply anatomical segmentation on dental CT scans, dividing the image into  
the segments enamel and dentin.

## Table of Contents
- [1. Introduction and Purpose](#1-introduction-and-purpose)
- [2. Installation](#2-installation)
- [3. Quick Start Guide](#3-quick-start-guide)
- [4. Tutorials](#4-tutorials)
- [5. Explanation](#5-explanation)
- [6. Reference Guide (Developers)](#6-reference-guide-developers)
- [7. Visualize and Save Results](#7-visualize-and-save-results)
- [8. Sample Data](#8-sample-data)
- [9. Contributors and Organisation](#9-contributors-and-organization)

## 1. Introduction and Purpose
As part of a proposal by the Dental Clinic, the goal is to implement automatic detection of cavities in  
micro-CT images using neural networks in the future. Since identifying carious lesions is not trivial,  
this extension is designed to assist with anatomical segmentation of the tooth.

![Screenshot of the application](/Screenshots/fullView.png)  
*Figure 1: Full view of the Tooth Analyser extension.*

## 2. Installation
To install the extension, follow the steps below in the correct order:
1. Download and install the latest stable version of 3D Slicer for your operating system:  
   [https://download.slicer.org](https://download.slicer.org).
2. Start the 3D Slicer application and open the Extension Manager (Menu: **View → Extension Manager**).
3. Search for the extension _ToothAnalyser_ and install it via the **INSTALL** button.

## 3. Quick Start Guide
To use the Tooth Analyser efficiently, follow these steps:

- Start 3D Slicer.  
- Load a CT image using the import function of the 3D Slicer core application (**Menu: Data**). The image does not need filtering.  
- Switch to the Tooth Analyser module (**Modules: Segmentation → Tooth Analyser**).  
- In the **Anatomical Segmentation** section, select the CT image you want to segment.  
- Check the box **Calculate Medial Surface** if medial surfaces should be calculated.  
- Start the algorithm by clicking the **Apply Anatomical** button.  
- The cursor will switch to waiting mode, and a progress bar will appear at the bottom.  

⚠️ **Notice**: The algorithm includes filtering and medial surface calculation. In the worst case  
(large image, medial flattening, filtering), the algorithm can take up to 17 minutes.

## 4. Tutorials
This chapter provides a detailed description of the parameter settings and capabilities of the Tooth Analyser.  
The extension is divided into several functions, each of which can be executed independently.  
This chapter covers all components and explains them in detail.

To start a tutorial, follow this link:  
[Start a Tutorial](Documentation/Tutorial.md)

## 5. Explanation
This chapter provides a detailed introduction to the functionality of the various features of the  
Tooth Analyser. The focus is on the procedure itself rather than the technical implementation.  
For more details, refer to the documentation.

[Check out the Explanation](Documentation/Explanation.md)

## 6. Reference Guide (Developers)
This section provides a technical introduction to the implementation.  
For developers who want to extend or understand this module, this chapter is particularly relevant.  
For more details, refer to the documentation.

[Check out the Reference Guide](Documentation/ReferenceGuide.md)

## 7. Visualize and Save Results
When the algorithm is finished, the results are automatically loaded into the Slicer scene,  
making them immediately accessible. However, you can also perform more detailed analyses with this segmentation.

**Single Process:**
- Open the **Data** module (**Modules: Data**)  
- Toggle the desired segments on and off using the hierarchy  
- Overlap other images  
- Rename the segmentation  
- Save your results via the menu (**Menu: Save**)  

**Batch Process:**
- Load the segmentation via the menu (**Menu: Data**)  
- Load the created label images as segmentation  
- If a 3D model is necessary, create one via the **Segment Editor** module (**Modules: Segment Editor**)  

![Screenshot of the application](./Screenshots/result.gif)  
*Figure 2: Result view in the module Data.*

## 8. Sample Data
The module includes sample data primarily for testing purposes.  
However, they can also be used to gain initial experience with the module.  
The sample data ensures that the module is accessible to everyone.

The sample images are micro-CT scans provided as open-source by the  
*Poliklinik für Zahnerhaltung und Parodontologie*. You can find the sample files  
under the assets in the current release.

You can download sample data here:  
[Download Sample Data](https://github.com/lukaskonietzka/ToothAnalyserSampleData/releases/download/v1.0.0/P01A-C0005278.nii.gz)

⚠️ **Notice**: The Tooth Analyser was specifically developed for CT scans  
with tooth structures, meaning other types of CT scans may result in errors.

## 9. Contributors and Organization
The development of this extension is a collaboration between LMU Munich  
and the Faculty of Computer Science at the Technical University of Augsburg.

- **Lukas Konietzka** _(THA)_  
- **Simon Hofmann** _(THA)_  
- **Dr. med. Elias Walter** _(LMU)_  
- **Prof. Dr. Peter Rösch** _(THA)_  
