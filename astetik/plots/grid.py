import seaborn as sns

from ..style.template import _header, _footer


def grid(data,
         x,
         y,
         col=None,
         hue=None,
         col_wrap=4,
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

    '''THE GRID

    The grid provides an overview of 4 features simultanously by
    drawing a grid of scatter plots.

    Inputs: 4
    Features: Ideally two continuous, and two categorical, but will
              also work with just one continuous and two categoricals.

    1. USE
    ======
    ast.grid(data=new_patients.head(1000),
              x='icu_stays',
              y='hospital_days',
              col='religion',
              palette='default',
              col_wrap=4);

    2. PARAMETERS
    =============
    2.1 INPUT PARAMETERS
    --------------------
    data :: pandas dataframe

    x :: x-axis data (continuous or categorical)

    y :: y-axis data (continuous)

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

    data = data.copy(deep=True)

    if hue != None:
        n_colors = len(data[hue].unique())
    else:
        n_colors = 1

    # HEADER STARTS >>>
    palette = _header(palette,
                      style,
                      n_colors=n_colors,
                      dpi=72,
                      fig_height=None,
                      fig_width=None)
    # <<< HEADER ENDS

    p = sns.factorplot(data=data,
                       x=x,
                       y=y,
                       col=col,
                       hue=hue,
                       palette=palette,
                       col_wrap=4,
                       kind='strip',
                       size=3)

    # FOOTER STARTS >>>
    _footer(p, x_label, y_label, save=save)

    sns.despine(bottom=True, left=True)
    p.set(xticklabels=[])
