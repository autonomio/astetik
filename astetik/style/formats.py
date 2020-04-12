def _thousand_sep(p, ax, data, x, y):

    '''Handles thousand separatos for tick labels.

    p | fig object | matplotlib figure object
    ax | axis object | a single axis object
    data | df | pandas dataframe with data
    x | str | column name for x
    y | str | column name for y

    NOTE: If x is list (e.g. hist or line) then x should be x[0].
          For example _thousand_sep(p, ax, data, x[0], y)

    '''

    from matplotlib import ticker

    # only apply if data is int
    if x != None:
        if isinstance(data[x].iloc[0], int):
            ax.get_xaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')));

    # only apply if data is int
    if y != None:
        if isinstance(data[y].iloc[0], int):
            ax.get_yaxis().set_major_formatter(ticker.FuncFormatter(lambda x, p: format(int(x), ',')));
