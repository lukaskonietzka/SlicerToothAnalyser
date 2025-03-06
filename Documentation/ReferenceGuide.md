# Reference Guide (Developers)
This chapter is intended as a reference for all developers who want to further develop
the Tooth Analyser. It discusses the architecture of the module and outlines the steps
required to add additional functionality.

## Table of contents
- [1. Get started with 3D Slicer development](#1-get-started-with-3d-slicer-development)
- [2. Setup your IDE and python environment](#2-setup-your-ide-and-python-environment)
- [3. Architecture of Tooth Analyser](#3-architecture-of-tooth-analyser)
  - [3.1. Imported classes and methods](#31-imported-classes)
  - [3.2. UI Connection](#32-ui-connection)
  - [3.3. ParameterNode](#33-parameternode)
  - [3.4. Static UI Elements](#34-static-ui-elements)
  - [3.5. Event-Functions](#35-event-functions)
  - [3.6. Logic interface](#36-logic-interface)
- [4. Add a new Feature to the ToothAnalyser](#4-add-a-new-feature-to-the-toothanalyser)
- [5. Build a python module](#5-build-a-python-module)

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
the **Tooth Analyser** must be launched in the local environment. To do this,
the module needs to be added to the **3D Slicer Path** via the Extension Wizard.  

- Clone the **main branch** of the repository to your file system  
- Open **3D Slicer**  
- Open the module **Extension Wizard** (Modules: **Developer Tools / Extension Wizard**)  
- Click the button **Select Extension**  
- Select the cloned **Tooth Analyser** repository  
- Click **OK**  
- Switch to the module **Tooth Analyser** (Modules: **Segmentation / Tooth Analyser**)  
- Now you can edit the **source code** and the **UI**  


## 2. Setup your IDE and Python environment
If you want to effectively develop the **Tooth Analyser**, it is highly recommended to use an **IDE**.  
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

## 3. Architecture of Tooth Analyser
The architecture of the **Tooth Analyser** has been kept as modular as possible.
Additionally, care has been taken to ensure that the complexity of the code remains low.  

### 3.1. Imported classes
The following table provides a rough overview of the most important classes in the
**Tooth Analyser**. The order represents a general orientation regarding their importance.

| Classes                    | Description                                                                                                                    |
|----------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| ToothAnalyserWidget        | This class provides the connection to the User Interface and the Slicer cor application.<br/>                                  |
| ToothAnalyserLogic         | This class represents an interface for alle Features in the ToothAnalyser. Every new Feature have to follow this interface     |
| ToothAnalyserParameterNode | The ParameterNode class handles the UI connection. Every parameter form the ui that needs an connection should be listed here. |

### 3.2. UI connection
**3D Slicer** provides the **Qt Designer** for creating a UI. This allows for quickly
and interactively building a UI. The Qt Designer generates an XML file, which can
then be integrated into the module. The **Tooth Analyser** implements this via the
method `createUI()`.
```python
def createUI(self) -> any:
    uiWidget = slicer.util.loadUI(self.resourcePath("UI/ToothAnalyser.ui"))
```
For building an ui we refer to the documentation of the OT-Designer

### 3.3. ParameterNode
For parsing the parameters in the UI, Slicer has developed its own mechanism called
**ParameterNode**. This links a UI element with a variable in the source code.
The **ParameterNode** ensures that the UI is updated whenever the variable in the
source code changes, and vice versa. The **ParameterNode** can be further broken
down and made more generic through the **ParameterPack**.
```python
@parameterPack
class AnatomicalParameters:
    currentAnatomicalVolume: vtkMRMLScalarVolumeNode
    calcMidSurface: bool
    useAnatomicalForBatch: bool

@parameterNodeWrapper
class ToothAnalyserParameterNode:
    anatomical: AnatomicalParameters
    status: str = ""
```
The **ParameterNode** and **ParameterPack** are implemented as classes with the corresponding annotations.  
This allows Slicer to parse them into the UI. This mechanism provides a benefit in terms of **usability**.
When elements are retrieved from the UI via the **ParameterNode**, they can be saved when the scene is saved.  

For the exact linkage of the **ParameterNode** to the UI, please refer to the 3D Slicer UI documentation:  
[3D Slicer UI Connection](https://slicer.readthedocs.io/en/latest/developer_guide/parameter_nodes/gui_connection.html)

### 3.4. Static UI elements
In the class **ToothAnalyserWidget**, there is a method that initializes all static UI elements and links them with an
event function. These are usually buttons, where pressing the button triggers a function.
```python
def connectStaticUiElements(self) -> None:
    self.ui.applyAnalytics.connect("clicked(bool)", self.onApplyAnalyticsButton)
    self.ui.applyAnatomical.connect("clicked(bool)", self.onApplyAnatomicalButton)
    self.ui.applyBatch.connect("clicked(bool)", self.onApplyBatchButton)
```

### 3.5. Event Functions
The class **ToothAnalyserWidget** handles the entire UI logic. All the click logic needed is implemented in this class.  
Additionally, this class has event methods that are triggered by specific user actions. This makes it easy to respond
to user events. A list of possible event methods is provided in the following code block.
```markdown
enter()             -> called each time the user enters the module
exit()              -> called each time the user opens a different module
cleanup()           -> called when the module closes
onSceneStartClose() -> called just before the scene is closed
onSceneEndClose()   -> called after the scene is closed
observerParameter() -> called each time the ui changes (ModifiedEvent)
```
The **ToothAnalyser** uses these methods to update the UI and to initialize and destroy the module when it is no
longer needed.

### 3.6. Logic Interface
The **ToothAnalyser** provides an interface for the various features that defines the structure a new feature should
have. There are four methods that differentiate between these features.
```python
class ToothAnalyserLogic(ScriptedLoadableModuleLogic):
    def preProcessing(self) -> None:
        """Implement pre processing here use 'pass' if not necessary"""
        pass
    
    def postProcessing(self) -> None:
        """implement post processing here use 'pass' if not necessary"""
        pass
      
    def execute(self, param: ToothAnalyserParameterNode) -> None:
        """Abstract method"""
        raise NotImplementedError("Please implement the methode")
    
    def executeAsBatch(self, param: ToothAnalyserParameterNode) -> None:
        """Abstract method"""
        raise NotImplementedError("Please implement the methode")
```
The methods `preProcessing()` and `postProcessing()` receive a standard implementation, allowing the same
pre- or post-processing to be applied for all current and future features. Each feature to be integrated into the
**ToothAnalyser** has the class **ToothAnalyserLogic** as its parent class. Therefore, for each functionality, the
methods `execute()` and `executeAsBatch()` must be implemented.

## 4. Add a new Feature to the ToothAnalyser
To add a new feature to the **Tooth Analyser**, there are generally four steps required, which are explained in more
detail below:

- Build your **UI** in the Designer  
- Add a **ParameterPack** to the existing **ParameterNode**  
- Register your **applyButton** in the **ToothAnalyserWidget** class  
- Add your **custom logic class**

### 4.1. Build your UI in the Designer
The first step is to build a UI using the **QT Designer**. The **Edit UI** button in Developer Mode in 3D Slicer can
be used for this. There are no strict limits when creating the UI, but it is highly recommended to follow the existing
structure and encapsulate a new feature completely within a collapsible button. Once the parameters and structure are
defined, you can move on to the next step.  

### 4.2 Add a ParameterPack for your Parameters
As previously described, a connection between the UI and the program code must be established using the **ParameterNode**.  
The process is as follows:
```python
# 1. add ParameterPack here
@parameterPack
class NewParameterPack:
  newParameter1: str
  newParameter2: bool

# already exists
@parameterNodeWrapper
class ToothAnalyserParameterNode:
    """
    All parameters needed by module
    separated in: analytical, anatomical, batch
    """
    analytical: AnalyticalParameters
    anatomical: AnatomicalParameters
    batch: Batch
    # 2. add ParameterPack here
    newParameterPacK: NewParameterPack
    status: str = ""
```
The types for the individual parameters must match the types of the UI elements. A good overview of possible connections
is provided in the Slicer documentation:  
[Available Connectors](https://slicer.readthedocs.io/en/latest/developer_guide/parameter_nodes/gui_connection.html).

### 4.3 Register your apply-button in the widget class
Once the parameters are available, an **Apply button** must be registered to later read all the parameters and trigger
the logic.
```python
def connectStaticUiElements(self) -> None:
    """
    This method connects all static ui elements that has no specific parameter
    More elements can be added.
    """
    self.ui.applyAnalytics.connect("clicked(bool)", self.onApplyAnalyticsButton)
    self.ui.applyAnatomical.connect("clicked(bool)", self.onApplyAnatomicalButton)
    self.ui.applyBatch.connect("clicked(bool)", self.onApplyBatchButton)
    # 1. add button here
    self.ui.applyNewFunction.connect("clicked(bool)", self.onApplyNewFunction)

# 2. add apply function
def onApplyNewFunction(self) -> None:
    # set processing mode
    self.activateComputingMode(True)
    with slicer.util.tryWithErrorDisplay(_("Failed to compute results."), waitCursor=True):
        # call logic here  
        NewFunction.execute(param=self._param)
    self.activateComputingMode(False)
```

### 4.4. Add your custom logic class
In the final step, the logic for the new feature must be added. It is important that the complete logic is encapsulated
within the class. If extensive logic is required, please refer to the following chapter. To add new logic, proceed as
follows.
```python
class NewFunction(ToothAnalyserLogic):
    def execute(self):
        self.preProcessing()
        # implement the logic here
        pass
    def executeAsBatch(self):
        # implement the logic for batch here
        pass
```
The new logic class must be a subclass of **ToothAnalyserLogic**, and the methods `execute()` and `executeAsBatch()`
should be implemented. These classes can then be called from the **Widget class** and will start the implemented
algorithm. The **execute** method can either be a class method or an instance method.

## 5. Build a python module
In many cases, the logic to be implemented is very complex and too large to fit into a single class.  
It is recommended to separate the algorithm from Slicer activities and provide a separate Python module for it.
```markdown
ToothAnalyser  
├── Resources  
├── Testing  
└── ToothAnalyserLib  
    |── AnatomicalSegmentation
    └── NewFunction
```