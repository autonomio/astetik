import scipy.stats as sc


def outliers(data, col, mode='zscore', threshold=3):

    '''OUTLIER FILTERING

    NOTE: this will automatically also drop nans from the dataset.

    '''

    # avoid destruction
    data = data.copy(deep=True)
    data = data[data[col].isna() == False]

    if mode == 'zscore':
        data['zscore'] = sc.zscore(data[col].astype(float))
        data = data[data.zscore < 3][data.zscore > -3].drop('zscore', axis=1)

    if mode == 'iqr':
        data = data[data[col] < sc.iqr(data[col]) * threshold]

    return data
