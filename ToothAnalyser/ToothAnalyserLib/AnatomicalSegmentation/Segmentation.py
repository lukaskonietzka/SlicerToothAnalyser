import os
import SimpleITK as sitk
from .isq_to_mhd import isq_to_mhd


def generate_tooth_set_keys(filter_selection_1, filter_selection_2):
    # Diese Funktion erzeugt die erweiterte Struktur für das Zahn-Set.
    # Hier werden die Namen für den jeweiligen Ergebnisstapel erzeugt.

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


#
# Globale Zustände
#


# Zahn-SET-Bauplan für einheitliche Namen
__TOOTH_SET = {
    'path',
    'name',
    'img',
    'img_smooth',
    'tooth',
}

# Zahn-Set-Erweiterungen
__TOOTH_SET_OTSU_OTSU = generate_tooth_set_keys('Otsu', 'Otsu')
__TOOTH_SET_RENYI_RENYI = generate_tooth_set_keys('Renyi', 'Renyi')

# Auswahl an adaptiven Schwellwertverfahren
# (streng genommen keine Filter, sondern Punktoperationen)
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

# Absolute Pfade der Originalbilder
__PATH_1_100 = '/data/shofmann/MicroCT/Original_ISQ/1_100/'
__PATH_101_200 = '/data/shofmann/MicroCT/Original_ISQ/101_200/'
__PATH_201_250 = '/data/shofmann/MicroCT/Original_ISQ/201_250/'


def parse_name(path):
    # '/data/shofmann/MicroCT/Original_ISQ/1_100/P01A-C0005278.ISQ' -> 'P01A-C0005278'
    name = path.split("/")[-1].split(".ISQ")[0]
    return name


def parse_names(path, offset=0, size=1):
    # 'path = "/data/shofmann/MicroCT/Original_ISQ/1_100/" -> ['P01A-C0005278', ...]
    isq_names = sorted([f for f in os.listdir(path) if f.endswith('.ISQ')]) # alle Filtern mit eine .isq am ende
    mhd_names = []

    if len(isq_names) < offset + size:
        size = len(isq_names) - offset

    for i in range(size):
        mhd_names.append(parse_name(path + isq_names[offset + i]))

    return mhd_names


#
# Morphologische Filter
#
def bcbr(img, size=10):
    return sitk.BinaryClosingByReconstruction(img, [size, size, size])

def bobr(img, size=10):
    return sitk.BinaryOpeningByReconstruction(img, [size, size, size])

def bmc(img, size=1):
    vectorRadius=(size,size,size)
    kernel=sitk.sitkBall
    return sitk.BinaryMorphologicalClosing(img,
                                           vectorRadius,
                                           kernel)

def bmo(img, size=1):
    vectorRadius=(size,size,size)
    kernel=sitk.sitkBall
    return sitk.BinaryMorphologicalOpening(img,
                                           vectorRadius,
                                           kernel)

#
# Glättungsfilter
#
def median(img, size=1):
    # Glättung mit kantenerhaltenderen Eigenschaften
    return sitk.Median(img, [size,size,size])

def grad(img, sigma=0.03):
    # nicht verwendet, aber liefert bestes Ergebnis mit diesem Filter
    return sitk.GradientMagnitudeRecursiveGaussian(img, sigma)


#
# Typinformation und Typumwandlung
#
def cast_255(img):
    return sitk.Cast(sitk.RescaleIntensity(img), sitk.sitkUInt8)

def cast_accordingly(img, img2):
    return sitk.Cast(img, img2.GetPixelID())

def pixel_type(img):
    return img.GetPixelIDTypeAsString()


#
# Zusammenhangskomponente
#
def cc_min_size(img, size = 10):
    # cc_min_size(sitk_img, 10) > 0 erzeugt Labeldatei mit einem Label ohne kleine Strukturen
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
def threshold_filter(img, mask=False, filter_selection = 'Otsu', debug=False):
    # angelehnt an eine Funktion in: https://github.com/InsightSoftwareConsortium/SimpleITK-Notebook
    # threshold_filter(sitk_img, mask=False, filter_selection = 'Renyi', debug=True)

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


#
# View, basierend auf Namen
# NICHT NOTWENDIG, öffnet nur die Datei mit itksnap, wir nur in view_10 verwendet

# def view(name):
#     # view("P01A-C0005278_img_smooth") -> öffnet P01A-C0005278_img_smooth.mhd
#     !itksnap - g
#     {name + ".mhd"}

# NICHT NOTWENDIG, öffnet die ersten 10 Datein in ITKSNAP, wird nicht verwendet

# def view_10(names, offset=0):
#     # Beispielverwendung:
#     # name = 'P01A-C0005278'
#     # names = []
#     # values = __TOOTH_SET_OTSU_OTSU.copy()
#     # values.remove('name')
#     # values.remove('path')
#     # for val in values:
#     #     names.append(name + '_' + val)
#     #
#     # view_10(names)
#
#     name_size = len(names)
#     view_size = 10
#     command = "itksnap -g "
#
#     if len(names) < offset + view_size:
#         view_size = len(names) - offset
#
#     print("view_size:", view_size)
#     print("offset:", offset)
#
#     if view_size == 1:
#         view(names[offset])
#     else:
#         command = command + names[offset] + ".mhd -o "
#         # command = command + names[offset] + ".mhd -s "
#         for index in range(1, view_size):
#             command = command + names[offset + index] + ".mhd "
#
#         print("command:", command)
#         !{command}


#
# Auswertfunktion, View, nur ein Satz an Labels, basierend auf Name und Verfahren
# NICHT NÖTIG, öffnet Datein anhand des ausgewählten filters, wird nicht verwendet

# def view_labels_by_filt(name, filter_selection_1, filter_selection_2):
#     # name = 'P01A-C0005278'
#     # view_labels_by_filt(name, 'Otsu', 'Otsu')
#
#     filt_1 = filter_selection_1.lower()
#     filt_2 = filter_selection_2.lower()
#     segmentation_labels_key = 'segmentation_' + filt_1 + '_' + filt_2 + '_labels'
#     enamel_midsurface_key = 'enamel_' + filt_1 + '_' + filt_2 + '_midsurface'
#     dentin_midsurface_key = 'dentin_' + filt_1 + '_' + filt_2 + '_midsurface'
#
#     command = "itksnap -g "
#     command = command + name + "_img.mhd -s "
#     command = command + name + "_" + segmentation_labels_key + ".mhd -o "
#     command = command + name + "_" + enamel_midsurface_key + ".mhd "
#     command = command + name + "_" + dentin_midsurface_key + ".mhd "
#     print("command:", command)
#     !{command}


#
# Auswertung, View, beide Sätze an Labels, basierend auf Name
# NICHT NÖTIG, ruft alle labesl in ITKSNAP auf, wird nicht verwendet

# def view_all_labels(name):
#     # name = 'P01A-C0005278'
#     # view_all_labels(name)
#
#     filt_1 = 'Renyi'.lower()
#     filt_2 = 'Renyi'.lower()
#     segmentation_labels_key = 'segmentation_' + filt_1 + '_' + filt_2 + '_labels'
#     enamel_midsurface_key = 'enamel_' + filt_1 + '_' + filt_2 + '_midsurface'
#     dentin_midsurface_key = 'dentin_' + filt_1 + '_' + filt_2 + '_midsurface'
#
#     command = "itksnap -g "
#     command = command + name + "_img.mhd -o "
#     command = command + name + "_" + segmentation_labels_key + ".mhd "
#     command = command + name + "_" + enamel_midsurface_key + ".mhd "
#     command = command + name + "_" + dentin_midsurface_key + ".mhd "
#
#     filt_1 = 'Otsu'.lower()
#     filt_2 = 'Otsu'.lower()
#     segmentation_labels_key = 'segmentation_' + filt_1 + '_' + filt_2 + '_labels'
#     enamel_midsurface_key = 'enamel_' + filt_1 + '_' + filt_2 + '_midsurface'
#     dentin_midsurface_key = 'dentin_' + filt_1 + '_' + filt_2 + '_midsurface'
#
#     command = command + name + "_" + segmentation_labels_key + ".mhd "
#     command = command + name + "_" + enamel_midsurface_key + ".mhd "
#     command = command + name + "_" + dentin_midsurface_key + ".mhd "
#
#     print("command:", command)
#     !{command}


#
# Full-View, basierend auf Name und vorgegebenes Tooth-Set
#NICHT NÖTIG, ruft nur Ergebnisse auf, wird nicht verwendet

# def view_full_dict_by_name(name, TOOTH_SET):
#     # name = 'P01A-C0005278'
#     # view_full_dict_by_name(name, __TOOTH_SET_OTSU_OTSU)
#
#     command = "itksnap -g "
#     command = command + name + "_img.mhd -o "
#     for key in TOOTH_SET:
#         if key == 'path':
#             pass
#         elif key == 'name':
#             pass
#         elif key == 'img':
#             pass
#         else:
#             command = command + name + "_" + key + ".mhd "
#
#     print("command:", command)
#     !{command}


#
# Full-View, basierend auf Tooth-Dictionary
# NICHT NÖTIG, wird nicht verwendet

# def view_full_dict_by_dict(tooth_dict):
#     # name = parse_names(__PATH_1_100, offset=0, size=1)[0]
#     # path = __PATH_1_100 + name + '.ISQ'
#     # tooth = load_full_dict_by_path(path, __TOOTH_SET_OTSU_OTSU)
#     # view_full_dict_by_dict(tooth)
#     # del tooth
#     command = "itksnap -g "
#     command = command + name + "_img.mhd -o "
#     for key in tooth_dict:
#         if key == 'path':
#             pass
#         elif key == 'name':
#             pass
#         elif key == 'img':
#             pass
#         else:
#             command = command + name + "_" + key + ".mhd "
#
#     print("command:", command)
#     !{command}

#
# Write, basierend auf Name
#
def write(img, name, path):
    # name = 'P01A-C0005278'
    # write(sitk_img, name) -> schreibt P01A-C0005278.mhd und P01A-C0005278.raw
    sitk.WriteImage(img, path + name + ".mhd")

#
# Write, basierend auf Tooth-Dictionary
#
def write_full_dict(tooth, path):
    # name = parse_names(__PATH_1_100, offset=0, size=1)[0]
    # tooth = load_full_dict_by_name(name, __TOOTH_SET_OTSU_OTSU)
    # write_full_dict(tooth)
    # del tooth
    name = tooth['name']

    for key in tooth:
        if key == 'path':
            pass
        elif key == 'name':
            pass
        else:
            write(tooth[key], name + "_" + key, path)


def getDirectoryForFile(file_path: str) -> str:
    """
    Extract the folder path from the given file
    """
    folder_path = os.path.dirname(file_path)
    if not folder_path:
        folder_path = os.getcwd()
    return folder_path


#
# Load ISQ
#
def load_isq(path, targetPath, name):
    # name = parse_names(__PATH_1_100, offset=0, size=1)[0] -> "P01A-C0005278"
    # path = __PATH_1_100 + name + ".ISQ"
    # img = load_isq(path, name) -> P01A-C0005278.mhd
    # del img
    name = targetPath + name + ".mhd"
    isq_to_mhd(path, name)
    return sitk.ReadImage(name)

#isq_to_mhd('/data/shofmann/MicroCT/Original_ISQ/1_100/P01A-C0005278.ISQ', 'P01A-C0005278.mhd')
#P01A-C0005278 = sitk.ReadImage('P01A-C0005278.mhd')


#
# Load MHD
#
def load_mhd(targetPath, name):
    # name = parse_names(__PATH_1_100, offset=0, size=1)[0]
    # img = load_mhd(name)
    # del img
    name = targetPath + name + ".mhd"
    return sitk.ReadImage(name)


#
# Load Tooth-Dictionary, basierend auf Pfad und vorgegebenes Tooth-Set
#
# NICHT NÖTIG, Wird nicht verwendet
# def load_full_dict_by_path(path, TOOTH_SET_PLAN):
#     # name = parse_names(__PATH_1_100, offset=0, size=1)[0]
#     # path = __PATH_1_100 + name + '.ISQ'
#     # tooth = load_full_dict_by_path(path, __TOOTH_SET_OTSU_OTSU)
#     # del tooth
#     name = parse_name(path)
#     tooth_dict = {
#         'path': path,
#         'name': name,
#     }
#     for key in TOOTH_SET_PLAN:
#         if key == 'path':
#             pass
#         elif key == 'name':
#             pass
#         else:
#             try:
#                 tooth_dict[key] = load_mhd(name + "_" + key)
#             except:  # Ignore if the key isn't in the dictionary
#                 pass
#
#     return tooth_dict

# path = '/data/shofmann/MicroCT/Original_ISQ/101_200/Z_117_C0005676.ISQ'


#
# Load Tooth-Dictionary, basierend auf Name und vorgegebenes Tooth-Set
#

# NICHT NÖTIG, wird nicht verwendet
# def load_full_dict_by_name(name, TOOTH_DICT_PLAN):
#     # name = parse_names(__PATH_1_100, offset=0, size=1)[0]
#     # tooth = load_full_dict_by_name(name, __TOOTH_SET_OTSU_OTSU)
#     # del tooth
#     path = !pwd
#     tooth_dict = {
#         'path': path[0],
#         'name': name,
#     }
#     for key in TOOTH_DICT_PLAN:
#         if key == 'path':
#             pass
#         elif key == 'name':
#             pass
#         else:
#             try:
#                 tooth_dict[key] = load_mhd(name + "_" + key)
#             except:  # Ignore if the key isn't in the dictionary
#                 pass
#
#     return tooth_dict

# path = '/data/shofmann/MicroCT/Original_ISQ/101_200/Z_117_C0005676.ISQ'
# name = 'Z_117_C0005676'



#
# Legacy Medial Surface
#

# NICHT NÖTIG, wird nicht verwendet
def medial_surface_legacy(segment):
    # print(__TOOTH_SET_OTSU_OTSU)
    # name = parse_names(__PATH_1_100, offset=0, size=1)[0]
    # name_enamel = name + '_enamel_otsu_otsu_layers'
    # enamel = load_mhd(name_enamel)
    # enamel_medial_surface = medial_surface_legacy(enamel)
    # print(enamel_medial_surface)
    #
    # del name_enamel
    # del enamel
    # del enamel_medial_surface

    dist_filter = sitk.SignedMaurerDistanceMapImageFilter()
    dist_filter.SetInsideIsPositive(False)
    dist_filter.SetSquaredDistance(False)
    dist_filter.SetUseImageSpacing(False)
    dist_map = dist_filter.Execute(segment)
    dist_map_masked = sitk.Mask(dist_map, segment)
    dist_map_sobel = sitk.SobelEdgeDetection(dist_map_masked)
    dist_map_sobel_laplace_edges = sitk.SobelEdgeDetection(sitk.Laplacian(dist_map_sobel))
    dist_map_sobel_laplace_edges_thres = threshold_filter(dist_map_sobel_laplace_edges)
    medial_surface = sitk.Mask(dist_map_sobel_laplace_edges_thres, segment)

    return medial_surface

#
# Medial Surface, spezifizierter Schwellwert
#

# NICHT NÖTIG, wird nicht verwendet
def medial_surface_threshold(segment, threshold=25):
    # 25 hat sich gelegentlich als guter Schwellwert erwiesen
    #
    # print(__TOOTH_SET_OTSU_OTSU)
    # name = parse_names(__PATH_1_100, offset=0, size=1)[0]
    # name_enamel = name + '_enamel_otsu_otsu_layers'
    # enamel = load_mhd(name_enamel)
    # enamel_medial_surface = medial_surface_threshold(enamel, 25)
    # print(enamel_medial_surface)
    #
    # del name_enamel
    # del enamel
    # del enamel_medial_surface

    dist_filter = sitk.SignedMaurerDistanceMapImageFilter()
    dist_filter.SetInsideIsPositive(False)
    dist_filter.SetSquaredDistance(False)
    dist_filter.SetUseImageSpacing(False)
    dist_map = dist_filter.Execute(segment)
    dist_map_masked = sitk.Mask(dist_map, segment)
    dist_map_sobel = sitk.SobelEdgeDetection(dist_map_masked)
    dist_map_sobel_thresh = dist_map_sobel < threshold
    medial_surface = sitk.Mask(dist_map_sobel_thresh, segment)

    return medial_surface


#
# Medial Surface
#
def medial_surface(segment):
    # print(__TOOTH_SET_OTSU_OTSU)
    # name = parse_names(__PATH_1_100, offset=0, size=1)[0]
    # name_enamel = name + '_enamel_otsu_otsu_layers'
    # enamel = load_mhd(name_enamel)
    # enamel_medial_surface = medial_surface(enamel)
    # print(enamel_medial_surface)
    #
    # del name_enamel
    # del enamel
    # del enamel_medial_surface

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

    name = parse_name(path)
    img = load_isq(path, targetPath, name)
    print("img: Done")

    # falls Median-Bild bereits in Ordner vorhanden, wird dieses verwendet
    # muss name_img_smooth benannt sein
    try:
        img_smooth = load_mhd(targetPath, name + "_" + 'img_smooth')
    except:  # smoothed img not already created
        img_smooth = median(img, 5)
        write(img_smooth, name + "_" + 'img_smooth', targetPath)
    print("img_smooth: Done")

    # falls Zahn-Segmentierung bereits in Ordner vorhanden, wird diese verwendet
    # muss name_tooth_smooth benannt sein
    # ansonsten erster adaptiver Schwellwert (entspricht ersten Schnitt im Histogramm)
    try:
        tooth = load_mhd(targetPath, name + "_" + 'tooth')
    except:
        tooth = threshold_filter(img_smooth)

    # Originalbild, Zahn maskiert
    tooth_masked = sitk.Mask(img, tooth)
    print("tooth: Done")

    # geglättetes Bild, Zahn maskiert
    tooth_smooth_masked = sitk.Mask(img_smooth, tooth)
    print("tooth_smooth: Done")

    # zweiter adaptiver Schwellwert (zweiter Schnitt im Histogramm)
    # auf maskierten Originalzahn
    enamel_select = threshold_filter(tooth_masked,
                                     tooth_masked,
                                     filter_selection=filter_selection_1)
    # Aufbereinigung
    enamel_select = bcbr(enamel_select)
    # größtes zusammenhängendes Objekt
    enamel_select = cc_min_size(enamel_select, 50) == 1
    # Schmelzsegment auf maskierten Originalzahn fertig
    print("enamel_select: Done")

    # zweiter adaptiver Schwellwert (zweiter Schnitt im Histogramm)
    # auf maskierten geglätteten Zahn
    enamel_smooth_select = threshold_filter(tooth_smooth_masked,
                                            tooth_smooth_masked,
                                            filter_selection=filter_selection_2)
    # Aufbereinigung
    enamel_smooth_select = bcbr(enamel_smooth_select)
    # Schmelzsegment auf maskierten geglätteten Zahn fertig
    print("enamel_smooth_select: Done")

    ### ab hier wird geschichtet

    enamel_layers = enamel_select + enamel_smooth_select
    enamel_layers = enamel_layers > 0
    enamel_layers_save = enamel_layers
    print("enamel_layers: Done")

    ### Aufbereinigung

    enamel_layers_extended = bcbr(enamel_layers)
    enamel_layers_extended_2 = bmc(enamel_layers_extended, 2)
    # vergleichbar mit Binary Opening Ergebnis, nur schneller
    enamel_layers_extended_smooth = sitk.SmoothingRecursiveGaussian(enamel_layers_extended_2, 0.04) > 0.7
    enamel_layers_extended_smooth_2 = bmc(enamel_layers_extended_smooth) > 0
    enamel_layers_extended_smooth_2 = cc_min_size(enamel_layers_extended_smooth_2, 10) == 1
    print("enamel_layers_smooth_extended: Done")

    ### Auffüllung

    # erweiterte Zahnkontur
    #contour_extended = sitk.BinaryDilate((sitk.BinaryContour(tooth) > 0), 2, sitk.BinaryDilateImageFilter.Ball) > 0
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
    print("enamel_layers_extended_smooth_3: Done")

    ### Auffüllung zusätzlich, hilft bei sehr wenigen Datensätzen

    # Invertierung Schmelz -> alles außerhalb Schmelz
    enamel_negative = ~enamel_layers_extended_smooth_3 == 255
    # alle zusammenhängenden Komponenten -> eine große außerhalb Schmelz Komponente und kleine Komponenten in Schmelz
    # "> 1" -> nicht die größte Kompononente -> kleine Komponenten in Schmelz
    holes_enamel = cc_min_size(enamel_negative, 1) > 1
    # Hinzufügen der kleinen Strukturen
    enamel_layers_extended_smooth_4 = enamel_layers_extended_smooth_3 + holes_enamel
    enamel_layers = enamel_layers_extended_smooth_4

    ### Schmelzsegment fertig
    print("enamel_layers_extended_smooth_4: Done")

    # ~tooth -> nicht Zahn -> alles außerhalb Zahn
    # Schmelz + alles außerhalb Zahn + dicke Kontur -> alles außer Dentin
    not_dentin = enamel_layers + (~tooth == 255) + contour_extended > 0
    # Invertierung alles außer Dentin -> Dentin
    dentin_layers = (~not_dentin) == 255
    # Abzug voneinander, um keine zweifach zugewiesnen Voxel zu haben
    dentin_layers = dentin_layers - enamel_layers == 1
    # falls noch einzelne Voxel vorhanden wären
    dentin_layers = cc_min_size(dentin_layers, 50) == 1
    print("dentin_layers: Done")

    # Labeldatei
    # dentin == 2
    # enamel == 3
    segmentation_labels = enamel_layers * 3 + dentin_layers * 2
    print("segmentation_labels: Done")

    # mediale Fläche Schmelz
    enamel_midsurface = medial_surface(enamel_layers)
    print("enamel_midsurface: Done")

    # mediale Fläche Dentin
    dentin_midsurface = medial_surface(dentin_layers)
    print("dentin_midsurface: Done")

    ### Erstellung Tooth-Dictionary (siehe Übersicht unten für Beispiellegende des Ergebnissatzes)

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

    print("tooth_dict: Done")

    return tooth_dict

#
# Wrapper für Pipelin, Selection
# berechnet die Pipeline für ein vorgegebenes Schwellwertverfahren
#
# def do_fast_selection(path, filter_selection_1 = 'Renyi', filter_selection_2 = 'Renyi'):
#     # path = '/data/shofmann/MicroCT/Original_ISQ/1_100/P01A-C0005278.ISQ'
#     # name = do_fast_selection(path, 'Otsu', 'Otsu')
#     tooth = pipe_full_dict_selection(path, filter_selection_1, filter_selection_2)
#     write_full_dict(tooth, path)
#     name = tooth['name']
#     print("Done: " + name)
#     return name


#
# Wrapper für Pipeline, Selection, skaliert
# berechnet die Pipeline für ein vorgegebenes Schwellwertverfahren
# und für die vorgegebene Anzahl von Datein in einem Ordner
#
# def do_fast_x_selection(path, offset=0, size=1, filter_selection_1='Renyi', filter_selection_2='Renyi'):
#     # path = "/data/shofmann/MicroCT/Original_ISQ/1_100/"
#     # names = do_fast_x_selection(path, offset=0, size=1, 'Otsu', 'Otsu')
#     isq_names = sorted([f for f in os.listdir(path) if f.endswith('.ISQ')])
#     mhd_names = []
#
#     if len(isq_names) < offset + size:
#         size = len(isq_names) - offset
#
#     for i in range(size):
#         print(path + isq_names[offset + i])
#         mhd_names.append(do_fast_selection(path + isq_names[offset + i], filter_selection_1, filter_selection_2))
#
#     return mhd_names


#
# Wrapper für kompletten Datensatz
# Berechnet den Datensatz für beide Schwellwertverfahren
#

# def do_fast(path):
#     # path = '/data/shofmann/MicroCT/Original_ISQ/1_100/P01A-C0005278.ISQ'
#     # name = do_fast(path)
#     tooth_renyi_renyi = pipe_full_dict_selection(path, 'Renyi', 'Renyi')
#     write_full_dict(tooth_renyi_renyi, path)
#     name = tooth_renyi_renyi['name']
#     tooth_otsu_otsu = pipe_full_dict_selection(path, 'Otsu', 'Otsu')
#     write_full_dict(tooth_otsu_otsu, path)
#     print("Done: " + name)
#     return name

def calcAnatomicalSegmentation(sourcePath, targetPath, segmentationType: str) -> None:
    """
    Calculates the files in the given path with the given algorithm
    """
    tooth_segmentation = pipe_full_dict_selection(sourcePath, targetPath, segmentationType, segmentationType)
    write_full_dict(tooth_segmentation, targetPath)
    tooth_segmentation_name = tooth_segmentation['name']
    print("Done: " + tooth_segmentation_name)


#
# Wrapper für Pipeline, kompletter Datensatz, skaliert
#
# def do_fast_x(path, offset=0, size=1):
#     # path = "/data/shofmann/MicroCT/Original_ISQ/1_100/"
#     # do_fast_x(path, offset=0, size=150)
#
#     isq_names = sorted([f for f in os.listdir(path) if f.endswith('.ISQ')])
#     mhd_names = []
#
#     if len(isq_names) < offset + size:
#         size = len(isq_names) - offset
#
#     for i in range(size):
#         print(path + isq_names[offset + i])
#         mhd_names.append(do_fast(path + isq_names[offset + i]))
#
#     return mhd_names