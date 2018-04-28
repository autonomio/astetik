import seaborn as sns

from ..style.template import _header, _footer
from ..utils.utils import _scaler


def bargrid(data,
            x,
            y,
            hue=None,
            row=None,
            col=None,
            col_wrap=None,
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

    '''BAR PLOT

    A multi-dimension bar plot that takes up to 5 features at a time.
    The most important thing to keep in mind is that only 'y' can and
    should be continuous. All other should be boolean/categoricalself.

    If you want to do a simple 1-d or 2-d barplot, you can do that with:

    - ast.bar() for 1-d
    - ast.bartwo() for 2-d

    This plot is only useful for the case where you have at least 4 dimensions
    you want to plot, and (again) all except 'y' are boolean/categorical.

    Inputs: 2 to 5
    Features: At least one continuous (or stepped) variable and rest
              can be categorical.

    1. USE
    ======
    ast.bars(data=patients,
              x='icu_days',
              y='insurance',
              hue='gender',
              col='religion',
              row='ethnicity')

    2. PARAMETERS
    =============
    2.1 INPUT PARAMETERS
    --------------------
    data :: pandas dataframe

    x :: x-axis data (categorical)

    y :: y-axis data (continuous or categorical)

    hue :: color highlight (categorical)

    row :: the comparison feature for side-by-side plots

    col :: the comparison feature for on top of each other plots

    --------------------
    2.2. PLOT PARAMETERS
    --------------------
    None

    ----------------------
    2.3. COMMON PARAMETERS
    ----------------------
    palette :: One of the astetik palettes:
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
                       y=y,
                       hue=hue,
                       row=row,
                       col=col,
                       col_wrap=col_wrap,
                       palette=palette,
                       size=4,
                       kind='bar')

    # SCALING AND LIMITS STARTS >>>
    if x_scale != 'linear' or y_scale != 'linear':
        _scaler(p, x_scale, y_scale)

    # FOOTER STARTS >>>
    _footer(p, x_label, y_label, save=save)
