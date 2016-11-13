import seaborn as sns
import matplotlib.pyplot as plt

def regression(data,x,y,xscale='linear',yscale='linear'):


    sns.set_context("notebook", font_scale=.8, rc={"lines.linewidth": 0})
    sns.set_style('white')

    g = sns.regplot(x=x, y=y, data=data)
    
    plt.tick_params(axis='both', which='major', pad=10)

    g.set(xscale=xscale)
    g.set(yscale=yscale)

    sns.despine()