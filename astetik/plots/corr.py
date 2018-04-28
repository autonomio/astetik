import warnings
warnings.filterwarnings("ignore")

import numpy as np
import matplotlib
matplotlib.use('Agg')
# ENDS #
import matplotlib.pyplot as plt
import seaborn as sns



from ..style.formats import _thousand_sep
from ..style.titles import _titles
from ..style.template import _header, _footer


def corr(data,
         corr_method='spearman',
         annot=False,
         mask=True,
         line_width=1,
         line_color='black',
         color_grades=5,
         auto_sizing=True,
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

    '''CORRELATION HEATMAP

    This is best used with less than 50 variables in the dataset.
    For best results, column labels should be clear and not too long.

   Inputs: a dataframe with several columns
   Features: Both categorical and continuous features will be used

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

    --------------------
    2.2. PLOT PARAMETERS
    --------------------
    corr_method :: The method that will be used for the correlation:
                    - 'pearson' : standard correlation coefficient
                    - 'kendall' : Kendall Tau correlation coefficient
                    - 'spearman' : Spearman rank correlation

    annotation :: True if each cell will be annotated with the value

    mask :: If set to False, a rectangular shape will be drawn instead
            of a triangular shapeself.

    line_width :: the width of the white lines between each element. Better
                  to set small when there are really many items.

    line_color :: the color of the lines between the elements e.g. 'black'

    auto_sizing :: If not True, then should be int value in inches which is used
                   for both width and height.

    color_grades :: The number of colors/shades to use in total. 5 is default.
                    Generally the best results come with 3 or 5 or 7, but looks
                    better with more colors.

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

    # # # # # PREP STARTS # # # # #
    data = data.corr(method=corr_method)

    if mask == True:
        mask = np.zeros_like(data)
        mask[np.triu_indices_from(mask)] = True
        line_color = 'white'
    else:
        mask = None
    # # # # # PREP ENDS # # # # #

    # HEADER STARTS >>>
    palette = _header(palette,
                      style,
                      n_colors=color_grades,
                      dpi=dpi)

    if auto_sizing == True:
        size = data.shape[0] / 2 + 5

    # PLOT
    p, ax = plt.subplots(figsize=(size, size))

    p = sns.heatmap(data,
                    mask=mask,
                    linewidths=line_width,
                    linecolor=line_color,
                    cmap=palette,
                    annot=annot)

    # HEADER
    _thousand_sep(p, ax)
    _titles(title, sub_title=sub_title)
    _footer(p, x_label, y_label, save=save, tight=False, despine=False)

    p.set_xticklabels(data, rotation=90)
    p.set_yticklabels(data, rotation=0)
