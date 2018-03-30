import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.pyplot import rcParams


def corr(data, title='',
         corr_method='spearman',
         annot=False,
         palette="RdYlGn",
         dpi=72):

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

    corr = data.corr(method='spearman')
    mask = np.zeros_like(corr)
    mask[np.triu_indices_from(mask)] = True

    sns.set(style="white")
    sns.set_context("notebook", font_scale=1.5, rc={"lines.linewidth": 0.3})

    rcParams['figure.figsize'] = 20, 10
    rcParams['font.family'] = 'Verdana'
    rcParams['figure.dpi'] = dpi

    g = sns.heatmap(corr, mask=mask, linewidths=2, cmap=palette, annot=annot)
    g.set_xticklabels(data, rotation=90, ha="right")
    g.set_yticklabels(data, rotation=0, ha="right")
    plt.tick_params(axis='both', which='major', pad=15)
