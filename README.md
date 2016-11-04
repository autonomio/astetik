# pretty
Pretty is a python library for producing publication quality descriptive statistics tables from a Pandas DataFrame. It is made specifically to be used with IPython / Jupyter notebooks and is the only such library currently available. It uses very simple and extremely easy to edit html code to produce the visualization. 

Basically it does one thing, and does it really well: 

[![Screen Shot 2016-11-04 at 18.37.44.png](https://s14.postimg.org/hnoexoujl/Screen_Shot_2016_11_04_at_18_37_44.png)](https://postimg.org/image/70uls9me5/)

You need to have Pandas and IPython/Jupyter. That's it. 

    import pretty as pretty 

### How pretty works? 

The first function is a data prep function:

    pretty.data(df)

The second function is the table function: 

    pretty.table(df)
    
Now we have some options as well > 'setting the main title'

    pretty.table(df,"Tweet Text Statistics")

If you leave the column parameter empty, pretty will use "Descriptive Statistics" as a default.

There is also an option for the table title (as is visual in the example): 

    pretty.table(df,"Table 2")

To put the two functions together, you could do: 

    data = pretty.data(df)
    pretty.table(data)
    
or

    pretty.data(pretty.table(df))

### Why support only 3 features per table (not more, not less)?

- It's sufficient for most use cases 
- It allowed keeping both the python code and html very simple
- It's very easy to modify the code to support any number of rows 
- 3 looks better than 2 or 4

This is only a problem if your dataframe has less than three rows of data. As long as you have more, you could choose any three, or use the default setting where pretty use three first columns from the dataframe. 

    pretty.table(pretty.data(df,['days_since_creation','quality_score','retweet_count']))

Then if you were repeatedly using various combinations from the same or similar dataset, you could create easy to remember groupings and save them in the pretty.ph file after the imports like so: 

    metrics = ['days_since_creation','quality_score','retweet_count']
    
And then just call: 

    pretty.table(pretty.data(df,metrics))
