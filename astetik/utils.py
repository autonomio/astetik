import matplotlib.pyplot as plt

def _highlight_color(data, color, highlight_color, highlight_mode,  highlight_value):

    '''Highlight Generator

    Takes as input colors and the highlight mode, and
    a highlight value, and then returns a color object
    to be used in a seaborn or matplotlib plot.

    '''

    if highlight_mode == '>=':
        colors = [highlight_color if _y >= highlight_value else color for _y in data]
    elif highlight_mode == '==':
        colors = [highlight_color if _y == highlight_value else color for _y in data]
    elif highlight_mode == '<=':
        colors = [highlight_color if _y <= highlight_value else color for _y in data]
    elif highlight_mode == '!=':
        colors = [highlight_color if _y != highlight_value else color for _y in data]

    return colors


def _sort_strings(data, column, sort):

    if sort == 'asc':
        asc = True
    elif sort == 'desc':
        asc = False
    data = data.sort_values(column, ascending=asc)

    return data

import pandas as pd


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


def _scaler(p, x_scale, y_scale):

    p.set(xscale=x_scale)
    p.set(yscale=y_scale)


def _limiter(x, y, x_limit, y_limit):

    if x_limit != 'auto':
        if type(x_limit) == type(list):
            plt.xlim(x_limit[0], x_limit[1])
        else:
            plt.xlim(x_limit,)
    else:
        plt.ylim(x.min(), x.max() * 1.1)


    if y_limit != 'auto':
        if type(y_limit) == type(list):
            plt.ylim(y_limit[0], y_limit[1])
        else:
            plt.ylim(y_limit,)
    else:
        plt.ylim(y.min(), y.max() * 1.1)
