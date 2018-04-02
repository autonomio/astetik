# astetik

## Some opinions about data visualization on Pythoh

As someone so eloquently put it, the merit, and also the curse, of Matplotlib is how everything (and then some) is possible. It is with this vast flexibility, that often also comes with great confusion. Seaborn does an amazing job in taking away a lot of that confusion, and bringing the data scientist far closer to the end goal; being able to tell visually compelling stories with data. If I might add, we want to tell those stories without having to think about the plots themselves too much, as that's just a means to an end. If you want to quench your thirst, you don't want to spend too much time thinking about the chemistry and physics that goes in to water, but drink it, and move. Data visualization in the pydata ecosystem should be like this. Amazing looking, publication quality visualizations should be available through single-line, easy-to-rememder, and easy-to-remember commands. One per plot. No more, no less. That's the problem astetik solves.

## What is Astetik

Astetik takes the amazing potential of matplotlib and seaborn, and makes it available through single-line commands. While much of the lower level complexity is made invisible, some completely new features are added. Whatever is added is further taking away from the complexity of the visualizastion workflow. 


*Five Essential Points of Data Visualization*[click here](https://medium.com/@mikkokotila/five-essential-points-on-data-visualization-2856b80730b3)






https://medium.com/@mikkokotila/five-essential-points-on-data-visualization-2856b80730b3



astetik is a python library for producing publication quality descriptive statistics tables from a Pandas DataFrame. It uses very simple and extremely easy to edit html code to produce the result. 

Basically it does one thing (display publication quality descriptive stat tables for three features at a time), and does it really well: 

[![Screen Shot 2016-11-04 at 18.37.44.png](https://s14.postimg.org/hnoexoujl/Screen_Shot_2016_11_04_at_18_37_44.png)](https://postimg.org/image/70uls9me5/)

You can see / try astetik in a live Jupyter notebook: 

https://nbviewer.jupyter.org/github/mikkokotila/astetik/blob/master/astetik.ipynb

### What dependencies astetik has? 

You need to have Pandas and IPython/Jupyter. That's it. 

### Getting started with astetik

1) copy the file astetik.py from this repo

2) save it in the folder where your notebooks reside / where you now how to call it

3) Open a IPython / Notebook in your browser and: 

    import astetik as astetik
    import pandas as pd
    
### How astetik works? 

There are just two functions, and an html "template". It's all in astetik.py file. 

The first function is a data prep function:

    astetik.data(df)

The second function is the table function: 

    astetik.table(df)
    
Now we have some options as well > 'setting the main title'

    astetik.table(df,"Tweet Text Statistics")

If you leave the column parameter empty, astetik will use "Descriptive Statistics" as a default.

There is also an option for the table title (as is visual in the example): 

    astetik.table(df,"Table 2")

To put the two functions together, you could do: 

    data = astetik.data(df)
    astetik.table(data)
    
or

    astetik.data(astetik.table(df))

### Why support only 3 features/variables per table (not more, not less)?

- It's sufficient for most use cases 
- It allowed keeping both the python code and html very simple
- It's very easy to modify the code to support any number of rows 
- 3 looks better than 2 or 4

This is only a problem if your dataframe has less than three rows of data. As long as you have more, you could choose any three, or use the default setting where astetik use three first columns from the dataframe. 

    astetik.table(astetik.data(df,['days_since_creation','quality_score','retweet_count']))

Then if you were repeatedly using various combinations from the same or similar dataset, you could create easy to remember groupings and save them in the astetik.ph file after the imports like so: 

    metrics = ['days_since_creation','quality_score','retweet_count']
    
And then just call: 

    astetik.table(astetik.data(df,metrics))
    
### Why just mean / median / std and total?

Because that's what I realised that most projects need, and also once you look at the code, you can realise that it will take seconds for you to change the math functions to whatever you like.
