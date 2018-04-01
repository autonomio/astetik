import seaborn as sns

from ..style.template import _header, _footer
from ..utils.utils import _limiter, _scaler


def swarm(data,
          x,
          y,
          hue=None,
          # ASTETIK PARAMS START >>
          palette='default',
          style='astetik',
          dpi=72,
          x_label='',
          y_label='',
          x_scale='linear',
          y_scale='linear',
          x_limit='auto',
          y_limit='auto'):

    '''SWARM PLOT
    This is similar to scatter plot, in the sense that overlapping of observations
    is avoided (each sample will be seen as a dot) but groups events based on a
    categorical value (x).

    USE
    ===
    swarm(data=patients),
          x='insurance',       # categorical value
          y='hospital_bill',   # continuous value
          hue='expired',       # binary value
          palette='default',
          x_limit=None,
          y_limit=[25,70],
          y_scale='log')

    PARAMETERS
    ----------
    data :: pandas dataframe
    x :: x-axis data (categorical)
    y :: y-axis data (continuous)
    hue :: color highlight (categorical or boolean)
    palette :: cmap, seaborn palette, matplotlib color code
    style :: any style from matplotlib or seaborn
    dpi :: the resolution of the plot
    x_label :: string value for x-axis label
    y_label :: string value for y-axis label
    x_scale :: 'linear' or 'log' or 'symlog' (NOTE: not useful with this plot)
    y_scale :: 'linear' or 'log' or 'symlog'
    x_limit :: int or list with two ints
    y_limit :: int or list with two ints

    '''

    # PLOT SPECIFIC START >>>
    if hue != None:
        n = len(data[hue].unique())
    else:
        n = 1
    # <<< PLOT SPECIFIC ENDS

    # HEADER STARTS >>>
    palette = _header(palette, style, n_colors=n, dpi=dpi)  # NOTE: y exception
    # <<< HEADER ENDS

    # # # # # # PLOT CODE STARTS # # # # # #
    p = sns.swarmplot(data=data,
                      x=x,
                      y=y,
                      hue=hue,
                      palette=palette,
                      linewidth=0.5,
                      size=4)
    # # # # # # PLOT CODE ENDS # # # # # #

    # SCALING AND LIMITS STARTS >>>
    if x_scale != 'linear' or y_scale != 'linear':
        _scaler(p, x_scale, y_scale)

    if x_limit != None or y_limit != None:
        _limiter(data[x], data[y], x_limit, y_limit)
    # <<< SCALING AND LIMITS ENDS

    # FOOTER STARTS >>>
    _footer(x_label, y_label)
    # <<< FOOTER ENDS
