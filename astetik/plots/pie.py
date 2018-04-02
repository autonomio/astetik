import pandas as pd
import matplotlib.pyplot as plt

from ..style.titles import _titles
from ..style.template import _header, _footer


def pie(data,
        x,
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
        y_limit='auto',
        quantile_cut=None,
        save=False):

    # PLOT SPECIFIC START >>>
    if quantile_cut != None:
        data = data.copy(deep=True)
        data[x] = pd.qcut(data[x], quantile_cut)
        n_colors = len(data[x].unique())
    else:
        n_colors = len(x)
    data = data.sort_values(x)
    labels = data[x].value_counts().index.values
    data = data[x].value_counts().values
    # << PLOT SPECIFIC END

    # HEADER STARTS >>>
    palette = _header(palette, style, n_colors, dpi)
    # <<< HEADER ENDS

    # # # # # # PLOT CODE STARTS # # # # # #
    p = plt.pie(x=data,
                colors=palette,
                autopct='%.1f%%',
                pctdistance=1.3,
                startangle=90)
    plt.axis('equal')
    # # # # # # PLOT CODE ENDS # # # # # #

    # LEGEND STARTS >>>
    plt.legend(p[0], labels, loc='center left', bbox_to_anchor=(1.1, 0.5))
    # <<< LEGEND ENDS

    # START OF TITLES >>>
    _titles(title, sub_title=sub_title)
    # <<< END OF TITLES

    # FOOTER STARTS >>>
    _footer(p, x_label, y_label, save=save)
    # <<< FOOTER ENDS
