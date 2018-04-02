
import seaborn as sns

from ..style.titles import _titles
from ..style.template import _header, _footer
from ..utils.utils import _limiter, _scaler


def kde(x,
        y=None,
        title='',
        sub_title='',
        x_label='',
        y_label='',
        palette='default',
        xscale='linear',
        yscale='linear',
        cbar=True,
        cumulative=False,
        style='astetik',
        dpi=72):

    # HEADER STARTS >>>
    palette = _header(palette, style, n_colors=1, dpi=dpi)
    # <<< HEADER ENDS

    p = sns.kdeplot(data=x,
                    data2=y,
                    shade=True,
                    cut=5,
                    shade_lowest=False,
                    legend=True,
                    cumulative=cumulative,
                    cbar=cbar,
                    kernel='gau',
                    bw='scott',
                    cbar_kws=dict(alpha=1))

    p.set(xscale=xscale)
    p.set(yscale=yscale)

    # START OF TITLES >>>
    _titles(title, sub_title=sub_title)
    # <<< END OF TITLES

    # FOOTER STARTS >>>
    _footer(p, x_label, y_label)
    # <<< FOOTER ENDS
