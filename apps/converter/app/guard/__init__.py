"""The guard (design 6.1): runs in the API process before any parsing. Checks the name, the extension, the size,
the content proof of each format, the archive limits and the declared part type. It never parses a document body:
it looks at signatures, directory entries and image headers only."""
from .checks import UploadInfo, check_extension, check_name, inspect_upload, sniff_kinds
from .problems import ProblemError

__all__ = ["ProblemError", "UploadInfo", "check_extension", "check_name", "inspect_upload", "sniff_kinds"]
