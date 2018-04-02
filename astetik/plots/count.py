import seaborn as sns

from ..style.template import _header, _footer


def count(data,
          x,
          hue=None,
          row=None,
          col=None,
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
          col_wrap=4):

    if hue != None:
        n_colors = len(data[hue].unique())
    else:
        n_colors = len(data[x].unique())

    # HEADER STARTS >>>
    palette = _header(palette,
                      style,
                      n_colors=n_colors,
                      dpi=dpi,
                      fig_height=None,
                      fig_width=None)
    # <<< HEADER ENDS

    p = sns.factorplot(data=data,
                       x=x,
                       y=None,
                       hue=hue,
                       row=row,
                       col=col,
                       col_wrap=col_wrap,
                       palette=palette,
                       size=4,
                       kind='count')

    # FOOTER STARTS >>>
    _footer(p, x_label, y_label)
    # <<< FOOTER ENDS
