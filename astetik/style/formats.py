import numpy as np

from matplotlib import ticker


def _thousand_sep(p, ax, y_sep=True, x_sep=True):

    '''Thousand Separator

    PARAMETERS
    ----------
    ax :: a single axis object
    '''
    # FOR MATPLOTLIB PLOTS

    x = ax.get_xlim()[1]
    y = ax.get_ylim()[1]

    if x_sep == True:
        if x > 10:
            ax.get_xaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')));
    if y_sep == True:
        if y > 10:
            ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')));
