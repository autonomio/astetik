"""Agent entrypoint: explicit scientific specifications compile into evidence."""

from ._catalog import DEFAULT_OPTIONS as DEFAULT_OPTIONS
from ._catalog import KINDS as KINDS
from ._catalog import SUPPORTED_OPTIONS as SUPPORTED_OPTIONS
from ._catalog import catalog as catalog
from ._catalog import select as select
from ._conveniences import (
    animate as animate,
)
from ._conveniences import (
    association as association,
)
from ._conveniences import (
    bar as bar,
)
from ._conveniences import (
    bargrid as bargrid,
)
from ._conveniences import (
    bartwo as bartwo,
)
from ._conveniences import (
    box as box,
)
from ._conveniences import (
    compare as compare,
)
from ._conveniences import (
    comparison as comparison,
)
from ._conveniences import (
    corr as corr,
)
from ._conveniences import (
    count as count,
)
from ._conveniences import (
    grid as grid,
)
from ._conveniences import (
    hist as hist,
)
from ._conveniences import (
    kde as kde,
)
from ._conveniences import (
    line as line,
)
from ._conveniences import (
    longitudinal as longitudinal,
)
from ._conveniences import (
    multicount as multicount,
)
from ._conveniences import (
    multikde as multikde,
)
from ._conveniences import (
    oned as oned,
)
from ._conveniences import (
    overlap as overlap,
)
from ._conveniences import (
    pie as pie,
)
from ._conveniences import (
    regs as regs,
)
from ._conveniences import (
    roc as roc,
)
from ._conveniences import (
    scat as scat,
)
from ._conveniences import (
    strip as strip,
)
from ._conveniences import (
    swarm as swarm,
)
from ._conveniences import (
    table as table,
)
from ._conveniences import (
    text as text,
)
from ._conveniences import (
    twod as twod,
)
from ._conveniences import (
    violin as violin,
)
from ._conveniences import (
    world as world,
)
from ._entry import plot as plot
from ._entry import render as render
from ._replay import replay as replay

__all__ = [
    'animate',
    'association',
    'bar',
    'bargrid',
    'bartwo',
    'box',
    'catalog',
    'compare',
    'comparison',
    'corr',
    'count',
    'grid',
    'hist',
    'kde',
    'line',
    'longitudinal',
    'multicount',
    'multikde',
    'oned',
    'overlap',
    'pie',
    'plot',
    'regs',
    'render',
    'replay',
    'roc',
    'scat',
    'select',
    'strip',
    'swarm',
    'table',
    'text',
    'twod',
    'violin',
    'world',
]
