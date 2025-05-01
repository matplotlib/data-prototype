from pathlib import Path
from . import _version


def _get_version() -> str:
    """Return the version string used for __version__."""
    # Only shell out to a git subprocess if really needed, and not on a
    # shallow clone, such as those used by CI, as the latter would trigger
    # a warning from setuptools_scm.
    # Adapted from Matplotlib
    root = Path(__file__).resolve().parents[2]
    if (root / ".git").exists() and not (root / ".git/shallow").exists():
        try:
            import setuptools_scm  # type: ignore

            return setuptools_scm.get_version(
                root=root,
                version_scheme="release-branch-semver",
                local_scheme="node-and-date",
                fallback_version=_version.version,
            )
        except ImportError:
            return _version.version
    else:  # Get the version from the _version.py setuptools_scm file.
        return _version.version


__version__ = _get_version()
