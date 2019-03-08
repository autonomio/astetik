def oned(data):

    '''1-d visualization for 1-d random sequences

    EXAMPLE
    =======

    test = random.sample(list(range(65000)),300)
    randhist(test)

    '''

    import matplotlib.pyplot as plt

    plt.figure(figsize=(12, 1))
    plt.eventplot(data,
                  orientation='horizontal',
                  colors='black',
                  linewidths=.8)
    plt.axis('off')
    plt.show()
