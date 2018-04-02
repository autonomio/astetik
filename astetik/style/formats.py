from matplotlib import ticker
from ..utils.utils import _check_type


def _thousand_sep(data, ax):

    '''Thousand Separator

    PARAMETERS
    ----------
    ax :: a single axis object
    '''
    if _check_type(data) == 'int':
        ax.get_xaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
