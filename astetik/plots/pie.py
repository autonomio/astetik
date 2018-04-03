import pandas as pd
import matplotlib.pyplot as plt

from ..style.titles import _titles
from ..style.template import _header, _footer


def pie(data,
        x,
        quantile_cut=None,
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

    '''PIE PLOT

    A classic pie chart.

    Inputs: 1
    Features: 1 categorical or continuous

    1. USE
    ======
    ast.pie(data=patients, x='age', palette='Blues')

    2. PARAMETERS
    =============
    2.1 INPUT PARAMETERS
    --------------------
    data :: pandas dataframe

    x :: x-axis data (categorical or continuous)

    --------------------
    2.2. PLOT PARAMETERS
    --------------------
    quantile_cut :: An int value for the number of buckets data will be cut.
                    This will always yield an evenly split pie, and is useful
                    for showing the IQR ranges for a given feature.

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
    if quantile_cut != None:
        data = data.copy(deep=True)
        data[x] = pd.qcut(data[x], quantile_cut)
        n_colors = len(data[x].unique())
    else:
        n_colors = len(x)
    data = data.sort_values(x)
    labels = data[x].value_counts().index.values
    data = data[x].value_counts().values
    # << PLOT SPECIFIC END

    # HEADER STARTS >>>
    palette = _header(palette, style, n_colors, dpi)
    # <<< HEADER ENDS

    # # # # # # PLOT CODE STARTS # # # # # #
    p = plt.pie(x=data,
                colors=palette,
                autopct='%.1f%%',
                pctdistance=1.3,
                startangle=90)
    plt.axis('equal')
    # # # # # # PLOT CODE ENDS # # # # # #

    # LEGEND STARTS >>>
    if legend != False:
        plt.legend(p[0], labels, loc='center left', bbox_to_anchor=(1.1, 0.5))
    # <<< LEGEND ENDS

    # START OF TITLES >>>
    _titles(title, sub_title=sub_title)
    _footer(p, x_label, y_label, save=save)
