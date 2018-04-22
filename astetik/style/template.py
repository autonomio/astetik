import time
from datetime import datetime

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.pyplot import rcParams
from ..style.color_picker import color_picker, color_blind, _label_to_hex
from ..utils.utils import _n_decider
from ..style.style import styles, default_colors
from ..style.random_colors import randomcolor


def _header(palette,
            style,
            n_colors,
            dpi,
            fig_width=None,
            fig_height=None):

    if palette == 'random':
        palette = randomcolor()

    elif style != 'astetik':
        plt.style.use(style)

    n = _n_decider(n_colors)

    try:
        if palette.startswith('colorblind'):
            palette = color_blind(palette)
    except AttributeError:
        palette = palette

    else:
        try:
            palette = color_picker(palette=palette, n_colors=n)
        except UnboundLocalError:
            palette = _label_to_hex(palette, n_colors=n)

    if fig_height != None and fig_width != None:
        plt.figure(figsize=(fig_width, fig_height))

    if style == 'astetik':
        rcParams['figure.facecolor'] = 'white'
        rcParams['axes.facecolor'] = 'white'
        rcParams['savefig.facecolor'] = 'white'

    style_dic = styles(dpi)
    for key in style_dic.keys():
        rcParams[key] = style_dic[key]

    return palette


def _footer(p,
            xlabel,
            ylabel,
            legend=False,
            n=None,
            save=False,
            tight=True,
            despine=True):

    default_color = default_colors()

    # LEGEND STARTS >>>
    if legend != False:
        plt.legend(loc=1, ncol=n)

    # HANDLE LABELS
    plt.xlabel(xlabel, color=default_color)
    plt.ylabel(ylabel, color=default_color)

    # DESPINE THE FIGURE
    if despine == True:
        try:
            p.spines['bottom'].set_color('black')
        except:
            pass
        sns.despine(left=True, right=True, top=True)

    # FORCE TIGHT LAYOUT
    if tight == True:
        plt.tight_layout()

    # SAVING THE PLOT
    if save != False:
        dt = datetime.now()
        time_stamp = time.strftime('%Y%m%d_%H%M%S_' + str(dt.microsecond))
        filename = "astetik_" + time_stamp + ".png"
        plt.savefig(filename, dpi=72)
