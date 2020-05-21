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
from .plots.bargrid import bargrid
from .plots.overlap import overlap
from .plots.multikde import multikde
from .plots.compare import compare
from .plots.multicount import multicount
from .plots.bar import bar
from .plots.bartwo import bartwo
from .plots.animate import Animation
from .plots.world import world
from .plots.regs import regs
from .plots.roc import roc
# from .plots.words import words

from .utils.gui import toggle as toggle
from .utils.gui import warning as warning

# TABLES
from .tables.table import table
from .tables.text import text
# from .tables.timeseries import timeseries

try:
    del plots
except:
    pass

try:
    del style
except:
    pass

try:
    del tables
except:
    pass

try:
    del utils
except:
    pass
