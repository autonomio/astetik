import seaborn as sns
import matplotlib.pyplot as plt


def dist(data, x,
         color='red',
         bins=True,
         title=None,
         xlabel=None,
         dropna=False,
         auto_xlim=True,
         kde=False,
         rug=False,
         vertical=False):

    '''Distribution Plot

    WHAT: creates a basic distribution plot out of 1-d data input

    USE: dist('score_161202', scores, dropna=True)

    INPUT: a pandas dataframe with at least one column of data

    OUTPUT: a distribution plot

    '''

    if dropna is True:
        data = data[x].dropna()
    else:
        data = data[x]

    if bins is True:
        bins = len(data) / 10

    sns.set_context("notebook", font_scale=1.2, rc={"lines.linewidth": 2})
    plt.figure(figsize=(12, 6))

    g = sns.distplot(data, bins=bins, norm_hist=False, color=color, kde=kde, rug=rug, vertical=vertical)

    if auto_xlim is True:
        g.set(xlim=(data.min(), None))
    if type(auto_xlim) is int:
        g.set(xlim=(auto_xlim, None))
    elif type(auto_xlim) is list:
        g.set(xlim=(auto_xlim[0], auto_xlim[1]))

    plt.tick_params(axis='both', which='major', pad=10)

    # handling title
    if title is not None:
        plt.title(title, fontsize=22, y=1.12,  x=0.48, color="gray")

    # show samplesize as subtitle
    plt.suptitle("n = " + str(len(data)), verticalalignment='top', fontsize=18, y=.95, x=0.48, color="gray")

    # handling x_labels
    if xlabel is not None:
        x = xlabel
    plt.xlabel(x, fontsize=15, labelpad=20, color="gray")

    plt.ylabel('Frequency', fontsize=15, labelpad=20, color="gray")

    plt.tick_params(axis='both', which='major', pad=25)

    plt.axhline(linewidth=2.5, color="black")
    plt.axvline(linewidth=2.5, color="black")

    sns.despine()
