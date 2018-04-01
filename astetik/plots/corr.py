import numpy as np

import matplotlib
matplotlib.use('Agg')  # this needs to be here exceptionslly
import matplotlib.pyplot as plt
from matplotlib.pyplot import rcParams

import seaborn as sns

from ..style.color_picker import color_picker, color_blind, _label_to_hex
from ..style.template import _header

def corr(data, title='',
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
    palette = _header(palette, style, y=n, dpi=dpi)  # NOTE: y exception
    # <<< HEADER ENDS

    # # # # # MAIN PLOT CODE STARTS # # # # # # #
    g = sns.heatmap(data, mask=mask, linewidths=2, cmap=palette, annot=annot)
    g.set_xticklabels(data, rotation=45, fontsize=12, ha="right")
    g.set_yticklabels(data, rotation=0, ha="right")
    # # # # # MAIN PLOT CODE ENDS # # # # # # #

    # ASTETIK FOOTER STARTS >>
    plt.xlabel("", fontsize=15, labelpad=20, color="gray")
    plt.tick_params(axis='both', which='major', labelsize=16, pad=12)
    plt.tight_layout()
    sns.despine()
    #  << ASTETIK FOOTER ENDS
