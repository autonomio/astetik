import glob
import os
import numpy as np
# EXCEPTIONAL IMPORT #

import matplotlib.pyplot as plt

from IPython.display import clear_output


class Animation():

    '''ANIMATED CHARTS

    Supports dataformat where x and y are compared against each other, and
    label_col provides the title (e.g. year) for each frame in the animation.

    y and x are used for the legend labels when relevant.

    '''

    def __init__(self, data, x, y, label_col, plot_type, filename='animation',
                 dpi=72, palette='default'):

        self.plot_type = plot_type
        self.data = data
        self.x = x
        self.y = y
        self.label_col = label_col
        self.palette = palette
        self.filename = filename
        self.frames = len(data)
        self.dpi = dpi

        # RUNTIME
        self._ = self._create_plots()
        self._ = self._create_gif()

    def _create_plots(self):

        for i in range(self.frames):
            data = np.array([self.data[self.x][i], self.data[self.y][i]]).astype(int)
            self.plot_type(data,
                           labels=[self.x, self.y],
                           palette=self.palette,
                           sub_title=self.data[self.label_col][i],
                           save=True,
                           dpi=self.dpi)
            clear_output()
            plt.show()

    def _create_gif(self):

        gif_name = self.filename
        file_list = glob.glob('astetik_*.png')
        list.sort(file_list, key=lambda x: int(x.split('_')[1].split('.png')[0]))

        with open('image_list.txt', 'w') as file:
            for item in file_list:
                file.write("%s\n" % item)

        os.system('convert @image_list.txt {}.gif'.format(gif_name)) # magick on windows
