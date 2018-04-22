import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from .exceptions import MissingParameter
from .transform import intervals


def _highlight_color(data,
                     color,
                     highlight_color,
                     highlight_mode,
                     highlight_value):

    '''Highlight Generator

    Takes as input colors and the highlight mode, and
    a highlight value, and then returns a color object
    to be used in a seaborn or matplotlib plot.

    '''
    try:
        if highlight_mode == '>=':
            colors = [highlight_color if _y >= highlight_value else color for _y in data]
        elif highlight_mode == '==':
            colors = [highlight_color if _y == highlight_value else color for _y in data]
        elif highlight_mode == '<=':
            colors = [highlight_color if _y <= highlight_value else color for _y in data]
        elif highlight_mode == '!=':
            colors = [highlight_color if _y != highlight_value else color for _y in data]
    except TypeError:
        raise MissingParameter("When highlight_mode is other than none you need to provide a highlight_value")
    return colors


def _sort_strings(data, column, sort):

    if sort == 'asc':
        asc = True
    elif sort == 'desc':
        asc = False
    data = data.sort_values(column, ascending=asc)

    return data


def table_prep(data, columns=''):

    """
      Data processor for table() function.

      You can call it separately as well and in
      return get a non-prettyfied summary table.

      Unless columns are defined, the three first
      columns are chosen by default.

      SYNTAX EXAMPLE:

      df['quality_score','influence_score','reach_score']

    """

    if data.shape[1] != 3:
        if len(columns) != 3:
            if data.shape[1] > 3:

                print("showing first three columns because no columns were \
                       specific / data had more than 3 columns")
                data = pd.DataFrame(data[data.columns[0:3]])

    if data.shape[1] < 3:

        print("You need at least 3 columns of data for this table")
        quit()

    if len(columns) == 3:
            data = data[columns]

    desc = pd.DataFrame({'sum': data.sum().astype('int'),
                         'median': data.median(),
                         'mean': data.mean(),
                         'std': data.std()})
    desc = desc.round(decimals=2)

    return desc


def _title_handling(p, data, title, sub_title, footnote, samplenote):

    '''TITLE HANDLER

    Takes care of the extremely painful task of positioning
    various titles and labels dynamically regardless of the plot.
    Or at least that's the idea...

    USE
    ===
    _title_handling(p, data, title, sub_title, samplenote, footnote)

    PARAMETERS
    ==========
    p :: the figure object
    data :: the data that is used in the plot
    title :: title string object or None
    sub_title :: sub_title string object or None
    footnote :: string object or None
    samplenote :: string object or None

    NOTE: At the moment works with one dimensional data.

    '''

    # handling title
    if title is not None:
        plt.title(title,
                  fontsize=28,
                  fontname='Verdana',
                  weight='bold',
                  verticalalignment='top',
                  horizontalalignment='left',
                  y=1.15,
                  x=.0,
                  color="grey")

    if sub_title is not None:
        plt.suptitle(sub_title,
                     fontsize=18,
                     fontname='Verdana',
                     verticalalignment='top',
                     horizontalalignment='left',
                     y=.9,
                     x=0.08,
                     color="grey")

    rel_bottom = 0 - (p.dataLim.bounds[3] / 7)

    if footnote is not None:
        plt.text(y=rel_bottom,
                 x=.2,
                 s="SOURCE: " + str(footnote),
                 color='grey',
                 verticalalignment='bottom',
                 horizontalalignment='left', )

    if samplenote is not None:
        plt.text(y=rel_bottom,
                 x=data.max(),
                 s="n = " + str(len(data)),
                 color='grey',
                 verticalalignment='bottom',
                 horizontalalignment='right')


def _scaler(p, x_scale=None, y_scale=None):

    if x_scale != None and x_scale != 'linear':
        p.set(xscale=x_scale)
    if y_scale != None and y_scale != 'linear':
        p.set(yscale=y_scale)


def _limiter(data=None, x=None, y=None, x_limit=None, y_limit=None):

    '''LIMITER (not for calling diretly )
    Handles x and y limits for all the plots. Can handle situations where
    there are more than one x as input.
    '''
    # SPECIAL CASE WITH MORE THAN ONE X
    if type(x) == type([]):
        max_list = []
        for i in range(len(x)):
            max_list.append(data[x[i]].max())
        x_max = max_list.index(max(max_list))

        min_list = []
        for i in range(len(x)):
            min_list.append(data[x[i]].min())
        x_min = min_list.index(min(min_list))

        x_max = data[x[x_max]].max()
        x_min = data[x[x_min]].min()

    # REGULAR CASE WITH JUST ONE X
    else:
        x_min = data[x].min()
        x_max = data[x].max()

    # HANDLING THE LIMITS STARTS
    if x_limit != None:
        # X-LIMS
        if x_limit != 'auto':
            if type(x_limit) == type(list):
                plt.xlim(x_limit[0], x_limit[1])
            else:
                plt.xlim(x_limit,)
        elif x_limit == 'auto':
            plt.xlim(x_min, x_max * 1.1)

    if y_limit != None:
        # SPECIAL CASES LIKE LINE PLOTS
        if y == '_R_E_S_':
            y_min = x_min
            y_max = x_max
        else:
            y_min = data[y].min()
            y_max = data[y].max()

        # Y-LIMS
        if y_limit != 'auto':
            if type(y_limit) == type(list):
                plt.ylim(y_limit[0], y_limit[1])
            else:
                plt.ylim(y_limit,)
        elif y_limit == 'auto':
            plt.ylim(y_min, y_max * 1.1)


def _n_decider(y):

    '''PRODUCE N-VALUE FOR _HEADER

    Takes in 'y' and based on the format
    returns the 'n' value that is used
    by the color picker.

    '''

    # no input value
    if type(y) == type(None):
        n = 10

    # equal to uniques
    elif type(y) == type(1):
        n = y

    # is a list or series
    elif type(y) == type(pd.Series()):
        n = 1

    elif type(y) == type([]) or type(y) == type(np.array(0)):
        n = len(y)

    elif type(y) == type(''):
        n = 1

    # equal to input value
    else:
        n = n

    return n


def _check_type(data):

    '''DTYPE CHECKER

    Checks if the first value in a dataset after
    dropping NAs is float or int.

    '''

    data_type = type(data.dropna().values[0])

    if np.issubdtype(data_type, int) == True:
        data_type = 'int'
    elif np.issubdtype(data_type, float) == True:
        data_type == 'float'

    return data_type


def multicol_transform(transform, data, x=None, y=None, func=None, freq=None):

    out = pd.DataFrame()

    if type(x) != type([]):
        x = [x]

    for col in x:
        if transform == 'interval':
            temp = intervals(data=data, x=col, dt_col=y, mode=func, freq=freq)
        out[col] = temp[col]
    out[y] = temp[y]

    return out


def factorplot_sizing(data, width=9, thickness=3, auto=False):

    '''COMPUTE SIZE AND ASPECT

    This is for the sole purpose of standardizing
    the factorplot sizing so that bar thickness
    is same regardless of the number of bars in the figure.
    '''

    if auto == True:
        items = len(data.value_counts())
    else:
        items = len(data)

    # compute the values
    value = items + 2.5
    size = value / thickness
    aspect = (width / size)

    return size, aspect
