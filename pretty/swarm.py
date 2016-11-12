import seaborn as sns
import matplotlib.pyplot as plt

def swarm(data,x,y,xscale='linear',yscale='linear'):
    
    # set default pretty settings from Seaborn
    
    sns.set(style="white", palette="muted")
    sns.set_context("notebook", font_scale=1, rc={"lines.linewidth": 0.2}) 

    # createthe plot
    
    g = sns.swarmplot(x=x, y=y, data=data, palette='RdYlGn')
    
    plt.tick_params(axis='both', which='major', pad=10)

    g.set(xscale=xscale)
    g.set(yscale=yscale)

    # Setting plot limits
    
    start = data[y].min().min()
    plt.ylim(start,);
    
    sns.despine()