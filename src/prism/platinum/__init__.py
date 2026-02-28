"""Platinum layer - Report and slide deck generation.

Generates PowerPoint presentations from clinical trial deliverables.
"""

from prism.platinum.agent import (
    ChartSeries,
    FigureSlideContent,
    ListingSlideContent,
    PlatinumAgent,
    SlideContent,
    SlideDeck,
    TableSlideContent,
)
from prism.platinum.renderer import (
    PPTXRenderer,
    render_deliverables,
    render_output,
)

__all__ = [
    "PlatinumAgent",
    "SlideContent",
    "SlideDeck",
    "TableSlideContent",
    "FigureSlideContent",
    "ListingSlideContent",
    "ChartSeries",
    "PPTXRenderer",
    "render_output",
    "render_deliverables",
]
