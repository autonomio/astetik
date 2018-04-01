import pandas as pd

# ASTETIK IMPORTS START >>
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.pyplot import rcParams
from ..style.color_picker import color_picker, color_blind, _label_to_hex
from ..utils.utils import _highlight_color
# << ASTETIK IMPORTS END



def freq(data,
         color='default',
         title='',
         order='desc',
         dropna=True,
         highlight_mode='!=',
         highlight_value=None,
         limit_values=30,
         dpi=72):

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

    sns.set_context("notebook", font_scale=1.2, rc={"lines.linewidth": 2})
    f, ax = plt.subplots(figsize=(12, 8))

    rcParams['font.family'] = 'Verdana'
    rcParams['figure.dpi'] = dpi

    sns.barplot(x='x',
                y='y',
                data=data,
                palette=colors,
                order=order,
                saturation=1,
                ax=ax)

    plt.xlabel("", fontsize=15, labelpad=30, color="gray")
    plt.ylabel("", fontsize=15, labelpad=30, color="gray")

    ax.set_xticklabels(data['x'], rotation=45, ha="right")

    # ASTETIK FOOTER STARTS >>
    plt.xlabel("", fontsize=15, labelpad=20, color="gray")
    plt.tick_params(axis='both', which='major', labelsize=16, pad=25)
    plt.tight_layout()
    sns.despine()
    #  << ASTETIK FOOTER ENDS
