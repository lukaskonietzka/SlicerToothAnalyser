# Tooth Analyser Extension
This is a 3D Slicer Extension for the examination of dental structures.
This module was developed for the dental caries research of the Dental
Clinic at the LMU in Munich. In this institution, three-dimensional
Micro CT images of teeth are captured. These images are stored in
the Scanio ISQ format and are intended for further processing for
research purposes.

## Tabel of contents
- [1. Introduction and purpose](#introduction-and-purpose)
- [2. Installation](#2-installation)
- [3. Quick start](#2-quick-start)
- [3. Tutorial](#3-tutorial)
  - [3.1. Analytical](#31-analytical)
  - [3.2. Anatomical Segmentation](#32-anatomical-segmentation)
  - [3.3. Batch Processing](#33-batch-processing)
- [5. Contributors and Organisation](#contributors-and-organisation)
- [6. Developers](#developers)
- [7. Acknowledgement](#acknowledgement)

## 1. Introduction and Purpose
Im Rahmen einer Projektausschreibung der Zahnklinik soll in ferner Zukunft durch einsatz von Neuronalen Netzwerken
eine automatische erkennung von Karies auf Micro CT Bildern realisiert werden. Da das identifizieren
kariöser Stellen nicht trivial ist, soll diese Erweiterung mit einer anatomischen Segmentierung des
Zahnes unterstüzten.

![Screenshot of the application](./Screenshots/slicerFullView.png)
*Abbildung 1: Vollansicht der Erweiterung Tooth Analyser.*

## 2. Installation
To install the Extension simply follow the steps below in the right order.
1. Download and install a latest stable version of 3D Slicer for our operating system (https://download.slicer.org).
2. Start 3D Slicer application, open the Extension Manager (menu: View / Extension manager)
3. Search for the Extension _ToothAnalyser_ and install it via the _INSTALL_ button

## 2. Quick start
Um den Tooth Analyser schnell und korrekt zu verwenden befolgen Sie die nachfolgenden Schritte.
- Start 3D Slicer
- Laden sie ein CT Bild mittels des Imports der 3d Slicer Kernanwendung (Dieses Bild muss nicht gefiltert sein)
- Wechseln Sie in das Modul Tooth Analyser (Modules: Segmentation/Tooth Analyser)
- Wählen Sie im Bereich _Anatomical Segmentation_ das CT aus, dass Sie segmnetieren wollen
- Wählen Sie die Checkbox _calculate medial surface_, wenn die medialen Flächen mitberechnet
  werden sollen und die Checkbox _show 3D_ wenn die medialenb Flächen ebenfalls im 3D Model
  gezeigt werden sollen.
- Starten Sie dann den Algorithmus, durch drücken auf den Button _Apply Anatomical_

⚠️ **Achtung**: Der Algorithmus benötigt iklusiver Filterung und berechnung der medial Fläche
                ca. 17 Minuten.

## 3. Tutorial
In diesem Kapitel sollen die Parametereinstellungen und möglichkeiten des Tooth Analyser genauer
beschrieben werden. Die Erweiterungen Teilt sich in mehrere Funktionen auf, die alle getrennt
gehalten wurden und deshalb auch getrennt ausgeführt werden können. Dieses Kapitel geht über alle
Teile und erläuter sie genauer.

### 3.1. Analytical
mit den analytischhen Funktionen kann aktuell ein histogramm des CTs erstellt werden. Dieses kann
bei der Wahl eines Verfahrens für die Segmentierung helfen.

| Beschreibung                                                                                                                                                                                      | Parameter                                                                                                                                     |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| **Volumen to be analyzed**: Wählen Sie hier das CT, da Sie analysieren möchten<br/><br/>**Show Histogram**: Wenn diese option gewählt wird, wird ein Histogram des zuvor gewählten Bildes erstellt | ![Screenshot of the application](./Screenshots/slicerAnalyticsParameter.png)<br/>*Abbildung 2: Parameterauswahl für die analytische Funktion* |


### 3.2. Anatomical Segmentation
Die anatomischen Segmentierung bildet das Herzstück dieser Erweiterung. Hiermit lässt sich das
Micro CT Bild eines Zahlen automatisch in die Zahnhauptsubstanzen Dentin und Schmelz segmentieren.
Außerdem können zusätzlich medial Flächen genneriert werden, welche für eine klassifizierung von
Karies wichtig sind.

| Beschreibung                                                                                                                                                                                                                                                                                                                                                                                                                                           | Parameter                                                                                                                                   |
|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| **Image for Segmentation**: Wählen Sie hier das CT, dass Sie segmentieren möchten<br/><br/>**Segmentation algorithm**: Wählen Sie hier den Algorithmus, den Sie für die Segmentieren haben wollen.<br/><br/> **Calculate Medial Surface**: Berechnet zu der Segmentierung die Medial Flächen des Dentin und des Schmelzes.<br/><br/>**Show Medial Surface As 3D**: Wenn die Medial Flächen berechnet wurden, können sie als 3D model angezeigt werden. | ![Screenshot of the application](./Screenshots/slicerASParameter.png)<br/>*Abbildung 2: Parameterauswahl für die Anatomische Segmentierung* |


### 3.3. Batch Processing
Im Btach processing können dann die erprobten  parameter an einem Bild auf eine ganze Reihe an
CT Bildern angewendet werden. Die Tooth Analyser erstellt dann im Hintergrund ein Verzeichniss,
indem die Bilder gesichert werden.

| Beschreibung                                                                                                                                                                                                                                                                                                        | Parameter                                                                                                                           |
|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|
| **Load file from**: Wählen Sie hier den Ordner aus, in dem die CTs liegen, die sie bearbeiten möchten<br/><br/>**Save files in**: Wählen Sie hier den Ordner aus, in dem die CTs nach dem Prozess gespeichert werden.<br/><br/>**Save files as**: Wählen Sie hier das Format in dem Sie die CTs abspeichern möchten | ![Screenshot of the application](./Screenshots/slicerBatchParameter.png)<br/>*Abbildung 3: Parameterauswahl für die Batch Funktion* |

## Visualize and save results
Wenn der Algorithmus fertig ist, werden die Ergebnisse automatisch in die SLicer Szene geladen,
sodass sie sofort einsehbar sind. Sie können jedoch mit dieser Segmentierung auch genauere
Analysen vornehemn. Gehen Sie dafür wie folgt vor.
- öffnen sie das Modul Data (Modules: Data)
- schalten sie die gewünschten segmente über die Hierarchie ein und aus
- Speichern Sie Ihre ergebnise über das Menü (Menü: Save)

![Screenshot of the application](./Screenshots/ResultatAS.gif)
*Abbildung 4: Ansicht der Ergebnisse im Modul Data*

## Contributors and Organisation
Die Entwicklung dieser Erweiterung ist eine Zusammenarbeit zwischen der LMU in München
und der Fakultät für Informatik an der technischen Hochschule Augsburg. 

- Lukas Konietzka _(THA)_
- Simon Hoffmann _(THA)_
- Dr. med. Elias Walter _(LMU)_
- Prof. Dr. Peter Rösch _(THA)_

## Developers
Dieses Modul wurde im Rahmen einer Abschhlussarbeit an der Fakultät für Informatik (THA) erstellt.

## Acknowledgement
This module was developed for the dental caries research of the Dental Clinic at
the LMU in Munich. The development is a collaboration between the LMU and the THA.




