"""Explicit datetime compatibility helpers with no hidden observation fabrication."""
from __future__ import annotations

from collections.abc import Sequence
from typing import NoReturn

import pandas as pd
from matplotlib import ticker
from matplotlib.axes import Axes
from matplotlib.dates import (
    DateFormatter,
    DayLocator,
    HourLocator,
    MinuteLocator,
    MonthLocator,
    SecondLocator,
)

from .._errors import AstetikError
from .._legacy import migration


def _time_freq(time_data: Sequence[pd.Timestamp] | pd.Series[pd.Timestamp] | pd.DatetimeIndex, divider1: float, divider2: float) -> int:
    if len(time_data) == 0 or divider1 <= 0 or divider2 <= 0:
        raise AstetikError('DATE_INTERVAL', 'Date ticks require observed timestamps and positive divisors.')
    return max(1, round((max(time_data) - min(time_data)).days / divider2 / divider1))


def date_handler(time_data: Sequence[pd.Timestamp] | pd.Series[pd.Timestamp] | pd.DatetimeIndex, ax: Axes, time_frame: str) -> None:
    """Apply an explicit observed-time formatter to the supplied axis only."""
    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=8))
    if time_frame == 'year':
        ax.xaxis.set_major_formatter(DateFormatter('%Y'))
    elif time_frame == 'month':
        ax.xaxis.set_major_locator(MonthLocator(bymonth=list(range(1, 13)), interval=_time_freq(time_data, 8, 30)))
        ax.xaxis.set_major_formatter(DateFormatter('%Y-%m'))
    elif time_frame == 'day':
        ax.xaxis.set_major_locator(DayLocator(bymonthday=list(range(1, 32)), interval=_time_freq(time_data, 8, 1)))
        ax.xaxis.set_major_formatter(DateFormatter('%Y-%m-%d'))
    elif time_frame == 'hour':
        ax.xaxis.set_major_locator(HourLocator(byhour=list(range(0, 24, 4))))
        ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    elif time_frame == 'minute':
        ax.xaxis.set_major_locator(MinuteLocator(byminute=list(range(0, 60)), interval=60))
        ax.xaxis.set_major_formatter(DateFormatter('%H:%M'))
    elif time_frame == 'second':
        ax.xaxis.set_major_locator(SecondLocator(bysecond=list(range(0, 60)), interval=10))
        ax.xaxis.set_major_formatter(DateFormatter('%M:%S'))
    else:
        raise AstetikError('DATE_FRAME', 'Choose year, month, day, hour, minute, or second.')


def _generate_datetime(*_args: object, **_kwargs: object) -> NoReturn:
    """Datetime identities must come from retained observations or explicit preparation."""
    migration('astetik.utils.datetime._generate_datetime',
              'Prepare timestamps explicitly with provenance; Astetik does not invent observation times.')

__all__ = ['_generate_datetime', '_time_freq', 'date_handler']
