import matplotlib.pyplot as plt
import seaborn as sns

from ..style.formats import _thousand_sep
from ..style.style import params
from ..style.titles import _titles
from ..style.template import _header, _footer
from ..utils.utils import _limiter, _scaler


def regs(data,
         x,
         y,
         marker='x',
         fit_reg=False,
         draw_scatter=True,
         logres=False,
         palette='default',
         style='astetik',
         dpi=72,
         title='',
         sub_title='',
         x_label='',
         y_label='',
         legend=True,
         x_scale='linear',
         y_scale='linear',
         x_limit=None,
         y_limit=None,
         outliers=False,
         save=False):

    '''REGRESSION SCATTER PLOT

    This can be used as a standard two variable scatter plot
    where both variables are continuous. If x is categorical,
    use scat() instead or swarm(), depending on your need.
    Here you can also choose logres as True in case one of your
    variables is a binary categorical.

    1. USE
    ======
    p = regs(data=df,
         x='Age',
         y='Fare',
         palette='default',
         style='astetik')

    2. PARAMETERS
    =============
    2.1 INPUT PARAMETERS
    --------------------
    data :: pandas dataframe

    x :: x-axis data

    y :: y-axis data

    --------------------
    2.2. PLOT PARAMETERS
    --------------------
    marker :: By default is 'x' but you can use any matplotlib supported

    fit_reg :: If the regression fit should be drawn

    draw_scatter :: if the scatter should be drawn

    logres :: for logistic regression when one feature is binary categorical.

    ----------------------
    2.3. COMMON PARAMETERS
    ----------------------
    palette :: One of the hand-crafted palettes:
                'default'
                'colorblind'
                'blue_to_red'
                'blue_to_green'
                'red_to_green'
                'green_to_red'
                'violet_to_blue'
                'brown_to_green'
                'green_to_marine'

                Or use any cmap, seaborn or matplotlib
                color or palette code, or hex value.

    style :: Use one of the three core styles:
                'astetik'     # white
                '538'         # grey
                'solarized'   # sepia

              Or alternatively use any matplotlib or seaborn
              style definition.

    dpi :: the resolution of the plot (int value)

    title :: the title of the plot (string value)

    sub_title :: a secondary title to be shown below the title

    x_label :: string value for x-axis label

    y_label :: string value for y-axis label

    x_scale :: 'linear' or 'log' or 'symlog'

    y_scale :: 'linear' or 'log' or 'symlog'

    x_limit :: int or list with two ints

    y_limit :: int or list with two ints

    outliers :: Remove outliers using either 'zscore' or 'iqr'

    '''

    # HEADER STARTS >>>
    palette = _header(palette, style, n_colors=1, dpi=dpi)  # NOTE: y exception
    # <<< HEADER ENDS

    # # # # # # PLOT CODE STARTS # # # # # #
    p, ax = plt.subplots(figsize=(params()['fig_width'],
                                  params()['fig_height']))

    sns.regplot(data=data,
                x=x, y=y,
                fit_reg=fit_reg,
                scatter=draw_scatter,
                color=palette[0],
                marker=marker,
                logistic=logres)
    # # # # # # PLOT CODE ENDS # # # # # #

    # SCALING AND LIMITS STARTS >>>
    if x_scale != 'linear' or y_scale != 'linear':
        _scaler(p, x_scale, y_scale)

    if x_limit != None or y_limit != None:
        _limiter(data=data, x=x, y=y, x_limit=x_limit, y_limit=y_limit)

    # START OF TITLES >>>
    _titles(title, sub_title=sub_title)

    _thousand_sep(p, ax, data, x, y)
    _footer(p=p, xlabel=x_label, ylabel=y_label, legend=False, n=1, save=save)

    ax.xaxis.set_major_locator(plt.MaxNLocator(5))
