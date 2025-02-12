# Explanation

Dieses Kapitel soll das Verfahren der Anatomischen Segmentierung genauer erläutern
und geht so in die Tiefe. Hierbei geht es nicht um die konkrete Implementierung, sondern
vielmehr um die Funktionsweise.

## Table of contents
- [1. Loading an image](#1-loading-an-image)
- [2. Smoothing an image](#2-smoothing-an-image)
- [3. Extracting tooth from background](#3-extracting-the-tooth-from-the-background)
- [4. Extracting enamel from tooth](#4-extracting-the-enamel-from-the-tooth)
- [5. Extracting dentin from the rest](#5-extracting-the-dentin-form-the-rest)
- [6. Creating label image](#6-creating-the-label-file)
- [7. Creating medial surface enamel and dentin](#7-creating-medial-surface-for-enamel-and-dentin)

Um den algorithmus besser zu verstehen seien hier die groben Schritte
in der Pipelin gezeigt. Dieses Kapitel greift jeden dieser Schritte kurz auf und geht auf die
wichtigsten merkmale ein.

![pipeline](/Screenshots/ASAlgorithm.png)
*Figure 1:* Pipeline steps for the anatomical segmentation of the CT scans


## 1. Loading an image
Mit dem Tooth analyser ist es prinzipel möglich, alle Bilder in den gängigen
Formaten zu laden. In erster Linie ist dieses Verfahren aber für das -ISQ- Format
für die Bilder der Firma [SCANCO MEDICAL](/https://www.scanco.ch) optimiert. Aus diesem
Grund wird zwischen folgenden Formaten unterschieden.

- .ISQ (original)
- .mhd (meta image file)
- all other files

[Figure 1 Step 1](#table-of-contents)

## 2. Smoothing an image
Wenn ein Bild geladen wurde, uss es im nächsten Schritt gefiltert werden, wenn es
noch keine filterung erhalten hat. Die Überprüfung, ob ein Bild bereits gefiltert wurde
findet über die Standardabweichung eines bilds statt. Wenn diese unter und über einem gewissen
Schwellwert liegt, dann wird das Bild als bereits gefiltert betrachte.

Für die Filterung selber verwendet der Tooth Analyser eine Medial Filterung.
Diese gehört zu der Gruppe der lokalen Operatoren und betrachtet die direkten Nachbarpixel um den
geglätteten Grauwert für den aktuell betrachteten Pixel zu errechnen.

[Figure 1 Step 2](#table-of-contents)

## 3. Extracting the tooth from the background
Nach dem ein Geglättetes Bild vorhanden ist. kann im nächsten Schritt der Zahn aus dem
Hintergund gelöst werden. Hierfür wird das Schwellwertverfahren ausgewählt, das der User
über die UI festlegen kann (Otsu, Renyi). Das Verfahre ermittelt dann einen optimalen Schwellwert
und erstellt somit ein binäres bild, das zwischen dem Zahn und dem Hintergrund unterscheidet siehe
figure 1.

Im selben schritt wird anschließend eine maske erzeugt, die den zahn im Bild fokusiert.
Diese makse wird auf das geglättete bild gelegt. So weise der nächste Schritt, welchen
Teil er betrachten soll.

[Figure 1 Step 3](#table-of-contents)

## 4. Extracting the enamel from the tooth
Mit der erstellten maske, kann nun das selbe Segmentierungsverfahrn wie im vorherigen
Schritt angewendet werden, um das Schmelz segment aus dem Zahn herauszulösen. Die
Segmentierung erfolgt wieder anhand der verschiedenen Grautöne. Das Ergebnis ist
ein Layer in form des Schmelzes

Zusätzlich finden noch Auffülungen und Kantenglättungen statt, die hier aber unberührt
bleiben sollen.

[Figure 1 Step 4](#table-of-contents)

## 5. Extracting the dentin form the rest
Nachdem das Schmel bereits erfolgreich aus dem Zahn extrahiert wurde ist die logische
konsequenz, dass der Rest das Dentin bildet. Um das Dentin zu extrahieren nutzen der
Tooth Analyser deshalb eine auf den ersten Blick einfache Technik. Er rechnet das Dentin
einfach aus dem Übrigen Zahn herraus. Das ergebnis ist dann ein layer in form des Dentin.

*Dentin = Tooth - Enamel*

Auch in diesem Schritt finden weiter kleine glättungen und kantenerhaltenden algorithmen
statt, die das Ergebnis noch weiter verbessern. Diese werden jedoch hier nicht weiter
berücksichtig.

[Figure 1 Step 5](#table-of-contents)

## 6. Creating the label file
In diesem letzten Schritt, der sich auf die Segmentierung bezieht, werden die Layer
für Schmelz und Dentin, die in den Schritten 4. und 5. erstellt wurden zu einer
gelabelten Datei zusammengefasst. Hier können auch Farbanpassungen gemacht werden.

[Figure 1 Step 6](#table-of-contents)

## 7. Creating Medial Surface for Enamel and Dentin
Die erstellung der medial Flächen ist komplett losgelöst von der Segmentierung und im
Tooth Analyser eine optionale Einstellung. Die Medialen Flächen werden vorallem zur
Klassifizierung von Karies eingesetzt. Die Erstellung dieser Flächen ist über
die Laplac interpolation realisert und ist Technisch für Dentin und Schmelz gleich.

[Figure 1 Step 7 and 8](#table-of-contents)