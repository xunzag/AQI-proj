"""Shared matplotlib style so every chart has a title, units and source, consistently.

Colours: the first three slots of a colour-blind-validated categorical palette
(blue, orange, aqua), always assigned to pollutants in the same fixed order.
"""

from __future__ import annotations

import matplotlib.pyplot as plt

from .config import FIGURES, SOURCE_NOTE

COLORS = {"PM10": "#2a78d6", "PM2.5": "#eb6834", "NO2": "#1baf7a"}
GREY = "#52514e"
LIGHT_GREY = "#8a8985"
WHO_COLOR = "#e34948"  # reserved for guideline/threshold lines only


def set_style() -> None:
    """Apply a clean, recessive style: light grid, no top/right spines, readable fonts."""
    plt.rcParams.update({
        "figure.figsize": (10, 4.5),
        "figure.dpi": 110,
        "savefig.dpi": 160,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": LIGHT_GREY,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "axes.axisbelow": True,
        "grid.color": "#e6e5e0",
        "grid.linewidth": 0.8,
        "axes.titlesize": 13,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "axes.labelcolor": GREY,
        "xtick.color": GREY,
        "ytick.color": GREY,
        "lines.linewidth": 2,
        "legend.frameon": False,
        "font.size": 10,
    })


def add_source(fig, extra: str = "") -> None:
    """Write the data source (and an optional note) in small grey text under the figure."""
    text = SOURCE_NOTE + (f". {extra}" if extra else "")
    fig.text(0.01, -0.02, text, ha="left", va="top", fontsize=8, color=LIGHT_GREY)


def save(fig, name: str) -> None:
    """Save a figure as PNG into ``figures/``."""
    FIGURES.mkdir(exist_ok=True)
    fig.savefig(FIGURES / f"{name}.png")
