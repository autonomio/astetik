import seaborn as sns

from ..style.template import _header, _footer


def multicount(data,
               x,
               hue=None,
               row=None,
               col=None,
               col_wrap=4,
               palette='default',
               style='astetik',
               dpi=72,
               title='',
               sub_title='',
               x_label='',
               y_label='',
               x_scale='linear',
               y_scale='linear',
               x_limit=None,
               y_limit=None,
               legend=True,
               save=False):

    '''MULTICOUNT PLOT

    A bar plot for counting values in a single feature and then
    comparing it with 'hue', 'col', and 'row' categorical variables.
    Prints out multiple plots. None of the values can be continuous.
    If you want to use continuous values then go for bargrid() instead.

    Inputs: 3 to 4
    Features: 1 continuous and 2 to 3 categoricals

    1. USE
    ======
    ast.multicount(data=patients,
                   x='expired',
                   hue='gender',
                   col='insurance')

    2. PARAMETERS
    =============
    2.1 INPUT PARAMETERS
    --------------------
    data :: pandas dataframe

    x :: x-axis data (categorical)

    y :: y-axis data (continuous or categorical)

    hue :: color highlight (categorical)

    col :: the side-by-side plot comparison feature

    --------------------
    2.2. PLOT PARAMETERS
    --------------------
    col_wrap :: the number of plots to show per row

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

    if row != None:
        col_wrap = None

    if hue != None:
        n_colors = len(data[hue].unique())
    else:
        n_colors = len(data[x].unique())

    # HEADER STARTS >>>
    palette = _header(palette,
                      style,
                      n_colors=n_colors,
                      dpi=dpi,
                      fig_height=None,
                      fig_width=None)
    # <<< HEADER ENDS

    p = sns.factorplot(data=data,
                       x=x,
                       y=None,
                       hue=hue,
                       row=row,
                       col=col,
                       col_wrap=col_wrap,
                       palette=palette,
                       size=4,
                       kind='count',
                       legend=legend,
                       legend_out=False)

    # FOOTER STARTS >>>
    _footer(p, x_label, y_label, save=save)
