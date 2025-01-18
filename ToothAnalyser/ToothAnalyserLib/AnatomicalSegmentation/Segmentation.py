"""
Contains the pipeline to calculate a label image from
an .ISQ image
"""

import os
from wsgiref.util import request_uri

import SimpleITK as sitk
from SimpleITK import Image
from .isq_to_mhd import isq_to_mhd


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

# Absolute Pfade der Originalbilder NICHT NÖTIG
#__PATH_1_100 = '/data/shofmann/MicroCT/Original_ISQ/1_100/'
#__PATH_101_200 = '/data/shofmann/MicroCT/Original_ISQ/101_200/'
#__PATH_201_250 = '/data/shofmann/MicroCT/Original_ISQ/201_250/'


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


# ----- Glättungsfilter ----- #
def gradGaussianFilter(img, sigma=0.03):
    # nicht verwendet, aber liefert bestes Ergebnis mit diesem Filter
    return sitk.GradientMagnitudeRecursiveGaussian(img, sigma)


# ----- Typinformation und Typumwandlung ----- #
# WIRD NICHT VERWENDET
def cast_255(img):
    return sitk.Cast(sitk.RescaleIntensity(img), sitk.sitkUInt8)

def cast_accordingly(img, img2):
    return sitk.Cast(img, img2.GetPixelID())

def pixel_type(img):
    return img.GetPixelIDTypeAsString()


# ----- Zusammenhangskomponente ----- #
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


#
# Adaptive Schwellwertverfahren
#
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
def write(img: any, name: str, path: str) -> None:
    """
    This method uses the simpleITK (sitk) library to store
    an image in the file system. The write action is based
    on the image name.
    @param img: the image to be stored
    @param name: the name of the stored image
    @param path: the storage location in the file system
    @example:
        write(sitk_img, 'P01A-C0005278') store P01A-C0005278.mhd and P01A-C0005278.raw
    """
    sitk.WriteImage(img, path + name + ".mhd")

def writeToothDict(tooth: dict, path:str, calcMidSurface: bool) -> None:
    """
    This method uses the simpleITK (sitk) library to store
    an image in the file system. The write action is based
    on the Tooth-Dictionary. If there is no image behind the dictionary key
    skip this key.‚
    @param tooth: the dictionary to be stored
    @param path: the storage location in the file system
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
        elif "midsurface" in key and not calcMidSurface:
            pass
        else:
            write(tooth[key], name + "_" + key, path)

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
def loadISQ(path: str, targetPath: str, name: str) -> Image:
    """
    This methode loads an ISQ-File from a given directory
    and convert it into an MHD-File by using the
    isq_to_mhd module from Peter Rösch
    @param path: the path to the ISQ-File to be loaded
    @param targetPath: the path to the MHD-File
    @param name: the name of the MHD-File
    @return: The loaded and converted MHD-File
    @example:
        path = "/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ"
        image = isq_to_mhd(path, "P01A-C0005278.mhd")
    """
    name = targetPath + name + ".mhd"
    isq_to_mhd(path, name)
    return sitk.ReadImage(name)


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
        name = targetPath + name + ".mhd"
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
def loadImage(path: str, targetPath: str) -> tuple[Image, str]:
    """
    This Methode try to load an .mhd file and parse the
    name of the file.
    @param path: the path to the file to be loaded
    @param targetPath: the path to the storage directory
    @returns: the loaded image and the name of the loaded image
    @example:
        img, name = loadImage(path, targetPath)
    """
    import time
    start = time.time()
    name = parseName(path)
    fileType = parseTyp(path)

    if fileType == "isq" or fileType == "mhd":
        try:
            img = loadISQ(path, targetPath, name)
        except:
            img = loadMHD(path, name)
    else:
        img = loadFile(path)
    stop = time.time()
    print("img: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return img, name

def smoothImage(img: Image, name: str, targetPath: str) -> Image:
    """
    This methode apply a median filter on the given image if there
    is no smoothed image in the current directory
    @param img: the image to be smoothed
    @param name: the name of the image to be smoothed
    @param targetPath: the path to the directory where a smooth image could be located
    @return: the smoothed image
    @example:
        smoothImage = smoothImage(img, name, targetPath)
    """
    import time

    start = time.time()
    # If a median image already exists, take that one. Must be named "name_img_smooth"
    try:
        img_smooth = loadMHD(targetPath, name + "_" + 'img_smooth')
    except:  # smoothed img not already created
        img_smooth = medianFilter(img, 1)  # size anpassen und schauen ob es schneller läuft size = 5
        write(img_smooth, name + "_" + 'img_smooth', targetPath)
    stop = time.time()
    print("img_smooth: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return img_smooth

def imageMask(img: Image, img_smooth: Image, name: str, targetPath: str) -> tuple:
    """
    This methode apply a threshold Filter on the given image
    and the given smoothed image if there is no mask. Needs to be
    named as "..._tooth_smooth".
    @param img: the image to be masked
    @param img_smooth: the smooth image to be masked
    @param name: the name of the image to be masked
    @param targetPath: the directory where a mask could be located
    @return: the Image with the mask
    @example:
       tooth, tooth_masked = imageMask(img, img_smooth, name, targetPath)
    """
    import time

    # first adaptive threshold value - corresponds to first cut in the histogram
    start = time.time()
    try:
        tooth = loadMHD(targetPath, name + "_" + 'tooth')
    except:
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

def enamelSelect(filter_selection_1: str, tooth_masked: any):
    """

    """
    import time

    # second adaptive threshold value - corresponds to second cut in the histogram
    # on masked original tooth
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

def enamelSmoothSelect(filter_selection_2, tooth_smooth_masked):
    """

    """
    import time

    # second adaptive threshold value - corresponds to second cut in the histogram
    # on masked original tooth
    start = time.time()
    enamel_smooth_select = thresholdFilter(img=tooth_smooth_masked,
                                           mask=tooth_smooth_masked,
                                           filter_selection=filter_selection_2)
    # preparation
    enamel_smooth_select = bcbr(enamel_smooth_select)
    # Schmelzsegment auf maskierten geglätteten Zahn fertig
    stop = time.time()
    print("enamel_smooth_select: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return enamel_smooth_select

def enamelLayering(enamel_select, enamel_smooth_select):
    """

    """
    import time

    start = time.time()
    enamel_layers = enamel_select + enamel_smooth_select
    enamel_layers = enamel_layers > 0
    enamel_layers_save = enamel_layers
    stop = time.time()
    print("enamel_layers: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return enamel_layers

def enamelPreparation(enamel_layers):
    """

    """
    import time

    start = time.time()
    enamel_layers_extended = bcbr(enamel_layers)
    enamel_layers_extended_2 = bmc(enamel_layers_extended, 2)  # size = 2
    # vergleichbar mit Binary Opening Ergebnis, nur schneller
    enamel_layers_extended_smooth = sitk.SmoothingRecursiveGaussian(enamel_layers_extended_2, 0.04) > 0.7
    enamel_layers_extended_smooth_2 = bmc(enamel_layers_extended_smooth) > 0
    enamel_layers_extended_smooth_2 = ccMinSize(enamel_layers_extended_smooth_2, 10) == 1  # size = 10
    stop = time.time()
    print("enamel_layers_smooth_extended: Done ", f" {(stop - start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")
    return enamel_layers_extended_smooth_2

def enamelFilling(enamel_layers_extended_smooth_2, tooth):
    """

    """
    import time

    # erweiterte Zahnkontur
    # contour_extended = sitk.BinaryDilate((sitk.BinaryContour(tooth) > 0), 2, sitk.BinaryDilateImageFilter.Ball) > 0
    start = time.time()
    contour_extended = sitk.BinaryDilate((sitk.BinaryContour(tooth) > 0), [2, 2, 2], sitk.sitkBall) > 0
    # Hintergrund
    background = (~tooth) == 255
    # enamel_layers_extended_smooth_2 + background -> Schmelz und Hintergund
    # ... + contour_extended -> Schmelz und Hintergrund und dicke Zahnkontur
    # ~ (...) -> NICHT Schmelz und Hintergrund und dicke Zahnkontur -> Dentin und kleine Strukturen innerhalb Zahn
    # == 255, da die Invertierung den Vordergrund auf 255 abbildet, danach ist Label wieder == 1
    dentin_and_partial_decay = (~((((enamel_layers_extended_smooth_2 + background) > 0) + contour_extended) > 0)) == 255
    # größter Teil in Dentin und kleine Strukturen innerhalb Zahn -> Dentin
    dentin_parts = ccMinSize(dentin_and_partial_decay, 10) == 1
    # Dentin und kleine Strukturen innerhalb Zahn - Dentin -> kleine Strukturen innerhalb Zahn
    partial_decay = dentin_and_partial_decay - dentin_parts
    # Hinzufügen der kleinen Strukturen zu Schmelzsegment
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

    # Invertierung Schmelz -> alles außerhalb Schmelz
    start = time.time()
    enamel_negative = ~enamel_layers_extended_smooth_3 == 255
    # alle zusammenhängenden Komponenten -> eine große außerhalb Schmelz Komponente und kleine Komponenten in Schmelz
    # "> 1" -> nicht die größte Kompononente -> kleine Komponenten in Schmelz
    holes_enamel = ccMinSize(enamel_negative, 1) > 1
    # Hinzufügen der kleinen Strukturen
    enamel_layers_extended_smooth_4 = enamel_layers_extended_smooth_3 + holes_enamel
    enamel_layers = enamel_layers_extended_smooth_4
    ### Schmelzsegment fertig
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


# ----- Pipeline, calculate tooth dictionary ----- #
def calcPipeline(path: str, targetPath: str, calcMidSurface: bool, filter_selection_1: str= 'Renyi', filter_selection_2: str= 'Renyi') -> dict:
    """
    This method forms the complete pipeline for the calculation of smoothing,
    labels and medial surfaces. It is very large but therefore the clearest
    @param path: the path to the file that should be entered in the pipeline
    @param targetPath: the path to the directory where the generated images are saved in the file system
    @param filter_selection_1: the segmentation algorithm
    @param filter_selection_2: the segmentation algorithm
    @return: the full created tooth dictionary with all images
    @example:
        path = '/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ'
        targetPath = '/data/MicroCT/Original_ISQ/anatomicalSegmentationOtsu/'
        tooth_dict = pipe_full_dict_selection(path, 'Otsu', 'Otsu')
    """
    # 1. load and filter image
    img, name = loadImage(path, targetPath)
    img_smooth = smoothImage(img, name, targetPath)

    # 2. generate a mask on the image and the smooth image
    tooth, tooth_masked = imageMask(img, img_smooth, name, targetPath)
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
        enamel_midsurface = ""
        dentin_midsurface = ""

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
        'path': path,
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


def calcAnatomicalSegmentation(sourcePath: str, targetPath: str, segmentationType: str, calcMidSurface: bool) -> None:
    """
    Calculates one files in the given source path with the given algorithm and store it
    in the given target path.
    @param sourcePath: The path to the file where the file to be calculated is located
    @param targetPath: the path to the directory, where the files from the calculation should be stored
    @param segmentationType: the thresholding algorithm for segmentation
    @param calcMidSurface: true, if the medial surfaces also should be calculated. False if note
    @example:
        sourcePath = '/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ'
        targetPath = '/data/MicroCT/Original_ISQ/P01A-C0005278AnatomicalSegmentationOtsu/'
        calcAnatomicalSegmentation(sourcePath, targetPath, "Otsu", True)
    """
    tooth_segmentation = calcPipeline(sourcePath, targetPath, calcMidSurface, segmentationType, segmentationType)
    writeToothDict(tooth_segmentation, targetPath, calcMidSurface)
    tooth_segmentation_name = tooth_segmentation['name']
    print("Done: " + tooth_segmentation_name)

