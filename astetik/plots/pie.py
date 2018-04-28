import matplotlib.pyplot as plt

from ..utils.exceptions import MissingLabel
from ..style.titles import _titles
from ..style.template import _header, _footer


def pie(data,
        x=None,
        labels=None,
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

    A classic pie chart. If dataframe is given as input, column sums
    will be automatically used as values. If you want to use a given
    row of data instead, indicate it using data.iloc[4] in the case of
    wanting to use the 5th row. If array is given as input, provide labels
    separately.

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
    NONE

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

    if x != None:

        # more than single column
        try:
            data[x].shape[1]
            labels = data[x].sum().index.values
            data = data[x].sum().values

        # single column
        except IndexError:
            labels = data[x].value_counts().index.values
            data = data[x].value_counts().values

    else:
        try:
            data.shape[1]
            labels = data.sum().index.values
            data = data.sum().values
        except IndexError or ValueError:
            pass

    n_colors = len(data)

    # HEADER STARTS >>>
    palette = _header(palette, style, n_colors, dpi)
    # <<< HEADER ENDS

    p, ax = plt.subplots(figsize=(8, 8))

    # # # # # # PLOT CODE STARTS # # # # # #
    p = plt.pie(x=data,
                colors=palette,
                autopct='%.1f%%',
                pctdistance=1.3,
                startangle=90)
    plt.axis('equal')
    # # # # # # PLOT CODE ENDS # # # # # #

    # LEGEND STARTS >>>

    try:
        if legend != False:
            plt.legend(p[0], labels, loc='center left', bbox_to_anchor=(1.1, 0.5))
    except TypeError:
        MissingLabel("Looks like you didn't provide 'label' parameter for legend")

    # <<< LEGEND ENDS

    # START OF TITLES >>>
    _titles(title, sub_title=sub_title)
    _footer(p, x_label, y_label, save=save)
