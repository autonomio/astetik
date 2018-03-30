import seaborn as sns


def color_picker(palette, center='light', n=10, show=False):

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
    'brown_to_green'
    'green_to_marine'
    '''

    if palette == 'default':
        palette = 'blue_to_red'

    if n < 3:
        n_input = n
        n = 6
    else:
        n_input = n

    if palette == 'blue_to_red':
        out = sns.color_palette("RdBu_r", n_colors=n)
    elif palette == 'blue_to_green':
        out = sns.color_palette("GnBu_d", n_colors=n)
    elif palette == 'red_to_green':
        out = sns.diverging_palette(16, 180, sep=5, center=center, n=n)
    elif palette == 'green_to_red':
        out = sns.diverging_palette(180, 16, sep=5, center=center, n=n)
    elif palette == 'violet_to_blue':
        out = sns.diverging_palette(1, 255, sep=5, center=center, n=n)
    elif palette == 'brown_to_green':
        out = sns.diverging_palette(50, 100, sep=5, center=center, n=n)
    elif palette == 'green_to_marine':
        out = sns.diverging_palette(100, 200, sep=5, center=center, n=n)

    if n_input == 1:
        out = out[0]

    elif n_input == 2:
        out = out[:2]

    if show == True:
        sns.palplot(out)

    return out
