<img width=250 src='https://raw.githubusercontent.com/mikkokotila/astetik/master/logo.png'>

## Some opinionated comments on data visualization and Python

As someone else so eloquently put it, the merit, and also the curse, of Matplotlib is how everything is made possible for the user. It is with this vast flexibility, that also comes great confusion. Still the only purpose a plotting library serves, is in its ability to bring the data scientist closer to the end goal; being able to tell visually compelling stories with data. We want to tell those stories without having to think about the plots too much, as a plot is just a means to an end. If you want to quench your thirst, you don't want to spend too much time producing water, but drink it, and move on. Data visualization in the pydata ecosystem should be like this. Amazing looking, publication quality visualizations should be available through single-line, easy-to-understand, and easy-to-remember commands. One command per plot. No more, no less. 

That's the problem astetik solves.

## What is Astetik

Astetik takes the amazing potential of matplotlib and seaborn, and makes it available through single-line commands. While much of the lower level complexity is made invisible, some completely new features are added. Whatever is added is further taking away from the complexity of the visualizastion workflow. 

In *Five Essential Points of Data Visualization* I explain some of the frustrations, and ideas, conceived over more than 20 years working with data visualization and data-driven storytelling, that led to Astetik. You can [read it here](https://medium.com/@mikkokotila/five-essential-points-on-data-visualization-2856b80730b3). It is my sincere wish that you will find Astetik beneficial. 

## Why Astetik

You might ask, why not use one of...

- plotly
- bokeh
- mpl3d
- seaborn

...and so forth. The short answer is simplicity. Simplicity that focus equally on the user experience of the data scientist, and the experience of the audience. While the data scientist should not have to think about it, the audience should be vowed by it. 


## Background 

It started from the realization that there was not a single library for Python, able to produce publication quality descriptive stats tables. The first version just did one thing, and it looked like this: 

[![Screen Shot 2016-11-04 at 18.37.44.png](https://s14.postimg.org/hnoexoujl/Screen_Shot_2016_11_04_at_18_37_44.png)](https://postimg.org/image/70uls9me5/)

## Features 

One of the key problems related with plotting library use is uncertainty related with settings and data format. With astetik you give away much of the low-level tinkering ability, and get amazing looking plots in return. The plots look just as good regardless of the dataset, length of titles, and other factors that typically make it hard to standardize look and feel across all of your plots. In terms of uncertainty, every single plot comes with a standard call for displaying an example dataframe, and an example output using the example data. The example data is always from the same dataset. For example: 

#### the call for the plot

    ast.corr()
    
#### the call to display the data format

    ast.corr.in()

#### the call to display the sample plot 

    ast.corr.out()

This way you never have to think twice if your data is suitable for a given plot. 

### Visualization

- Over 20 plot types

- Descriptive table

- Wordcloud

### Data Preparation 


## Getting Started 

### Install from PyPi Package 

   pip install astetik

### Fire up a notebook or console

   import astetik as ast
   
That's it, you're ready to go. 

## TODO

1) transform all the plot codes to be template driven

2) add sample data to all functions

3) add an example plot for all functions

4) unify the docstrings for common parameters

5) unify the parameters to the extent possible

6) test title and subtitle for all plots

7) unify the color picker

8) add data scaler function (to do it before plot creation) 

9) TEST TEST TEST ... AND STILL A LITTLE TEST

10) push the new version to pypi

9) outliers
