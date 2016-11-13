import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def bars(data,color='black',title=''):

    data = pd.DataFrame(data.value_counts())
    data = data.reset_index()
    data.columns = ['keyword','value']
    data['keyword'] = data['keyword'][1:]
    data = data.dropna()
    data = data.reset_index(drop=True)
    data = data.sort_values('value',ascending=False)

    sns.set_context("notebook", font_scale=1.2, rc={"lines.linewidth": 0})

    x = data.head(20)['keyword'].astype(str)
    y = data.head(20)['value'].astype(int)

    f, ax = plt.subplots(figsize=(16, 3))

    sns.set_style('white')

    ## change color of the bar based on value

    colors = [color if _y >=0 else 'red' for _y in y]

    sns.barplot(x, y, palette=colors, ax=ax)
    
    plt.title(title, fontsize=18, y=1.12, color="gray");
    
    ax.set_xticklabels('')
    ax.set_ylabel('')
    ax.set_xlabel('')
    ax.tick_params(axis='both', which='major', pad=30)

    for n, (label, _y) in enumerate(zip(x, y)):
        ax.annotate(
            s='{:.1f}'.format(abs(_y)),
            xy=(n, _y),
            ha='center',va='center',
            xytext=(0,-10),
            size=12,
            textcoords='offset points',
            color="white",
            weight="bold"
        )
    ax.set_yticklabels("");
    ax.set_xticklabels(data.head(20)['keyword'],rotation=25,ha="right");
    ax.tick_params(axis='both', which='major', pad=15)
    sns.despine(left=True)