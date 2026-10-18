#-----------------------------------------------------------------------------
set(MODULE_NAME ToothAnalyserMicroCT)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  ${MODULE_NAME}Lib/Algorithms/__init__.py
  ${MODULE_NAME}Lib/Algorithms/Anatomical.py
  ${MODULE_NAME}Lib/Algorithms/Scanco.py
  ${MODULE_NAME}Lib/Algorithms/utils.py
  ${MODULE_NAME}Lib/SampleData/__init__.py
  ${MODULE_NAME}Lib/SampleData/ToothCrownMicroCT.py
  ${MODULE_NAME}Lib/tha/__init__.py
  ${MODULE_NAME}Lib/tha/filtering.py
  ${MODULE_NAME}Lib/tha/ml.py
  ${MODULE_NAME}Lib/tha/segmentation.py
  ${MODULE_NAME}Lib/tha/util.py
  Testing/Python/${MODULE_NAME}Tests.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  Resources/UI/${MODULE_NAME}.ui
  Resources/Icons/logo.png
  Resources/Icons/logoTHA.png
  Resources/Icons/logoLMU.svg
  Resources/Icons/SampleData.png
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
