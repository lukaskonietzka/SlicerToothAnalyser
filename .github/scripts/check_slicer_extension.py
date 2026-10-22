"""Validate the repository layout expected for a Slicer scripted extension."""

from pathlib import Path
import ast
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
MODULE_ROOT = ROOT / "ToothAnalyserMicroCT"
LIB_ROOT = MODULE_ROOT / "ToothAnalyserMicroCTLib"


REQUIRED_FILES = (
    ROOT / "CMakeLists.txt",
    MODULE_ROOT / "CMakeLists.txt",
    MODULE_ROOT / "ToothAnalyserMicroCT.py",
    MODULE_ROOT / "Resources" / "UI" / "ToothAnalyserMicroCT.ui",
    MODULE_ROOT / "Testing" / "CMakeLists.txt",
    MODULE_ROOT / "Testing" / "Python" / "CMakeLists.txt",
    MODULE_ROOT / "Testing" / "Python" / "ToothAnalyserMicroCTTests.py",
    LIB_ROOT / "Algorithms" / "__init__.py",
    LIB_ROOT / "SampleData" / "__init__.py",
    LIB_ROOT / "tha" / "__init__.py",
)

EXPECTED_PYTHON_SCRIPTS = (
    "${MODULE_NAME}.py",
    "${MODULE_NAME}Lib/Algorithms/__init__.py",
    "${MODULE_NAME}Lib/Algorithms/Anatomical.py",
    "${MODULE_NAME}Lib/Algorithms/Scanco.py",
    "${MODULE_NAME}Lib/Algorithms/utils.py",
    "${MODULE_NAME}Lib/SampleData/__init__.py",
    "${MODULE_NAME}Lib/SampleData/ToothCrownMicroCT.py",
    "${MODULE_NAME}Lib/tha/__init__.py",
    "${MODULE_NAME}Lib/tha/filtering.py",
    "${MODULE_NAME}Lib/tha/ml.py",
    "${MODULE_NAME}Lib/tha/segmentation.py",
    "${MODULE_NAME}Lib/tha/util.py",
    "Testing/Python/${MODULE_NAME}Tests.py",
)

EXPECTED_RESOURCES = (
    "Resources/Icons/${MODULE_NAME}.png",
    "Resources/UI/${MODULE_NAME}.ui",
    "Resources/Icons/logo.png",
    "Resources/Icons/logoTHA.png",
    "Resources/Icons/logoLMU.svg",
    "Resources/Icons/SampleData.png",
)


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def check_required_files(errors: list[str]) -> None:
    for path in REQUIRED_FILES:
        if not path.is_file():
            fail(f"Missing required file: {path.relative_to(ROOT)}", errors)


def check_generated_files(errors: list[str]) -> None:
    generated_names = {".DS_Store"}
    tracked_files = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=False,
    ).stdout.split(b"\0")
    for relative_name in tracked_files:
        if not relative_name:
            continue
        path = ROOT / relative_name.decode("utf-8")
        if path.name in generated_names or path.suffix in {".pyc", ".pyo"}:
            fail(f"Generated or platform-specific file must not be committed: "
                 f"{path.relative_to(ROOT)}", errors)
        if "__pycache__" in path.parts:
            fail(f"Generated directory must not be committed: "
                 f"{path.relative_to(ROOT)}", errors)


def check_cmake(errors: list[str]) -> None:
    root_cmake = (ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    module_cmake = (MODULE_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")

    for expression in (
        "find_package(Slicer REQUIRED)",
        "include(${Slicer_USE_FILE})",
        "add_subdirectory(ToothAnalyserMicroCT)",
        "include(${Slicer_EXTENSION_GENERATE_CONFIG})",
        "include(${Slicer_EXTENSION_CPACK})",
    ):
        if expression not in root_cmake:
            fail(f"Root CMakeLists.txt is missing: {expression}", errors)

    for expression in (
        "set(MODULE_NAME ToothAnalyserMicroCT)",
        "slicerMacroBuildScriptedModule(",
        "NAME ${MODULE_NAME}",
        "SCRIPTS ${MODULE_PYTHON_SCRIPTS}",
        "RESOURCES ${MODULE_PYTHON_RESOURCES}",
    ):
        if expression not in module_cmake:
            fail(f"Module CMakeLists.txt is missing: {expression}", errors)

    for entry in EXPECTED_PYTHON_SCRIPTS:
        if entry not in module_cmake:
            fail(f"Python script is missing from MODULE_PYTHON_SCRIPTS: {entry}", errors)
        actual_path = entry.replace("${MODULE_NAME}", "ToothAnalyserMicroCT")
        if not (MODULE_ROOT / actual_path).is_file():
            fail(f"Python script listed in CMake does not exist: {actual_path}", errors)

    for entry in EXPECTED_RESOURCES:
        if entry not in module_cmake:
            fail(f"Resource is missing from MODULE_PYTHON_RESOURCES: {entry}", errors)
        actual_path = entry.replace("${MODULE_NAME}", "ToothAnalyserMicroCT")
        if not (MODULE_ROOT / actual_path).is_file():
            fail(f"Resource listed in CMake does not exist: {actual_path}", errors)


def check_python_syntax(errors: list[str]) -> None:
    for path in ROOT.rglob("*.py"):
        if ".git" in path.parts:
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as error:
            fail(f"Invalid Python syntax in {path.relative_to(ROOT)}: {error}", errors)


def main() -> int:
    errors: list[str] = []
    check_required_files(errors)
    check_generated_files(errors)
    check_cmake(errors)
    check_python_syntax(errors)

    if errors:
        print("Slicer extension structure check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Slicer extension structure check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
