import numpy as np

import matplotlib
matplotlib.use('Agg')  # this needs to be here exceptionslly
import matplotlib.pyplot as plt
from matplotlib.pyplot import rcParams

import seaborn as sns

from ..style.color_picker import color_picker, color_blind, _label_to_hex


def corr(data, title='',
         corr_method='spearman',
         annot=False,
         palette="RdYlGn",
         dpi=72,
         style='astetik'):

    '''CORRELATION HEATMAP

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
    # # # # # DATA PREP ENDS # # # # #

    # ASTETIK HEADER STARTS >>
    if style != 'astetik':
        plt.style.use(style)

    try:
        if y == None:
            n = 1
        else:
            n = 2
    except:
        n = data.shape[1]


    if palette == 'colorblind':
        palette = color_blind()
    else:
        try:

            palette = color_picker(palette=palette, n=n)
        except UnboundLocalError:
            palette = _label_to_hex(palette, n=n)

    sns.set_context("notebook", font_scale=1.2, rc={"lines.linewidth": 2})
    plt.figure(figsize=(12, 8))

    rcParams['font.family'] = 'Verdana'
    rcParams['figure.dpi'] = dpi
    # << ASTETIK HEADER ENDS

    # # # # # MAIN PLOT CODE STARTS # # # # # # #
    g = sns.heatmap(data, mask=mask, linewidths=2, cmap=palette, annot=annot)
    g.set_xticklabels(data, rotation=90, ha="right")
    g.set_yticklabels(data, rotation=0, ha="right")
    # # # # # MAIN PLOT CODE ENDS # # # # # # #

    # ASTETIK FOOTER STARTS >>
    plt.xlabel("", fontsize=15, labelpad=20, color="gray")
    plt.tick_params(axis='both', which='major', labelsize=16, pad=25)
    plt.tight_layout()
    sns.despine()
    #  << ASTETIK FOOTER ENDS
