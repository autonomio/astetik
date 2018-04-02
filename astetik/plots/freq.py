import pandas as pd

# ASTETIK IMPORTS START >>
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.pyplot import rcParams

from ..style.titles import _titles
from ..style.color_picker import color_picker
from ..utils.utils import _highlight_color
from ..style.template import _header, _footer
from ..utils.utils import _limiter, _scaler
# << ASTETIK IMPORTS END


def freq(data,
         color='default',
         title='',
         sub_title='',
         x_label='',
         y_label='',
         order='desc',
         dropna=True,
         highlight_mode='!=',
         highlight_value=None,
         limit_values=30,
         dpi=72,
         save=False):

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

    color, highlight_color = color_picker(palette=color, n_colors=2)

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

    p = sns.barplot(x='x',
                    y='y',
                    data=data,
                    palette=colors,
                    order=order,
                    saturation=1,
                    ax=ax)

    ax.set_xticklabels(data['x'], rotation=45, ha="right")

    # START OF TITLES >>>
    _titles(title, sub_title=sub_title)
    # <<< END OF TITLES

    # FOOTER STARTS >>>
    _footer(p, x_label, y_label, save=save)
    # <<< FOOTER ENDS
