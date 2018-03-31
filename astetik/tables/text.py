from IPython.core.display import display, HTML

from ..utils.utils import _sort_strings


def text(data,
         column,
         sort=False,
         title='_column_name_',
         max_rows=20,
         contains=''):

    '''PRETTY TEXT PRINTER

    USE
    ---
    text(data=df, column='Name', contains='Miss')

    This will yield a printed out list of string
    items in the Name column where 'Miss' is present.

    PARAMETERS
    ----------
    data ::  a dataframe with the data
    column :: a column of values to print
    title :: the title to be printed before content
    max_rows :: max number of rows to be printed
    sort :: sorts 'asc' or 'desc' when not 'False'
    contains :: string to be matched (accepts regex)
    '''

    if title == '_column_name_':
        title = column

    if contains != '':
        data = data[data[column].str.contains(contains) == True]

    if sort != False:
        data = _sort_strings(data, column, sort)

    if max_rows >= len(data):
        max_rows = len(data)

    # reset the index to avoid issues
    data.reset_index(inplace=True)

    # display the content
    display(HTML("<h4>" + str(title) + "</h4>"))
    for row in range(max_rows):
        s = str(data[column][row])
        html = display(HTML("<font size=2 face=Verdana>" + s + "</font>"))

    return html
