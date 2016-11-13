import pandas as pd

from IPython.core.display import display, HTML

def text(data,column,title='',rows=6, sort_by='',contains=''):
    
    if sort_by != '':
        data = data.sort_values(sort_by)
    
    data = data[column]
    
    if len(data) < rows:
        rows = len(data)

    display(HTML("<h3>"+ str(title) +"</h3>"))

    for i in range(rows):

        html = display(HTML("<font size=2 face=Helvetica>"+ str(pd.DataFrame(data[data.str.contains(contains)].value_counts()).index[i]) + "</font>"))

    return html