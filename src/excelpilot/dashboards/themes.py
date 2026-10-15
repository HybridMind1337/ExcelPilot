"""Visual design themes and color palettes for generated Excel dashboards."""

from pydantic import BaseModel, Field


class ThemeColors(BaseModel):
    """Hex color codes defining the visual hierarchy."""

    primary: str = "#1E3A8A"  # Deep Navy / Header
    secondary: str = "#3B82F6"  # Royal Blue / Accent
    accent: str = "#0D9488"  # Teal / Highlights
    neutral_dark: str = "#1F2937"  # Text Charcoal
    neutral_light: str = "#F3F4F6"  # Background Tint / Card fill
    card_border: str = "#E5E7EB"  # Card borders
    kpi_delta_positive: str = "#10B981"  # Emerald
    kpi_delta_negative: str = "#EF4444"  # Red
    chart_palette: list[str] = Field(
        default_factory=lambda: [
            "#1E3A8A",
            "#3B82F6",
            "#0D9488",
            "#F59E0B",
            "#6366F1",
            "#EC4899",
            "#8B5CF6",
            "#14B8A6",
        ]
    )


class DashboardTheme(BaseModel):
    """Complete typographic, spacing, and styling specification for an Excel dashboard."""

    name: str
    font_name: str = "Segoe UI"
    title_size: int = 16
    section_header_size: int = 12
    kpi_label_size: int = 9
    kpi_value_size: int = 18
    body_size: int = 10
    colors: ThemeColors = Field(default_factory=ThemeColors)


def get_theme(name: str) -> DashboardTheme:
    """Retrieve theme configuration by name with safe fallback to Executive theme."""
    lower = name.lower()
    if lower == "financial":
        return DashboardTheme(
            name="financial",
            font_name="Calibri",
            colors=ThemeColors(
                primary="#064E3B",  # Forest green
                secondary="#059669",
                accent="#D97706",
                neutral_dark="#111827",
                neutral_light="#F0FDF4",
                card_border="#D1FAE5",
                chart_palette=["#064E3B", "#059669", "#10B981", "#D97706", "#3B82F6"],
            ),
        )
    if lower == "operational":
        return DashboardTheme(
            name="operational",
            font_name="Aptos",
            colors=ThemeColors(
                primary="#1E293B",  # Slate
                secondary="#475569",
                accent="#0284C7",
                neutral_dark="#0F172A",
                neutral_light="#F8FAFC",
                card_border="#E2E8F0",
                chart_palette=["#0284C7", "#0EA5E9", "#64748B", "#F59E0B", "#10B981"],
            ),
        )
    if lower == "minimal":
        return DashboardTheme(
            name="minimal",
            font_name="Arial",
            colors=ThemeColors(
                primary="#18181B",  # Zinc
                secondary="#71717A",
                accent="#2563EB",
                neutral_dark="#09090B",
                neutral_light="#FAFAFA",
                card_border="#E4E4E7",
                chart_palette=["#18181B", "#52525B", "#71717A", "#A1A1AA", "#2563EB"],
            ),
        )
    # Default Executive Theme
    return DashboardTheme(name="executive")
