import seaborn as sns
import matplotlib.pyplot as plt

def kde(x,y,title='',color='YlGnBu',xscale='linear',yscale='linear'):
    
    sns.set_style('white')
    sns.set_context('notebook', font_scale=1, rc={"lines.linewidth": 0.5})
    g = sns.kdeplot(x,y,shade=True, cut=2, cmap=color, shade_lowest=False, legend=True, set_title="test")
    plt.tick_params(axis='both', which='major', pad=10)
    sns.plt.title(title)
    
    g.set(xscale=xscale)
    g.set(yscale=yscale)
    
    sns.despine()