## pretty implementation of matplotlib scatter plot and seaborn 
## facetgrid to dynamically create standard and amazing looking
## bubble chart with zero configuration option. 

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def bubble(data,x,y,hue,bsize,palette='Reds',xscale='linear',yscale='linear',title='',suptitle=0,xlim_start=0,ylim_start=0,xlim_end=0,ylim_end=0):

    import seaborn as sns
    import matplotlib.pyplot as plt
        
    """ 
    
    x > should be int or float
    y > should be int or float
    hue > should be boolean or category
    bsize > should be int or float 
    
    
    """
    
    if suptitle == 0:
        suptitle = bsize    
        
    y_modifier = (data[y].max() - data[y].min()) * 0.1
    x_modifier = (data[x].max() - data[x].min()) * 0.1

    if ylim_start == 0:
        ylim_start = data[y].min()

    if xlim_start == 0:
        xlim_start = data[x].min()
        
    if ylim_end == 0:
        ylim_end = data[y].max() + y_modifier

    if xlim_end == 0:
        
        xlim_end = data[x].max() + (x_modifier * 2)

    sns.set(style="whitegrid")
    sns.set_context("notebook", font_scale=3, rc={"lines.linewidth": 0.3})

    sns.set_color_codes("bright")
     
    size = (1500 / float(data[bsize].max()))
    size = data[bsize] * size
     
    g = sns.PairGrid(data, hue=hue, palette=palette, y_vars=y, x_vars=x, size=12, aspect=3)
    g.map(plt.scatter, s=5000);
    g.set(xscale=xscale)
    g.set(yscale=yscale)
    g.add_legend(title=hue, bbox_to_anchor=(0.9, 0.6))
    
    plt.title(title, fontsize=48, y=1.12, color="gray");
    plt.suptitle("size = " + suptitle, verticalalignment='top', fontsize=35, y=1.01, x=0.48, color="gray")
    plt.xlabel(x, fontsize=38, labelpad=30, color="gray");
    plt.ylabel(y, fontsize=38, labelpad=30, color="gray");
    plt.tick_params(axis='both', which='major', pad=25)
    plt.axhline(linewidth=2.5, color="black");
    plt.axvline(linewidth=2.5, color="black");
    plt.ylim(ylim_start,ylim_end);
    plt.xlim(xlim_start,xlim_end);
