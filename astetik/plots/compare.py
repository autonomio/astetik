import seaborn as sns
import pandas as pd

from ..style.template import _header
from ..utils.transform import _groupby


def compare(data,
            x,
            y,
            label_col,
            sort=False,
            transform=None,
            transform_func='mean',
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
            y_limit='auto'):

    '''COMPARE PLOT

    This needs to have a single row per entity, for example a patient
    or a state and so forth. It will be best if the columns are
    normalized data, percentages, or something similar.

    USE
    ===

    ast.compare(data=patients,
            x='hospital_stays',
            y=['died_hospital','died_out'],
            label_col='religion',
            transform=True)

    PARAMETERS
    ----------
    data :: a pandas dataframe
    x :: the main feature
    cols :: a list with one or more columns
    label_col :: the label column


    '''

    if transform == True:
        plot_data = _groupby(data, label_col, transform_func)
    else:
        plot_data = data

    index_cols = y
    index_cols.insert(0, x)

    # HEADER STARTS >>>
    palette = _header(palette,
                      style,
                      n_colors=1,
                      dpi=dpi,
                      fig_height=None,
                      fig_width=None)
    # <<< HEADER ENDS

    # Make the PairGrid
    g = sns.PairGrid(plot_data.sort_values(x, ascending=sort),
                     x_vars=pd.Index(index_cols),
                     y_vars=[label_col],
                     size=10,
                     aspect=.25)

    # Draw a dot plot using the stripplot function
    g.map(sns.stripplot,
          size=10,
          orient="h",
          palette=palette,
          edgecolor="gray")

    g.set(xlabel="", ylabel="")
    titles = index_cols
    for ax, title in zip(g.axes.flat, titles):
        ax.set(title=title)
        ax.xaxis.grid(False)
        ax.yaxis.grid(True)

    sns.despine(left=True, bottom=True)
