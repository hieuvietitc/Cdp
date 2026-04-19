# SQLBuilder has been moved to cdp_shared for reuse across api and segmentation services.
# This file is kept as a shim for backwards compatibility.
from cdp_shared.sql_builder import SQLBuilder  # noqa: F401

__all__ = ["SQLBuilder"]
