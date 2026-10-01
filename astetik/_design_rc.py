"""Construct local Matplotlib rc settings from validated design fields."""
from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Literal, Protocol

from ._manifest_types import Axes, FontInfo, Paper, Typography


class RcPolicy(Protocol):
    @property
    def colors(self) -> Mapping[str, str]: ...
    @property
    def typography(self) -> Typography: ...
    @property
    def axes(self) -> Axes: ...
    @property
    def paper(self) -> Paper: ...
    @property
    def font_info(self) -> FontInfo: ...
    def dimensions(self, paper: bool = False, panels: int = 1) -> tuple[float, float]: ...


def rc_settings(policy: RcPolicy, paper: bool = False) -> dict[str, object]:
    """Return rc_context settings; never mutate matplotlib global state."""
    floor = policy.paper["min_fontsize"] if paper else 0
    def size(key: Literal["fontsize", "labelsize", "titlesize", "ticksize", "legendsize"]) -> float:
        return max(policy.typography[key], floor)
    colors, axes = policy.colors, policy.axes
    result: dict[str, object] = {
        "font.family": [policy.font_info["resolved"]], "font.weight": "normal",
        "font.size": size("fontsize"), "axes.labelsize": size("labelsize"),
        "axes.titlesize": size("titlesize"), "axes.titleweight": "normal",
        "xtick.labelsize": size("ticksize"), "ytick.labelsize": size("ticksize"),
        "legend.fontsize": size("legendsize"), "legend.frameon": False,
        "figure.facecolor": colors["paper"], "axes.facecolor": colors["paper"],
        "savefig.facecolor": colors["paper"], "text.color": colors["ink"],
        "axes.labelcolor": colors["ink"], "axes.edgecolor": colors["ink"],
        "xtick.color": colors["ink"], "ytick.color": colors["ink"],
        "axes.linewidth": axes["linewidth"], "axes.grid": axes["grid"],
        "grid.color": colors["line"], "grid.linewidth": axes["linewidth"],
        "grid.alpha": 1.0, "axes.axisbelow": True,
        "xtick.direction": axes["tick_direction"], "ytick.direction": axes["tick_direction"],
        "xtick.major.size": axes["tick_length"], "ytick.major.size": axes["tick_length"],
        "xtick.major.width": axes["linewidth"], "ytick.major.width": axes["linewidth"],
        "figure.figsize": policy.dimensions(paper), "figure.dpi": policy.paper["dpi"] if paper else 120,
        "savefig.dpi": policy.paper["dpi"], "pdf.fonttype": 42, "ps.fonttype": 42,
        "svg.fonttype": "path", "axes.formatter.useoffset": False,
        "axes.formatter.use_mathtext": False, "figure.constrained_layout.use": True,
    }
    result.update({f"axes.spines.{spine}": spine in axes["spines"] for spine in ("left", "right", "top", "bottom")})
    return result


def dimensions_for(policy: Paper, paper: bool, panels: object) -> tuple[float, float]:
    if isinstance(panels, bool) or not isinstance(panels, int) or panels < 1:
        raise ValueError('panels must be a positive integer')
    columns = 2 if policy['preset'] == 'double' and panels > 1 else 1
    width = policy['width_mm'] / 25.4 if paper else 6.2
    return width, (width / columns / policy['aspect']) * math.ceil(panels / columns)
