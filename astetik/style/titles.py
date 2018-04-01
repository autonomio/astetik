import matplotlib.pyplot as plt


def _titles(p, data, title, sub_title, footnote, samplenote):

    '''TITLE HANDLER

    Takes care of the extremely painful task of positioning
    various titles and labels dynamically regardless of the plot.
    Or at least that's the idea...

    USE
    ===
    _title_handling(p, data, title, sub_title, samplenote, footnote)

    PARAMETERS
    ==========
    p :: the figure object
    data :: the data that is used in the plot
    title :: title string object or None
    sub_title :: sub_title string object or None
    footnote :: string object or None
    samplenote :: string object or None

    NOTE: At the moment works with one dimensional data.

    '''

    # handling title
    if title is not None:
        plt.title(title,
                  fontsize=28,
                  fontname='Verdana',
                  weight='bold',
                  verticalalignment='top',
                  horizontalalignment='left',
                  y=1.15,
                  x=.0,
                  color="grey")

    if sub_title is not None:
        plt.suptitle(sub_title,
                     fontsize=18,
                     fontname='Verdana',
                     verticalalignment='top',
                     horizontalalignment='left',
                     y=0.913,
                     x=0.112,
                     color="grey")
