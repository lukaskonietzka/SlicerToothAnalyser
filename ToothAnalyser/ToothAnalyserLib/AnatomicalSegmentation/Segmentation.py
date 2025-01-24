"""
Copyright (C) 2025  Lukas Konietzka, lukas.konietzka@tha.de
                    Simon Hoffmann, simon.hoffmann@tha.de

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
--------------------------------------------------------------------

This package contains all the logic required to
calculate an anatomical segmentation of one or more tooth CTs
"""

import os
import SimpleITK as sitk
from SimpleITK import Image
from .isq_to_mhd import isq_to_mhd_as_string


def generateToothSetKeys(filter_selection_1: str, filter_selection_2: str) -> set:
    """
    This function creates the extended structure for the tooth set.
    The names for the respective result stack are generated here.
    @param filter_selection_1: the first possible algorithm
    @param filter_selection_2: the second possible algorithm
    @returns tooth_set: the complete tooth set for one algorithm
    @example:
        tooth_set_otsu = generate_tooth_set_keys('Otsu', 'Otsu')
    """
    tooth_set = __TOOTH_SET.copy()

    filt_1 = filter_selection_1.lower()
    filt_2 = filter_selection_2.lower()

    enamel_key = 'enamel_' + filt_1
    enamel_smooth_key = 'enamel_smooth_' + filt_2

    enamel_layers_key = 'enamel_' + filt_1 + '_' + filt_2 + '_layers'
    dentin_layers_key = 'dentin_' + filt_1 + '_' + filt_2 + '_layers'

    segmentation_labels_key = 'segmentation_' + filt_1 + '_' + filt_2 + '_labels'

    enamel_midsurface_key = 'enamel_' + filt_1 + '_' + filt_2 + '_midsurface'
    dentin_midsurface_key = 'dentin_' + filt_1 + '_' + filt_2 + '_midsurface'

    tooth_set.add(enamel_key)
    tooth_set.add(enamel_smooth_key)
    tooth_set.add(enamel_layers_key)
    tooth_set.add(dentin_layers_key)
    tooth_set.add(segmentation_labels_key)
    tooth_set.add(enamel_midsurface_key)
    tooth_set.add(dentin_midsurface_key)
    return tooth_set


# ----- Global variables ----- #
# ----- Tooth SET for standardized names ----- #
__TOOTH_SET = {
    'path',
    'name',
    'img',
    'img_smooth',
    'tooth',
}


# ----- Tooth SET extension ----- #
__TOOTH_SET_OTSU_OTSU = generateToothSetKeys('Otsu', 'Otsu')
__TOOTH_SET_RENYI_RENYI = generateToothSetKeys('Renyi', 'Renyi')


# ----- Selection of adaptive thresholding methods ----- #
# not filters, but point operations
__THRESHOLD_FILTERS = {'Otsu': sitk.OtsuThresholdImageFilter(),
                     'Huang' : sitk.HuangThresholdImageFilter(),
                     'MaxEntropy' : sitk.MaximumEntropyThresholdImageFilter(),
                     'Intermodes' : sitk.IntermodesThresholdImageFilter(),
                     'IsoData' : sitk.IsoDataThresholdImageFilter(),
                     'Kittler' : sitk.KittlerIllingworthThresholdImageFilter(),
                     'Renyi' : sitk.RenyiEntropyThresholdImageFilter(),
                     'Moments' : sitk.MomentsThresholdImageFilter(),
                     'Shanbhag' : sitk.ShanbhagThresholdImageFilter(),
                     'Yen' : sitk.YenThresholdImageFilter()}


# ----- Name parser -----#
def parseName(path: str) -> str:
    """
    The name parser is for a uniform conversion
    of the names of the source files for the result files.
    The functions parse only one name. The parser cut of the
    ending after the last point.
    @param path: the path to the file that should be parsed
    @return name: the parsed name for the given file
    @example:
        path = "/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ"
        name = parse_name(path=path)
        name -> 'P01A-C0005278'
    """
    name = os.path.basename(path).rsplit('.', 1)[0]
    return name

def parseNames(path: str, offset: int=0, size: int=1) -> list[str]:
    """
    The name parser is for a uniform conversion
    of the names of the source files for the result files.
    The functions parse only one name.
    @param path: the path to the directory that should be parsed
    @param offset:
    @param size:
    @return name: the parsed names for the given directory collected in a list
    @example:
        directoryPath = "/data/MicroCT/Original_ISQ/"
        names = parse_names(path=directoryPath)
        names -> ['P01A-C0005278', ...]
    """
    # collect all files that ends with .ISQ
    isq_names = sorted([f for f in os.listdir(path) if f.endswith('.ISQ')])
    mhd_names = []

    if len(isq_names) < offset + size:
        size = len(isq_names) - offset

    for i in range(size):
        mhd_names.append(parseName(path + isq_names[offset + i]))
    return mhd_names

def parseTyp(path: str) -> str:
    """
    This method parse the typ from a given file
    @param path: the full path to the file
    @return: the type of the given file
    @example:
        path = '/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ'
        fileType = parseType(path)
        fileType -> 'ISQ'
    """
    fileType = os.path.basename(path).rsplit('.', 1)[1]
    return fileType.lower()


# ----- Morphological filters ----- #
def bcbr(img: Image, size: int=10) -> Image:
    """
    Filter for closing small holes within the segment (Closing).
    @param img: the image to be filtered
    @param size: the size of the filter mask
    @return: the filtered image
    @example:
        path = "/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ"
        image = isq_to_mhd(path=path, name="P01A-C0005278.mhd")
        filteredImage = bcbr(img=image, size=10)
    """
    return sitk.BinaryClosingByReconstruction(img, [size, size, size])

def bobr(img: Image, size:int =10) -> Image:
    """
    Filter for removing small structures outside the segment (Opening).
    @param img: the image to be filtered
    @param size: the size of the filter mask
    @return: the filtered image
    @example:
        path = "/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ"
        image = isq_to_mhd(path=path, name="P01A-C0005278.mhd")
        filteredImage = bobr(img=image, size=10)
    """
    return sitk.BinaryOpeningByReconstruction(img, [size, size, size])

def bmc(img: Image, size: int=1) -> Image:
    """
    Filter for closing small holes within the segment (Closing).
    @param img: the image to be filtered
    @param size: the size of the filter mask
    @return: the filtered image
    @example:
        path = "/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ"
        image = isq_to_mhd(path=path, name="P01A-C0005278.mhd")
        filteredImage = bmc(img=image, size=1)
    """
    vectorRadius=(size,size,size)
    kernel=sitk.sitkBall
    return sitk.BinaryMorphologicalClosing(img, vectorRadius, kernel)

def bmo(img: Image, size: int=1) -> Image:
    """
    Filter for removing small structures outside the segment (Opening).
    @param img: the image to be filtered
    @param size: the size of the filter mask
    @return: the filtered image
    @example:
        path = "/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ"
        image = isq_to_mhd(path=path, name="P01A-C0005278.mhd")
        filteredImage = bmo(img=image, size=1)
    """
    vectorRadius=(size,size,size)
    kernel=sitk.sitkBall
    return sitk.BinaryMorphologicalOpening(img, vectorRadius, kernel)


# ----- Smoothing filter Edge preserving ----- #
def medianFilter(img: Image, size: int=1) -> Image:
    """
    this method filters a given image using median
    filtering known as the local operator. Edge preserving
    @param img: the image to be filtered
    @param size: the size of the local operator mask
    @return: the filtered image
    @example:
        path = "/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ"
        image = isq_to_mhd(path=path, name="P01A-C0005278.mhd")
        filteredImage = medianFilter(img=Image, size=5)
    """
    return sitk.Median(img, [size,size,size])


# ----- Smoothing filter ----- #
def gradGaussianFilter(img: Image, sigma: float=0.03) -> Image:
    """
    This method apply a gaussian filter on the given image
    to perform a smoothing
    @param img: the image to be smoothed
    @param sigma: the intensity
    @return: the smoothed image
    @example:
        path = "/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ"
        image = isq_to_mhd(path=path, name="P01A-C0005278.mhd")
        filteredImage = gradGaussianFilter(img=Image, sigma=0.05)
    """
    # provides the best result
    return sitk.GradientMagnitudeRecursiveGaussian(img, sigma)


# ----- Typ information and typ parsing ----- #
def cast255(img: Image) -> Image:
    """
    Rescales the intensity of an image to the range [0, 255]
    and casts it to an 8-bit unsigned integer type.
    @param img: The input image to be processed.
    @returns: The processed image with intensity values rescaled to [0, 255] and cast to sitkUInt8.
    @example:
        castImg = cast255(itkImg)
    """
    return sitk.Cast(sitk.RescaleIntensity(img), sitk.sitkUInt8)

def castAccordingly(img: Image, img2: Image) -> Image:
    """
    Casts the pixel type of the input image to match the
    pixel type of a reference image.
    @param img: The input image to be cast to a new pixel type
    @param img2: The reference image whose pixel type will be used for the casting
    @return: The input image `img` cast to the pixel type of the reference image `img2`
    @example:
        castImg = castAccordingly(itkImg1, itkImg2)
    """
    return sitk.Cast(img, img2.GetPixelID())

def pixelType(img: Image) -> str:
    """
    Retrieves the pixel type of the given image as a
    human-readable string.
    @param img: The input image whose pixel type is to be retrieved
    @return: A string representing the pixel type of the image (e.g., 'sitkUInt8', 'sitkFloat32')
    @example:
        pixel = pixelType(itkImg)
        pixel -> 'Float32'
    """
    return img.GetPixelIDTypeAsString()


# ----- Context component ----- #
def ccMinSize(img: any, size: int=10) -> Image:
    """
    This filter searches for related components. Then components
    below an adjustable size are removed.The effect is comparable
    o a morphological opening and removes small structures.
    It should be noted that a label file is then returned.
    If a specific label is expected, this must be filtered. If you
    want to have all structures, then ‘> 0’ is used and all labels
    are merged into one.
    @param img: the image to be filtered
    @param size: the size of the filter mask
    @return: the labeled image
    @example:
        path = "/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ"
        image = isq_to_mhd(path=path, name="P01A-C0005278.mhd")
        cc = cc_min_size(img=Image, size=10)
    """
    # cc_min_size(sitk_img, 10) > 0 creates a label file with a label without small structures
    cc_filt = sitk.ConnectedComponentImageFilter()
    cc = cc_filt.Execute(img)
    relabel_filt = sitk.RelabelComponentImageFilter()
    relabel_filt.SetMinimumObjectSize(size)
    relabel_filt.SetSortByObjectSize(True)
    cc_objects = relabel_filt.Execute(cc)
    return cc_objects


# ----- Adaptive threshold method ----- #
def thresholdFilter(img: Image, mask: bool=False, filter_selection: str= 'Otsu', debug: bool=False) -> Image:
    """
    This methode apply a threshold filter on the given
    image. The possible threshold filters are listed in __THRESHOLD_FILTERS.
     @param img: the immage to be threshed
     @param mask: apply a mask on the filter if true is given
     @param filter_selection: the specific algorithm for the methode
     @param debug: prints logs if true is given
     @return: the threshed image
     @example:
        threshedImage = threshold_filter(sitk_img, mask=False, filter_selection = 'Renyi', debug=True)
    """
    try:
        thresh_filter = __THRESHOLD_FILTERS[filter_selection]
        thresh_filter.SetInsideValue(0)
        thresh_filter.SetOutsideValue(1)
        if filter_selection == 'Intermodes':
            if debug:
                print("SetNumberOfHistogramBins(5000) because of IntermodesThreshold")
            thresh_filter.SetNumberOfHistogramBins(500)
        else:
            thresh_filter.SetNumberOfHistogramBins(20000)
        if mask:
            if debug:
                print("mask specified")
            thresh_img = thresh_filter.Execute(img, sitk.Cast(mask, sitk.sitkUInt8))
        else:
            if debug:
                print("no mask specified")
            thresh_img = thresh_filter.Execute(img)
        thresh_value = thresh_filter.GetThreshold()
    except KeyError:
        print("KeyError")
        thresh_value = 0
        thresh_img = img>thresh_value

    if debug:
        print("Threshold used: " + str(thresh_value))
    return thresh_img


# ----- Write to file system ----- #
def write(img: any, name: str, path: str, fileType: str) -> None:
    """
    This method uses the simpleITK (sitk) library to store
    an image in the file system. The write action is based
    on the image name.
    @param img: the image to be stored
    @param name: the name of the stored image
    @param path: the storage location in the file system
    @param fileType: the typ of the file to be written
    @example:
        write(sitk_img, 'P01A-C0005278') store P01A-C0005278.mhd and P01A-C0005278.raw
    """
    sitk.WriteImage(img, path + name + fileType)

def writeToothDict(tooth: dict, path:str, calcMidSurface: bool, fileType: str) -> None:
    """
    This method uses the simpleITK (sitk) library to store
    an image in the file system. The write action is based
    on the Tooth-Dictionary. If there is no image behind the dictionary key
    skip this key.‚
    @param tooth: the dictionary to be stored
    @param path: the storage location in the file system
    @param calcMidSurface: true if the medial surface should be calculated
    @param fileType: the typ of the file to be written
    @example:
        name = parse_names(__PATH_1_100, offset=0, size=1)[0]
        tooth = load_full_dict_by_name(name, __TOOTH_SET_OTSU_OTSU)
        write_full_dict(tooth)
    """
    name = tooth['name']

    for key in tooth:
        if key == 'path':
            pass
        elif key == 'name':
            pass
        elif key == "tooth":
            pass
        elif key == "enamel_otsu" or key == "enamel_renyi":
            pass
        elif "smooth" in key:
            pass
        elif "layers" in key:
            pass
        elif "midsurface" in key and not calcMidSurface:
            pass
        else:
            write(tooth[key], name + "_" + key, path, fileType)

def getDirectoryForFile(filePath: str) -> str:
    """
    Extract the folder path from the given file
    @param filePath: the file to be extracted
    @return folderPath: the path to the folder for the given file
    @example:
        directory = getDirectoryForFile("/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ")
        directory -> "/data/MicroCT/Original_ISQ/"
    """
    folderPath = os.path.dirname(filePath)
    if not folderPath:
        folderPath = os.getcwd()
    return folderPath


# ----- Load ISQ-File ----- #
def loadISQ(path: str) -> Image:
    """
    This methode loads an ISQ-File from a given directory
    and convert it into an MHD-File by using the
    isq_to_mhd module from Peter Rösch
    @param path: the path to the ISQ-File to be loaded
    @return: The loaded and converted MHD-File
    @example:
        path = "/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ"
        image = isq_to_mhd(path)
        image -> "P01A-C0005278.mhd"
    """
    img = isq_to_mhd_as_string(path)
    return sitk.ReadImage(img)


# ----- Load MHD-File ----- #
def loadMHD(targetPath: str, name: str) -> Image:
    """
    This methode loads an MHD-File from a given directory
    @param targetPath: the path to the file to be loaded
    @param name: the name of the file
    @return: the loaded .MHD-File
    @example:
        path = "/data/MicroCT/Original_ISQ/"
        name = parse_names(targetPath=path, offset=0, size=1)[0]
        img = load_mhd(name)
    """
    if ".mhd" in targetPath.lower():
        return sitk.ReadImage(targetPath)
    else:
        name = targetPath + name + "MHD.mhd"
    return sitk.ReadImage(name)

def loadFile(path: str) -> Image:
    """
    This methode loads any file with any type into the module
    @param path: the path to the file to be loaded
    @return: the loaded Image
    @example:
        path = '/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ'
        image = loadFile(path)
    """
    return sitk.ReadImage(path)


# ----- Medial Surface ----- #
def medialSurface(segment: any) -> any:
    """
    This methode calculate the medial surfaces for each segment
    @param segment: the segment for wiche the medial surface to be needed
    @return: the medial surface for the given segment
    @example:
        path = '/data/MicroCT/Original_ISQ/'
        name = parse_names(path, offset=0, size=1)[0]
        name_enamel = name + '_enamel_otsu_otsu_layers'
        enamel = load_mhd(name_enamel)
        enamel_medial_surface = medial_surface(enamel)
    """
    dist_filter = sitk.SignedMaurerDistanceMapImageFilter()
    dist_filter.SetInsideIsPositive(False)
    dist_filter.SetSquaredDistance(False)
    dist_filter.SetUseImageSpacing(False)
    dist_map = dist_filter.Execute(segment)
    dist_map_masked = sitk.Mask(dist_map, segment)
    dist_map_sobel = sitk.SobelEdgeDetection(dist_map_masked)
    dist_map_sobel_laplace = sitk.Laplacian(dist_map_sobel)
    dist_map_sobel_laplace_thresh = thresholdFilter(dist_map_sobel_laplace)
    medial_surface = sitk.Mask(dist_map_sobel_laplace_thresh, segment)
    return medial_surface


# ----- Pipeline methods ----- #
def loadImage(path: str) -> tuple[Image, str]:
    """
    This methode loads an image into the algorithm
    depending on the type.
    @param path: the path to the file to be loaded
    @returns: the loaded image and the name of the loaded image
    @example:
        img, name = loadImage(path)
    """
    import time
    start = time.time()
    name = parseName(path)
    fileType = parseTyp(path)
    try:
        if fileType == "isq":
            img = loadISQ(path)
        elif fileType == "mhd":
            img = loadMHD(path, name)
        else:
            img = loadFile(path)
    except:
        img = loadFile(path)
    stop = time.time()
    print("img: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return img, name

def smoothImage(img: Image) -> Image:
    """
    This methode apply a median filter on the given image if there
    is no smoothed image in the current directory
    @param img: the image to be smoothed
    @return: the smoothed image
    @example:
        img, name = loadImage(path)
        smoothImage = smoothImage(img)
    """
    import time

    start = time.time()
    # If a median image already exists, take that one. Must be named "name_img_smooth"
    img_smooth = medianFilter(img, 5)
    stop = time.time()
    print("img_smooth: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return img_smooth

def imageMask(img: Image, img_smooth: Image) -> tuple:
    """
    This methode apply a threshold Filter on the given image
    and the given smoothed image if there is no mask. Needs to be
    named as "..._tooth_smooth".
    @param img: the image to be masked
    @param img_smooth: the smooth image to be masked
    @return: the Image with the mask
    @example:
        img, name = loadImage(path)
        smoothImage = smoothImage(img)
        tooth, tooth_masked = imageMask(img, img_smooth)
    """
    import time

    # first adaptive threshold value - corresponds to first cut in the histogram
    start = time.time()
    tooth = thresholdFilter(img_smooth)
    # original image, tooth masked
    tooth_masked = sitk.Mask(img, tooth)
    stop = time.time()
    print("tooth: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return tooth, tooth_masked

def smoothImageMask(img_smooth: Image, tooth: Image) -> any:
    """
    This methode is for smoothing the mask wiche was generated previously
    @param img_smooth: the smoothed image to be masked
    @param tooth: the previous generated mask
    @return: the smooth mask
    @example:
        tooth_smooth_masked = smoothImageMask(img_smooth, tooth)
    """
    import time

    # smoothed image, tooth masked
    start = time.time()
    tooth_smooth_masked = sitk.Mask(img_smooth, tooth)
    stop = time.time()
    print("tooth_smooth: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return tooth_smooth_masked

def enamelSelect(filter_selection_1: str, tooth_masked: any) -> NotImplemented:
    """
    This methode extract the enamel area from the rest of the tooth by
    choosing the largest coherent object in the image.
    @param filter_selection_1: the current segmentation typ (e.g. "otsu", "renyi")
    @param tooth_masked: the created tooth mask
    @return: the extracted enamel from the tooth
    @example:
        enamel_select = enamelSelect(filter_selection_1, tooth_masked)
    """
    import time

    # second adaptive threshold value - corresponds to second cut in the histogram
    start = time.time()
    enamel_select = thresholdFilter(img=tooth_masked,
                                    mask=tooth_masked,
                                    filter_selection=filter_selection_1)
    # preparation
    enamel_select = bcbr(enamel_select)
    # largest coherent object
    enamel_select = ccMinSize(enamel_select, 50) == 1
    # Enamel segment finished on masked original tooth
    stop = time.time()
    print("enamel_select: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return enamel_select

def enamelSmoothSelect(filter_selection_2: str, tooth_smooth_masked: any) -> Image:
    """
    This methode apply a smoothing on the extracted enamel segment
    @param filter_selection_2: the current segmentation typ (e.g. "otsu", "renyi")
    @param tooth_smooth_masked: the created tooth mask
    @return: the smoothed enamel area
    @example:
        enamel_smooth_select = enamelSmoothSelect(filter_selection_2, tooth_smooth_masked)
    """
    import time

    # second adaptive threshold value - corresponds to second cut in the histogram
    # on masked original tooth
    start = time.time()
    enamel_smooth_select = thresholdFilter(
        img=tooth_smooth_masked,
        mask=tooth_smooth_masked,
        filter_selection=filter_selection_2)
    # preparation
    enamel_smooth_select = bcbr(enamel_smooth_select)
    # Enamel segment finished on masked smoothed tooth
    stop = time.time()
    print("enamel_smooth_select: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return enamel_smooth_select

def enamelLayering(enamel_select: any, enamel_smooth_select: Image) -> Image:
    """
    This methode takes the enamel selection and the smoothed enamel selection
    and create a layer image for the enamel segment.
    @param enamel_select: the selected enamel area
    @param enamel_smooth_select: the selected and smoothed enamel area
    @return: the enamel layer image
    @example:
        enamelLayers = enamelLayering(enamelSelect, enamelSmoothSelect)
    """
    import time

    start = time.time()
    enamel_layers = enamel_select + enamel_smooth_select
    enamel_layers = enamel_layers > 0
    stop = time.time()
    print("enamel_layers: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return enamel_layers

def enamelPreparation(enamel_layers: Image) -> NotImplemented:
    """
    This methode performs an extended smoothing on the given enamel layer
    @param enamel_layers: the enamel layer to be smooth extended
    @return: the extended smoothed enamel layer image
    @example:
        enamel_layers_extended_smooth_2 = enamelPreparation(enamel_layers)
    """
    import time

    start = time.time()
    enamel_layers_extended = bcbr(enamel_layers)
    enamel_layers_extended_2 = bmc(enamel_layers_extended, 2)  # size = 2
    # comparable to binary opening result, only faster
    enamel_layers_extended_smooth = sitk.SmoothingRecursiveGaussian(enamel_layers_extended_2, 0.04) > 0.7
    enamel_layers_extended_smooth_2 = bmc(enamel_layers_extended_smooth) > 0
    enamel_layers_extended_smooth_2 = ccMinSize(enamel_layers_extended_smooth_2, 10) == 1  # size = 10
    stop = time.time()
    print("enamel_layers_smooth_extended: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return enamel_layers_extended_smooth_2

def enamelFilling(enamel_layers_extended_smooth_2: any, tooth: Image) -> tuple:
    """
    This methode fills up the small structures inside the
    enamel segment in the tooth. This happens on the filtered enamel layer
    @param enamel_layers_extended_smooth_2: the image to be filled
    @param tooth: the image of the tooth that contains the enamel part
    @return: the filled and smoothed image
    @example:
        contourExtended, enamelLayersExtendedSmooth3 = enamelFilling(enamelLayersExtendedSmooth2, tooth)
    """
    import time

    # extended tooth contour
    start = time.time()
    contour_extended = sitk.BinaryDilate((sitk.BinaryContour(tooth) > 0), [2, 2, 2], sitk.sitkBall) > 0
    # image background
    background = (~tooth) == 255
    # enamel_layers_extended_smooth_2 + background -> enamel and image background
    # ... + contour_extended -> enamel and image background and thick tooth contour
    # ~ (...) -> NOT enamel and image background and thick tooth contour -> dentin and small structures inside tooth
    # == 255, as the inversion maps the foreground to 255, then Label == 1 again
    dentin_and_partial_decay = (~((((enamel_layers_extended_smooth_2 + background) > 0) + contour_extended) > 0)) == 255
    # biggest part in dentin and smallest structure inside tooth -> dentin
    dentin_parts = ccMinSize(dentin_and_partial_decay, 10) == 1
    # dentin and small structures inside tooth -> dentin -> small structures inside tooth
    partial_decay = dentin_and_partial_decay - dentin_parts
    # adding the small structures to the enamel segment
    enamel_layers_extended_smooth_3 = enamel_layers_extended_smooth_2 + partial_decay
    stop = time.time()
    print("enamel_layers_extended_smooth_3: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return contour_extended, enamel_layers_extended_smooth_3

def additionalEnamelFilling(enamel_layers, enamel_layers_extended_smooth_3):
    """
    this method performs an additional filtering of the enamel segment.
    This is needed for the Calculation of the dentin Segment.
    @param enamel_layers:
    @param enamel_layers_extended_smooth_3:
    @return:
    @example:
       enamelLayers = additionalEnamelFilling(enamel_layers, enamel_layers_extended_smooth_3)
    """
    import time

    # Inversion enamel -> everything outside enamel
    start = time.time()
    enamel_negative = ~enamel_layers_extended_smooth_3 == 255
    # all connected components -> one large component outside enamel and small components inside enamel
    # "> 1" -> not the biggest component in enamel -> its a small component
    holes_enamel = ccMinSize(enamel_negative, 1) > 1
    # add small structures
    enamel_layers_extended_smooth_4 = enamel_layers_extended_smooth_3 + holes_enamel
    enamel_layers = enamel_layers_extended_smooth_4
    # enamel segment is ready!
    stop = time.time()
    print("enamel_layers_extended_smooth_4: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return enamel_layers

def dentinLayers(contour_extended: Image, enamel_layers: Image, tooth: any) -> any:
    """
    This methode calculates the layer Image for the dentin segment
    by using the smoothed image and the already created enamel layer.
    Dentin = Enamel + everything outside the tooth + thick contour
    @param contour_extended:
    @param enamel_layers:
    @param tooth:
    @return:
    @example:
        dentinLayers = dentinLayers(contour_extended, enamel_layers, tooth)
    """
    import time

    # ~tooth -> not tooth -> everything outside tooth
    # Enamel + everything outside the tooth + thick contour -> everything except dentin
    start = time.time()
    not_dentin = enamel_layers + (~tooth == 255) + contour_extended > 0
    # Inversion everything except dentin -> dentin
    dentin_layers = (~not_dentin) == 255
    # Deduction from each other to avoid double assigned voxels
    dentin_layers = dentin_layers - enamel_layers == 1
    # if individual voxels were still available
    dentin_layers = ccMinSize(dentin_layers, 50) == 1
    stop = time.time()
    print("dentin_layers: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return dentin_layers

def segmentationLabels(dentin_layers: any, enamel_layers: any) -> Image:
    """
    This methode calculates a label image based on the
    given dentin layer and the enamel layer.
    @param dentin_layers: the dentin layer for the label image
    @param enamel_layers: the enamel layer for the label image
    @return: the calculated label image
    @example:
        segmentationLabels = segmentationLabels(dentinLayers, enamelLayers)
    """
    import time

    # Label file, dentin == 2, enamel == 3
    start = time.time()
    segmentation_labels = enamel_layers * 3 + dentin_layers * 2
    stop = time.time()
    print("segmentation_labels: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return segmentation_labels

def enamelMidSurface(enamel_layers: any) -> Image:
    """
    This method calculate the medial surfaces for the enamel
    segment by using the enamel layer
    @param enamel_layers: The layer for which the medial surface should be calculated
    @return: the calculated medial surface as image
    @example:
        enamelMidSurface = enamelMidSurface(enamel_layers)
    """
    import time

    start = time.time()
    enamel_midsurface = medialSurface(enamel_layers)
    stop = time.time()
    print("enamel_midsurface: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return enamel_midsurface

def dentinMidSurface(dentin_layers: any) -> Image:
    """
    This method calculate the medial surfaces for the dentin
    segment by using the dentin layer
    @param dentin_layers: The layer for which the medial surface should be calculated
    @return: the calculated medial surface as image
    @example:
        dentinMidSurface = dentinMidSurface(dentin_layers)
    """
    import time

    start = time.time()
    dentin_midsurface = medialSurface(dentin_layers)
    stop = time.time()
    print("dentin_midsurface: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return dentin_midsurface

def isSmoothed(image: Image) -> bool:
    import numpy as np
    array = sitk.GetArrayFromImage(image)
    std_dev = np.std(array)
    print(f"Standardabweichung des Bildes: {std_dev}")
    # Beispielschwelle anpassen:
    return std_dev < 3200.00


# ----- Pipeline, calculate tooth dictionary ----- #
def calcPipeline(sourcePath: str, calcMidSurface: bool, filter_selection_1: str= 'Renyi', filter_selection_2: str= 'Renyi') -> dict:
    """
    This method forms the complete pipeline for the calculation of smoothing,
    labels and medial surfaces. It is very large but therefore the clearest
    @param sourcePath: the path to the file that should be entered in the pipeline
    @param calcMidSurface: the path to the directory where the generated images are saved in the file system
    @param filter_selection_1: the segmentation algorithm
    @param filter_selection_2: the segmentation algorithm
    @return: the full created tooth dictionary with all images
    @example:
        path = '/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ'
        targetPath = '/data/MicroCT/Original_ISQ/anatomicalSegmentationOtsu/'
        tooth_dict = pipe_full_dict_selection(path, 'Otsu', 'Otsu')
    """
    # 1. load and filter image
    img, name = loadImage(sourcePath)

    if isSmoothed(image=img):
        print("Bild ist gefiltert")
        img_smooth = img
    else:
        print("Bild ist nicht gefiltert")
        img_smooth = smoothImage(img)

    # 2. generate a mask on the image and the smooth image
    tooth, tooth_masked = imageMask(img, img_smooth)
    tooth_smooth_masked = smoothImageMask(img_smooth, tooth)

    # 3. select enamel area
    enamel_select = enamelSelect(filter_selection_1, tooth_masked)
    enamel_smooth_select = enamelSmoothSelect(filter_selection_2, tooth_smooth_masked)

    # 4. stack the enamels
    enamel_layers = enamelLayering(enamel_select, enamel_smooth_select)

    # 5. Prepare the enamel
    enamel_layers_extended_smooth_2 = enamelPreparation(enamel_layers)

    # 6. Filling of small structures within the tooth
    contour_extended, enamel_layers_extended_smooth_3 = enamelFilling(enamel_layers_extended_smooth_2, tooth)

    # 7. Filling of small structures within the tooth, important with many datasets
    enamel_layers = additionalEnamelFilling(enamel_layers, enamel_layers_extended_smooth_3)

    # 8. generate dentin segment
    dentin_layers = dentinLayers(contour_extended, enamel_layers, tooth)

    # 9. generate label file for segmentation
    segmentation_labels = segmentationLabels(dentin_layers, enamel_layers)

    # 10. generating medial surface for enamel and dentin
    if calcMidSurface:
        enamel_midsurface = enamelMidSurface(enamel_layers)
        dentin_midsurface = dentinMidSurface(dentin_layers)
    else:
        enamel_midsurface = None
        dentin_midsurface = None

    # 11. generate tooth dictionary to store all generated data sets local
    filt_1 = filter_selection_1.lower()
    filt_2 = filter_selection_2.lower()

    enamel_key = 'enamel_' + filt_1
    enamel_smooth_key = 'enamel_smooth_' + filt_2

    enamel_layers_key = 'enamel_' + filt_1 + '_' + filt_2 + '_layers'
    dentin_layers_key = 'dentin_' + filt_1 + '_' + filt_2 + '_layers'

    segmentation_labels_key = 'segmentation_' + filt_1 + '_' + filt_2 + '_labels'

    enamel_midsurface_key = 'enamel_' + filt_1 + '_' + filt_2 + '_midsurface'
    dentin_midsurface_key = 'dentin_' + filt_1 + '_' + filt_2 + '_midsurface'

    tooth_dict = {
        'path': sourcePath,
        'name': name,
        'img': img,
        'img_smooth': img_smooth,
        'tooth': tooth,
        enamel_key: enamel_select,
        enamel_smooth_key: enamel_smooth_select,
        enamel_layers_key: enamel_layers,
        dentin_layers_key: dentin_layers,
        segmentation_labels_key: segmentation_labels,
        enamel_midsurface_key: enamel_midsurface,
        dentin_midsurface_key: dentin_midsurface
    }
    return tooth_dict


# ----- calculate pipeline in a batch process ----- #
def calcPipelineAsBatch(sourcePath: str, targetPath: str, segmentationType: str, calcMidSurface: bool, fileType: str) -> None:
    """
    This methode calculates the images in a batch process.
    It is recommended to name the destination folder like the image
    @param sourcePath: The directory path to the files where the file to be calculated is located
    @param targetPath: the path to the directory, where the files from the calculation should be stored
    @param segmentationType: the thresholding algorithm for segmentation
    @param calcMidSurface: true, if the medial surfaces also should be calculated. False if note
    @param fileType: the format in which the files are to be saved (e.g. '.nii' or '.mhd' or ...)
    @example:
        sourcePath = '/data/MicroCT/Original_ISQ/'
        targetPath = '/data/MicroCT/Original_ISQ/P01A-C0005278/'
        calcAnatomicalSegmentation(sourcePath, targetPath, "Otsu", True, '.nii')
    """
    tooth_segmentation = calcPipeline(sourcePath, calcMidSurface, segmentationType, segmentationType)
    writeToothDict(tooth_segmentation, targetPath, calcMidSurface, fileType)
    tooth_segmentation_name = tooth_segmentation['name']
    print("Done: " + tooth_segmentation_name)
