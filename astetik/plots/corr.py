import numpy as np
import seaborn as sns

from ..style.titles import _titles
from ..style.template import _header, _footer
from ..utils.utils import _limiter, _scaler


def corr(data,
         title='',
         sub_title='',
         x_label='',
         y_label='',
         corr_method='spearman',
         annot=False,
         palette="RdYlGn",
         dpi=72,
         style='astetik',
         save=False):

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
    # # # # # PREP STARTS # # # # #
    data = data.corr(method=corr_method)
    mask = np.zeros_like(data)
    mask[np.triu_indices_from(mask)] = True
    # # # # # PREP ENDS # # # # #

    # HEADER STARTS >>>
    palette = _header(palette, style, n_colors=10, dpi=dpi)  # NOTE: y exception
    # <<< HEADER ENDS

    # # # # # MAIN PLOT CODE STARTS # # # # # # #
    p = sns.heatmap(data, mask=mask, linewidths=2, cmap=palette, annot=annot)
    p.set_xticklabels(data, rotation=45)
    # # # # # MAIN PLOT CODE ENDS # # # # # # #

    # START OF TITLES >>>
    _titles(title, sub_title=sub_title)
    # <<< END OF TITLES

    # FOOTER STARTS >>>
    _footer(p, x_label, y_label, save=save)
    # <<< FOOTER ENDS
