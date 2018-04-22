import pandas as pd
import numpy as np
import random
import string

import astetik as ast


# generate random data

def create_data():

    df = pd.DataFrame(np.random.randint(0, 100, size=(100, 8)), columns=list('ABCDEFGH'))
    df['odd'] = df.A % 2 == True
    df['even'] = df.A % 2 == False
    df['other'] = (df.A + df.B) % 2 == False
    df = df.reset_index()
    df['text'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(23))
    df['cats'] = np.random.randint(0,5, 100)

    return df


def test_tables(df):

    ast.text(df, 'text', sort='asc', max_rows=5)
    ast.table(df[['A', 'B', 'C']], table_title='test')
    ast.ols(df, 'B', 'A', 'even', 'C')


def test_simple_minimal(df):

    ast.corr(df)
    ast.kde(data=df, x='A')
    ast.hist(df, x='A')
    ast.pie(df, x='other')
    ast.swarm(df, x='A', y='B', hue='even')
    ast.scat(df, x='A', y='B', hue='even')
    ast.line(df, x='A')
    ast.grid(df, x='A', y='B', col='even')
    ast.box(df, x='odd', y='A', hue='even')
    ast.violin(df, x='odd', y='A', hue='even')
    ast.strip(df, x='odd', y='B', hue='even')
    ast.count(df, x='cats')
    ast.bargrid(df, x='even', y='B', hue='other', col='odd')
    ast.overlap(df, x='A', y='B', label_col='other')
    ast.multikde(df, x='A', label_col='even')
    ast.compare(df, x='A', y=['B', 'C'], label_col='other')
    ast.multicount(df, x='even', hue='odd', col='other')


def corr_full(df):

    ast.corr(df,
             corr_method='pearson',
             annot=True, palette='colorblind',
             style='fivethirtyeight',
             dpi=240,
             title='This is a title',
             sub_title='And this a subtitle',
             x_label='this is x label',
             y_label='and this y',
             legend=False,
             x_scale='log',
             y_scale='symlog',
             x_limit=1,
             y_limit=[1,199])


def kde_full(df):

    ast.kde(data=df,
            x='C',
            cumulative=True,
            palette='Reds',
            style='astetik',
            dpi=72,
            title='This is a title',
            sub_title='And this a subtitle',
            x_label='this is x label',
            y_label='and this y',
            legend=False,
            x_scale='log',
            y_scale='symlog',
            x_limit=1)

    ast.kde(data=df,
            x='A',
            y='B',
            palette='Reds',
            style='astetik',
            dpi=72,
            title='This is a title',
            sub_title='And this a subtitle',
            x_label='this is x label',
            y_label='and this y',
            legend=False,
            x_scale='log',
            y_scale='symlog',
            x_limit=1,
            y_limit=[1,199])


def hist_full(df):

    ast.hist(data=df,
             x='A',
             bins=40,
             dropna=True,
             vertical=True,
             palette='colorblind',
             style='fivethirtyeight',
             dpi=240,
             title='This is a title',
             sub_title='And this a subtitle',
             x_label='this is x label',
             y_label='and this y',
             legend=False,
             x_scale='log',
             x_limit=24)


def pie_full(df):

    ast.pie(data=df,
             x='A',
             palette='colorblind',
             style='fivethirtyeight',
             dpi=240,
             title='This is a title',
             sub_title='And this a subtitle',
             x_label='this is x label',
             y_label='and this y',
             legend=False)


def swarm_full(df):

    ast.swarm(data=df,
              x='A',
              y='B',
              hue='even',
              palette='Reds',
              style='astetik',
              dpi=72,
              title='This is a title',
              sub_title='And this a subtitle',
              x_label='this is x label',
              y_label='and this y',
              legend=False,
              x_scale='log',
              y_scale='symlog',
              x_limit=1,
              y_limit=[1,21])


def scat_full(df):

    ast.swarm(data=df,
              x='A',
              y='B',
              hue='odd',
              palette='Reds',
              style='astetik',
              dpi=72,
              title='This is a title',
              sub_title='And this a subtitle',
              x_label='this is x label',
              y_label='and this y',
              legend=False,
              x_scale='log',
              y_scale='symlog',
              x_limit=1,
              y_limit=[1,21])


def line_full(df):

    ast.line(data=df,
             x='A',
             y='index',
             median_line=True,
             drawstyle='steps',
             linestyle='solid',
             markerstyle='.',
             palette='red_to_green',
             style='astetik',
             dpi=72,
             title='This is a title',
             sub_title='And this a subtitle',
             x_label='this is x label',
             y_label='and this y',
             legend=False,
             #x_scale='log',
             #y_scale='symlog',
             x_limit=1,
             y_limit=[1,21])


def grid_full(df):

    ast.grid(data=df,
             x='A',
             y='B',
             col='other',
             hue='odd',
             col_wrap=3,
             palette='Reds',
             style='astetik',
             dpi=72,
             title='This is a title',
             sub_title='And this a subtitle',
             x_label='this is x label',
             y_label='and this y',
             legend=False,
             x_scale='log',
             y_scale='linear',
             x_limit=12,
             y_limit=[1,21])


def box_full(df):

    ast.box(data=df,
            x='A',
            y='even',
            hue='odd',
            style='astetik',
            dpi=72,
            title='This is a title',
            sub_title='And this a subtitle',
            x_label='this is x label',
            y_label='and this y',
            legend=False,
            x_scale='log',
            y_scale='symlog',
            x_limit=1,
            y_limit=[1, 21])


def violin_full(df):

    ast.violin(data=df,
               x='A',
               y='even',
               hue='odd',
               split=False,
               style='astetik',
               dpi=72,
               title='This is a title',
               sub_title='And this a subtitle',
               x_label='this is x label',
               y_label='and this y',
               legend=False,
               x_scale='log',
               y_scale='symlog',
               x_limit=1,
               y_limit=[1, 21])


def strip_full(df):

    ast.strip(data=df,
              x='A',
              y='even',
              hue='odd',
              jitter=5,
              dodge=True,
              style='astetik',
              dpi=72,
              title='This is a title',
              sub_title='And this a subtitle',
              x_label='this is x label',
              y_label='and this y',
              legend=False,
              x_scale='log',
              y_scale='symlog',
              x_limit=[10,20],
              y_limit=[1,21])


def count_full(df):

    ast.count(data=df,
              x='cats',
              style='astetik',
              dpi=72,
              title='This is a title',
              sub_title='And this a subtitle',
              x_label='this is x label',
              y_label='and this y',
              legend=False,
              x_scale='log',
              y_scale='symlog',
              x_limit=[10, 20],
              y_limit=[1, 21])


def bars_full(df):

    ast.bargrid(data=df,
                x='cats',
                y='B',
                hue='odd',
                row='even',
                col='other',
                style='astetik',
                dpi=72,
                title='This is a title',
                sub_title='And this a subtitle',
                x_label='this is x label',
                y_label='and this y',
                legend=False,
                x_scale='log',
                y_scale='symlog',
                x_limit=[10, 20],
                y_limit=[1, 21])


def overlap_full(df):

    ast.overlap(data=df,
                x='A',
                y='B',
                label_col='cats',
                sort=True,
                transform_func='max',
                style='astetik',
                dpi=72,
                title='This is a title',
                sub_title='And this a subtitle',
                x_label='this is x label',
                y_label='and this y',
                legend=False,
                x_scale='log',
                y_scale='symlog',
                x_limit=[10, 20],
                y_limit=[1, 21])


def multikde_full(df):

    ast.multikde(data=df,
                 x='A',
                 label_col='cats',
                 sort=True,
                 transform_func='first',
                 style='astetik',
                 dpi=72,
                 title='This is a title',
                 sub_title='And this a subtitle',
                 x_label='this is x label',
                 y_label='and this y',
                 legend=False,
                 x_scale='log',
                 y_scale='symlog',
                 x_limit=[10,20],
                 y_limit=[1,21])

def compare_full(df):

    ast.compare(data=df,
                x='A',
                y='B',
                label_col='cats',
                sort=True,
                transform_func='first',
                style='astetik',
                dpi=72,
                title='This is a title',
                sub_title='And this a subtitle',
                x_label='this is x label',
                y_label='and this y',
                legend=False,
                x_scale='log',
                y_scale='symlog',
                x_limit=[10, 20],
                y_limit=[1, 21])


def multicount_full(df):

    ast.multicount(data=df,
                   x='A',
                   hue='cats',
                   col='other',
                   row='odd',
                   style='astetik',
                   dpi=72,
                   title='This is a title',
                   sub_title='And this a subtitle',
                   x_label='this is x label',
                   y_label='and this y',
                   legend=False,
                   x_scale='log',
                   y_scale='symlog',
                   x_limit=[10, 20],
                   y_limit=[1, 21])


# create the dataset
df = create_data()

# run table tests
test_tables(df)

# run simple plot tests
# test_simple_minimal(df)

# test plots with parameters
corr_full(df)
kde_full(df)
hist_full(df)
pie_full(df)
swarm_full(df)
scat_full(df)
line_full(df)
grid_full(df)
box_full(df)
violin_full(df)
strip_full(df)
count_full(df)
bars_full(df)
overlap_full(df)
multikde_full(df)
compare_full(df)
multicount_full(df)
