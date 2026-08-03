"""Institutional quantitative research platform foundation."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("institutional-factor-platform")
except PackageNotFoundError:  # Source tree import without an installed distribution.
    __version__ = "0.1.0"

__all__ = ["__version__"]
