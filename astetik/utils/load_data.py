import pandas as pd


def read():

    def csv(filename):
        out = pd.read_csv(filename, sep=',', encoding='latin-1', error_bad_lines=True)
        return out
