import seaborn as sns
import matplotlib.pyplot as plt

from matplotlib.pyplot import rcParams

def kde(x, y=None, title='',color='YlGnBu',xscale='linear',yscale='linear', cbar=True, cumulative=False, dpi=72):

    sns.set(style="white")
    sns.set_context("notebook", font_scale=1.5, rc={"lines.linewidth": 0.3})

    rcParams['figure.figsize'] = 20, 10
    rcParams['font.family'] = 'Verdana'
    rcParams['figure.dpi'] = dpi

    g = sns.kdeplot(data=x,
                    data2=y,
                    shade=True,
                    cut=5,
                    shade_lowest=False,
                    legend=True,
                    cumulative=cumulative,
                    cbar=cbar,
                    kernel='gau',
                    bw='scott')

    plt.tick_params(axis='both', which='major', pad=10)
    plt.title(title)

    g.set(xscale=xscale)
    g.set(yscale=yscale)

    sns.despine()
