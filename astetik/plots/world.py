import pkg_resources
import numpy as np
import pandas as pd
from geonamescache import GeonamesCache

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

from ..utils.exceptions import MissingImport
from ..utils.country_code import country_to_code
from ..style.formats import _thousand_sep
from ..utils.outliers import outliers

shapefile = pkg_resources.resource_filename(__name__, '../extras/countries')


def world(data,
          area_col,
          value_col,
          area_to_code=False,
          bin_mode='linear',
          log=None,
          title='',
          value_col_to_title=True,
          descripton='',
          num_colors=9,
          palette='Reds',
          filter_outlier=False):

    '''WORLD MAP PLOT

    Takes in data where one column is the values and another is either
    country or 3-alphabet country code according to ISO standard.

    USE
    ===

    world(data=emission,
          area_col='area',
          value_col=1999,
          area_to_code=True,
          title='Emission Intensity of Food Production (co2/kg)',
          value_col_to_title=False,
          palette='Reds',
          num_colors=9)


    area_col :: the column where is either country name or country code
    value_col :: the column with the values

    area_to_code :: must be True if area is not 3-alphabet code
    num_colors :: the number of colors to be used to describe intensity

    value_to_col_title :: Useful when the column is a year and you want to
                          have it shown in the title.

    log :: if true will use log values instead. Only works when bin_mode is
           linear.

    '''

    data = data.copy(deep=True)

    if filter_outlier == True:
        data = outliers(data, value_col)

    if value_col_to_title == True:
        title = title + ' {}'.format(value_col)

    descripton.strip()

    if area_to_code == True:
        data[area_col] = data[area_col].apply(country_to_code)
        data.set_index(area_col, inplace=True)

    if data.index.name != area_col:
        data.set_index(area_col, inplace=True)

    # filter data based on geo codes
    gc = GeonamesCache()
    iso3_codes = list(gc.get_dataset_by_key(gc.get_countries(), 'iso3').keys())
    data = data.loc[iso3_codes]
    data = data[~data[value_col].isna()]
    data[value_col] = data[value_col].astype(int)

    # set plot stuff
    values = data[value_col].dropna()

    if log == True:
        values = np.log1p(values)
        data[value_col] = np.log(data[value_col])

    if bin_mode == 'linear':
        bins = np.linspace(values.min(), values.max(), num_colors)
    elif bin_mode == 'quantile':
        bins = np.nanpercentile(values, np.arange(0,
                                                  100,
                                                  num_colors))
    cm = plt.get_cmap(palette)
    scheme = [cm(i / num_colors) for i in range(num_colors)]

    # create the bin column
    data['temp'] = pd.cut(data[value_col], bins)
    cat_columns = data.select_dtypes(['category']).columns
    data['bin'] = data[cat_columns].apply(lambda x: x.cat.codes)
    data.drop('temp', axis=1, inplace=True)

    p = plt.figure(figsize=(17, 12))
    p.patch.set_facecolor('white')

    ax = p.add_subplot(111, frame_on=False)
    p.suptitle(title,
               color='grey',
               weight='bold',
               fontsize=26,
               y=.85)

    try:
        from mpl_toolkits.basemap import Basemap
        m = Basemap(lon_0=0, projection='robin')
    except ImportError:
        raise MissingImport("Install Basemap >> pip install git+https://github.com/matplotlib/basemap.git")

    m.drawmapboundary(color='w')

    m.readshapefile(shapefile, 'units', color='#444444', linewidth=.2)
    for info, shape in zip(m.units_info, m.units):
        iso3 = info['ADM0_A3']
        if iso3 not in data.index:
            color = '#dddddd'
        else:
            color = scheme[data.loc[iso3]['bin'].astype(int)]

        patches = [Polygon(np.array(shape), True)]
        pc = PatchCollection(patches)
        pc.set_facecolor(color)
        ax.add_collection(pc)

    # Cover up Antarctica so legend can be placed over it.
    ax.axhspan(0, 1000 * 1800, facecolor='w', edgecolor='w', zorder=2)

    # Draw color legend.
    ax_legend = p.add_axes([0.35, 0.24, 0.3, 0.03], zorder=3)
    cmap = mpl.colors.ListedColormap(scheme)
    cb = mpl.colorbar.ColorbarBase(ax_legend,
                                   cmap=cmap,
                                   ticks=bins,
                                   boundaries=bins,
                                   orientation='horizontal')

    cb.ax.set_xticklabels([str(round(i, 1)) for i in bins], rotation=45, ha='right')

    plt.annotate(descripton, xy=(-.8, -3.2), size=14, xycoords='axes fraction')

    _thousand_sep(p, ax)
