<img width=250 src='https://raw.githubusercontent.com/mikkokotila/astetik/master/logo.png'>

[![Build Status](https://travis-ci.org/mikkokotila/astetik.svg?branch=master)](https://travis-ci.org/mikkokotila/astetik)  [![Coverage Status](https://coveralls.io/repos/github/mikkokotila/astetik/badge.svg?branch=master)](https://coveralls.io/github/mikkokotila/astetik?branch=master) [![Dependency Status](https://gemnasium.com/badges/github.com/mikkokotila/astetik.svg)](https://gemnasium.com/github.com/mikkokotila/astetik) [![PEP8](https://img.shields.io/badge/code%20style-pep8-blue.svg)](https://www.python.org/dev/peps/pep-0008/)

    pip install astetik      # TL;DR

## Why Astetik

Astetik takes the amazing potential of matplotlib and seaborn, and makes it available through single-line commands. While much of the lower level complexity is made invisible, some completely new features are added. Whatever is added is further taking away from the complexity of the visualizastion workflow.

You might ask, why not use one of...

- matplotlib
- plotly
- bokeh
- mpl3d
- seaborn

...and so forth. The short answer is simplicity. Simplicity that focus equally on the user experience of the data scientist, and the experience of the audience. While the data scientist should not have to think about it, the audience should be vowed by it. Without compromising the capabilities that are essential for visual storytelling.

In *Five Essential Points of Data Visualization* I explain some of the frustrations, and ideas, conceived over more than 20 years working with data visualization and data-driven storytelling, that led to Astetik. You can [read it here](https://medium.com/@mikkokotila/five-essential-points-on-data-visualization-2856b80730b3).

## Simplicity

### Parameters

Every plot has three kinds of parameters; data inputs, plot specific, and common. The common are identical, and presented in the identical order in every plot. This means that once you learn one plot, you've more or less learn the all. The only exception is the plot specific parameters, which have been kept to absolute minimum, in many cases as few as 2 or 3.

### Docstrings

Partially owing to the well unified parameter space between the plots, the docstrings are very clear, and easy to digest. The input related are given first, following the plot specifics, and last the common parameters, in which case the dosctring is identical in every plot. At the top of each docstring several key points are made clear:

- range of dimensions the plot supports
- type of features (e.g. categorical and continous) work the best
- recommended max number of features/columns

## Some opinionated comments on data visualization and Python

As someone else so eloquently put it, the merit, and also the curse, of Matplotlib is how everything is made possible for the user. It is with this vast flexibility, that also comes great confusion. Still the only purpose a plotting library serves, is in its ability to bring the data scientist closer to the end goal; being able to tell visually compelling stories with data. We want to tell those stories without having to think about the plots too much, as a plot is just a means to an end. If you want to quench your thirst, you don't want to spend too much time producing water, but drink it, and move on. Data visualization in the pydata ecosystem should be like this. Amazing looking, publication quality visualizations should be available through single-line, easy-to-understand, and easy-to-remember commands. One command per plot. No more, no less.

That's the problem astetik solves.

## Background

It started from the realization that there was not a single library for Python, able to produce publication quality descriptive stats tables. The first version just did one thing, and it looked like this:

[![pretty table](https://s14.postimg.org/hnoexoujl/Screen_Shot_2016_11_04_at_18_37_44.png)](https://postimg.org/image/70uls9me5/)

At the time I was doing a lot of analysis that involved correlation, and ended up doing a simple heatmap plot which took about 20 lines of codes to polish it, and several hours of work having no previous knowledge of matplotlib or seaborn. The first plot looked like this:

<img width=600 src=https://raw.githubusercontent.com/mikkokotila/astetik/master/examples/images/heat_titanic.png>

The code to run it was (and still is):

    ast.corr(titanic, title='TITANIC SURVIVAL DATA', sub_title="Economics of Making it Alive")

Today Astetik include, in addition to the original descriptive table and the heatmap correlation, over 20 unique plots and many unique features to make the daily life of data scientists and visual storytellers more enjoyable. The focus remains on simplicity in both use and aesthetic:

<img width=600 src=https://raw.githubusercontent.com/mikkokotila/astetik/master/examples/images/foon_line.png>

The code to produce the above line graph: 

    ast.line(data=global_totals,
             x=['population','food'],
             y='year',
             palette='colorblind',
             legend=True,
             title='Global Food Trends',
             sub_title='Production on its own trajectory since 1992')

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

FEATURES:
- add limiter to all relevant plots
- add scaler to all relevant plots
- add outlier removal to all plots

USABILITY:
- add sample data to all plots
- add sample plot resulting from the data
- unify docstrings
- unify parameters

OTHER:
- unify the color pickers
- add saving figure to all

## GATCHAS

- Not all plots can handle x and y limits in the same way (just few are exceptions)
- Scaling is not applicable to all plots
