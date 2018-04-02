import seaborn as sns

from ..style.titles import _titles
from ..style.template import _header, _footer
from ..utils.utils import _limiter, _scaler
from ..style.sizer import _sizer


def scat(data,
         x,
         y,
         hue=None,
         size=None,
         # ASTETIK PARAMS START >>
         palette='default',
         style='astetik',
         dpi=72,
         title='',
         sub_title='',
         x_label='',
         y_label='',
         x_scale='linear',
         y_scale='linear',
         x_limit='auto',
         y_limit='auto'):

    '''SCATTER PLOT

    Observations may overlap, and sizing is possible. Both x and y should
    be continuous variables. If you want to use categorical on x-axis, use
    ast.swarm() instead.

    USE
    ===
    p = scat(data=df,
         x='Age',
         y='Fare',
         hue='Survived',
         size='Rand',
         palette='default',
         style='astetik')

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

    # PLOT SPECIFIC START >>>
    if hue != None:
        n = len(data[hue].unique())
    else:
        n = 1

    if size == None:
        size = 8
    else:
        size = _sizer(data[size])
    # <<< PLOT SPECIFIC ENDS

    # HEADER STARTS >>>
    palette = _header(palette, style, n_colors=n, dpi=dpi)  # NOTE: y exception
    # <<< HEADER ENDS

    # # # # # # PLOT CODE STARTS # # # # # #
    p = sns.stripplot(data=data,
                      x=x,
                      y=y,
                      hue=hue,
                      palette=palette,
                      linewidth=1,
                      size=size)
    # # # # # # PLOT CODE ENDS # # # # # #

    # SCALING AND LIMITS STARTS >>>
    if x_scale != 'linear' or y_scale != 'linear':
        _scaler(p, x_scale, y_scale)

    if x_limit != None or y_limit != None:
        _limiter(data[x], data[y], x_limit, y_limit)
    # <<< SCALING AND LIMITS ENDS

    # START OF TITLES >>>
    _titles(title, sub_title=sub_title)
    # <<< END OF TITLES

    # FOOTER STARTS >>>
    _footer(p, x_label, y_label)
    # <<< FOOTER ENDS

    # SPECIAL CASE (to reset the x-labels)
    p.set(xscale='linear')
    # SPECIAL CASE ENDS
