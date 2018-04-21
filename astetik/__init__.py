# PLOTS
from .plots.corr import corr
from .plots.hist import hist
from .plots.kde import kde
from .plots.pie import pie
from .plots.swarm import swarm
from .plots.scat import scat
from .plots.line import line
from .plots.grid import grid
from .plots.box import box
from .plots.violin import violin
from .plots.strip import strip
from .plots.count import count
from .plots.bars import bars
from .plots.overlap import overlap
from .plots.multikde import multikde
from .plots.compare import compare
from .plots.multicount import multicount
from .plots.bar1 import bar1
from .plots.animate import Animation
# from .plots.words import words


# TABLES
from .tables.ols import ols
from .tables.table import table
from .tables.text import text
# from .tables.timeseries import timeseries

from .utils.transform import boolcols_to_cat

__version__ = "1.9.1"
