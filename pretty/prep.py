import pandas as pd

def prep(data,columns=''):
    
    """
      Data processor for desc_table() function.
      
      You can call it separately as well and in 
      return get a non-prettyfied summary table. 
      
      Unless columns are defined, the three first 
      columns are chosen by default. 
      
      SYNTAX EXAMPLE: 
      
      df['quality_score','influence_score','reach_score']
    
    """
       
    if data.shape[1] != 3:
        if len(columns) !=3:
            if data.shape[1] > 3:
                
                print "showing first three columns because no columns were specific / data had more than 3 columns"
                data = pd.DataFrame(data[data.columns[0:3]])
    
    if data.shape[1] < 3:
        
        print "You need at least 3 columns of data for this table"
        quit()
        
    if len(columns) == 3:
            data = data[columns]
            
    desc = pd.DataFrame({'sum' : data.sum().astype('int'),
                         'median' : data.median(),
                         'mean' : data.mean(),
                         'std' : data.std()})
    desc = desc.round(decimals=2)      
    
    return desc
