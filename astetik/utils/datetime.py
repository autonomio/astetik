import pandas as pd

from matplotlib.dates import HourLocator, DayLocator, MonthLocator, YearLocator, MinuteLocator, SecondLocator
from matplotlib.dates import DateFormatter
from matplotlib import ticker


def _time_freq(time_data, divider1, divider2):

    out = (time_data.max() - time_data.min()).days
    print(out)
    out = round(out / divider2 / divider1)
    print(out)
    return out


def date_handler(time_data, ax, time_frame):

    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=8))

    if time_frame == 'year':
        ax.xaxis.set_major_formatter(DateFormatter('%Y'))

    elif time_frame == 'month':
        ax.xaxis.set_major_locator(MonthLocator(bymonth=range(1, 13), interval=_time_freq(time_data, 8, 30)))
        ax.xaxis.set_major_formatter(DateFormatter('%Y-%m'))

    elif time_frame == 'day':
        ax.xaxis.set_major_locator(DayLocator(bymonthday=range(1, 32), interval=_time_freq(time_data, 8, 1)))
        ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))

    elif time_frame == 'hour':
        ax.xaxis.set_major_locator(HourLocator(byhour=range(0, 24, 4)))
        ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))

    elif time_frame == 'minute':
        ax.xaxis.set_major_locator(MinuteLocator(byminute=range(0, 60, 1), interval=60))
        ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))

    elif time_frame == 'second':
        ax.xaxis.set_major_locator(SecondLocator(bysecond=range(0, 60, 1), interval=10))
        ax.xaxis.set_major_formatter(DateFormatter('%M:%S'))


def _generate_datetime(data, start, end, freq):

    '''DATETIME GENERATOR

    Takes in a series or dataframe, and based on the length creates
    a datetime series with a desired frequency. It's important to
    provide the start and end time precisely, together with the time
    unit, as otherwise there will be a mismatch of the valuesself.

    1.USE
    =====

    _generate_datetime(data, '1999-02-12','1999-03-05', 'hour')

    This example will generate datetimes with hourly frequency starting
    from midnight on the 12th of February (1999) up until midnight of
    5th of March.

    _generate_datetime(data, '1999-02-12-09:00','1999-03-05', 'hour')

    This example will do the same, but will start on 9:00 am instead.

    start :: the startime of the data (first observation timestamp)

    end :: the endtime of the data (last observation timestamp)

    freq :: This should be the frequency of observations in the dataset.
            Can be either pd.date_range frequency parameter, or:

            'year', 'month', 'day', 'hour', 'minute', 'second'
    '''

    if freq == 'year':
        freq = '365D'
    elif freq == 'month':
        freq = '30D'
    elif freq == 'day':
        freq = '1D'
    elif freq == 'hour':
        freq = '60Min'
    elif freq == 'minute':
        freq = '1Min'
    elif freq == 'second':
        freq = '1S'

    out = pd.Series(pd.date_range(start, end, freq=freq))

    if len(out) > len(data):
        print("Too many observation for the selected parameters.")
    elif len(out) < len(data):
        print("Not enough observations for the selected parameters.")

    return out
