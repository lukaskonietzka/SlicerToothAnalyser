"""
Contains the pipeline to calculate a label image from
an .ISQ image
"""

import os
import SimpleITK as sitk
from SimpleITK import Image

from .isq_to_mhd import isq_to_mhd


def generate_tooth_set_keys(filter_selection_1: str, filter_selection_2: str) -> set:
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
__TOOTH_SET_OTSU_OTSU = generate_tooth_set_keys('Otsu', 'Otsu')
__TOOTH_SET_RENYI_RENYI = generate_tooth_set_keys('Renyi', 'Renyi')

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
__PATH_1_100 = '/data/shofmann/MicroCT/Original_ISQ/1_100/'
__PATH_101_200 = '/data/shofmann/MicroCT/Original_ISQ/101_200/'
__PATH_201_250 = '/data/shofmann/MicroCT/Original_ISQ/201_250/'


# ----- Namen Parser -----#
def parse_name(path: str) -> str:
    """
    The name parser is for a uniform conversion
    of the names of the source files for the result files.
    The functions parse only one name. The parser cut of the
    ending after the last point.
    @param path: the path to the file that should be parsed
    @return name: the parsed name for the given file
    @example:
        name = parse_name("/data/MicroCT/Original_ISQ/1_100/P01A-C0005278.ISQ") -> 'P01A-C0005278'
    """
    name = os.path.basename(path).rsplit('.', 1)[0]
    return name

def parse_names(path: str, offset: int=0, size: int=1) -> list[str]:
    """
    The name parser is for a uniform conversion
    of the names of the source files for the result files.
    The functions parse only one name.
    @param path: the path to the directory that should be parsed
    @param offset
    @param size
    @return name: the parsed names for the given directory collected in a list
    @example:
        parse_names("/data/shofmann/MicroCT/Original_ISQ/1_100/") -> ['P01A-C0005278', ...]
    """
    # collect all files that ends with .ISQ
    isq_names = sorted([f for f in os.listdir(path) if f.endswith('.ISQ')])
    mhd_names = []

    if len(isq_names) < offset + size:
        size = len(isq_names) - offset

    for i in range(size):
        mhd_names.append(parse_name(path + isq_names[offset + i]))

    return mhd_names


# ----- Morphological filters ----- #
def bcbr(img: Image, size: int=10) -> Image:
    """
    Filter for closing small holes within the segment (Closing).
    @param img: the image to be filtered
    @param size: the size of the filter mask
    @return: the filtered image
    @example:
        filteredImage = bcbr(image, 10)
    """
    return sitk.BinaryClosingByReconstruction(img, [size, size, size])

def bobr(img: Image, size:int =10) -> Image:
    """
    Filter for removing small structures outside the segment (Opening).
    @param img: the image to be filtered
    @param size: the size of the filter mask
    @return: the filtered image
    @example:
        filteredImage = bobr(image, 10)
    """
    return sitk.BinaryOpeningByReconstruction(img, [size, size, size])

def bmc(img: Image, size: int=1) -> Image:
    """
    Filter for closing small holes within the segment (Closing).
    @param img: the image to be filtered
    @param size: the size of the filter mask
    @return: the filtered image
    @example:
        smoothImage = bmc(img, 1)
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
        smoothImage = bmo(img, 1)
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
    @param size: the size of the filter mask
    @return: the filtered image
    @example:
        smoothImage = medianFilter(img, 5)
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
def cc_min_size(img: any, size: int=10) -> Image:
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
        cc = cc_min_size(img, 10)
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
def threshold_filter(img: Image, mask: bool=False, filter_selection: str='Otsu', debug: bool=False) -> Image:
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

def write_full_dict(tooth: dict, path:str) -> None:
    """
    This method uses the simpleITK (sitk) library to store
    an image in the file system. The write action is based
    on the Tooth-Dictionary.
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
def load_isq(path: str, targetPath: str, name: str) -> Image:
    """
    Load an ISQ-File and convert it into an MHD-File by
    using the isq_to_mhd module from Peter Rösch
    @param path: the path to the ISQ-File to be loaded
    @param targetPath: the path to the MHD-File
    @param name: the name of the MHD-File
    @return: The loaded and converted MHD-File
    @example:
        isq_to_mhd("/data/MicroCT/Original_ISQ/P01A-C0005278.ISQ", "P01A-C0005278.mhd")
    """
    name = targetPath + name + ".mhd"
    isq_to_mhd(path, name)
    return sitk.ReadImage(name)


# ----- Load MHD-File ----- #
def load_mhd(targetPath: str, name: str) -> Image:
    """
    This methode load an MHD-File from an directory
    @param targetPath: the path to the file to be loaded
    @param name: the name of the file
    @return: the loaded .MHD-File
    @example:
        name = parse_names(__PATH_1_100, offset=0, size=1)[0]
        img = load_mhd(name)
    """
    if ".mhd" in targetPath.lower():
        return sitk.ReadImage(targetPath)
    else:
        name = targetPath + name + ".mhd"
    return sitk.ReadImage(name)

def loadFile(path: str) -> Image:
    """

    """
    return sitk.ReadImage(path)


# ----- Medial Surface ----- #
def medialSurface(segment: any) -> any:
    """
    This methode calculate the medial surfaces for each segment
    @param segment: the segment for wiche the medial surface to be needed
    @return: the medial surface for the given segment
    @example:
        name = parse_names(__PATH_1_100, offset=0, size=1)[0]
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
    dist_map_sobel_laplace_thresh = threshold_filter(dist_map_sobel_laplace)
    medial_surface = sitk.Mask(dist_map_sobel_laplace_thresh, segment)

    return medial_surface


#
# Pipeline, mit Selection, berechnet Tooth-Dictionary
#
def pipe_full_dict_selection(path, targetPath, filter_selection_1='Renyi', filter_selection_2='Renyi'):
    # path = '/data/shofmann/MicroCT/Original_ISQ/1_100/P01A-C0005278.ISQ'
    # tooth_dict = pipe_full_dict_selection(path, 'Otsu', 'Otsu')

    import time

    start = time.time()
    name = parse_name(path)
    try:
        img = load_isq(path, targetPath, name)
    except:
        img = load_mhd(path, name)
    stop = time.time()
    print("img: Done ",  f" {(stop-start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")


    # falls Median-Bild bereits in Ordner vorhanden, wird dieses verwendet
    # muss name_img_smooth benannt sein
    start = time.time()
    try:
        img_smooth = load_mhd(targetPath, name + "_" + 'img_smooth')
    except:  # smoothed img not already created
        img_smooth = medianFilter(img, 1) # size anpassen und schauen ob es schneller läuft size = 5
        write(img_smooth, name + "_" + 'img_smooth', targetPath)
    stop = time.time()
    print("img_smooth: Done ",  f" {(stop-start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")

    # falls Zahn-Segmentierung bereits in Ordner vorhanden, wird diese verwendet
    # muss name_tooth_smooth benannt sein
    # ansonsten erster adaptiver Schwellwert (entspricht ersten Schnitt im Histogramm)

    start = time.time()
    try:
        tooth = load_mhd(targetPath, name + "_" + 'tooth')
    except:
        tooth = threshold_filter(img_smooth)

    # Originalbild, Zahn maskiert
    tooth_masked = sitk.Mask(img, tooth)
    stop = time.time()
    print("tooth: Done ", f" {(stop-start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")

    # geglättetes Bild, Zahn maskiert
    start = time.time()
    tooth_smooth_masked = sitk.Mask(img_smooth, tooth)
    stop = time.time()
    print("tooth_smooth: Done ", f" {(stop-start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")

    # zweiter adaptiver Schwellwert (zweiter Schnitt im Histogramm)
    # auf maskierten Originalzahn

    start = time.time()
    enamel_select = threshold_filter(tooth_masked,
                                     tooth_masked,
                                     filter_selection=filter_selection_1)
    # Aufbereinigung
    enamel_select = bcbr(enamel_select)
    # größtes zusammenhängendes Objekt
    enamel_select = cc_min_size(enamel_select, 50) == 1
    # Schmelzsegment auf maskierten Originalzahn fertig
    stop = time.time()
    print("enamel_select: Done ", f" {(stop-start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")

    # zweiter adaptiver Schwellwert (zweiter Schnitt im Histogramm)
    # auf maskierten geglätteten Zahn
    start = time.time()
    enamel_smooth_select = threshold_filter(tooth_smooth_masked,
                                            tooth_smooth_masked,
                                            filter_selection=filter_selection_2)
    # Aufbereinigung
    enamel_smooth_select = bcbr(enamel_smooth_select)
    # Schmelzsegment auf maskierten geglätteten Zahn fertig
    stop = time.time()
    print("enamel_smooth_select: Done ", f" {(stop-start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")

    ### ab hier wird geschichtet

    start = time.time()
    enamel_layers = enamel_select + enamel_smooth_select
    enamel_layers = enamel_layers > 0
    enamel_layers_save = enamel_layers
    stop = time.time()
    print("enamel_layers: Done ", f" {(stop-start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")

    ### Aufbereinigung

    start = time.time()
    enamel_layers_extended = bcbr(enamel_layers)
    enamel_layers_extended_2 = bmc(enamel_layers_extended, 2) #size = 2
    # vergleichbar mit Binary Opening Ergebnis, nur schneller
    enamel_layers_extended_smooth = sitk.SmoothingRecursiveGaussian(enamel_layers_extended_2, 0.04) > 0.7
    enamel_layers_extended_smooth_2 = bmc(enamel_layers_extended_smooth) > 0
    enamel_layers_extended_smooth_2 = cc_min_size(enamel_layers_extended_smooth_2, 10) == 1 # size = 10
    stop = time.time()
    print("enamel_layers_smooth_extended: Done ", f" {(stop-start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")

    ### Auffüllung

    # erweiterte Zahnkontur
    #contour_extended = sitk.BinaryDilate((sitk.BinaryContour(tooth) > 0), 2, sitk.BinaryDilateImageFilter.Ball) > 0
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
    dentin_parts = cc_min_size(dentin_and_partial_decay, 10) == 1
    # Dentin und kleine Strukturen innerhalb Zahn - Dentin -> kleine Strukturen innerhalb Zahn
    partial_decay = dentin_and_partial_decay - dentin_parts
    # Hinzufügen der kleinen Strukturen zu Schmelzsegment
    enamel_layers_extended_smooth_3 = enamel_layers_extended_smooth_2 + partial_decay
    stop = time.time()
    print("enamel_layers_extended_smooth_3: Done ", f" {(stop-start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")

    ### Auffüllung zusätzlich, hilft bei sehr wenigen Datensätzen

    # Invertierung Schmelz -> alles außerhalb Schmelz
    start = time.time()
    enamel_negative = ~enamel_layers_extended_smooth_3 == 255
    # alle zusammenhängenden Komponenten -> eine große außerhalb Schmelz Komponente und kleine Komponenten in Schmelz
    # "> 1" -> nicht die größte Kompononente -> kleine Komponenten in Schmelz
    holes_enamel = cc_min_size(enamel_negative, 1) > 1
    # Hinzufügen der kleinen Strukturen
    enamel_layers_extended_smooth_4 = enamel_layers_extended_smooth_3 + holes_enamel
    enamel_layers = enamel_layers_extended_smooth_4

    ### Schmelzsegment fertig
    stop = time.time()
    print("enamel_layers_extended_smooth_4: Done ", f" {(stop-start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")

    # ~tooth -> nicht Zahn -> alles außerhalb Zahn
    # Schmelz + alles außerhalb Zahn + dicke Kontur -> alles außer Dentin
    start = time.time()
    not_dentin = enamel_layers + (~tooth == 255) + contour_extended > 0
    # Invertierung alles außer Dentin -> Dentin
    dentin_layers = (~not_dentin) == 255
    # Abzug voneinander, um keine zweifach zugewiesnen Voxel zu haben
    dentin_layers = dentin_layers - enamel_layers == 1
    # falls noch einzelne Voxel vorhanden wären
    dentin_layers = cc_min_size(dentin_layers, 50) == 1
    stop = time.time()
    print("dentin_layers: Done ", f" {(stop-start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")

    # Labeldatei
    # dentin == 2
    # enamel == 3
    start = time.time()
    segmentation_labels = enamel_layers * 3 + dentin_layers * 2
    stop = time.time()
    print("segmentation_labels: Done ", f" {(stop-start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")

    # mediale Fläche Schmelz
    start = time.time()
    enamel_midsurface = medialSurface(enamel_layers)
    stop = time.time()
    print("enamel_midsurface: Done ", f" {(stop-start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")

    # mediale Fläche Dentin
    start = time.time()
    dentin_midsurface = medialSurface(dentin_layers)
    stop = time.time()
    print("dentin_midsurface: Done ", f" {(stop-start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")

    ### Erstellung Tooth-Dictionary (siehe Übersicht unten für Beispiellegende des Ergebnissatzes)

    start = time.time()
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

    stop = time.time()
    print("tooth_dict: Done ", f" {(stop-start) // 60:.0f}:{(stop - start) % 60:.0f} minutes")

    return tooth_dict


def calcAnatomicalSegmentation(sourcePath, targetPath, segmentationType: str) -> None:
    """
    Calculates the files in the given path with the given algorithm
    """
    tooth_segmentation = pipe_full_dict_selection(sourcePath, targetPath, segmentationType, segmentationType)
    write_full_dict(tooth_segmentation, targetPath)
    tooth_segmentation_name = tooth_segmentation['name']
    print("Done: " + tooth_segmentation_name)

