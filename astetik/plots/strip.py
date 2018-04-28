import seaborn as sns

import matplotlib.pyplot as plt

from ..style.style import params
from ..style.titles import _titles
from ..style.formats import _thousand_sep
from ..style.template import _header, _footer
from ..utils.utils import _limiter, _scaler


def strip(data,
          x,
          y,
          hue,
          jitter=1,
          dodge=False,
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

    '''STRIP PLOT

    Similar to swarm but now there can be overlapping of observations and
    many more x categorical can be included. Also in this plot 'hue' is
    not optional.

    Inputs: 3
    Features: 1 continuous and 2 categoricals, one should be not more than
              a few unique values (hue).

    1. USE
    ======
    ast.strip(data=patients,
              x='religion',
              y='age',
              hue='expired',
              dodge='true',
              palette='colorblind')

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
    jitter :: an integer value that defines the lateral movement
              of observations. This will effect the visual outputself.

    dodge :: If True then 'hue' values will be separated in their own
             stacks.

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

    n = len(data[hue].unique())

    # HEADER STARTS >>>
    palette = _header(palette, style, n_colors=n, dpi=dpi)  # NOTE: y exception
    # <<< HEADER ENDS
    p, ax = plt.subplots(figsize=(params()['fig_width'],
                                  params()['fig_height']))
    order = data[x].unique()
    p = sns.stripplot(data=data,
                      x=x,
                      y=y,
                      hue=hue,
                      palette=palette,
                      size=4,
                      order=order,
                      dodge=dodge,
                      jitter=jitter)

    # SCALING AND LIMITS STARTS >>>
    if x_scale != 'linear' or y_scale != 'linear':
        _scaler(p, x_scale, y_scale)

    if x_limit != None or y_limit != None:
        _limiter(data=data, x=x, y=y, x_limit=None, y_limit=y_limit)

    # FOOTER STARTS >>>
    _thousand_sep(p, ax)
    _titles(title, sub_title=sub_title)
    _footer(p, x_label, y_label, legend, n, save)

    p.spines['bottom'].set_color('black')
    p.set_xticklabels(order, rotation=90)
