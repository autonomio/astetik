import matplotlib.pyplot as plt
import seaborn as sns

from ..style.formats import _thousand_sep
from ..style.style import params
from ..style.titles import _titles
from ..style.template import _header, _footer
from ..utils.utils import _limiter, _scaler
from ..style.sizer import _sizer


def scat(data,
         x,
         y,
         hue=None,
         size=None,
         palette='default',
         style='astetik',
         dpi=72,
         title='',
         sub_title='',
         x_label='',
         y_label='',
         legend=True,
         x_scale='linear',
         y_scale='linear',
         x_limit=None,
         y_limit=None,
         outliers=False,
         save=False):

    '''SCATTER PLOT

    Observations may overlap, and sizing is possible. All except 'hue' should
    be continuous variables (or sizing can be stepped). If you want to use
    categorical on x-axis, use ast.swarm() or ast.strip() instead.

    1. USE
    ======
    p = scat(data=df,
         x='Age',
         y='Fare',
         hue='Survived',
         size='Rand',
         palette='default',
         style='astetik')

    2. PARAMETERS
    =============
    2.1 INPUT PARAMETERS
    --------------------
    data :: pandas dataframe

    x :: x-axis data

    y :: y-axis data

    hue :: color highlight (categorical or boolean)

    size :: the size of the dots in the plot (continuous or stepped)

    --------------------
    2.2. PLOT PARAMETERS
    --------------------
    None

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

    # PLOT SPECIFIC START >>>
    if hue != None:
        n = len(data[hue].unique())
    else:
        n = 1
        legend = False

    if size == None:
        size = 8
    else:
        size = _sizer(data[size])
    # <<< PLOT SPECIFIC ENDS

    # HEADER STARTS >>>
    palette = _header(palette, style, n_colors=n, dpi=dpi)  # NOTE: y exception
    # <<< HEADER ENDS

    # # # # # # PLOT CODE STARTS # # # # # #
    p, ax = plt.subplots(figsize=(params()['fig_width'],
                                  params()['fig_height']))
    p = sns.stripplot(data=data,
                      x=x,
                      y=y,
                      hue=hue,
                      palette=palette,
                      linewidth=1,
                      size=size)
    # # # # # # PLOT CODE ENDS # # # # # #

    # SCALING AND LIMITS STARTS >>>
    if x_scale != 'linear' or y_scale != 'linear':
        _scaler(p, x_scale, y_scale)

    if x_limit != None or y_limit != None:
        _limiter(data=data, x=x, y=y, x_limit=x_limit, y_limit=y_limit)

    # START OF TITLES >>>
    _titles(title, sub_title=sub_title)
    _thousand_sep(p, ax)
    _footer(p, x_label, y_label, legend, n, save)

    ax.xaxis.set_major_locator(plt.MaxNLocator(5))
