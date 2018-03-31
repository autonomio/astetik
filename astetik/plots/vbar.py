import seaborn as sns
import matplotlib.pyplot as plt


def vbar(data, x, y, highlight, color='red', sort=True, sort_ascending=False, title=''):

    '''Vertical Bars with Highlight

    WHAT: A bar plot where one value is highlighted.

    USE: vertbar(df, 'max_score', 'country_code', 'uk')

    INPUT: A pandas dataframe where x is numeric and y is string labels

    OUTPUT: a vertical bar plot


    '''

    if sort is True:
        data = data.sort_values(x, ascending=sort_ascending)

    f, ax = plt.subplots(figsize=(5, 8))

    sns.set_style('white')
    sns.set_context("notebook", font_scale=1.3, rc={"lines.linewidth": 2})
    colors = [color if _y == highlight else 'grey' for _y in data[y]]

    g = sns.barplot(data[x], data[y], palette=colors, ax=ax, saturation=.3)

    # setting the xlim automatically
    xlim = data[x].min() - (data[x].min() * 0.2)
    g.set(xlim=(xlim, None))
    plt.tick_params(axis='both', labelsize=11, which='major', pad=10)

    plt.title(x, fontsize=22, y=1.03, color="gray");
    plt.xlabel(x, fontsize=15, labelpad=20, color="gray");
    plt.ylabel(title, fontsize=15, labelpad=20, color="gray");

    sns.despine()
