import seaborn as sns

from ..style.titles import _titles
from ..style.template import _header, _footer
from ..utils.utils import _limiter, _scaler


def strip(data,
          x,
          y,
          hue=None,
          jitter=1,
          dodge=False,
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
          x_limit='auto',
          y_limit='auto',
          save=False):

    n = len(data[hue].unique())

    # HEADER STARTS >>>
    palette = _header(palette, style, n_colors=n, dpi=dpi)  # NOTE: y exception
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

    # START OF TITLES >>>
    _titles(title, sub_title=sub_title)
    # <<< END OF TITLES

    # FOOTER STARTS >>>
    _footer(p, x_label, y_label, legend, n, save)
    # <<< FOOTER ENDS

    p.spines['bottom'].set_color('black')
    p.set_xticklabels(order, rotation=90)
