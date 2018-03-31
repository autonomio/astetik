import seaborn as sns

#from .color_picker import color_picker, color_blind, _label_to_hex
from .template import _footer, _header
from .utils import _limiter, _scaler


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

    USE
    ===
    swarm(df,'Age','Fare', hue='Survived', x_limit=[50,80], y_limit=[10,20])

    PARAMETERS
    ----------
    data :: pandas dataframe
    x :: x-axis data
    y :: y-axis data
    hue :: color highlight (categorical or boolean)
    palette :: cmap, seaborn palette, matplotlib color code
    style :: any style from matplotlib or seaborn
    dpi :: the resolution of the plot
    x_label :: string value for x-axis label
    y_label :: string value for y-axis label
    x_scale :: 'linear' or 'log' or 'symlog'
    y_scale :: 'linear' or 'log' or 'symlog'
    x_limit :: int or list with two ints
    y_limit :: int or list with two ints

    '''

    # HEADER STARTS >>>
    palette = _header(palette, style, y, dpi)
    # <<< HEADER ENDS

    # # # # # # PLOT CODE STARTS # # # # # #
    p = sns.swarmplot(data=data,
                      x=x,
                      y=y,
                      hue=hue,
                      palette=palette,
                      linewidth=1,
                      size=8)
    # # # # # # PLOT CODE ENDS # # # # # #

    # SCALING AND LIMITS STARTS >>>
    _scaler(p, x_scale, y_scale)
    _limiter(data[x], data[y], x_limit, y_limit)
    # <<< SCALING AND LIMITS ENDS

    # FOOTER STARTS >>>
    _footer(x_label, y_label)
    # <<< FOOTER ENDS
