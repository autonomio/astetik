import numpy as np


def randomcolor():

    ''' PICKS COLORS RANDOMLY

    '''

    colors = []
    for i in range(20):
        colors.append(list((np.random.randint(0, 255, 3) / 255)))

    return colors
