import pandas as pd

import pkg_resources

countries = pkg_resources.resource_filename(__name__, '../extras/countries.csv')
countries = pd.read_csv(countries)


def code_to_country(code):

    out = countries.set_index('alpha-3')
    out = out['name'].to_dict()

    try:
        return out[code]
    except:
        return 'UNKNOWN_CODE'


def country_to_code(country):

    out = countries.set_index('name')
    out = out['alpha-3'].to_dict()

    try:
        return out[country]
    except:
        return 'UNKNOWN_COUNTRY'
