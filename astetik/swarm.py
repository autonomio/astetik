from math import sqrt
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import rcParams

from .color_picker import color_picker


def swarm(data, x, y, hue=None, xscale='linear',yscale='linear', palette=None):

    sns.set(style="white", palette="muted")
    sns.set_context("notebook", font_scale=1.5)

    rcParams['figure.figsize'] = 12, 12
    rcParams['font.family'] = 'Verdana'
    rcParams['font.size'] = 1
    rcParams['figure.dpi'] = 72
    rcParams['lines.linewidth'] = 10

    if palette == None:
        if hue != None:
            n = 2
        else:
            n = sqrt(len(data))
    try:
        palette = color_picker(palette=palette, n=n)
    except UnboundLocalError:
        pass

    # createthe plot
    g = sns.swarmplot(data=data, x=x, y=y, hue=hue, palette=palette, linewidth=1)

    plt.tick_params(axis='both', which='major', pad=10)
    g.set(xscale=xscale)
    g.set(yscale=yscale)

    # Setting plot limits
    start = data[y].min().min()
    plt.ylim(start,)

    sns.despine()
