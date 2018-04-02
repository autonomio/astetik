import warnings

import seaborn as sns
import matplotlib.pyplot as plt

from ..style.titles import _titles
from ..style.template import _header, _footer


def hist(data,
         x,
         palette='default',
         bins=True,
         title='',
         sub_title='',
         x_label='',
         y_label='',
         dropna=False,
         auto_xlim=True,
         kde=False,
         rug=False,
         vertical=False,
         style='astetik',
         dpi=72):

    '''Distribution Plot

    WHAT: creates a basic distribution plot out of 1-d data input

    USE: dist('score_161202', scores, dropna=True)

    INPUT: a pandas dataframe with at least one column of data

    OUTPUT: a distribution plot

    '''

    warnings.simplefilter("ignore")

    if bins == True:
        bins = int(len(data[x].unique()) / 10)

    if dropna is True:
        data = data[x].dropna()
    else:
        data = data[x]

    if bins is True:
        bins = len(data) / 10

    # HEADER STARTS >>>
    palette = _header(palette, style, n_colors=1, dpi=dpi)
    # <<< HEADER ENDS

    p = sns.distplot(data.dropna(),
                     bins=bins,
                     norm_hist=False,
                     color=palette,
                     kde=kde,
                     rug=rug,
                     vertical=vertical,
                     hist_kws=dict(alpha=1))

    if auto_xlim is True:
        p.set(xlim=(data.min(), None))
    if type(auto_xlim) is int:
        p.set(xlim=(auto_xlim, None))
    elif type(auto_xlim) is list:
        p.set(xlim=(auto_xlim[0], auto_xlim[1]))

    plt.tick_params(axis='both', which='major', pad=10)

    # show samplesize as subtitle
    _titles(title, sub_title)

    # FOOTER STARTS >>>
    _footer(p, x_label, y_label)
    # <<< FOOTER ENDS
