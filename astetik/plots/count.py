import seaborn as sns

from ..style.template import _header, _footer
from ..style.formats import _thousand_sep
from ..style.titles import _titles
from ..utils.utils import factorplot_sizing


def count(data,
          x,
          sort=None,
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

    '''COUNT PLOT

    A bar plot for counting values in a single feature. Useful for
    categoricals and stepped data.

    Inputs: 1
    Features: 1 categorical or stepped

    1. USE
    ======
    ast.count(x='insurance', data=patients, palette='Reds')

    2. PARAMETERS
    =============
    2.1 INPUT PARAMETERS
    --------------------
    data :: pandas dataframe

    x :: x-axis data (categorical or stepped)

    --------------------
    2.2. PLOT PARAMETERS
    --------------------
    sort :: If True, will be sorted based on input values.

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
    size, aspect = factorplot_sizing(data[x], auto=True)
    #aspect = int(len(data[x].unique()) / 5)

    if sort != None:
        sort = data[x].value_counts().index.values

    # HEADER STARTS >>>
    palette = _header(palette,
                      style,
                      n_colors=1,
                      dpi=dpi,
                      fig_height=None,
                      fig_width=None)

    p = sns.factorplot(data=data,
                       y=x,
                       palette=palette,
                       size=size,
                       aspect=aspect,
                       kind='count',
                       legend=legend,
                       legend_out=False,
                       order=sort)

    # FOOTER
    _titles(title, sub_title)
    _thousand_sep(p, p.ax, y_sep=False)
    _footer(p, x_label, y_label, save=save)

    p.set_xticklabels(None, rotation=90)
