import seaborn as sns

from ..style.template import _header, _footer
#from ..utils.utils import _limiter, _scaler


def strip(data,
        x,
        y,
        hue=None,
        jitter=1,
        dodge=False,
        palette='default',
        style='astetik',
        dpi=72,
        x_label='',
        y_label='',
        x_scale='linear',
        y_scale='linear',
        x_limit='auto',
        y_limit='auto'):

    # HEADER STARTS >>>
    palette = _header(palette, style, n_colors=2, dpi=dpi)  # NOTE: y exception
    # <<< HEADER ENDS

    order = data[x].unique()
    p = sns.stripplot(data=data,
                      x=x,
                      y=y,
                      hue=hue,
                      palette=palette,
                      size=4,
                      order=order,
                      dodge=dodge,
                      jitter=jitter)

    #FOOTER STARTS >>>
    _footer(p, x_label, y_label)
    #<<< FOOTER ENDS

    p.spines['bottom'].set_color('black')
    p.set_xticklabels(order, rotation=90)
