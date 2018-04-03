def default_colors():

    return '#696969'


def params():

    param_dic = {'fig_height': 6.6,
                 'fig_width': 10}

    return param_dic

def styles(dpi):

    default_color = default_colors()

    label_sizes = 12

    style_dic = {
            # FONT
            'font.size': 12,
            'font.family': 'Verdana',
            'font.stretch': 'normal',
            'font.style': 'normal',
            'font.variant': 'normal',
            'font.weight': 'normal',

            # AXES
            'axes.linewidth': 1,        # spine thickness
            'axes.xmargin': 0.05,       # spine distance from grid
            'axes.ymargin': 0.05,

                # AXES TITLE
                'axes.titlesize': 11.0,
                'axes.titlepad': 10.0,
                'axes.titleweight': 'normal',

            # FIGURE
            'figure.dpi': dpi,
            'figure.frameon': False,

            # GRID
            'axes.grid': True,          # turn grid lines on and off
            'grid.alpha': .1,
            'grid.color': 'grey',
            'grid.linewidth': 1,
            'grid.linestyle': '-',

            # LINES
            #'lines.antialiased': True,
            'lines.linestyle': '-',
            'lines.linewidth': 0.75,           # plot element outlines
            'lines.color': '#000000',

            # LEGEND
            'legend.framealpha': 1,
            'legend.frameon': True,
            'legend.handleheight': 2.5,
            'legend.handlelength': 2.5,
            'legend.loc': 'upper right',
            'legend.labelspacing': 0.8,
            'legend.borderpad': 0.5,
            'legend.columnspacing': 2.0,

            # SAVEFIG
            'savefig.bbox': None,
            'savefig.directory': '~',
            'savefig.dpi': 'figure',
            'savefig.edgecolor': 'white',
            'savefig.facecolor': 'white',
            'savefig.format': 'png',
            'savefig.frameon': False,
            'savefig.jpeg_quality': 95,
            'savefig.orientation': 'portrait',
            'savefig.pad_inches': 0.1,

            # # # TICKS START

            # X-TICK
            'xtick.alignment': 'center',
            'xtick.bottom': True,
            'xtick.color': default_color,
            'xtick.direction': 'out',
            'xtick.labelbottom': True,
            'xtick.labelsize': label_sizes,
            'xtick.labeltop': True,

                # MAJOR X-TICK
                'xtick.major.bottom': True,
                'xtick.major.pad': 7.0,
                'xtick.major.size': 0.0,
                'xtick.major.top': False,
                'xtick.major.width': 0.0,

                # MINOR X-TICK
                'xtick.minor.bottom': True,
                'xtick.minor.pad': 3.4,
                'xtick.minor.size': 0.0,
                'xtick.minor.top': True,
                'xtick.minor.visible': False,
                'xtick.minor.width': 0.5,
                'xtick.top': False,

            # Y-TICK
            'ytick.alignment': 'center_baseline',
            'ytick.color': default_color,
            'ytick.direction': 'out',
            'ytick.labelleft': True,
            'ytick.labelright': False,
            'ytick.labelsize': label_sizes,
            'ytick.left': True,

                # MAJOR Y-TICK
                'ytick.major.left': True,
                'ytick.major.pad': 15.0,
                'ytick.major.right': False,
                'ytick.major.size': 0.0,
                'ytick.major.width': 11.0,

                # MINOR Y-TICK
                'ytick.minor.left': False,
                'ytick.minor.pad': 3.4,
                'ytick.minor.right': False,
                'ytick.minor.size': 6.0,
                'ytick.minor.visible': False,
                'ytick.minor.width': 1,
                'ytick.right': False,

            # BOXPLOT SPECIFIC
            'boxplot.notch': False,
            'boxplot.patchartist': False,
            'boxplot.showbox': True,
            'boxplot.showcaps': False,
            'boxplot.showfliers': False,
            'boxplot.showmeans': False,
            'boxplot.vertical': False,

    }

    return style_dic
