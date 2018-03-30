import scipy.stats as sc
import pandas as pd


def outlier_series(data, iqr_x=3):

    '''Removes Outliers from a Series / List
    '''

    return data[data < sc.iqr(data) * iqr_x]


def outlier_col(data, col, iqr_x=3):

    '''Removes Outliers from a single column in a Dataframe
    '''

    return data[data[col] < sc.iqr(data[col]) * iqr_x]


def outlier_cols(data, cols, iqr_x=3):

    '''Removes Outliers from multiple columns in a Dataframe
    '''

    temp = pd.DataFrame(data)
    for col in cols:
        temp = temp[temp[col] < sc.iqr(temp[col]) * iqr_x]
    return temp
