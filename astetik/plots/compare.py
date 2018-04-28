import seaborn as sns
import pandas as pd

from ..style.template import _header
from ..utils.transform import _groupby


def compare(data,
            x,
            y,
            label_col,
            sort=False,
            transform_func=False,
            palette='default',
            style='astetik',
            dpi=72,
            title='',
            sub_title='',
            x_label='',
            y_label='',
            legend=True,
            x_scale='linear',
            y_scale='linear',
            x_limit=None,
            y_limit=None,
            save=False):

    '''COMPARE PLOT

    This needs to have a single row per entity, for example a patient
    or a state and so forth. It will be best if the columns are
    normalized data, percentages, or something similar.

   Inputs: at least 3
   Features: At least two continuous and one categorical.

    1. USE
    ======
    ast.compare(data=patients,
                x='hospital_stays',
                y=['died_hospital','died_out'],
                label_col='religion',
                transform=True)

    1. USE
    ======
    ast.box(data=patients,
            x='insurance',
            y='age',
            hue='expired')

    2. PARAMETERS
    =============
    2.1 INPUT PARAMETERS
    --------------------
    data :: a pandas dataframe

    x :: the main feature (continuous)

    y :: two or more features in a list (continuous)

    label_col :: the label column (categorical)

    --------------------
    2.2. PLOT PARAMETERS
    --------------------
    sort :: True for ascending and False for descending

    transform_func :: If not false, the selected function such as
                      'mean' will be used to group by the label_col.
                      Available functions:
                        - 'median'
                        - 'mean'
                        - 'first'
                        - 'last',
                        - 'std',
                        - 'mode',
                        - 'max',
                        - 'min',
                        - 'sum',
                        - 'random'

    ----------------------
    2.3. COMMON PARAMETERS
    ----------------------
    palette :: One of the astetik palettes:
                'default'
                'colorblind'
                'blue_to_red'
                'blue_to_green'
                'red_to_green'
                'green_to_red'
                'violet_to_blue'
                'brown_to_green'
                'green_to_marine'

                Or use any cmap, seaborn or matplotlib
                color or palette code, or hex value.

    style :: Use one of the three core styles:
                'astetik'     # white
                '538'         # grey
                'solarized'   # sepia

              Or alternatively use any matplotlib or seaborn
              style definition.

    dpi :: the resolution of the plot (int value)

    title :: the title of the plot (string value)

    sub_title :: a secondary title to be shown below the title

    x_label :: string value for x-axis label

    y_label :: string value for y-axis label

    x_scale :: 'linear' or 'log' or 'symlog'

    y_scale :: 'linear' or 'log' or 'symlog'

    x_limit :: int or list with two ints

    y_limit :: int or list with two ints

    outliers :: Remove outliers using either 'zscore' or 'iqr'
    '''

    if transform_func != False:
        plot_data = _groupby(data, label_col, transform_func)
    else:
        plot_data = data

    if type(y) != type([]):
        y = [y]
    index_cols = y
    index_cols.insert(0, x)

    # HEADER STARTS >>>
    palette = _header(palette,
                      style,
                      n_colors=1,
                      dpi=dpi,
                      fig_height=None,
                      fig_width=None)
    # <<< HEADER ENDS

    # Make the PairGrid
    g = sns.PairGrid(plot_data.sort_values(x, ascending=sort),
                     x_vars=pd.Index(index_cols),
                     y_vars=[label_col],
                     size=10,
                     aspect=.25)

    # Draw a dot plot using the stripplot function
    g.map(sns.stripplot,
          size=10,
          orient="h",
          palette=palette,
          edgecolor="gray")

    g.set(xlabel="", ylabel="")
    titles = index_cols
    for ax, title in zip(g.axes.flat, titles):
        ax.set(title=title)
        ax.xaxis.grid(False)
        ax.yaxis.grid(True)

    sns.despine(left=True, bottom=True)
