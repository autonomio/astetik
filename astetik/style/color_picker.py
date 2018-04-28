import numpy as np
import seaborn as sns
from matplotlib.colorbar import cm


def color_picker(palette, center='light', n_colors=10, show=False):

    '''COLOR PICKER
    Provides access to several color palettes that will
    serve the purpose of most usecases with astetik plots.

    PARAMETERS
    ----------
    palette :: name of the palette (see list below)
    center :: if the center of the palette is 'light' or 'dark'
    n :: number of colors in the color
    show :: if the palette will be shown for visual reference

    PALETTES
    --------
    NOTE: all two color palettes will reflect the first color
    in the selected range. For example blue_to_red will have
    two shades of blue.

    'blue_to_red'
    'blue_to_green'
    'red_to_green'
    'green_to_red'
    'violet_to_blue'
    'brown_to_green'
    'green_to_marine'
    '''

    if palette == 'default':
        palette = 'blue_to_red'

    # handle the case where few colors only are used
    if n_colors <= 5:
        n_input = n_colors
        n_colors = 8  # this decides how dark colors will be
    else:
        n_input = n_colors

    if palette == 'blue_to_red':
        out = sns.color_palette("RdBu_r", n_colors=n_colors)
    elif palette == 'blue_to_green':
        out = sns.color_palette("GnBu_d", n_colors=n_colors)
    elif palette == 'red_to_green':
        out = sns.diverging_palette(16, 180, sep=5, center=center, n=n_colors)
    elif palette == 'green_to_red':
        out = sns.diverging_palette(180, 16, sep=5, center=center, n=n_colors)
    elif palette == 'violet_to_blue':
        out = sns.diverging_palette(1, 255, sep=5, center=center, n=n_colors)
    elif palette == 'brown_to_green':
        out = sns.diverging_palette(50, 100, sep=5, center=center, n=n_colors)
    elif palette == 'green_to_marine':
        out = sns.diverging_palette(100, 200, sep=5, center=center, n=n_colors)

    if n_input == 1:
        out = out[0]

    elif n_input == 2:
        out = out[:2]

    if show == True:
        sns.palplot(out)

    if np.ndim(out) == 1:
        out = [out]

    return out


def color_blind(mode='colorblind'):

    '''COLOR BLIND COLORS

    Provides a color palette that is colorblind friendly.
    '''

    if mode == 'colorblind':

        colors = [[0, 0, 0],
                  [255/255, 255/255, 109/255],
                  [255/255, 109/255, 182/255],
                  [0, 73/255, 73/255],
                  [0, 146/255, 146/255],
                  [255/255, 182/255, 119/255],
                  [73/255, 0, 146/255],
                  [0, 109/255, 219/255],
                  [182/255, 109/255, 255/255],
                  [109/255, 182/255, 255/255],
                  [182/255, 219/255, 255/255],
                  [146/255, 0, 0],
                  [146/255, 73/255, 0],
                  [219/255, 209/255, 0],
                  [36/255, 255/255, 36/255]]

    elif mode == 'colorblind6':
        colors = [[0, 0, 0],
                  [230/255, 159/255, 0],
                  [86/255, 180/255, 233/255],
                  [0, 158/255, 115/255],
                  [213/255, 94/255, 0],
                  [0, 114/255, 178/255]]

    elif mode == 'colorblind1':
        colors = [[222/255, 188/255, 146/255],
                  [251/255, 175/255, 148/255],
                  [131/255, 215/255, 142/255],
                  [225/255, 191/255, 147/255],
                  [250/255, 109/255, 81/255],
                  [101/255, 170/255, 53/255],
                  [204/255, 146/255, 68/255],
                  [221/255, 51/255, 48/255],
                  [95/255, 130/255, 24/255],
                  [149/255, 115/255, 32/255],
                  [164/255, 23/255, 30/255],
                  [61/255, 105/255, 22/255],
                  [119/255, 81/255, 24/255]]


    return colors


def cmaps(cmap):

    if cmap == 'paired':
        cmap = cm.Paired
    elif cmap == 'jet':
        cmap = cm.jet
    elif cmap == 'prism':
        cmap = cm.prism
    elif cmap == 'RdYlGn':
        cmap = cm.RdYlGn
    elif cmap == 'seismic':
        cmap = cm.seismic
    elif cmap == 'coolwarm':
        cmap = cm.coolwarm
    elif cmap == 'inferno':
        cmap = cm.inferno
    elif cmap == 'plasma':
        cmap = cm.plasma
    elif cmap == 'OrRd':
        cmap = cm.OrRd
    elif cmap == 'tab20c':
        cmap = cm.tab20c

    return cmap


def _label_to_hex(label, n_colors):

    hex = sns.color_palette(label, n_colors)
    return hex.as_hex()
