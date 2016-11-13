import pandas as pd

from prep import prep
from table import table

def descriptive(data,columns='',title="Descriptive Stats",table_title=""):
    
    """
    
    Example use: 
        
        descriptive(df,['neg','neu','pos'],"This is the Title")
    
    """
    
    if columns == '':
        
        table(prep(data),title=title,table_title=table_title)
        
    else:
        
        table(prep(data[columns]),title=title,table_title=table_title)