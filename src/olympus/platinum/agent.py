"""PydanticAI agent for Platinum slide generation.

Generates slide content for clinical trial deliverables (tables, figures, listings).
"""

import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from olympus.agent.base import BaseAgent


class TableSlideContent(BaseModel):
    """Content for a table slide."""

    headers: List[str] = Field(..., description="Column headers")
    rows: List[List[str]] = Field(
        default_factory=list, description="Table rows (each row is list of cell values)"
    )
    column_widths: Optional[List[int]] = Field(
        None, description="Relative column widths (optional)"
    )
    transpose: bool = Field(
        default=False, description="Transpose table (rows become columns)"
    )


class ChartSeries(BaseModel):
    """A single series in a chart."""

    name: str = Field(..., description="Series name (e.g., 'Treatment A')")
    values: List[float] = Field(..., description="Data values")
    labels: Optional[List[str]] = Field(
        None, description="X-axis labels (if different)"
    )


class FigureSlideContent(BaseModel):
    """Content for a figure/chart slide."""

    chart_type: str = Field(
        ..., description="Chart type: line, bar, column, scatter, pie"
    )
    title: str = Field(..., description="Chart title")
    x_axis_label: str = Field(default="", description="X-axis label")
    y_axis_label: str = Field(default="", description="Y-axis label")
    series: List[ChartSeries] = Field(default_factory=list, description="Data series")
    x_labels: List[str] = Field(default_factory=list, description="X-axis labels")
    show_legend: bool = Field(default=True, description="Show legend")


class ListingSlideContent(BaseModel):
    """Content for a data listing slide."""

    columns: List[str] = Field(..., description="Column names")
    data: List[List[str]] = Field(default_factory=list, description="Row data")
    max_rows: int = Field(default=20, description="Max rows per slide")
    show_row_numbers: bool = Field(default=True, description="Show row numbers")


class SlideContent(BaseModel):
    """Generated content for a single slide."""

    slide_type: str = Field(
        ..., description="Slide type: title, table, figure, listing, text"
    )
    title: str = Field(..., description="Slide title")
    subtitle: Optional[str] = Field(None, description="Slide subtitle")
    footer: Optional[str] = Field(None, description="Footer text (e.g., 'Study XYZ')")
    table_content: Optional[TableSlideContent] = Field(
        None, description="Table content (if slide_type=table)"
    )
    figure_content: Optional[FigureSlideContent] = Field(
        None, description="Figure content (if slide_type=figure)"
    )
    listing_content: Optional[ListingSlideContent] = Field(
        None, description="Listing content (if slide_type=listing)"
    )
    text_content: Optional[str] = Field(
        None, description="Text content (if slide_type=text)"
    )
    notes: Optional[str] = Field(None, description="Speaker notes")
    confidence: str = Field(
        default="high", description="Generation confidence (high/medium/low)"
    )


class DeliverableSlides(BaseModel):
    """All slides for a single deliverable."""

    deliverable_id: str = Field(..., description="Deliverable ID (e.g., 14.1.1)")
    deliverable_type: str = Field(
        ..., description="Deliverable type (table/listing/figure)"
    )
    slides: List[SlideContent] = Field(default_factory=list, description="Slides")


class SlideDeck(BaseModel):
    """Complete slide deck for a study."""

    title: str = Field(..., description="Presentation title")
    subtitle: Optional[str] = Field(None, description="Presentation subtitle")
    author: Optional[str] = Field(None, description="Author")
    date: Optional[str] = Field(None, description="Date")
    slides: List[SlideContent] = Field(default_factory=list, description="All slides")


SYSTEM_PROMPT_PLATINUM = """You are a clinical trial slide deck expert.

Generate slide content for clinical trial deliverables including tables, figures, and listings.
You understand clinical data presentation standards and statistical reporting.

SLIDE TYPES:
1. **Title slide**: Presentation title, study info, date
2. **Table slide**: Demographics, efficacy endpoints, safety summaries
3. **Figure slide**: Line charts (longitudinal), bar charts (categorical), scatter plots
4. **Listing slide**: Raw data listings with key columns
5. **Text slide**: Key findings, conclusions

LAYOUT RULES:
- Title slides: Large title, subtitle, footer with study info
- Table slides: Title above, table with headers, footnotes below
- Figure slides: Title above, chart centered, legend visible
- Listing slides: Compact table, row numbers, scroll if needed

CLINICAL TRIAL CONVENTIONS:
- Demographics table: N, Mean, SD, Median, Min, Max for continuous
- Demographics table: n, % for categorical
- Efficacy tables: Show by treatment group, p-values if applicable
- Safety tables: TEAEs by SOC/PT, SAEs, deaths
- Longitudinal figures: Line charts with error bars
- Categorical figures: Bar charts with counts/percentages

OUTPUT FORMAT:
Return JSON matching the requested schema exactly.
"""


class PlatinumAgent(BaseAgent):
    """PydanticAI agent for generating slide content."""

    def __init__(
        self,
        provider: str = "deepseek",
        db_path: Optional[str] = None,
    ):
        super().__init__(provider=provider, db_path=db_path)

    def _get_system_prompt(self) -> str:
        return SYSTEM_PROMPT_PLATINUM

    def generate_title_slide(
        self,
        study_title: str,
        protocol_no: str,
        subtitle: Optional[str] = None,
    ) -> SlideContent:
        """Generate a title slide.

        Args:
            study_title: Study title
            protocol_no: Protocol number
            subtitle: Optional subtitle

        Returns:
            SlideContent for title slide
        """
        return SlideContent(
            slide_type="title",
            title=study_title,
            subtitle=subtitle or f"Protocol {protocol_no}",
            footer=f"Confidential - {protocol_no}",
            confidence="high",
        )

    def generate_deliverable_slides(
        self,
        deliverable: Dict[str, Any],
        data: Optional[Dict[str, Any]] = None,
    ) -> DeliverableSlides:
        """Generate slides for a single deliverable.

        Args:
            deliverable: Deliverable info from meta.platinum_dictionary
            data: Optional data from Gold/Silver layer

        Returns:
            DeliverableSlides with all slides for this deliverable
        """
        deliv_id = deliverable.get("deliverable_id", "unknown")
        deliv_type = deliverable.get("deliverable_type", "table")
        title = deliverable.get("title", deliv_id)
        population = deliverable.get("population", "")
        elements = deliverable.get("elements", [])

        prompt = f"""## Task: Generate Slide Content for Deliverable {deliv_id}

### Deliverable Info
- ID: {deliv_id}
- Type: {deliv_type}
- Title: {title}
- Population: {population}
- Elements: {json.dumps(elements, indent=2)[:2000]}

### Data (if available)
```json
{json.dumps(data, indent=2)[:3000] if data else "No data provided"}
```

---

## Output Schema

Return JSON matching DeliverableSlides schema:

```json
{{
  "deliverable_id": "{deliv_id}",
  "deliverable_type": "{deliv_type}",
  "slides": [
    {{
      "slide_type": "table|figure|listing|text",
      "title": "Slide title",
      "subtitle": "Optional subtitle",
      "footer": "{population}",
      "table_content": {{...}},  // if table
      "figure_content": {{...}},  // if figure
      "listing_content": {{...}},  // if listing
      "text_content": "...",  // if text
      "notes": "Speaker notes",
      "confidence": "high|medium|low"
    }}
  ]
}}
```

---

## Rules

1. **Table slides**: Include headers and rows with actual data values
2. **Figure slides**: Define chart type, series, and axis labels
3. **Listing slides**: Show key columns, max 20 rows per slide
4. **Multiple slides**: If data is large, generate multiple slides
5. **Confidence**:
   - "high" = data provided, standard layout
   - "medium" = some assumptions made
   - "low" = no data, placeholder content

Generate 1-3 slides for this deliverable based on content.
"""

        return self.run(prompt, result_type=DeliverableSlides)

    def generate_slide_deck(
        self,
        study_info: Dict[str, Any],
        deliverables: List[Dict[str, Any]],
        gold_data: Optional[Dict[str, Any]] = None,
    ) -> SlideDeck:
        """Generate complete slide deck for a study.

        Args:
            study_info: Study information (title, protocol, etc.)
            deliverables: List of deliverables from meta.platinum_dictionary
            gold_data: Optional Gold layer data

        Returns:
            SlideDeck with all slides
        """
        all_slides = []

        title_slide = self.generate_title_slide(
            study_title=study_info.get("study_title", "Clinical Study Report"),
            protocol_no=study_info.get("protocol_no", ""),
            subtitle=study_info.get("subtitle"),
        )
        all_slides.append(title_slide)

        for deliverable in deliverables:
            deliv_id = deliverable.get("deliverable_id", "")
            data = gold_data.get(deliv_id) if gold_data else None

            try:
                deliv_slides = self.generate_deliverable_slides(deliverable, data)
                all_slides.extend(deliv_slides.slides)
                print(f"  Generated {len(deliv_slides.slides)} slides for {deliv_id}")
            except Exception as e:
                print(f"  Warning: Failed to generate slides for {deliv_id}: {e}")

        return SlideDeck(
            title=study_info.get("study_title", "Clinical Study Report"),
            subtitle=study_info.get("protocol_no", ""),
            slides=all_slides,
        )
