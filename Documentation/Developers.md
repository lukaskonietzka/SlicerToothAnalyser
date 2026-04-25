# Developers
This chapter is intended as a reference for all developers who want to further develop
ToothAnalyserMicroCT. It discusses the architecture of the module and outlines the steps
required to add additional functionality.

## Table of contents
- [1. Get started with 3D Slicer development](#1-get-started-with-3d-slicer-development)
- [2. Setup your IDE and python environment](#2-setup-your-ide-and-python-environment)
- [3. Architecture of ToothAnalyserMicroCT](#3-architecture-of-toothanalysermicroct)
  - [3.1. Architecture Overview](#31-architecture-overview)
  - [3.2. Imported classes and methods](#32-imported-classes)
  - [3.3. Extending the Architecture](#33-extending-the-architecture)
  - [3.4. Extending Example (Pathological Segmentation)](#34-extending-example)
- [4. Build a Python module](#4-build-a-python-module)

## 1. Get started with 3D Slicer development
Before development can begin, settings must be configured in both Slicer and the module
itself. This section provides an introduction to the necessary steps.

**Enable Developer Mode:**
- Select the **Edit** tab in the menu  
- Then choose **Application Settings**  
- Navigate to the **Developers** page  
- Enable the **Developer Mode** via the checkbox  
- Restart **Slicer**  

In Developer Mode, a section is added to the UI of each module, allowing for editing of
the respective module. Additionally, this mode enables running tests.

**Load Module via Extension Wizard:**  

Once Developer Mode is enabled and the software has been restarted,
**ToothAnalyserMicroCT** must be launched in the local environment. To do this,
the module needs to be added to the **3D Slicer Path** via the Extension Wizard.  

- Clone the **main branch** of the repository to your file system  
- Open **3D Slicer**  
- Open the module **Extension Wizard** (Modules: **Developer Tools / Extension Wizard**)  
- Click the button **Select Extension**  
- Select the cloned **ToothAnalyserMicroCT** repository  
- Click **OK**  
- Switch to the module **ToothAnalyserMicroCT** (Modules: **Segmentation / ToothAnalyserMicroCT**)  
- Now you can edit the **source code** and the **UI**

## 2. Setup your IDE and Python environment
If you want to effectively develop **ToothAnalyserMicroCT**, it is highly recommended to use an **IDE**.  
[PyCharm](https://www.jetbrains.com/pycharm/download/) is a great choice, but any other environment can be used as well.  
Slicer comes with its own **Python environment**, which needs to be selected in the IDE settings.  
You can find it in the **installation folder** of Slicer:
```
./Slicer/bin/PythonSlicer
```
All the packages included with Slicer will then be available. For more detailed information, refer to the Slicer
documentation: [3D Slicer Developer Guide](https://slicer.readthedocs.io/en/latest/developer_guide/python_faq.html).

⚠️ **Notice**: For development with Slicer, it is **mandatory** to use this environment.
You cannot use a custom environment.

## 3. Architecture of ToothAnalyserMicroCT
The architecture of **ToothAnalyserMicroCT** has been kept as modular as possible.
Additionally, care has been taken to ensure that the complexity of the code remains low.

### 3.1. Architecture Overview
**ToothAnalyserMicroCT** follows a simple flow:
- The **ToothAnalyserMicroCTWidget** owns the UI and reads user input from the **ToothAnalyserMicroCTParameterNode**.
- The widget triggers a concrete **ToothAnalyserMicroCTLogic** implementation.
- Each logic class executes its algorithm and can optionally support batch processing.

This separation keeps UI wiring in `ToothAnalyserMicroCT.py` and concentrates algorithms in
`ToothAnalyserMicroCT/ToothAnalyserMicroCTLib/`.

### 3.2. Imported classes
The following table provides a rough overview of the most important classes in the
**ToothAnalyserMicroCT**. The order represents a general orientation regarding their importance.

| Classes                    | Description                                                                                                                    |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| ToothAnalyserMicroCTWidget        | This class provides the connection to the user interface and the Slicer core application.<br/>                                      |
| ToothAnalyserMicroCTLogic         | This class represents an interface for all features in ToothAnalyserMicroCT. Every new feature has to follow this interface.        |
| ToothAnalyserMicroCTParameterNode | The parameter node class handles the UI connection. Every parameter from the UI that needs a connection should be listed here.      |

### 3.3. Extending the Architecture
To extend the module with a new segmentation algorithm or feature:
- Create a **new class** that **derives from `ToothAnalyserMicroCTLogic`**.
- Implement `execute()` and (if needed) `executeAsBatch()`.
- Add a **new segmentation option** in the **ParameterNode** at the top of the file by extending the
  `segmentation` choice list in `ToothAnalyserMicroCTParameterNode`.

This keeps the UI stable while allowing you to swap algorithms based on the selected segmentation option.

### 3.4. Extending Example
The module already includes an example class for **pathological segmentation**. It is intentionally minimal but shows
how a new segmentation algorithm can be integrated. Use it as a template for your own logic class:
- Subclass `ToothAnalyserMicroCTLogic`.
- Provide a readable `__str__()` name for the segmentation selector.
- Implement `execute()` and `executeAsBatch()`.

When you add your own segmentation class, also add it to the `segmentation` field in the
**ToothAnalyserMicroCTParameterNode** so it appears in the UI selector.

## 4. Build a Python module
Complex algorithms should live in a **standalone Python module** under
`ToothAnalyserMicroCT/ToothAnalyserMicroCTLib/` so that UI and Slicer glue stay minimal.
Use this structure as a reference:
```markdown
└── ToothAnalyserMicroCTLib
    ├── Algorithms
    │   ├── Anatomical.py
    │   ├── Scanco.py
    │   └── utils.py
    ├── SampleData
    └── tha
```

Recommended workflow:
- Create a new module file in `ToothAnalyserMicroCT/ToothAnalyserMicroCTLib/Algorithms/` (or in `tha/` if it fits that package).
- Keep the module **Slicer-agnostic**. Accept plain Python types where possible and isolate Slicer-specific IO to
  `ToothAnalyserMicroCT.py` or thin adapters.
- Expose a small public API (one or two functions or a class) that your `ToothAnalyserMicroCTLogic` subclass can call.
- Import and call the module from your logic class, not from the widget.
