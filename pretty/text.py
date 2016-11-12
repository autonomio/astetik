def text(data,column,rows=6, sort_by='',contains=''):
    
    if sort_by != '':
        data = data.sort_values(sort_by)
    
    data = data[column]
    
    if len(data) < rows:
        rows = len(data)

    for i in range(rows):

        html = display(HTML("<font size=2 face=Helvetica>"+ str(pd.DataFrame(data[data.str.contains(contains)].value_counts()).index[i]) + "</font>"))

    return html