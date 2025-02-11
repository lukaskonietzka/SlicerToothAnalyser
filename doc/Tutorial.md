# Tutorial
This chapter provides a detailed description of the parameter settings and capabilities of the Tooth Analyser.  
The extension is divided into several functions, each of which has been kept separate. As a result, they can also
be executed independently of one another. This chapter covers all features and explains them in detail. Therefor
we take a look on the UI to identify the main features:

![Screenshot of the application](/Screenshots/uiOverview.png)
*Figure 1: Overview of the core Tooth Analyser features.*

## Analytical
With the analytical functions, it is currently possible to create a histogram of the CT scan.
A histogram shows how often different grayscale values appear in the image.  
Additionally, the intensity on the X-axis indicates the image format (8UInt, 16Int, ...).

**User Interface:**

| Description                                                                                                                                                                                 | Parameters                                                                                                                                   |
|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| **Volume to be analyzed**: Select the CT scan you want to analyze here.<br/><br/>**Show Histogram**: If this option is selected, a histogram of the previously chosen image will be created. | ![Screenshot of the application](../Screenshots/slicerAnalyticsParameter.png)<br/>*Figure 2: Parameter selection for the analytical function* |


**Results:**

A histogram shows how often different grayscale values appear in the image. Additionally, the intensity on the X-axis
indicates the image format (8UInt, 16Int, ...).


| Description                                                                                                                                                           | Result View                                                                                                             |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| A histogram shows how often different grayscale values appear in the image. Additionally, the intensity on the X-axis indicates the image format (8UInt, 16Int, ...). This is helpful because the thresholding methods used for anatomical segmentation are based on the image histogram data. Examining the histogram can therefore facilitate the selection of the appropriate method.| ![Screenshot of the application](/Screenshots/resultHistogram.png)<br/>*Figure 3: Resul view ot the created histogram.* |


## Anatomical Segmentation
The anatomical segmentation is the core of this extension. It allows the automatic segmentation of the
micro-CT image of a tooth into the main dental substances, dentin and enamel. Additionally, medial surfaces can
be generated, which are important for the classification of cavities.

| Description                                                                                                                                                                                                                                                                                                                                                                                                                 | Parameters                                                                                                                               |
|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------|
| **Image for Segmentation**: Select the CT scan you want to segment here.<br/><br/> **Segmentation algorithm**: Choose the algorithm you want to use for segmentation.<br/><br/> **Calculate Medial Surface**: Calculates the medial surfaces of the dentin and enamel based on the segmentation.<br/><br/> **Show Medial Surface As 3D**: If the medial surfaces have been calculated, they can be displayed as a 3D model.  | ![Screenshot of the application](../Screenshots/slicerASParameter.png) <br/> *Figure 4: Parameter selection for anatomical segmentation* |


## Batch Processing
In batch processing, the tested parameters can then be applied to a whole series of CT images. The Tooth Analyser
will then create a directory in your file system where the images will be saved.


| Description                                                                                                                                                                                                                                                        | Parameters                                                                                                                           |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| **Load file from**: Select the folder where the CTs you want to process are located.<br/><br/> **Save files in**: Select the folder where the CTs will be saved after processing.<br/><br/> **Save files as**: Choose the format in which you want to save the CTs. | ![Screenshot of the application](../Screenshots/slicerBatchParameter.png)<br/> *Figure 3: Parameter selection for the batch function* |

## Processing Mode