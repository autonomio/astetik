import warnings

# ASTETIK IMPORTS START >>
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.pyplot import rcParams
from ..style.color_picker import color_picker, color_blind, _label_to_hex
from ..utils.utils import _title_handling
# << ASTETIK IMPORTS END


def hist(data,
         x,
         palette='default',
         bins=True,
         title=None,
         sub_title=None,
         footnote=None,
         samplenote=None,
         xlabel=None,
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

    # ASTETIK HEADER STARTS >>
    if style != 'astetik':
        plt.style.use(style)

    try:
        if y == None:
            n = 1
        else:
            n = 2
    except:
        try:
            n = data.shape[1]
        except IndexError:
            n = 1

    if palette == 'colorblind':
        palette = color_blind()
    else:
        try:

            palette = color_picker(palette=palette, n_colors=n)
        except UnboundLocalError:
            palette = _label_to_hex(palette, n_colors=n)

    sns.set_context("notebook", font_scale=1.2, rc={"lines.linewidth": 2})
    plt.figure(figsize=(12, 8))

    rcParams['font.family'] = 'Verdana'
    rcParams['figure.dpi'] = dpi
    # << ASTETIK HEADER ENDS

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
    _title_handling(p, data, title, sub_title, samplenote, footnote)

    # handling x_labels
    if xlabel is not None:
        x = xlabel
    plt.xlabel("", fontsize=15, labelpad=20, color="gray")

    plt.tick_params(axis='both', which='major', labelsize=16, pad=25)
    plt.axhline(y=0, color='black', linewidth=1.3, alpha=.7)
    plt.axvline(x=0, color='black', linewidth=1.3, alpha=.7)

    plt.tight_layout()

    sns.despine()
