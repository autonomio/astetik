# Scientific protocols

Three research kinds compute a declared method before rendering: `comparison`, `association`, and `longitudinal`. This surface owns numerical method and interval rules; [the guide](../Guides/Research-Protocols.md) owns the study workflow.

## Declaration and shared requirements

Use `astetik.render()` or `astetik.plot()` with `analysis` containing an explicit `method` and nonempty `observation_unit`. Declare observation keys. Each protocol requires one x column and one y column.

Protocol `row`/`col` facets fail. Run a separately declared protocol for each subgroup instead of duplicating pooled estimates across panels. Unused analysis fields fail, even when another method would accept them. Declaring an observation unit records an assumption; it does not establish independence.

## Two-group comparison

| Setting | Contract |
| --- | --- |
| Kind | `comparison` |
| Methods | `welch`, `paired_t` |
| `groups` | Exactly two ordered groups, matching the input's full group set |
| Contrast | Second group minus first group |
| `confidence` | Optional, defaults to `0.95`; finite and strictly between 0 and 1 |
| Minimum sample | At least two observations per group; paired inference also needs at least two complete pairs |
| `subject` | Required only for `paired_t` |

Group summaries contain n, mean, sample standard deviation, and Student t intervals for group means. Welch's contrast interval uses its standard error and Welch-Satterthwaite degrees of freedom; paired inference uses exact subject differences and paired Student t degrees of freedom. Zero sampling variance fails.

Paired data must contain one observation per subject and group, with both groups represented for every subject. No incomplete pairs are silently dropped. Additional comparison hue grouping is unsupported.

The analysis includes `summary`, `contrast`, `methods`, and a computed `caption`. Contrast fields include estimate, lower/upper bounds, confidence, statistic, degrees of freedom, p value, and n.

## Association

| Setting | Contract |
| --- | --- |
| Kind | `association` |
| Methods | `pearson`, `spearman` |
| Minimum sample | Four independent observations |
| Constant variables | Rejected as undefined correlation |
| Pearson interval | Fisher transformation; optional `confidence`, default `0.95` |
| Spearman interval | Not estimated; declaring `confidence` fails |
| Spearman p value | Asymptotic approximation |

Analysis includes a coefficient summary, statistics, methods, and a bound caption. A coefficient does not establish causation. Small-sample precision and independence remain study-design responsibilities.

## Observed trajectory

`longitudinal` accepts `method="observed"`. It orders observations by ascending time within each declared hue series and connects them with straight segments. Duplicate times within a series fail; aggregation belongs in preparation. Native datetime time columns are supported.

`confidence`, groups, subject declarations, altered draw style, and disabled sorting are unused or contradictory protocol choices and fail. This method computes no trend, repeated-measures inference, or confidence interval.

## Minimum method declarations

These are schema examples, not supplied study observations:

```json
{
  "method": "welch",
  "groups": ["control", "treatment"],
  "observation_unit": "independently sampled specimen",
  "confidence": 0.95
}
```

```json
{
  "method": "observed",
  "observation_unit": "one recorded visit in a declared series"
}
```

## Failures and authority

Methods and unused-field checks raise structured codes including `METHOD_REQUIRED`, `ANALYSIS_FIELDS`, `ANALYSIS_FACETS`, `PAIRING_INCOMPLETE`, `SAMPLE_SIZE`, `DEGENERATE_ANALYSIS`, and `TIME_DUPLICATE`. These checks validate the declared calculation, not universal scientific validity.

Authority: [analysis implementation](../../astetik/_analysis.py) and [protocol tests](../../tests/test_api.py).

Next: [study workflow](../Guides/Research-Protocols.md), then [evidence publication](../Guides/Evidence-Bundle.md).
