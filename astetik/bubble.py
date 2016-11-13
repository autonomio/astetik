import seaborn as sns
import matplotlib.pyplot as plt

def bubble(data,x,y,hue,bsize,palette='Reds',xscale='linear',yscale='linear',title='',suptitle=0):
    
    if suptitle == 0:
        suptitle = bsize
    
    sns.set(style="whitegrid")
    sns.set_context("notebook", font_scale=3, rc={"lines.linewidth": 0.3})

    sns.set_color_codes("bright")

    size = (1500 / float(data[bsize].max()))
    size = data[bsize] * size

    g = sns.PairGrid(data, hue=hue, palette=palette, y_vars=y, x_vars=x, size=12, aspect=3)
    
    g.map(plt.scatter, s=size);
    
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
    plt.ylim(0,);
    plt.xlim(0,);