import seaborn as sns
import matplotlib.pyplot as plt

from ..style.titles import _titles
from ..style.template import _header, _footer
from ..utils.transform import _groupby
from ..style.formats import _thousand_sep


def overlap(data,
            x,
            y,
            label_col,
            sort=None,
            transform=None,
            transform_func='sum',
            palette='default',
            style='astetik',
            dpi=72,
            title='',
            sub_title='',
            x_label='',
            y_label='',
            x_scale='linear',
            y_scale='linear',
            x_limit='auto',
            y_limit='auto',
            save=False):

    '''OVERLAP BAR PLOT

    Useful for the cases where you have a categorical
    feature, and then you want to compare two overlapping
    continuous features (e.g. all days and rainy days) with
    each other per category. Each category will have its own
    bar, where the 'x' and 'y' features will be overlapping.

    NOTE: 'y' should be a subset of 'x'.

    USE
    ===
    overlap(data=patients,
            x='hospital_days',
            y='icu_days',
            label_col='insurance',
            sort=False,
            transform=True,
            transform_func='sum',
            palette='colorblind')

    PARAMETERS
    ----------
    data :: a pandas data frame
    x :: a continuous variable
    y :: a countinuous variable that is a subset of 'x'
    label_col :: a variable with the labels for comparison
    sort :: data will be sorted either 'asc' or 'desc' or None
    transform :: None or True, if True then data will be grouped
                 according to the label_col parameter. Otherwise
                 the data should be in the right format already
    transform_func = the function to be applied for the groupby
                 in transform: median, mean, first, last, std,
                 mode, max, min, sum, random.
    '''

    if transform == True:
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
                label=x,
                color=palette[0])

    sns.barplot(data=data,
                x=y,
                y=label_col,
                label=y,
                color=palette[1])

    # # # # PLOT ENDS # # # #

    ax.legend(ncol=2, loc="lower right", frameon=True)
    ax.set(ylabel=y_label, xlabel=x_label)
    sns.despine(bottom=True)
    ax.xaxis.set_major_locator(plt.MaxNLocator(5))

    _thousand_sep(data[x], ax)

    # START OF TITLES >>>
    _titles(title, sub_title=sub_title)
    # <<< END OF TITLES
