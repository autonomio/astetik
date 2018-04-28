import seaborn as sns
import matplotlib.pyplot as plt

from ..style.formats import _thousand_sep
from ..style.style import params
from ..style.titles import _titles
from ..style.template import _header, _footer
from ..utils.utils import _limiter, _scaler


def swarm(data,
          x,
          y,
          hue=None,
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
          save=False):

    '''SWARM PLOT
    This is similar to scatter plot, in the sense that overlapping observations
    are avoided (each sample will be seen as a dot), but observations are
    grouped based on 'x'.

    NOTE: this plot takes time to draw, so if your sample is tens or hundreds
          of thousands of observations, be patient. Or if it's not that important
          that observations do not overlap, try strip() instead. 

    Inputs: 2 to 3
    Features: 1 continuous and 1 or 2 categoricals

    1. USE
    ======
    ast.violin(data=patients,
                x='insurance',
                y='age',
                hue='expired',
                y_limit=None)

    2. PARAMETERS
    =============
    2.1 INPUT PARAMETERS
    --------------------
    data :: pandas dataframe

    x :: x-axis data (categorical)

    y :: y-axis data (continuous or categorical)

    hue :: color highlight (categorical)

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
        legend = False
        n = 1
    # <<< PLOT SPECIFIC ENDS

    # HEADER STARTS >>>
    palette = _header(palette, style, n_colors=n, dpi=dpi)  # NOTE: y exception
    # <<< HEADER ENDS
    p, ax = plt.subplots(figsize=(params()['fig_width'],
                                  params()['fig_height']))
    # # # # # # PLOT CODE STARTS # # # # # #
    order = data[x].unique()
    p = sns.swarmplot(data=data,
                      x=x,
                      y=y,
                      hue=hue,
                      palette=palette,
                      order=order,
                      linewidth=0.5,
                      size=4)
    # # # # # # PLOT CODE ENDS # # # # # #

    # SCALING AND LIMITS STARTS >>>
    if x_scale != 'linear' or y_scale != 'linear':
        _scaler(p, x_scale, y_scale)

    if x_limit != None or y_limit != None:
        _limiter(data=data, x=x, y=y, x_limit=None, y_limit=y_limit)
    # <<< SCALING AND LIMITS ENDS

    # START OF TITLES >>>
    _titles(title, sub_title=sub_title)
    # <<< END OF TITLES

    _thousand_sep(p, ax)
    _footer(p, x_label, y_label, legend, n, save)
    # <<< FOOTER ENDS
    p.set_xticklabels(order, rotation=90)
