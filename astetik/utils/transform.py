import math
import pandas as pd
import numpy as np


def groupby_func(data, func):

    if func == 'median':
        out = data.median()
    elif func == 'mean':
        out = data.mean()
    elif func == 'first':
        out = data.first()
    elif func == 'last':
        out = data.last()
    elif func == 'std':
        out = data.std()
    elif func == 'mode':
        out = data.mode()
    elif func == 'max':
        out = data.max()
    elif func == 'min':
        out = data.min()
    elif func == 'sum':
        out = data.sum()
    elif func == 'random':
        out = data.agg(np.random.choice)
    elif func == 'freq':
        out = data.agg(lambda x: x.value_counts().index[0])

    out = out.reset_index()

    return out


def rescaler(values, scale=1, to_int=False):

    '''MinMax Rescaler
    WHAT: rescales a set of values on to a fixed scale.
    HOW: max_rescale([10,6,2],1)
    INPUT: an array, list or Series
    OUTPUT: an array with rescaled values.
    '''

    multiplier = scale / np.array(values).max().astype(float)
    new_shape = np.array(values) * multiplier

    if to_int is True:

        l = []

        for value in new_shape:
            l.append(int(math.ceil(value)))

        return np.array(l)

    else:
        return new_shape


def intervals(data, x, dt_col, mode='first', freq=60):

    """BREAK TIMESERIES TO INTERVALS
    USE
    ===
    test = intervals(time_data, 'value','time_stamp', mode='min')

    PARAMETERS
    ----------
    data :: a dataframe with the values and a datetime column
    x :: the column with the value
    dt_col :: the column with the datetime values
    mode :: 'median', 'mean', 'mode', 'first', 'last', 'std', 'mode'
            'max', 'min', 'sum', 'random', 'freq'
    freq :: number of minutes per sample as int or a string 'quarter', 'half',
            'full' (days), 'week', 'month' (30 days), 'year'.

    """

    if type(freq) == type('s'):
        if freq == 'quarter':
            freq = 240
        elif freq == 'half':
            freq = 720
        elif freq == 'full':
            freq = 1440
        elif freq == 'week':
            freq = 10080
        elif freq == 'month':
            freq = 32400
        elif freq == 'year':
            freq = 525600

    freq = str(freq) + "Min"

    time_temp = data[[x, dt_col]].set_index(dt_col)
    time_temp = time_temp.groupby(pd.Grouper(freq=freq, label='right'))

    return groupby_func(data=time_temp, func=mode)


def equal_samples(data, col, sample_size):

    '''Resamples based on unique labels in a column.

    Results in a dataframe with equal number of rows
    per label in a given column.
    '''
    new_data = pd.DataFrame()

    for col_label in data[col].unique():
        sample = data[data[col] == col_label].sample(sample_size)
        new_data = new_data.append(sample)
    out = new_data

    return out


def mean_zero(data, retain=None):

    '''ZERO MEAN SCALER

    Takes in a dataframe or series, and rescales features
    so that mean for each feature becomes 0 and standard
    deviation becomes 1.

    USE
    ===
    mean_zero(df[['Age','Fare','Pclass']],retain='Pclass')

    PARAMETERS
    ==========
    data :: pandas dataframe or series object
    retain :: if some column should be excluded from rescaling

    '''
    # avoiding transformation of y, labels, etc

    data = data.copy(deep=True)

    try:
        col_list = list(data.columns)
    except AttributeError:
        col_list = list(pd.DataFrame(data.columns))

    if retain is not None:
        col_list.remove(retain)

    for col in col_list:

        # storing the temp values
        data_mean = data[col].mean(axis=0)
        data_std = data[col].std(axis=0)

        # transforming the data
        col_data = data[col] - data_mean
        data[col] = col_data / data_std

    return data


def _groupby(data, by, func):

    '''GROUP BY

    Takes in a dataframe and returns it in a grouped by format.

    PARAMETERS
    ----------
    data :: a pandas dataframe
    by :: the column by which the grouping is done
    func ::


    '''

    temp = data.groupby(by)

    return groupby_func(data=temp, func=func)


def _boolcols_to_cat(data, labels, other_label='NA'):

    '''CONVERT BOOLEAN COLS TO CATEGORICAL

    Returns a single categorical label seqeuence
    that is produced from 2 or more boolean columns.

    '''

    c = len(data)
    l = ['~'] * c

    for i in range(c):
        for label in labels:
            if data[label][i] == True:
                l[i] = label
                break

    l = [label.replace('~', other_label) for label in l]

    return l
