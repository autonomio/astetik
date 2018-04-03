import pandas as pd
from IPython.core.display import display, HTML

from ..utils.utils import table_prep


def table(data, title="Descriptive Stats", table_title=""):

    """PRETTY TABLE

    USE
    ===
    NOTE: you have to input a dataframe with exactly
    three columns of data!

    ast.table(df[['Age','Fare','Pclass']])

    PARAMETERS
    ----------
    data :: a dataframe with three columns of numeric data
    title :: title to be used immediately above the table
    table_title :: main title, which is useful when 'title'
    parameter is used for description or table number etc.

    """

    data = table_prep(data)

    display(HTML("<style type=\"text/css\"> .tg {border-collapse:collapse;border-spacing:0;border:none;} .tg td{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;} .tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;} .tg .tg-ejgj{font-family:Verdana, Geneva, sans-serif !important;;vertical-align:top} .tg .tg-anay{font-family:Verdana, Geneva, sans-serif !important;;text-align:right;vertical-align:top} .tg .tg-jua3{font-weight:bold;font-family:Verdana, Geneva, sans-serif !important;;text-align:right;vertical-align:top} h5{font-family:Verdana;} h4{font-family:Verdana;} hr{height: 3px; background-color: #333;} .hr2{height: 1px; background-color: #333;} </style> <table class=\"tg\" style=\"undefined;table-layout: fixed; width: 500px; border-style: hidden; border-collapse: collapse;\"> <colgroup> <col style=\"width: 150px\"> <col style=\"width: 120px\"> <col style=\"width: 120px\"> <col style=\"width: 120px\"> <col style=\"width: 120px\"> </colgroup> <h5>" + str(table_title) + "</h5> <h4><i>" + str(title) + "</i></h4> <hr align=\"left\", width=\"630\"> <tr> <th class=\"tg-ejgj\"></th> <th class=\"tg-anay\">median</th> <th class=\"tg-anay\">mean</th> <th class=\"tg-anay\">std</th> <th class=\"tg-anay\">total</th> </tr> <tr> <td class=\"tg-ejgj\">" + data.index[0] + "</td> <td class=\"tg-jua3\">" + str(data['median'][0]) + "</td> <td class=\"tg-jua3\">" + str(data['mean'][0]) + "</td> <td class=\"tg-jua3\">" + str(data['std'][0]) + "</td> <td class=\"tg-jua3\">" + str(data['sum'][0]) + "</td> </tr> <tr> <td class=\"tg-ejgj\">" + data.index[1] + "</td> <td class=\"tg-jua3\">" + str(data['median'][1]) + "</td> <td class=\"tg-jua3\">" + str(data['mean'][1]) + "</td> <td class=\"tg-jua3\">" + str(data['std'][1]) + "</td> <td class=\"tg-jua3\">" + str(data['sum'][1]) + "</td> </tr> <tr> <td class=\"tg-ejgj\">" + data.index[2] + "</td> <td class=\"tg-jua3\">" + str(data['median'][2]) + "</td> <td class=\"tg-jua3\">" + str(data['mean'][2]) + "</td> <td class=\"tg-jua3\">" + str(data['std'][2]) + "</td> <td class=\"tg-jua3\">" + str(data['sum'][2]) + "</td> </tr> </table> <hr align=\"left\", width=\"630\">"))
