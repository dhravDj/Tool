"""Presentation intelligence adapters."""

from app.modules.presentation_intelligence.adapters.base import BasePresentationAdapter
from app.modules.presentation_intelligence.adapters.odp_adapter import (
    ODPPresentationAdapter,
)
from app.modules.presentation_intelligence.adapters.ppt_adapter import (
    PPTPresentationAdapter,
)
from app.modules.presentation_intelligence.adapters.pptx_adapter import (
    PPTXPresentationAdapter,
)

__all__ = [
    "BasePresentationAdapter",
    "ODPPresentationAdapter",
    "PPTPresentationAdapter",
    "PPTXPresentationAdapter",
]
