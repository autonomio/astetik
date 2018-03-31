import matplotlib.pyplot as plt
import warnings
from ..style.color_picker import _label_to_hex, color_blind, color_picker


def timeline(data, x,
             columns=None,
             palette='colorblind',
             style='fivethirtyeight',
             title='',
             sub_title='',
             footnote=None,
             samplenote=None,
             legend=True,
             log_x=False,
             log_y=False,
             fig_height=12,
             fig_width=8):

    '''TIMELINE PLOT

    Provides standardized high quality look and feel
    for several plot options:

    - 'line' : line plot (default)
    - 'hist' : histogram
    - 'box' : boxplot
    - 'kde' : KDE plot
    - 'area' : area plot
    - 'scatter' : scatter plot

    data :: a pandas dataframe
    x :: the column with the time value
    columns :: the columns with the data

    '''

    warnings.simplefilter("ignore")

    try:
        n = len(columns)
    except TypeError:
        n = 1

    plt.style.use(style)

    if palette == 'colorblind':
        palette = color_blind()
    else:
        try:

            palette = color_picker(palette=palette, n=n)
        except UnboundLocalError:
            palette = _label_to_hex(palette, n=n)

    # create the plot
    p = data.plot(x=x, y=columns,
                  figsize=(fig_height, fig_width),
                  color=palette,
                  legend=legend,
                  logx=log_x,
                  logy=log_y)

    # make some style adjustments
    p.tick_params(axis='both', which='major', labelsize=16)
    p.axhline(y=0, color='black', linewidth=1.3, alpha=.7)
    p.xaxis.label.set_visible(False)

    # setting the chart boundaries
    left = data[x].min()
    right = data[x].max()
    total_width = (right - left) * 0.025
    left = left - (total_width)
    right = right + (total_width)
    p.set_xlim(left=left, right=right)

    # creating the titles
    if title is not None:
        plt.title("\n" + title,
                  fontsize=28,
                  fontname='Verdana',
                  weight='bold',
                  verticalalignment='top',
                  horizontalalignment='left',
                  y=1.2,
                  x=.0,
                  color="grey")

    if sub_title is not None:
        plt.suptitle("\n" + sub_title,
                     fontsize=18,
                     fontname='Verdana',
                     verticalalignment='top',
                     horizontalalignment='left',
                     y=0.97,
                     x=0.08,
                     color="black")

    rel_bottom = data[columns].min().min() - (p.dataLim.bounds[3] / 5)

    if footnote is not None:
        plt.text(y=rel_bottom,
                 x=1970,
                 s="SOURCE: " + footnote,
                 color='grey',
                 verticalalignment='bottom',
                 horizontalalignment='left', )

    if samplenote is not None:
        plt.text(y=rel_bottom,
                 x=data[x].max(),
                 s="n = " + str(len(data)),
                 color='grey',
                 verticalalignment='bottom',
                 horizontalalignment='right')

    p.tick_params(axis='both', which='major', pad=10)
