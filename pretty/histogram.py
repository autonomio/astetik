import matplotlib.pylab as plt
import seaborn as sns
import numpy as np

def histogram(data,variables):
    
    sns.set_context("notebook", font_scale=1.5, rc={"lines.linewidth": 0})

    sns.set_style('white')

    var_length = len(variables)
    
    fig, axes = plt.subplots(1, var_length, figsize=(19, 5))
    
    for i in range(var_length):
        
        axes[i].hist(data[variables[i]],lw=0,color="indianred",bins=8);
        axes[i].tick_params(axis='both', which='major', pad=15)
        axes[i].set_xlabel(variables[i])
        axes[i].set_yticklabels("");
    
    sns.despine(left=True)
    