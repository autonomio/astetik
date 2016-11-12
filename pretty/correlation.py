import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

from matplotlib.pyplot import rcParamas


def correlation(data,title=''):
    
    corr = data.corr(method='spearman')
    mask = np.zeros_like(corr)
    mask[np.triu_indices_from(mask)] = True

    rcParams['figure.figsize'] = 25, 12
    rcParams['font.size'] = 20
    rcParams['font.weight'] = 'bold'
    rcParams['font.family'] = 'Verdana'
    rcParams['figure.dpi'] = 300

    g = sns.heatmap(corr, mask=mask, linewidths=1, cmap="RdYlGn", annot=False)
    g.set_xticklabels(data,rotation=25,ha="right");