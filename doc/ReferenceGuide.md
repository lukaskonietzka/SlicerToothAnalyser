# Reference Guide (Developers)
Diese Kapitel ist als Referenc für alle Entwickler gedacht, die en Tooth Analyser
weiternetwickeln wollen. Es wird die Architektur des Moduls besprochen und welche
Schritte nötig sind, um weitere Funktionalität hinzuzufügen.

## Table of contents
- [1. Get started with 3D Slicer development](#)
- [2. Setup your IDE and python environment](#)
- [3. Architecture of Tooth Analyser](#)
- [4. Add a new Feature to the ToothAnalyser](#)


## 1. Get started with 3D Slicer development
Befor mit dem Entwickeln selbst begonnen werden kann müssen in Slicer und im Modul selber
Einstellungen vorgenommen werden. Dieser Abschnitt gibt eine Einführung in die zu erledigenden
Schritte.

**Aktiviere den Entwicklermodus:**
- Wähle im Menü den Reite Edit
- Wähle dann Application Settings
- Wechsle zu der Seite Developers
- Enable the Developer Mode via the checkox
- Restart Slicer

Im Developer Modus wird in jedes Modul eine Section in die Ui eingebaut mit der eine
Bearbeitung des jeweiligen Moduls erfolgen kann. Außerdem lassen sich so Tests ausführen.

BILD der SECTION

**Modul über den Extension Wizard laden:**

Sobald der Developer Modus aktiviert und die Software neu gestartet wurde, muss der Tooth Analyser in der lokalen
Umgebung gestartet werden. Hierzu muss das Modul über den Extension Wizard dem 3D Slicer Path hinzugefügt werden.

- clone the main Branch of the Repository to your file system
- open 3D Slicer
- open the module Extension Wizward (Modules: Developers Tools / Extension Wizard)
- kick the Button *Select Extension*
- now select the cloned Tooth Analyser repo
- klick ok
- switch to the Modul Tooth Analyser (Modules: Segmentation/Tooth Analyser)
- now you can edit the source code and the ui

## 2. Setup your IDE and Python environment
Wenn efektiv am Tooth Analyser weiterentwickelt werden soll, dann ist es sehr zu empfehlen, eine IDE zu nutzen.
Hierfür eignet sich [PyCharm](https://www.jetbrains.com/pycharm/download/). Es kann aber auch jede andere Umgebung
verwendet werden. Slicer bringt sein eigenes Python environment mit, dass in den Einstellungen ausgewählt werden muss.
Zu finden ist es im Install ordner von Slicer:
```
./Slicer/bin/PythonSlicer
```
Es stehen dann alle packete zur verfügung, die dieses Packet mitbringt. Für genauere Informationen sei auf die
Dokumentation von Slicer verwiesen [3D Slicer Developer Guide](https://slicer.readthedocs.io/en/latest/developer_guide/python_faq.html).

⚠️ **Notice**: Für eine Entwicklung mit Slicer ist es zwingend nötig diese Umgebung zu verwenden. Es kan kein
eigenens Environment verwendet werden.


## 3. Architecture of Tooth Analyser


## 4. Add a new Feature to the ToothAnalyser