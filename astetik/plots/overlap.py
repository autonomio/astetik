import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from ..style.titles import _titles
from ..style.template import _header
from ..utils.transform import _groupby
from ..style.formats import _thousand_sep


def overlap(data,
            x,
            y,
            label_col,
            sort=None,
            limit=None,
            transform_func=False,
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

    '''OVERLAP BAR PLOT

    Useful for the cases where you have a categorical
    feature, and then you want to compare two overlapping
    continuous features (e.g. all days and rainy days) with
    each other per category. Each category will have its own
    bar, where the 'x' and 'y' features will be overlapping.

    Inputs: 3
    Features: 2 continuous and 1 categorical

    NOTE: 'y' should be a subset of 'x'.

    1. USE
    ======
    ast.overlap(data=patients,
                x='hospital_days',
                y='icu_days',
                label_col='insurance',
                sort=False,
                transform=True,
                transform_func='sum',
                palette='colorblind')

    2. PARAMETERS
    =============
    2.1 INPUT PARAMETERS
    --------------------
    data :: pandas dataframe

    x :: x-axis data (continuous)
    y :: x-axis overlap data (continuous)
    label_col :: the column with the label values

    --------------------
    2.2. PLOT PARAMETERS
    --------------------
    sort :: either True or False for ascending sort based on the
            x-axis data.

    limit :: limit the number of items to be shown

    transform_func :: If not False, the selected function such as
                      'mean' will be used to group by the label_col.
                      Available functions:
                        - 'median'
                        - 'mean'
                        - 'first'
                        - 'last',
                        - 'std',
                        - 'mode',
                        - 'max',
                        - 'min',
                        - 'sum',
                        - 'random'

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

    if transform_func != False:
        data = _groupby(data, label_col, transform_func)

    if sort != None:
        data = data.sort_values(x, ascending=sort)

    fig_height = len(data[label_col].unique()) * 0.6
    p, ax = plt.subplots(figsize=(6, fig_height))

    # HEADER STARTS >>>
    palette = _header(palette,
                      style,
                      n_colors=2,
                      dpi=dpi,
                      fig_height=None,
                      fig_width=None)
    # <<< HEADER ENDS

    # # # # PLOT STARTS # # # #

    sns.barplot(data=data,
                x=x,
                y=label_col,
                orient='h',
                color=palette[0])

    sns.barplot(data=data,
                x=y,
                y=label_col,
                orient='h',
                color=palette[1])

    # # # # PLOT ENDS # # # #
    if legend != False:
        x_patch = mpatches.Patch(color=palette[0], label=x)
        y_patch = mpatches.Patch(color=palette[1], label=y)
        ax.legend(handles=[x_patch, y_patch], ncol=1, loc="upper right", frameon=True)

    ax.set(ylabel=y_label, xlabel=x_label)
    sns.despine(bottom=True)
    ax.xaxis.set_major_locator(plt.MaxNLocator(5))

    _thousand_sep(p, ax)
    if len(title) + len(sub_title) < 0:
        _titles(title, sub_title=sub_title)
