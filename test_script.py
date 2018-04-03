import pandas as pd
import numpy as np
import random
import string

import astetik as ast

# generate random data
df = pd.DataFrame(np.random.randint(0,100,size=(100, 8)), columns=list('ABCDEFGH'))
df['other'] = (df.A + df.B) % 2 == False
df = df.reset_index()

def strings():
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(23))

df['text'] = strings()

ast.text(df, 'text', sort='asc', max_rows=5)
ast.table(df[['A', 'B', 'C']], table_title='test')
ast.ols(df, 'A', 'B', 'C', 'D')
ast.corr(df)
ast.kde(data=df,
        x='B',
        palette='blue_to_red')
