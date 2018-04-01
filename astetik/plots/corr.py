import numpy as np

import matplotlib
matplotlib.use('Agg')  # this needs to be here exceptionslly
import matplotlib.pyplot as plt
from matplotlib.pyplot import rcParams

import seaborn as sns

from ..style.template import _header, _footer
from ..utils.utils import _limiter, _scaler


def corr(data,
         title='',
         sub_title='',
         footnote='',
         samplenote='',
         x_label='',
         y_label='',
         corr_method='spearman',
         annot=False,
         palette="RdYlGn",
         dpi=72,
         style='astetik'):

    '''CORRELATION HEATMAP

    This is best used with less than 10 variables in the datasetself.
    For best results, split the analysis to several parts.

    PARAMETERS
    ----------
    data :: a dataframe
    title :: title for the plot
    dpi :: the resolution for the plot
    corr_method ::

    'pearson' : standard correlation coefficient
    'kendall' : Kendall Tau correlation coefficient
    'spearman' : Spearman rank correlation

    annot :: show the annotation (values) on each cell

    '''
    # # # # # DATA PREP STARTS # # # # #
    data = data.corr(method='spearman')
    mask = np.zeros_like(data)
    mask[np.triu_indices_from(mask)] = True
    n = 14
    # # # # # DATA PREP ENDS # # # # #

    # HEADER STARTS >>>
    palette = _header(palette, style, n_colors=n, dpi=dpi)  # NOTE: y exception
    # <<< HEADER ENDS

    # # # # # MAIN PLOT CODE STARTS # # # # # # #
    p = sns.heatmap(data, mask=mask, linewidths=2, cmap=palette, annot=annot)
    p.set_xticklabels(data, rotation=45)
    # FOOTER STARTS >>>
    _footer(p, x_label, y_label)
    # <<< FOOTER ENDS
