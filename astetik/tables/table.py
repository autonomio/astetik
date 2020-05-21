import pandas as pd
from IPython.core.display import display, HTML


def table(data,
          title="Descriptive Stats",
          sub_title="",
          table_width=630,
          indexcol_width=150,
          return_html=False):

    '''Displays a publication quality data table 
    with any number of columns and aspects. Works
    best for 6-7 or less columns datasets.

    data | DataFrame | a dataframe with three columns of numeric data
    title | str | the main title of the table
    sub_title | str | shown below the title
    table_width | int | the width of the table in pixels
    indexcol_width | int | the width of th index column in pixels.
    
    Width of the data columns is computed based on `table_width` and
    `indexcol_width` values. 

    '''
        
    html = '''
            <style type=\"text/css\">
            
            .tg {
                border-collapse:collapse;
                border-spacing:0;
                border:none;} 
            
            .tg td {
                font-family: Arial, sans-serif;
                font-size:14px;
                padding:10px 5px;
                border-style:solid;
                border-width:0px;
                overflow:hidden;
                word-break:normal;
                } 
                
            .tg th {
                font-family:Arial, sans-serif,
                sans-serif;
                font-size:14px;
                font-weight:normal;
                padding:10px 5px;
                border-style:solid;
                border-width:0px;
                overflow:hidden;
                word-break:normal;
                } 
                
            .tg .tg-index {
                font-family:Verdana, Geneva, sans-serif !important;
                text-align: left;
                padding-left: 10px;
                vertical-align:top
                } 
                
            .tg .tg-anay {
                    font-family:Verdana, Geneva, sans-serif !important;
                    text-align:right;
                    vertical-align:top
                    } 
                    
            .tg .tg-jua3 {
                    font-weight:bold;
                    font-family:Verdana, Geneva, sans-serif !important;
                    text-align:right;vertical-align:top
                    } 
            
            hr {
                height: 1px;
                background-color: #333;
                padding: 0px;
                margin: 0px;
            } 
            
            .hr2 {
                height: 2px !important;
                background-color: #333;
                }
                
            table {
                table-layout: fixed;
                width: 500px;
                border-style:hidden; 
                border-collapse: collapse;\"
                margin-top: 0px;
                padding-top: 0px;
            }
            
            .title {
                font-family: Arial, sans-serif;
                font-style: italic;
                font-size: 22px;
                font-weight: bold;
                padding-bottom: 0px;
                
                } 
                
            .sub_title {
                font-size: 18px;
                font-family: Arial, sans-serif;
                margin-top: 8px !important;
                padding-bottom: 12px;
                } 
                
            </style> 
            
            <table class=\"tg\"> 
            
            <colgroup> 
                <col style=\"width: _INDEXCOL_WIDTH_px\"> 
                <col style=\"width: _COL_WIDTH_px\"> 
                <col style=\"width: _COL_WIDTH_px\"> 
                <col style=\"width: _COL_WIDTH_px\"> 
                <col style=\"width: _COL_WIDTH_px\"> 
            </colgroup> 
            <p class='title'> _TABLE_TITLE_ </p> 
            <p class='sub_title'> _TABLE_SUBTITLE_ </p> 
            <hr align=\"left\", width=\"_TABLE_WIDTH_\"> 
        <tr>
            <th class=\"tg-index\"></th> 
        '''
    
    # add columns
    for col in data.columns:
        html += '<th class=\"tg-anay\">' + str(col) + '</th>' 

    for index in data.index:
        
        html += '</tr><tr><td class=\"tg-index\">' + str(index) + '</td>' 
        
        for col in data.columns:
            
            html += '<td class=\"tg-jua3\">' + f'{data.loc[index][col]:,}' + '</td>'
            
    html +='''    
        </tr> 
        </table> 
        <hr align=\"left\", width=\"_TABLE_WIDTH_\">
    
    '''
    
    col_width = int((table_width - indexcol_width) / len(data.columns))
    
    html = html.replace('_TABLE_TITLE_', title)
    html = html.replace('_TABLE_SUBTITLE_', sub_title)
    html = html.replace('_TABLE_WIDTH_', str(table_width))
    html = html.replace('_COL_WIDTH_', str(col_width))
    html = html.replace('_INDEXCOL_WIDTH_', str(indexcol_width))
    
    display(HTML(html))

    if return_html:
        return print(html)