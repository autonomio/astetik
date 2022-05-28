import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker

from ..style.formats import _thousand_sep
from ..style.style import params
from ..style.titles import _titles
from ..style.template import _header, _footer
from ..style.legend import _legend
from ..utils.utils import _limiter, _scaler
from ..utils.utils import multicol_transform
from ..utils.datetime import date_handler


def line(data,
         x=None,
         y=None,
         xtick_labels=None,
         highlight_x=None,
         interval=False,
         interval_func=None,
         time_frame=None,
         dropna=False,
         median_line=False,
         drawstyle='default',
         linestyle=None,
         linewidth=None,
         markerstyle=None,
         markersize=7,
         markeredgewidth=1,
         smooth=None,
         legend_labels=None,
         annotate_line_end=False,
         annotate_text=None,
         annotate_xy=(),
         annotate_text_xy=(),
         palette='default',
         alpha=1,
         style='astetik',
         dpi=72,
         title='',
         sub_title='',
         titles_align='center',
         x_label='',
         y_label='',
         legend=False,
         legend_position=[],
         x_scale=None,
         y_scale=None,
         x_limit=None,
         y_limit=None,
         save=False):

    '''TIMESERIES LINE PLOT

    A line plot for one or more columns all with a comparable
    value, in a time sequence. IF 'x' is None, all columns except
    'y' will be included.

    1.USE
    =====
    line_plot(data=ldata,
              x='value',
              linestyle='dashdot',
              palette='colorblind',
              title="The main title comes here",
              sub_title="Suptibtle comes here")

    Inputs: 1 or more continuous and an optional timestamp
    Features: Continuous and optional datetime format

    2. PARAMETERS
    =============
    2.1 INPUT PARAMETERS
    --------------------
    data :: pandas dataframe

    x :: one or more columns of data

    y :: a single timeseries column (no need to be dt)
         and if y is not defined, then a sequence will
         be automatically generated as time labels.

    --------------------
    2.2. PLOT PARAMETERS
    --------------------
    interval :: If not False, should be number of minutes per
                 sample as int or one of the presets:
                 - 'quarter'
                 - 'half',
                 - 'full' (days)
                 - 'week'
                 - 'month' (30 days)
                 - 'year'.

    interval_func :: The grouping by function that will be used:

                        'median', 'mean', 'mode',
                        'first', 'last', 'std', 'mode'
                        'max', 'min', 'sum', 'random',
                        or 'freq'

    time_frame :: the time frame to be used for x-axis labels:

                  'year', 'month', 'day', 'hour', 'minute', 'second'

    median_line :: If True, a median line will be drawn

    drawstyle :: 'default', 'steps', 'steps-pre','steps-mid' or 'steps-post'

    linestyle :: 'solid', 'dashed', 'dashdot' , 'dotted'

    markerstyle :: ".", ",", "o", "+", "x", "|", "_", "^", "v"

    markersize :: the width of the marker in pixels

    markeredgewidth :: the width of the marker edge in pixels

    ----------------------
    2.3. COMMON PARAMETERS
    ----------------------
    palette :: One of the hand-crafted palettes:
               'default'
               'colorblind'
               'blue_to_red'
               'blue_to_green'
               'red_to_green'
               'green_to_red'
               'violet_to_blue'
               'brown_to_green'
               'green_to_marine'

               Or use any cmap, seaborn or matplotlib
               color or palette code, or hex value.

    alpha :: Color saturation (float)

    style :: Use one of the three core styles:
               'astetik'     # white
               '538'         # grey
               'solarized'   # sepia

             Or alternatively use any matplotlib or seaborn
             style definition.

    dpi :: the resolution of the plot (int value)

    title :: the title of the plot (string value)

    sub_title :: a secondary title to be shown below the title

    titles_align :: by default 'center'

    x_label :: string value for x-axis label

    y_label :: string value for y-axis label

    x_scale :: 'linear' or 'log' or 'symlog'

    y_scale :: 'linear' or 'log' or 'symlog'

    x_limit :: int or list with two ints

    y_limit :: int or list with two ints

    outliers :: Remove outliers using either 'zscore' or 'iqr'

    legend_position | list | optionally pass legend `loc` and `ncol` values.

    '''

    data = data.copy(deep=True)

    # START OF PLOT SPECIFIC >>>

    if isinstance(x, list) is False:
        x = [x]

    lines = len(x)

    if dropna:
        data = data[data[x].isna() == False]

    if y == None:
        data[y] = range(len(data))

    if interval != False:
        data = multicol_transform(transform='interval',
                                  data=data,
                                  x=x,
                                  y=y,
                                  func=interval_func,
                                  freq=interval)
    if smooth is not None:

        from scipy.ndimage import gaussian_filter1d
        data[x] = data[x].apply(gaussian_filter1d, sigma=smooth)

    if isinstance(markerstyle, list):
        markers = markerstyle

    elif markerstyle is None:
        markers = ["o", "+", "x", "|", "1", "8", "s", "p",
                   "o", "+", "x", "|", "1", "8", "s", "p"]

    elif isinstance(markerstyle, str):
        markers = []
        for i in range(lines):
            markers.append(markerstyle)
    # <<< END OF PLOT SPECIFIC

    if linestyle is None:
        linestyle = ['solid'] * lines
    elif isinstance(linestyle, str):
        linestyle = [linestyle] * lines

    if linewidth is None:
        linewidth = [2] * lines
    elif isinstance(linewidth, list) is False:
        linewidth = [linewidth] * lines

    if highlight_x is not None:
        linestyle = ['--'] * lines
        linestyle[x.index(highlight_x)] = 'solid'
        linewidth = [2] * lines
        linewidth[x.index(highlight_x)] = 4
    
    # START OF HEADER >>>
    palette = _header(palette, style, n_colors=lines, dpi=dpi)
    # <<< END OF HEADER

    p, ax = plt.subplots(figsize=(params()['fig_width'] + 2,
                                  params()['fig_height']))

    # # # # PLOT STARTS # # # #
    for i in range(lines):
        p = plt.plot(data[y],
                     data[x[i]],
                     marker=markers[i],
                     drawstyle=drawstyle,
                     linestyle=linestyle[i],
                     c=palette[i],
                     linewidth=linewidth[i],
                     markersize=markersize,
                     markeredgewidth=markeredgewidth,
                     mfc='white',
                     rasterized=True,
                     aa=True,
                     alpha=alpha)

    if len(annotate_xy) > 0:

        ax.annotate(annotate_text,
                    xy=(annotate_xy[0], annotate_xy[1]),
                    xycoords='data',
                    xytext=(annotate_text_xy[0], annotate_text_xy[1]),
                    textcoords='axes fraction',
                    color='#888888',
                    size=15,
                    arrowprops=dict(facecolor='#888888',
                                    shrink=0.05,
                                    color='#888888',
                                    lw=2),
                    horizontalalignment='right', 
                    verticalalignment='top')

    if annotate_line_end:

        for i, col in enumerate(x):

            ax.annotate(col + ' ' + str(round(data[col][-1:].values[0], 2)),
                        xy=(len(data[col]), data[col][-1:].values), 
                        xytext=(6, data[col][-1:].values), 
                        color=palette[i], 
                        xycoords='data', 
                        textcoords="offset points",
                        size=14,
                        va="center")

    plt.gcf().axes[0].yaxis.get_major_formatter().set_scientific(False)

    # SCALING
    if y_scale != None or x_scale != None:
        for i in range(lines):
            _scaler(p[i], x_scale, y_scale)

    # # # # PLOT ENDS # # # #
    if median_line:
        if len(x) > 1:
            print("You can only have mean line with single line")
        else:
            x_median = data[x].median()
            x_median = np.full(len(data), x_median)
            plt.plot(data[y], x_median)

    # DATETIME FORMAT
    if time_frame != None:
        data[y] = pd.to_datetime(data[y])
        date_handler(data[y], ax, time_frame)

    # LIMITS
    if x_limit != None or y_limit != None:
        _limiter(data=data, x=x, y='_R_E_S_', x_limit=None, y_limit=y_limit)

    _thousand_sep(p, ax, data, y, x[0])
    _titles(title, sub_title=sub_title, location=titles_align)
    _footer(p, x_label, y_label, save=save, tight=False)
    _legend(x, legend, legend_labels, legend_position)

    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=5, integer=True))

    if xtick_labels is not None:
        _len_ = len(xtick_labels)
        _picks_ = list(range(0, _len_, int(_len_ / 7)))
        plt.xticks(ticks=_picks_, labels=xtick_labels[_picks_])
