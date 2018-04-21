import matplotlib.pyplot as plt


def _titles(title,
            sub_title,
            location='left',
            fontname='Verdana',
            fontsize='24'):

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
    if len(title) + len(sub_title) > 0:
        title = title.replace(' ', '\,')

        plt.title(r"$\bf{" + title + "}$" + '\n' + sub_title,
                  loc=location,
                  fontsize=fontsize,
                  fontname=fontname,
                  weight='normal',
                  y=1.03,
                  color="grey");
