import pandas as pd
import numpy as np
import scipy.stats as sc

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colorbar import cm

import seaborn as sns

from .cmaps import cmaps


def scat(data,
         x,
         y,
         color,
         labels=None,
         x_scale=False,
         y_scale=False,
         outlier=False,
         title='',
         suptitle=0,
         cmap=cm.rainbow,
         legend_loc=1,
         alpha=0.9):

    # handling legend labels

    if labels is not None:

        a = data[labels].unique()
        b = data[color].unique()
        temp_df = pd.DataFrame(a, b).reset_index()
        temp_df = temp_df.sort_values(0)
        classes = temp_df[0].values

    else:
        classes = data[color].unique()
        classes = range(len(classes))


    if cmap is not cm.rainbow:
        cmap = cmaps(cmap)

    if suptitle == 0:
        suptitle = "color = " + str(suptitle)

    elif suptitle == None:
        suptitle = ''

    x_label = x
    y_label = y
    color_label = color

    ## dealing with outliers

    if outlier == True:

        if labels is not None:
            labels_temp = data[labels]

        temp = pd.DataFrame({
            'color' : data[color],
            'y': np.array(data[y]),
            'x': np.array(data[x])
        })

        lower_bound_x = temp.x.median() - (sc.iqr(temp.x) * 4.5)
        upper_bound_x = temp.x.median() + (sc.iqr(temp.x) * 4.5)

        temp = temp[temp.x >= lower_bound_x]
        temp = temp[temp.x <= upper_bound_x]

        lower_bound_y = temp.y.median() - (sc.iqr(temp.y) * 4.5)
        upper_bound_y = temp.y.median() + (sc.iqr(temp.y) * 4.5)

        temp = temp[temp.y >= lower_bound_y]
        temp = temp[temp.y <= upper_bound_y]

        data = temp

        data.columns = [[color_label, x_label, y_label]]

    # my_cmap = ListedColormap(test_color)

    ## figure settings

    sns.set_context("paper", font_scale=2)
    plt.rcParams['figure.figsize'] = 20, 10

    ## make the plot

    plt.scatter(data[x],
                data[y],
                s=120,
                c=data[color],
                marker='o',
                alpha=alpha,
                cmap=cmap,
                edgecolor='black',
                linewidth=1.5)

    ## labels and text

    plt.title(title, fontsize=28, y=1.12, color="gray");
    plt.suptitle(suptitle, verticalalignment='top', fontsize=25, y=0.93, x=0.48, color="gray")

    plt.xlabel(x_label, fontsize=18, labelpad=20, color="grey");
    plt.ylabel(y_label, fontsize=18, labelpad=20, color="grey");

    #plt.axhline(linewidth=0.9, color="grey");
    #plt.axvline(linewidth=0.9, color="grey");

    plt.tick_params(axis='both', which='major', pad=20)
    plt.ticklabel_format()

    ## dealing with range / log and
    ## plot range limits

    y = data[y]
    x = data[x]

    if x_scale == True or y_scale == True:

        y_lim_lo = y.min()
        x_lim_lo = x.min()

    if x_scale == True:

        plt.xscale('symlog')

    if y_scale == True:

        plt.yscale('symlog')

    else:

        y_lim_lo = y.min() - ((y.max() - y.min()) * 0.01)
        x_lim_lo = x.min() - ((x.max() - x.min()) * 0.01)

    plt.ylim(y_lim_lo,);
    plt.xlim(x_lim_lo,);

    color = iter(cmap(np.linspace(0,1,len(classes))))

    recs = []
    for i in range(len(classes)):
        recs.append(mpatches.Rectangle((0, 0), 1, 1, fc=next(color)))


    plt.legend(recs, classes, loc=legend_loc)

    sns.despine(top=True, right=True, left=False, bottom=False)
