# Tooth Analyser Extension
This is a 3D Slicer Extension for the examination of dental structures.
This module was developed for the dental caries research of the Dental
Clinic at the LMU in Munich. In this institution, three-dimensional
Micro CT images of teeth are captured. These images are stored in
the Scanio ISQ format and are intended for further processing for
research purposes.

## Tabel of contents
- [1. Introduction and purpose](#introduction-and-purpose)
- [2. Installation](#installation)
- [3. Quick start](#quick-start)
- [3. Usage](#usage)
  - [3.1. Analytical](#analytical)
  - [3.2. Anatomical Segmentation](#anatomical-segmentation)
  - [3.3. Batch Processing](#batch-processing)
- [4. Tutorial](#tutorial)
- [5. Contributors and Organisation](#contributors-and-organisation)
- [6. Developers](#developers)
- [7. Acknowledgement](#acknowledgement)
- [8. Licence](#licence)

## 1. Introduction and Purpose
Die Entwicklung dieser Erweiterung ist eine Zusammenarbeit zwischen der LMU in München
und der Fakultät für Informatik an der technischen Hochschule Augsburg. Im Rahmen einer 
Projektausschreibung der Zahnklinik soll in ferner Zukunft durch einsatz von Neuronalen Netzwerken
eine automatische erkennung von Karies auf Micro CT Bildern realisiert werden. Da das identifizieren
kariöser Stellen nicht trivial ist, soll diese Erweiterung mit einer anatomischen Segmentierung des
Zahnes unterstüzten.

![Screenshot of the application](./Screenshots/slicerFullView.png)


## 2. Installation
To install the Extension simply follow the steps below in the right order.
1. Download and install a latest stable version of 3D Slicer for our operating system (https://download.slicer.org).
2. Start 3D Slicer application, open the Extension Manager (menu: View / Extension manager)
3. Search for the Extension _ToothAnalyser_ and install it via the _INSTALL_ button

## Quick start

## 3. Usage
Um den Tooth Analyser korrekt zu verwenden befolgen Sie die nachfolgenden Schritte.
- Start 3D Slicer
- Laden sie ein CT Bild mittels des Imports der 3d Slicer Kernanwendung
- Wechseln Sie in das Modul Tooth Analyser (Modules: Segmentation/Tooth Analyser) Hier sehen sie über
    die UI, dass die Erweiterung unterschiedliche Funktionen bereit hält.

### 3.1. Analytical
mit den analytischhen Funktionen kann aktuell ein histogramm des CTs erstellt werden. Dieses kann
bei der Wahl eines Verfahrens für die Segmentierung helfen

| Beschreibung                                                                                                                                                                                      | Parameter                                                                   |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| **Volumen to be analyzed**: Wählen Sie hier das CT, da Sie analysieren möchten<br/><br/>**Show Histogram**: Wenn diese option gewählt wird, wird ein Histogram des zuvor gewählten Bildes erstellt | ![Screenshot of the application](./Screenshots/slicerAnalyticsParameter.png) |


### 3.2. Anatomical Segmentation
Die anatomischen Segmentierung bildet das Herzstück dieser Erweiterung. Hiermit lässt sich das
Micro CT Bild eines Zahlen automatisch in die Zahnhauptsubstanzen Dentin und Schmelz segmentieren.
Außerdem können zusätzlich medial Flächen genneriert werden, welche für eine klassifizierung von
Karies wichtig sind.

| Beschreibung                                                                                                                                                                                                                                                                                                                                                                                                                                           | Parameter                                                             |
|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| **Image for Segmentation**: Wählen Sie hier das CT, dass Sie segmentieren möchten<br/><br/>**Segmentation algorithm**: Wählen Sie hier den Algorithmus, den Sie für die Segmentieren haben wollen.<br/><br/> **Calculate Medial Surface**: Berechnet zu der Segmentierung die Medial Flächen des Dentin und des Schmelzes.<br/><br/>**Show Medial Surface As 3D**: Wenn die Medial Flächen berechnet wurden, können sie als 3D model angezeigt werden. | ![Screenshot of the application](./Screenshots/slicerASParameter.png) |


### 3.3. Batch Processing
Im Btach processing können dann die erprobten  parameter an einem Bild auf eine ganze Reihe an
CT Bildern angewendet werden. Die Tooth Analyser erstellt dann im Hintergrund ein Verzeichniss,
indem die Bilder gesichert werden.

| Beschreibung                                                                                                                                                                                                                                                                                                        | Parameter                                                                |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| **Load file from**: Wählen Sie hier den Ordner aus, in dem die CTs liegen, die sie bearbeiten möchten<br/><br/>**Save files in**: Wählen Sie hier den Ordner aus, in dem die CTs nach dem Prozess gespeichert werden.<br/><br/>**Save files as**: Wählen Sie hier das Format in dem Sie die CTs abspeichern möchten | ![Screenshot of the application](./Screenshots/slicerBatchParameter.png) |


## Tutorial
- In dem Modul haben Sie die Möglichkeit unter verschiedenen Hauptfunktionalitäten zu wählen.
    Alle drei Teile sind getrennt voneinander gebaut und können so auch getrennt ausgeführt werden
  - Analytics - liefert analytische Daten über das Bild
  - Anatomical Segmentation - zerlegt ein Zahn CT in die Zahnhauptteile Dentin und Schmelz
  - Batch Processing - Mittels Batch lässt sich die Anatomical Segmentation auf mehrere Bilder loslassen


![Screenshot of the application](./Screenshots/ResultatAS.gif)


## Contributors and Organisation

## Developers

## Acknowledgement

## Licence
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.



