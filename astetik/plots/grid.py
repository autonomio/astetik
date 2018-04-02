import matplotlib.pyplot as plt
import seaborn as sns

from ..style.template import _header, _footer
from ..utils.transform import equal_samples
from ..utils.utils import _limiter, _scaler


def grid(data,
         x,
         y,
         col,
         even_observations=False,
         col_count=4,
         ascending=True,
         palette='default',
         style='astetik',
         title='',
         sub_title='',
         x_label='',
         y_label='',
         dpi=72,
         save=False):

    '''GRID PLOT
    This plot is especially useful for investigating
    2-axis of continuous data against multiple labels
    on one axis. For example, you might want to compare
    the hours of the day, and have side-by-side plots
    drawn out for each hour. Grid plot is that plot.

    USE
    ===
    grid(data=new_patients,
         x='icu_stays',
         y='icu_days',
         col='insurance',
         even_observations=200, # takes 200 observations per label
         palette='default',
         style='astetik')

    data :: a pandas dataframe
    x :: any continous value
    y :: any continuous value
    equal_samples :: an int value for number of observations
    for each sample (based on the 'col' categorical)
    col_count :: number of columns to plot by row
    ascending = sort ascending or not

    '''

    if even_observations != False:
        equal_samples(data, col, even_observations)

    data = data.sort_values(col, ascending=ascending)

    uniques = len(data[col].unique())

    if uniques is 1:
        print ("ERROR: column has only one unique item")

    if uniques < 4:
        col_count = uniques

    row_modulus = uniques % col_count
    row_count = uniques / col_count

    if row_modulus is not 0:
        row_count = row_count + 1

    row_count = int(row_count)
    col_count = int(col_count)

    # START OF HEADER >>>
    palette = _header(palette,
                      style,
                      n_colors=1,
                      dpi=dpi,
                      fig_width=None,
                      fig_height=None)  # EXCEPTION

    # <<< END OF HEADER
    fig, axs = plt.subplots(row_count,
                            col_count,
                            figsize=(16, row_count*4),
                            sharex=True,
                            sharey=True)

    axs = axs.ravel()

    for i in range(uniques):

        item = data[col].unique()[i]
        temp = data[data[col] == item]
        axs[i].scatter(temp[x],
                       temp[y],
                       c=palette,
                       s=40,
                       linewidths=1,
                       edgecolors='black',
                       alpha=1)
        axs[i].set_title(item)
        axs[i].tick_params(axis='both', which='major', pad=15)
        sns.despine(top=True, bottom=True, left=True, right=True)

    for i in range(uniques, row_count*col_count):
        fig.delaxes(axs[i])
