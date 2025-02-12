# Explanation
This chapter aims to explain the process of anatomical segmentation in more detail and
delve deeper into the subject. The focus is not on the specific implementation but
rather on the functionality.

## Table of contents
- [1. Loading an image](#1-loading-an-image)
- [2. Smoothing an image](#2-smoothing-an-image)
- [3. Extracting tooth from background](#3-extracting-the-tooth-from-the-background)
- [4. Extracting enamel from tooth](#4-extracting-the-enamel-from-the-tooth)
- [5. Extracting dentin from the rest](#5-extracting-the-dentin-form-the-rest)
- [6. Creating label image](#6-creating-the-label-file)
- [7. Creating medial surface enamel and dentin](#7-creating-medial-surface-for-enamel-and-dentin)

To better understand the algorithm, the main steps in the pipeline are shown here.
This chapter briefly covers each of these steps and highlights the most important features.

![pipeline](/Screenshots/ASAlgorithm.png)
*Figure 1:* Pipeline steps for the anatomical segmentation of the CT scans

## 1. Loading an image
With the Tooth Analyser, it is generally possible to load all images in common formats.
However, this method is primarily optimized for the -ISQ- format for images from the
company [SCANCO MEDICAL](https://www.scanco.ch). For this reason, the following formats
are distinguished:

- .ISQ (original)
- .mhd (meta image file)
- all other files

[Figure 1 Step 1](#table-of-contents)

## 2. Smoothing an image
When an image is loaded, it must be smoothed in the next step if it has not already been
smoothed. The check to determine whether an image has already been smoothed is based on
the standard deviation of the image. If it is below or above a certain threshold, the
image is considered to be already smoothed.

For the smoothing itself, the Tooth Analyser uses a Median Filter. This belongs to the
group of local operators and considers the direct neighboring pixels to calculate the
smoothed gray value for the currently considered pixel.

[Figure 1 Step 2](#table-of-contents)

## 3. Extracting the tooth from the background
After a smoothed image is available, the next step is to separate the tooth from the
background. For this, the thresholding method is selected, which the user can define via
the UI (Otsu, Renyi). The method then determines an optimal threshold and creates a
binary image that differentiates between the tooth and the background.

In the same step, a mask is created that focuses on the tooth in the image. This mask
is applied to the smoothed image, indicating which part should be considered in the
next step.

[Figure 1 Step 3](#table-of-contents)

## 4. Extracting the enamel from the tooth
With the created mask, the same segmentation method as in the previous step can now be
applied to separate the enamel segment from the tooth. The segmentation is again based
on the different shades of gray. The result is a layer in the form of the enamel.

Additionally, fillings and edge smoothing occur, but these should remain untouched
here.

[Figure 1 Step 4](#table-of-contents)

## 5. Extracting the dentin form the rest
After the enamel has been successfully extracted from the tooth, the logical consequence
is that the remaining part is the dentin. To extract the dentin, the Tooth Analyser uses
a seemingly simple technique. It simply calculates the dentin by subtracting it from the
rest of the tooth. The result is a layer in the form of the dentin.

*Dentin = Tooth - Enamel*

In this step, further small smoothing and edge-preserving algorithms are applied to
improve the result. However, these are not considered here.

[Figure 1 Step 5](#table-of-contents)

## 6. Creating the label file
In this final step, which relates to segmentation, the layers for enamel and dentin
created in steps 4 and 5 are combined into a labeled file. Color adjustments can also
be made here.

[Figure 1 Step 6](#table-of-contents)

## 7. Creating Medial Surface for Enamel and Dentin
The creation of the medial surfaces is completely independent of the segmentation and is
an optional setting in the Tooth Analyser. The medial surfaces are primarily used for the
classification of cavities. The creation of these surfaces is implemented via Laplace
interpolation and is technically the same for both dentin and enamel.

[Figure 1 Step 7 and 8](#table-of-contents)