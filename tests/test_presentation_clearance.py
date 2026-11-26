"""Legends clear visible stroke extents, and repeated label layout uses data anchors."""

from itertools import pairwise

import numpy as np
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.transforms import Bbox

from astetik._presentation_clearance import covered, required_limit
from astetik._presentation_legend import Placement, clear_legends, place_legend
from astetik._presentation_notes import end_labels, spread_end_labels


@pytest.mark.parametrize('kind', ['line', 'patch', 'collection', 'polygon', 'scatter', 'marker'])
def test_legend_clearance_includes_strokes_whose_centrelines_are_outside_the_box(kind):
    figure = Figure(figsize=(4, 3), dpi=72)
    FigureCanvasAgg(figure)
    axis = figure.add_subplot()
    axis.set(xlim=(0, 1), ylim=(0, 1))
    if kind == 'line':
        axis.plot([0.4, 0.6], [0.5, 0.5], linewidth=20)
    elif kind == 'patch':
        axis.add_patch(Rectangle((0.4, 0.4), 0.2, 0.1, fill=False, linewidth=20))
    elif kind == 'collection':
        axis.add_collection(LineCollection([[(0.4, 0.5), (0.6, 0.5)]], linewidths=20))
    elif kind == 'polygon':
        axis.add_collection(PolyCollection([[(0.4, 0.4), (0.6, 0.4), (0.5, 0.5)]],
                                          facecolors='none', edgecolors='black', linewidths=20))
    elif kind == 'scatter':
        axis.scatter([0.5], [0.5], s=4, linewidths=20, edgecolors='black')
    else:
        axis.plot([0.5], [0.5], linestyle='none', marker='o', markersize=2, markeredgewidth=20)
    x, y = axis.transData.transform((0.5, 0.5))
    near, far = Bbox.from_bounds(x - 2, y + 5, 4, 4), Bbox.from_bounds(x - 2, y + 20, 4, 4)
    assert covered(axis, near)
    assert not covered(axis, far)
    assert required_limit(axis, near, False) > 1


@pytest.mark.parametrize('kind', ['line', 'patch', 'collection', 'scatter', 'marker'])
def test_invisible_strokes_do_not_add_legend_clearance(kind):
    figure = Figure(figsize=(4, 3), dpi=72)
    FigureCanvasAgg(figure)
    axis = figure.add_subplot()
    axis.set(xlim=(0, 1), ylim=(0, 1))
    if kind == 'line':
        axis.plot([0.4, 0.6], [0.5, 0.5], linewidth=20, color='none')
    elif kind == 'patch':
        axis.add_patch(Rectangle((0.4, 0.4), 0.2, 0.1, linewidth=20, edgecolor='none'))
    elif kind == 'collection':
        axis.add_collection(PolyCollection([[(0.4, 0.4), (0.6, 0.4), (0.5, 0.5)]],
                                          linewidths=20, edgecolors=(0, 0, 0, 0)))
    elif kind == 'scatter':
        axis.scatter([0.5], [0.5], s=4, linewidths=20, edgecolors=(0, 0, 0, 0))
    else:
        axis.plot([0.5], [0.5], linestyle='none', marker='o', markersize=2,
                  markeredgewidth=20, markeredgecolor='none')
    x, y = axis.transData.transform((0.5, 0.5))
    assert not covered(axis, Bbox.from_bounds(x - 2, y + 5, 4, 4))


@pytest.mark.parametrize('horizontal', [False, True])
def test_fixed_legend_headroom_clears_the_stroke_in_both_orientations(horizontal):
    figure = Figure(figsize=(4, 3), dpi=72)
    FigureCanvasAgg(figure)
    axis = figure.add_subplot()
    axis.set(xlim=(0, 1), ylim=(0, 1))
    legend = place_legend(axis, Placement('upper right', [Line2D([], [], label='Series')], 9, False))
    figure.canvas.draw()
    box = legend.get_window_extent()
    point = (box.x0 - 6, (box.y0 + box.y1) / 2) if horizontal else ((box.x0 + box.x1) / 2, box.y0 - 6)
    x, y = axis.transData.inverted().transform(point)
    xs, ys = ([x, x], [y - 0.02, y + 0.02]) if horizontal else ([x - 0.02, x + 0.02], [y, y])
    line = axis.plot(xs, ys, linewidth=20)[0]
    path = line.get_transform().transform_path(line.get_path())
    assert not path.intersects_bbox(box.padded(2), filled=False)
    assert path.intersects_bbox(box.padded(12), filled=False)
    clear_legends([axis], {'kind': 'bar'}, horizontal)
    path = line.get_transform().transform_path(line.get_path())
    assert not path.intersects_bbox(legend.get_window_extent().padded(12), filled=False)


def test_end_label_offsets_are_recomputed_from_their_anchors_after_resizing():
    figure = Figure(figsize=(4, 3), dpi=72)
    FigureCanvasAgg(figure)
    axis = figure.add_subplot()
    axis.set(xlim=(0, 1), ylim=(0, 1))
    end_labels(axis, [('First', (0.9, 0.5), 'black'), ('Second', (0.9, 0.501), 'black')], 9)
    spread_end_labels(figure)
    offsets = [label.xyann for label in axis.texts]
    assert any(offset[1] != 0 for offset in offsets)
    spread_end_labels(figure)
    assert np.allclose([label.xyann for label in axis.texts], offsets)
    figure.set_figheight(1.5)
    spread_end_labels(figure)
    boxes = sorted((label.get_window_extent() for label in axis.texts), key=lambda box: box.y0)
    assert all(lower.y1 <= upper.y0 for lower, upper in pairwise(boxes))
