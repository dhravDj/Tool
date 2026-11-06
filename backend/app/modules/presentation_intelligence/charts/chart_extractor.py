"""Chart extraction logic for native and inferred presentation charts."""

from typing import Any

from app.modules.presentation_intelligence.schemas.presentation_document import (
    ChartType,
    ElementDimensions,
    ElementPosition,
    SlideChart,
    SlideChartSeries,
)


class PresentationChartExtractor:
    """Extracts native chart elements from PPTX shapes, preserving series and categories."""

    CHART_TYPE_MAP: dict[str, ChartType] = {
        "COLUMN": ChartType.COLUMN,
        "BAR": ChartType.BAR,
        "LINE": ChartType.LINE,
        "PIE": ChartType.PIE,
        "DOUGHNUT": ChartType.DOUGHNUT,
        "AREA": ChartType.AREA,
        "XY_SCATTER": ChartType.SCATTER,
        "RADAR": ChartType.RADAR,
        "BUBBLE": ChartType.SCATTER,
    }

    @classmethod
    def map_chart_type(cls, raw_type_name: str) -> ChartType:
        """Map python-pptx chart type name to canonical ChartType."""
        upper = raw_type_name.upper()
        for key, val in cls.CHART_TYPE_MAP.items():
            if key in upper:
                return val
        return ChartType.UNKNOWN

    @classmethod
    def extract_pptx_chart(
        cls,
        shape: Any,
        slide_id: str,
        slide_number: int,
        chart_counter: int,
    ) -> SlideChart:
        """Extract native chart data from a python-pptx chart shape."""
        chart_id = f"{slide_id}_chart_{chart_counter}"
        chart = shape.chart

        raw_type_name = getattr(chart.chart_type, "name", str(chart.chart_type))
        chart_type = cls.map_chart_type(raw_type_name)

        title: str | None = None
        if getattr(chart, "has_title", False) and chart.chart_title:
            try:
                title = chart.chart_title.text_frame.text.strip()
            except Exception:
                title = None

        categories: list[str] = []
        series_list: list[SlideChartSeries] = []
        legends: list[str] = []

        try:
            plots = getattr(chart, "plots", [])
            for plot in plots:
                # Categories
                if not categories and hasattr(plot, "categories"):
                    for cat in plot.categories:
                        cat_label = getattr(cat, "label", str(cat))
                        categories.append(str(cat_label).strip())

                # Series
                if hasattr(plot, "series"):
                    for s in plot.series:
                        s_name = getattr(s, "name", f"Series {len(series_list) + 1}")
                        raw_values = getattr(s, "values", [])
                        float_values: list[float | None] = []
                        for val in raw_values:
                            try:
                                float_values.append(float(val) if val is not None else None)
                            except (ValueError, TypeError):
                                float_values.append(None)

                        series_list.append(
                            SlideChartSeries(name=str(s_name).strip(), values=float_values)
                        )
                        legends.append(str(s_name).strip())
        except Exception:
            pass

        # Position and dimensions
        left = float(getattr(shape, "left", 0)) / 914400.0  # convert EMU to inches
        top = float(getattr(shape, "top", 0)) / 914400.0
        width = float(getattr(shape, "width", 0)) / 914400.0
        height = float(getattr(shape, "height", 0)) / 914400.0

        return SlideChart(
            chart_id=chart_id,
            slide_id=slide_id,
            slide_number=slide_number,
            chart_type=chart_type,
            title=title,
            categories=categories,
            series=series_list,
            legends=legends,
            position=ElementPosition(left=round(left, 2), top=round(top, 2)),
            dimensions=ElementDimensions(width=round(width, 2), height=round(height, 2)),
            is_inferred=False,
            confidence=1.0,
        )
