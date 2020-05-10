def _legend(x, legend, legend_labels, legend_position):

    import matplotlib.pyplot as plt

    if legend:
        if legend_labels != None:
            x = legend_labels

        if len(legend_position) == 0:
            plt.legend(x, loc=1, ncol=1, bbox_to_anchor=(1.25, 1.0))
        else:
            plt.legend(x, loc=legend_position[0], ncol=legend_position[1])
