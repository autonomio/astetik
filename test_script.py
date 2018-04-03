import pandas as pd
import numpy as np
import random
import string

import astetik as ast


# generate random data
def create_data():

    df = pd.DataFrame(np.random.randint(0, 100, size=(100, 8)), columns=list('ABCDEFGH'))
    df['other'] = (df.A + df.B) % 2 == False
    df = df.reset_index()
    df['text'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(23))

    return df


def test_tables(df):

    ast.text(df, 'text', sort='asc', max_rows=5)
    ast.table(df[['A', 'B', 'C']], table_title='test')
    ast.ols(df, 'odd', 'A', 'even', 'B')


def test_simple_minimal(df):

    ast.corr(df)
    ast.kde(data=df, x='A')
    ast.hist(df, x='A')
    ast.pie(df, x='other')
    ast.swarm(df, x='A', y='B')
    ast.scat(df, x='A', y='B')
    ast.line(df, x='A')
    ast.grid(df, x='A', y='B', col='even')
    ast.box(df, x='A', y='even')
    ast.violin(df, x='A', y='even')
    ast.strip(df, x='odd', y='B', hue='even')
    ast.count(df, x='odd')
    ast.bars(df, x='even', y='B', hue='other', col='odd')
    ast.overlap(df, x='A', y='B', label_col='other')
    ast.multikde(df, x='A', label_col='even')
    ast.compare(df, x='A', y=['B', 'C'], label_col='other')
    ast.multicount(df, x='even', y='A', hue='odd', col='other')


# create the dataset
df = create_data()

# run table tests
test_tables(df)

# run simple plot tests
test_simple_minimal(df)
