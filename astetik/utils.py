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
