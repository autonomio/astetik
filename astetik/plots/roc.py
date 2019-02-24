import matplotlib.pyplot as plt
from matplotlib import ticker

from ..style.titles import _titles
from ..style.template import _header, _footer

from sklearn.metrics import roc_curve


def roc(y_pred,
        y_true,
        interval=False,
        interval_func=None,
        time_frame=None,
        dropna=False,
        median_line=False,
        drawstyle='default',
        linestyle='solid',
        legend_labels=None,
        palette='default',
        style='astetik',
        dpi=72,
        title='',
        sub_title='',
        x_label='',
        y_label='',
        legend=False,
        x_scale='linear',
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

    style :: Use one of the three core styles:
               'astetik'     # white
               '538'         # grey
               'solarized'   # sepia

             Or alternatively use any matplotlib or seaborn
             style definition.

    dpi :: the resolution of the plot (int value)

    title :: the title of the plot (string value)

    sub_title :: a secondary title to be shown below the title

    x_label :: string value for x-axis label

    y_label :: string value for y-axis label

    x_scale :: 'linear' or 'log' or 'symlog'

    y_scale :: 'linear' or 'log' or 'symlog'

    x_limit :: int or list with two ints

    y_limit :: int or list with two ints

    outliers :: Remove outliers using either 'zscore' or 'iqr'

    '''

    # START OF PLOT SPECIFIC >>>

    fpr, tpr, thresholds = roc_curve(y_pred, y_true)

    # START OF HEADER >>>
    palette = _header(palette, style, n_colors=1, dpi=dpi)
    # <<< END OF HEADER

    p, ax = plt.subplots(figsize=(7, 7))

    plt.plot([0, 1], [0, 1], linewidth=2, color='#1B2F33', linestyle='dashed')
    plt.plot(fpr, tpr,
             linewidth=3,
             color=palette,
             linestyle=linestyle,
             drawstyle=drawstyle,
             c=palette,
             rasterized=True,
             aa=True,
             alpha=1)

    # HEADER
    _titles(title, sub_title=sub_title)
    _footer(p, x_label, y_label, save=save)

    plt.axis([0, 1, 0, 1])

    if legend != False:
        if legend_labels != None:
            x = legend_labels
        plt.legend(x,
                   framealpha=0.0,
                   fontsize=14,
                   loc=1,
                   ncol=1,
                   bbox_to_anchor=(1.35, 1.0))

    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=6))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(nbins=6))
