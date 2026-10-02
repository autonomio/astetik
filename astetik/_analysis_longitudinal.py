"""Observed trajectories retain record identities and never imply trend inference."""
from __future__ import annotations

import pandas as pd

from ._analysis_policy import fail
from ._analysis_types import AnalysisMethods, AnalysisResult
from ._json import json_object
from ._spec_types import PlotSpec


def longitudinal(data: pd.DataFrame, spec: PlotSpec, x: str, y: str, methods: AnalysisMethods) -> AnalysisResult:
    hue = spec.get('hue')
    grouping = [hue] if hue else []
    if data.duplicated([*grouping, x]).any():
        fail('TIME_DUPLICATE', 'Observed trajectories require one value per time and series; declare a separate preparation for aggregation.')
    methods.update(order='Ascending time within each declared series', interpolation='Straight segments between observations', inference='None')
    fields = list(dict.fromkeys([*spec['key'], *grouping, x, y]))
    rows = data[fields].sort_values([*grouping, x], kind='stable').to_dict('records')
    summary = [json_object({key: value.isoformat() if isinstance(value, (pd.Timestamp, pd.Timedelta)) else value
                            for key, value in row.items()}) for row in rows]
    return {'summary': summary, 'methods': methods,
            'caption': f'Observed trajectory; {len(data)} observations. Straight segments connect observations; no trend inference.'}
