import seaborn as sns
import matplotlib.pyplot as plt

from ..style.template import _header, _footer
from ..utils.utils import _limiter, _scaler


def vbar(data,
         x,
         y,
         highlight,
         color='red',
         sort=True,
         sort_ascending=False,
         title='',
         sub_title='',
         footnote='',
         samplenote='',
         x_label='',
         y_label=''):

    '''Vertical Bars with Highlight

    WHAT: A bar plot where one value is highlighted.

    USE: vertbar(df, 'max_score', 'country_code', 'uk')

    INPUT: A pandas dataframe where x is numeric and y is string labels

    OUTPUT: a vertical bar plot


    '''

    if sort is True:
        data = data.sort_values(x, ascending=sort_ascending)

    f, ax = plt.subplots(figsize=(5, 8))

    sns.set_style('white')
    sns.set_context("notebook", font_scale=1.3, rc={"lines.linewidth": 2})
    colors = [color if _y == highlight else 'grey' for _y in data[y]]

    g = sns.barplot(data[x], data[y], palette=colors, ax=ax, saturation=.3)

    # setting the xlim automatically
    xlim = data[x].min() - (data[x].min() * 0.2)
    g.set(xlim=(xlim, None))

    # FOOTER STARTS >>>
    _footer(p, x_label, y_label)
    # <<< FOOTER ENDS
