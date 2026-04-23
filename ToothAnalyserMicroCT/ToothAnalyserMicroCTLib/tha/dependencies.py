"""
Helpers for optional runtime dependencies used by the tha package.
"""

import slicer


class DependencyInstallationRequired(RuntimeError):
    """Raised to stop the current workflow after an on-demand install."""


def ensure_numba_available() -> object:
    """
    Import ``numba`` or start its installation in Slicer.

    If installation is triggered, abort the current workflow so the caller can
    ask the user to run the algorithm again afterwards.
    """
    try:
        import numba  # type: ignore
    except ModuleNotFoundError:
        if slicer.util.confirmOkCancelDisplay(
                "This module requires the 'numba' Python package. Click OK to install it now."):
            slicer.util.pip_install("numba")
            raise DependencyInstallationRequired(
                "The module is being installed. Please start the algorithm again afterwards."
            )
        raise
    return numba
