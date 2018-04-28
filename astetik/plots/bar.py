import seaborn as sns
import pandas as pd

from ..style.template import _header, _footer
from ..utils.utils import _scaler
from ..utils.utils import factorplot_sizing
from ..style.titles import _titles


def bar(data,
        x=None,
        y=None,
        sort=None,
        multi_color=False,
        group_duplicate=True,
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

    A 1-dimensional bar graph for the case where there is a single
    value per label. Accepts either dataframe or series. If series,
    then labels will come from index.

    Inputs: 1 (Series), 2(DataFrame)

    1. USE
    ======
    ast.bar1d(data=patients,
              x='icu_days',
              y='insurance')

    2. PARAMETERS
    =============
    2.1 INPUT PARAMETERS
    --------------------
    data :: pandas dataframe

    x :: x-axis data (single value per label)

    y :: y-axis data (labels)

    --------------------
    2.2. PLOT PARAMETERS
    --------------------
    sort :: If True, values will be sorted ascending, if False descending.

    multi_color :: If True, label values will be used for hue.

    group_duplicate :: If set to False, duplicate values will not be merged.

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
    # convert series to dataframe
    if x == None and y == None:
        data = data.copy(deep=True)
        data = pd.DataFrame(data)
        data.reset_index(inplace=True)
        data.columns = ['x', 'y']
        x = 'y'
        y = 'x'

    size, aspect = factorplot_sizing(data[x])

    # merge duplicate items
    if group_duplicate == True:
        data = data.groupby(y).sum().reset_index()
        data.columns = [y, x]

    if sort != None:
        data = data.sort_values(x, ascending=sort)

    if multi_color == True:
        n_colors = len(data[x].unique())
    else:
        n_colors = 1

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
                       palette=palette,
                       aspect=aspect,
                       size=size,
                       kind='bar')

    # SCALING AND LIMITS STARTS >>>
    if x_scale != 'linear' or y_scale != 'linear':
        _scaler(p, x_scale, y_scale)

    # FOOTER STARTS >>>
    _titles(title, sub_title=sub_title)
    _footer(p, x_label, y_label, save=save)

    if data[x].min() < 0:
        sns.despine(left=True)
