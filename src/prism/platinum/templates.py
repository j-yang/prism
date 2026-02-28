"""Slide layout templates for PPTX generation.

Defines layout constants and styling for different slide types.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class SlideLayout:
    """Layout dimensions for a slide."""

    width: int = 9144000  # 10 inches in EMUs (914400 EMUs per inch)
    height: int = 6858000  # 7.5 inches in EMUs

    margin_top: int = 457200  # 0.5 inch
    margin_bottom: int = 457200
    margin_left: int = 457200
    margin_right: int = 457200

    title_height: int = 914400  # 1 inch
    subtitle_height: int = 457200  # 0.5 inch
    footer_height: int = 457200  # 0.5 inch


@dataclass
class TextStyle:
    """Text styling configuration."""

    font_name: str = "Arial"
    font_size_title: int = 32  # pt
    font_size_subtitle: int = 20
    font_size_body: int = 12
    font_size_table: int = 10
    font_size_footer: int = 9

    color_title: Tuple[int, int, int] = (0, 51, 102)  # Dark blue
    color_subtitle: Tuple[int, int, int] = (102, 102, 102)  # Gray
    color_body: Tuple[int, int, int] = (0, 0, 0)  # Black
    color_footer: Tuple[int, int, int] = (128, 128, 128)  # Light gray


@dataclass
class TableStyle:
    """Table styling configuration."""

    header_bg_color: Tuple[int, int, int] = (0, 51, 102)  # Dark blue
    header_font_color: Tuple[int, int, int] = (255, 255, 255)  # White
    row_bg_color_odd: Tuple[int, int, int] = (240, 240, 240)  # Light gray
    row_bg_color_even: Tuple[int, int, int] = (255, 255, 255)  # White
    border_color: Tuple[int, int, int] = (200, 200, 200)  # Gray

    cell_padding: int = 76200  # 0.083 inch in EMUs
    min_row_height: int = 304800  # 0.333 inch in EMUs


@dataclass
class ChartStyle:
    """Chart styling configuration."""

    color_palette: Tuple[Tuple[int, int, int], ...] = (
        (0, 112, 192),  # Blue
        (192, 80, 77),  # Red
        (79, 129, 89),  # Green
        (128, 100, 162),  # Purple
        (247, 150, 70),  # Orange
        (75, 172, 198),  # Cyan
    )

    axis_font_size: int = 10
    legend_font_size: int = 9
    title_font_size: int = 14


DEFAULT_LAYOUT = SlideLayout()
DEFAULT_TEXT_STYLE = TextStyle()
DEFAULT_TABLE_STYLE = TableStyle()
DEFAULT_CHART_STYLE = ChartStyle()


LAYOUT_TITLE = "title"
LAYOUT_TITLE_CONTENT = "title_content"
LAYOUT_BLANK = "blank"


SLIDE_TYPE_LAYOUTS = {
    "title": LAYOUT_TITLE,
    "table": LAYOUT_TITLE_CONTENT,
    "figure": LAYOUT_TITLE_CONTENT,
    "listing": LAYOUT_TITLE_CONTENT,
    "text": LAYOUT_TITLE_CONTENT,
}
