import numpy as np
import matplotlib.pyplot as plt

from ..style.titles import _titles
from ..style.template import _header, _footer
from ..utils.utils import _limiter, _scaler

def line(data,
         x,
         y='auto',
         dropna=True,
         median_line=False,
         legend=False,
         y_scale='linear',
         palette='default',
         style='astetik',
         title='',
         sub_title='',
         footnote=None,
         samplenote=None,
         x_label='',
         y_label='',
         drawstyle='default',
         linestyle='solid',
         markerstyle='o',
         dpi=72):

    """TIMESERIES LINE PLOT

    USE
    ===
    line_plot(data=ldata,
          x='value',
          linestyle='dashdot',
          palette='colorblind',
          title="The main title comes here",
          sub_title="Suptibtle comes here")

    data :: pandas dataframe
    x :: one or more columns of data
    y :: a single timeseries column (no need to be dt)

    linestyle :: 'solid', 'dashed', 'dashdot' , 'dotted'
    markerstyle :: ".", ",", "o", "+", "x", "|", "_", "^", "v"

    """

    # START OF PLOT SPECIFIC >>>
    if type(x) != type([]):
        x = [x]

    lines = len(x)

    if dropna == True:
        data = data[data[x].isna() == False]

    x_data = []

    for i in range(len(x)):
        x_data.append(np.array(data[x[i]]))

    if y == 'auto':
        y = range(len(data))
    else:
        y = data[y]

    markers = ["o", "+", "x", "|", "-", ",", ".", "^", "v"]
    # <<< END OF PLOT SPECIFIC


    # START OF HEADER >>>
    palette = _header(palette, style, n_colors=lines, dpi=dpi)  # NOTE: y exception
    # <<< END OF HEADER

    # # # # PLOT STARTS # # # #
    for i in range(lines):
        p = plt.plot(y,
                     x_data[i],
                     marker=markers[i],
                     drawstyle=drawstyle,
                     linestyle=linestyle,
                     c=palette[i],
                     linewidth=2,
                     markersize=7,
                     markeredgewidth=2,
                     mfc='white',
                     rasterized=True,
                     aa=True,
                     alpha=1)
    # # # # PLOT ENDS # # # #

    if median_line:
        x_mean = x.mean()
        x_mean = np.full(len(data), x_mean)
        plt.plot(y, x_mean)

    # START OF TITLES >>>
    _titles(p, data, title, sub_title, samplenote, footnote)
    # <<< END OF TITLES

    if legend != False:
        plt.legend(x, loc=1)

    # FOOTER STARTS >>>
    _footer(p, x_label, y_label)
    # <<< FOOTER ENDS
