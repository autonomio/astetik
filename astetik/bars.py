import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from .color_picker import color_picker
from .utils import _highlight_color


def freq(data,
         color='default',
         title='',
         order='desc',
         dropna=True,
         highlight_mode='!=',
         highlight_value=25,
         limit_values=30):

    '''Frequency Bar
    Works best for max 30 unique values in the column, where
    values are either category labels or strings.

    PARAMETERS
    ----------
    data :: a series or a list with string or other values
    color :: one of the colors from the list below
    title :: the title of the plot
    order :: if the bars will be sorted 'desc', 'asc', or 'none'
    dropna :: if nan values will be dropped
    highlight_mode :: which boolean operator to use for highlights
    highlight_value :: the value for the highlight operation
    limit_values :: the maximum bars to show in the plot

    PALETTES
    --------
    'blue_to_red'
    'blue_to_green'
    'red_to_green'
    'green_to_red'
    'brown_to_green'
    'green_to_marine'

    '''

    color, highlight_color = color_picker(palette=color, n=2)

    # preps the data to frequency format
    data = pd.DataFrame(data)
    data.columns = ['value']
    data = data['value'].value_counts()
    data = data.reset_index()
    data.columns = ['x', 'y']

    # drops the NaN values
    if dropna == True:
        data = data.dropna()

    if limit_values != False:
        data = data.head(limit_values)

    # creates the right order
    if order == 'desc':
        order = data['x']
    elif order == 'asc':
        order = data['x'][::-1]
    else:
        order = None

    # highlights bars based on value
    colors = _highlight_color(data['y'],
                              color,
                              highlight_color,
                              highlight_mode,
                              highlight_value)

    # create the plot
    sns.set_context("notebook", font_scale=1.5, rc={"lines.linewidth": 0})
    sns.set_style('white')

    f, ax = plt.subplots(figsize=(18, 6))

    sns.barplot(x='x', y='y', data=data,
                palette=colors, order=order,
                saturation=1, ax=ax)

    plt.title(title, fontsize=18, y=1, color="gray")
    plt.xlabel("", fontsize=15, labelpad=30, color="gray")
    plt.ylabel("", fontsize=15, labelpad=30, color="gray")
    ax.tick_params(axis='both', which='major', pad=15)

    ax.set_xticklabels(data['x'], rotation=45, ha="right")
    sns.despine()
