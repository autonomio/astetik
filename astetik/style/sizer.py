from math import sqrt
from ..utils.transform import rescaler


def _sizer(data):

    sizes = data.apply(sqrt)
    sizes = rescaler(sizes, 10)

    return sizes
