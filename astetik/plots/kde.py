import seaborn as sns
import matplotlib.pyplot as plt

from ..style.formats import _thousand_sep
from ..style.style import params
from ..style.titles import _titles
from ..style.template import _header, _footer
from ..utils.utils import _limiter, _scaler


def kde(data,
        x,
        y=None,
        cumulative=False,
        palette='default',
        style='astetik',
        dpi=72,
        title='',
        sub_title='',
        x_label='',
        y_label='',
        legend=False,
        x_scale='linear',
        y_scale='linear',
        x_limit=None,
        y_limit=None,
        save=False):

    '''KDE PLOT

    Create a single Kernel Estimation Density (KDE) style
    histogram.

    Inputs: 1 or 2
    Features: At least 1 continuous

    1. USE
    ======
    ast.kde(data=df
            x='Fare',
            palette='blue_to_red')

    2. PARAMETERS
    =============
    2.1 INPUT PARAMETERS
    --------------------
    data :: pandas dataframe

    x :: x-axis data (continuous)

    y :: x-axis overlap data (continuous or categorical)

    --------------------
    2.2. PLOT PARAMETERS
    --------------------
    cumulative :: If True, showing the cumulative distribution.

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

    if y != None:
        n = 2
        data2 = data[y]
    else:
        n = 1
        data2 = None

    # HEADER
    palette = _header(palette, style, n_colors=n, dpi=dpi)

    p, ax = plt.subplots(figsize=(params()['fig_width'],
                                  params()['fig_height']))

    p = sns.kdeplot(data=data[x],
                    y=data2,
                    shade=True,
                    cut=5,
                    shade_lowest=False,
                    color=palette[0],
                    legend=legend,
                    cumulative=cumulative,
                    kernel='gau',
                    bw='scott')

    # SCALING AND LIMITS
    if x_scale != 'linear' or y_scale != 'linear':
        _scaler(p, x_scale, y_scale)

    if x_limit != None or y_limit != None:
        _limiter(data=data, x=x, y=y, x_limit=x_limit, y_limit=y_limit)

    # FOOTER
    _thousand_sep(p, ax, data, x, y)
    _titles(title, sub_title=sub_title)
    _footer(p, x_label, y_label, save=save)
