# ASTETIK IMPORTS START >>
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.pyplot import rcParams
from ..style.color_picker import color_picker, color_blind, _label_to_hex
# << ASTETIK IMPORTS END

from ..style.template import _header, _footer
from ..utils.utils import _limiter, _scaler


def kde(x,
        y=None,
        title='',
        sub_title='',
        footnote='',
        samplenote='',
        x_label='',
        y_label='',
        palette='default',
        xscale='linear',
        yscale='linear',
        cbar=True,
        cumulative=False,
        style='astetik',
        dpi=72):

    # ASTETIK HEADER STARTS >>
    if style != 'astetik':
        plt.style.use(style)

    if y == None:
        n = 1
    else:
        n = 2

    if palette == 'colorblind':
        palette = color_blind()
    else:
        try:

            palette = color_picker(palette=palette, n_colors=n)
        except UnboundLocalError:
            palette = _label_to_hex(palette, n_colors=n)

    sns.set_context("notebook", font_scale=1.2, rc={"lines.linewidth": 2})
    plt.figure(figsize=(12, 8))

    rcParams['font.family'] = 'Verdana'
    rcParams['figure.dpi'] = dpi
    # << ASTETIK FOOTER ENDS

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

    plt.title(title)

    p.set(xscale=xscale)
    p.set(yscale=yscale)

    # ASTETIK FOOTER STARTS >>
    # FOOTER STARTS >>>
    _footer(p, x_label, y_label)
    # <<< FOOTER ENDS

    #  << ASTETIK FOOTER ENDS
