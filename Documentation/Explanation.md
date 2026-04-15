# Explanation of the Anatomical Segmentation
This chapter explains the functionality and the algorithmic formulation of the
anatomical segmentation pipeline. The focus is limited to the segmentation logic
itself and does not cover implementation details.

## Table of contents
- [1. Image Input](#1-image-input)
- [2. Image Smoothing](#2-image-smoothing)
- [3. Tooth Separation from the Background](#3-tooth-separation-from-the-background)
- [4. Enamel Segmentation](#4-enamel-segmentation)
- [5. Dentin Derivation](#5-dentin-derivation)
- [6. Label Image Generation](#6-label-image-generation)
- [7. Optional Post-processing: Medial Surfaces](#7-optional-post-processing-medial-surfaces)

To better understand the algorithm, the main steps in the pipeline are shown here.
This chapter briefly covers each of these steps and highlights the most important features.

![pipeline](/Screenshots/asAlgorithm.png)
*Figure 1:* Pipeline steps of the anatomical segmentation, followed by optional post-processing

## 1. Image Input
With the Tooth Analyser, it is generally possible to load all images in common formats.
However, this method is primarily optimized for the -ISQ- format for images from the
company [SCANCO MEDICAL](https://www.scanco.ch). For this reason, the following formats
are distinguished:

- .ISQ (original)
- .mhd (meta image file)
- all other files

[Figure 1 Step 1](#table-of-contents)

## 2. Image Smoothing
When an image is loaded, it must be smoothed in the next step if it has not already been
smoothed. The check to determine whether an image has already been smoothed is based on
the standard deviation of the image. If it is below or above a certain threshold, the
image is considered to be already smoothed.

For the smoothing itself, the Tooth Analyser uses a Median Filter. This belongs to the
group of local operators and considers the direct neighboring pixels to calculate the
smoothed gray value for the currently considered pixel.

[Figure 1 Step 2](#table-of-contents)

## 3. Tooth Separation from the Background
After a smoothed image is available, the next step is to separate the tooth from the
background. For this, the thresholding method is selected, which the user can define via
the UI (Otsu, Renyi). The method then determines an optimal threshold and creates a
binary image that differentiates between the tooth and the background.

In the same step, a mask is created that focuses on the tooth in the image. This mask
is applied to the smoothed image, indicating which part should be considered in the
next step.

[Figure 1 Step 3](#table-of-contents)

## 4. Enamel Segmentation
With the created mask, the same segmentation method as in the previous step can now be
applied to separate the enamel segment from the tooth. The segmentation is again based
on the different shades of gray. The result is a layer in the form of the enamel.

Additionally, fillings and edge smoothing occur, but these should remain untouched
here.

[Figure 1 Step 4](#table-of-contents)

## 5. Dentin Derivation
After the tooth mask and the enamel mask have been determined, the dentin is not
segmented as an independent third structure. Instead, it is derived algorithmically from
the existing segmentation results. The dentin region is defined as the part of the tooth
that remains after removing the enamel mask from the full tooth mask.

*Dentin = Tooth - Enamel*

Functionally, this step completes the anatomical segmentation by assigning the remaining
tooth volume to dentin. In algorithmic terms, it is therefore a mask subtraction step
within the segmentation pipeline. Small additional smoothing or edge-preserving
operations may be applied afterwards to stabilize the result, but they are not part of
the core formulation described here.

[Figure 1 Step 5](#table-of-contents)

## 6. Label Image Generation
In this final step, which relates to segmentation, the layers for enamel and dentin
created in steps 4 and 5 are combined into a labeled file. Color adjustments can also
be made here.

[Figure 1 Step 6](#table-of-contents)

## 7. Optional Post-processing: Medial Surfaces
The creation of medial surfaces is independent of the anatomical segmentation itself and
therefore belongs to optional post-processing rather than to the core segmentation
algorithm. These surfaces are primarily used for the classification of cavities. The
creation of these surfaces is implemented via Laplace interpolation and is technically
the same for both dentin and enamel.

[Figure 1 Step 7 and 8](#table-of-contents)
