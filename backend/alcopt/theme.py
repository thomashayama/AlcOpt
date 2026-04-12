"""Single source of truth for app colors.

The Streamlit theme in .streamlit/config.toml mirrors these values — keep
them in sync. Use these constants directly when styling matplotlib/plotly
charts or generating custom CSS so the whole app shifts together if the
palette changes.
"""

# Brand
PRIMARY = "#A4243B"  # burgundy — buttons, links, active sidebar item
ACCENT = "#D4A24C"  # warm gold — highlights, chart accents

# Surfaces (dark, warm)
BACKGROUND = "#1A1410"  # main page
SURFACE = "#2A1F1A"  # sidebar, containers, dataframe rows
TEXT = "#F5F0E8"  # body copy on dark surfaces
