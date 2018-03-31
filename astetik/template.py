import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.pyplot import rcParams
from .color_picker import color_picker, color_blind, _label_to_hex


def _header(palette, style, y, dpi):

    if style != 'astetik':
        plt.style.use(style)

    if y == None:
        n = 1
    else:
        n = 2

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

    return palette


def _footer(xlabel, ylabel):

    plt.xlabel(xlabel, fontsize=15, labelpad=20, color="gray")
    plt.ylabel(ylabel, fontsize=15, labelpad=20, color="gray")
    plt.tick_params(axis='both', which='major', labelsize=16, pad=25)
    plt.tight_layout()
    sns.despine()
