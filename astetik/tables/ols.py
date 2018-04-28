import pandas as pd

import warnings
warnings.filterwarnings("ignore")

import statsmodels.api as sm
from patsy import dmatrices
from IPython.core.display import display, HTML

def ols(data, iv, dv1, dv2, dv3, title='OLS Summary', table_title=''):

    '''ORDINARY LEAST SQUARES
    NOTE: You can input up to three depedent variables
    together with one independent variable.

    USE
    ===
    ast.ols(df, 'Survived','Age','Sex','Fare')

    PARAMETERS
    ----------
    data :: a dataframe
    iv :: an indepedent variable
    dv1, dv2, dv3 :: depedent variables
    title :: title to be used immediately above the table
    table_title :: main title, which is useful when 'title'
    parameter is used for description or table number etc.
    '''


    if len(table_title) == 0:

        table_title = "Independent Variable : " + str(iv)

    features = str(iv + ' ~ ' + dv1 + ' + ' + dv2 + ' + ' + dv3)
    y, X = dmatrices(features, data=data, return_type='dataframe')
    mod = sm.OLS(y, X)
    res = mod.fit()
    result = pd.DataFrame.transpose(pd.DataFrame([res.params,
                                                  res.tvalues,
                                                  res.pvalues,
                                                  res.bse]))
    result.columns = ['coef', 't', 'p_t', 'std_error']

    data = result.round(decimals=4)

    html = display(HTML("<style type=\"text/css\"> .tg {border-collapse:collapse;border-spacing:0;border:none;} .tg td{font-family:Arial, sans-serif;font-size:14px;padding:10px 5px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;} .tg th{font-family:Arial, sans-serif;font-size:14px;font-weight:normal;padding:10px 5px;border-style:solid;border-width:0px;overflow:hidden;word-break:normal;} .tg .tg-ejgj{font-family:Verdana, Geneva, sans-serif !important;;vertical-align:top} .tg .tg-anay{font-family:Verdana, Geneva, sans-serif !important;;text-align:right;vertical-align:top} .tg .tg-jua3{font-weight:bold;font-family:Verdana, Geneva, sans-serif !important;;text-align:right;vertical-align:top} h5{font-family:Verdana;} h4{font-family:Verdana;} hr{height: 3px; background-color: #333;} .hr2{height: 1px; background-color: #333;} </style> <table class=\"tg\" style=\"undefined;table-layout: fixed; width: 500px; border-style: hidden; border-collapse: collapse;\"> <colgroup> <col style=\"width: 150px\"> <col style=\"width: 120px\"> <col style=\"width: 120px\"> <col style=\"width: 120px\"> <col style=\"width: 120px\"> </colgroup> <h5>" + str(table_title) + "</h5> <h4><i>" + str(title) + "</i></h4> <hr align=\"left\", width=\"630\"> <tr> <th class=\"tg-ejgj\"></th> <th class=\"tg-anay\">" + str(data.keys()[0]) + "</th> <th class=\"tg-anay\">" + str(data.keys()[1]) + "</th> <th class=\"tg-anay\">" + str(data.keys()[2]) + "</th> <th class=\"tg-anay\">" + str(data.keys()[3]) + "</th> </tr> <tr> <td class=\"tg-ejgj\">" + str(data.index[0]) + "</td> <td class=\"tg-jua3\">" + str(data[data.keys()[0]][0]) + "</td> <td class=\"tg-jua3\">" + str(data[data.keys()[1]][0]) + "</td> <td class=\"tg-jua3\">" + str(data[data.keys()[2]][0]) + "</td> <td class=\"tg-jua3\">" + str(data[data.keys()[3]][0]) + "</td> </tr> <tr> <td class=\"tg-ejgj\">" + str(data.index[1]) + "</td> <td class=\"tg-jua3\">" + str(data[data.keys()[0]][1]) + "</td> <td class=\"tg-jua3\">" + str(data[data.keys()[1]][1]) + "</td> <td class=\"tg-jua3\">" + str(data[data.keys()[2]][1]) + "</td> <td class=\"tg-jua3\">" + str(data[data.keys()[3]][1]) + "</td> </tr> <tr> <td class=\"tg-ejgj\">" + str(data.index[2]) + "</td> <td class=\"tg-jua3\">" + str(data[data.keys()[0]][2]) + "</td> <td class=\"tg-jua3\">" + str(data[data.keys()[1]][2]) + "</td> <td class=\"tg-jua3\">" + str(data[data.keys()[2]][2]) + "</td> <td class=\"tg-jua3\">" + str(data[data.keys()[3]][2]) + "</td> </tr> <tr> <td class=\"tg-ejgj\">" + str(data.index[3]) + "</td> <td class=\"tg-jua3\">" + str(data[data.keys()[0]][3]) + "</td> <td class=\"tg-jua3\">" + str(data[data.keys()[1]][3]) + "</td> <td class=\"tg-jua3\">" + str(data[data.keys()[2]][3]) + "</td> <td class=\"tg-jua3\">" + str(data[data.keys()[3]][3]) + "</td> </tr>"))

    return html
