import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.pyplot import rcParams
from ..style.color_picker import color_picker, color_blind, _label_to_hex
from ..utils.utils import _n_decider


def _header(palette,
            style,
            n_colors,
            dpi,
            fig_width=12,
            fig_height=8):

    if style != 'astetik':
        plt.style.use(style)

    n = _n_decider(n_colors)

    if palette == 'colorblind':
        palette = color_blind()
    else:
        try:
            palette = color_picker(palette=palette, n_colors=n)
        except UnboundLocalError:
            palette = _label_to_hex(palette, n_colors=n)

    sns.set_context("notebook")

    if fig_height != None and fig_width != None:
        plt.figure(figsize=(fig_width, fig_height))

    if style == 'astetik':
        rcParams['figure.facecolor'] = 'white'
        rcParams['axes.facecolor'] = 'white'
        rcParams['savefig.facecolor'] = 'white'

    rcParams['font.size'] = 14
    rcParams['font.family'] = 'Verdana'
    rcParams['figure.dpi'] = dpi
    rcParams['lines.linewidth'] = 2


    return palette


def _footer(xlabel, ylabel):

    plt.xlabel(xlabel, fontsize=15, labelpad=20, color="gray")
    plt.ylabel(ylabel, fontsize=15, labelpad=20, color="gray")
    plt.tick_params(axis='both', which='major', labelsize=16, pad=25)
    plt.tight_layout()
    sns.despine()
