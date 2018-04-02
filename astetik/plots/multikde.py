import seaborn as sns
import matplotlib.pyplot as plt

from ..style.template import _header, _footer
from ..utils.transform import _groupby


def multikde(data,
             x,
             label_col,
             sort=None,
             transform=None,
             transform_func='sum',
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
             y_limit='auto'):

    '''JOY PLOT

    Takes two columns, where the other has to be a categorical
    and the other continuous.


    USE
    ===
    multikde(data=patients[patients.age < 80],
             x='age',
             label_col='insurance')


    '''

    palette = _header(palette,
                      style,
                      n_colors=1,
                      dpi=dpi,
                      fig_height=None,
                      fig_width=None)
    # <<< HEADER ENDS

    sns.set(style="white", rc={"axes.facecolor": (0, 0, 0, 0)})
    g = sns.FacetGrid(data, row=label_col, hue=label_col, aspect=15, size=1, palette=palette)
    g.map(sns.kdeplot, x, clip_on=False, shade=True, alpha=1, lw=1.5, bw=.2)
    g.map(plt.axhline, y=0, lw=2, clip_on=False)

    # Define and use a simple function to label the plot in axes coordinates
    def label(x, color, label):
        ax = plt.gca()
        ax.text(0, .2,
                label,
                fontweight="bold",
                fontsize=14,
                color=color,
                ha="left",
                va="center",
                transform=ax.transAxes)

    g.map(label, x)

    # Set the subplots to overlap
    g.fig.subplots_adjust(hspace=-.25)

    # Remove axes details that don't play will with overlap
    g.set_titles("")
    g.set(yticks=[])
    g.despine(bottom=True, left=True);
