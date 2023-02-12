import pkg_resources
from . import util
from .logging import PMMLogger
from .args import PMMArgs, Version
from .exceptions import Continue, Deleted, Failed, FilterFailed, LimitReached, NonExisting, NotScheduled, NotScheduledRange, TimeoutExpired


try:
    __version__ = pkg_resources.get_distribution("pmmutils").version
except pkg_resources.DistributionNotFound:
    __version__ = ""
__author__ = "Nathan Taggart"
__credits__ = "meisnate12"
__package_name__ = "pmmutils"
__project_name__ = "PMM-Utils"
__description__ = "Util Methods for PMM"
__url__ = "https://github.com/meisnate12/pmmutils"
__email__ = 'meisnate12@gmail.com'
__license__ = 'MIT License'
__all__ = [
    "PMMLogger",
    "PMMArgs",
    "Version",
    "Continue",
    "Deleted",
    "Failed",
    "FilterFailed",
    "LimitReached",
    "NonExisting",
    "NotScheduled",
    "NotScheduledRange",
    "TimeoutExpired",
]
