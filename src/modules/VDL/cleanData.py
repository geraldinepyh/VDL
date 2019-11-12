import os
import pandas as pd
import numpy as np
import pickle

def cleanRace(df):
    df.loc[df.Race=='','Race'] = 'other'
    df.loc[df.Race.str.startswith('multiracial'),'Race'] = 'mixed race'
    df.loc[df.Race.str.startswith('white'),'Race'] = 'white'
    df.loc[df.Race.str.startswith('black'),'Race'] = 'black'
    df.loc[df.Race.str.startswith('asian'),'Race'] = 'asian'
    df.loc[df.Race.str.startswith('hispanic'),'Race'] = 'hispanic'
    df.loc[df.Race.str.contains('or'),'Race'] = 'other'
    df.loc[df.Race.str.contains('other'),'Race'] = 'other'
    df.loc[df.Race.str.contains('pacific'),'Race'] = 'native american'
    df.loc[df.Race.str.contains('hawaiian'),'Race'] = 'native american'
    df.Race = df.Race.replace({'^[a-z]{1}$|[0-9]':'other',
                        'mexican|puerto rican|jamaican|dominican' : 'hispanic',
                        'caucasian' : 'white',
                        'african american' : 'black',
                        'americanindianalaskannative': 'native american',
                        'amer indian/alaskan native' : 'native american',
                        'mixed race|multi raci|biracial|multiracial' : 'mixed race',
                        'unable to obtain|other race|declined to specify|unknown|otherotherotherother-other|other not elsewhere classified|declined|patient unavailable':'other'
                        },
                        regex=True)
    return df

def cleanSex(df):
    sexes=['M','F'] # not very progressive, but
    df.loc[~df.Sex.isin(sexes),'Sex'] = 'Unknown'
    return df

def cleanDemogs(in_file,out_file):
    demogs = pickle.load(open(in_file,'rb'))
    df = cleanRace(demogs)
    df = cleanSex(df)

    with open(out_file, 'wb') as f:
        pickle.dump(df, f)

def cleanVisits(in_file,out_file):
    # create disease categories 
    visits_data = pickle.load(open(in_file,'rb'))
    diagnosis_dsmno = pd.read_csv('../data/raw_data/disorders_dsmno.csv')

    visits_data['DiseaseCat'] = 'others'
    # use masking to map for each dsm (replace entire string based on substring match)
    for i, (disorders, counts, regex, dsmno) in diagnosis_dsmno.iterrows():
        if disorders != 'others':
            visits_data.loc[visits_data.DSMNo.str.contains(regex), 'DiseaseCat'] = disorders

    # visits_data.loc[visits_data.DiseaseCat.str.contains('[0-9]|code'), 'DiseaseCat'] = 'others'
    print(visits_data.DiseaseCat.unique())

    with open(out_file,'wb') as f:
        pickle.dump(visits_data, f) 


def main(resultsDict):

    ### Cleaning Demographics ###
    # in_file = '../data/intermediate/patient_demographics.pkl'
    # out_file = '../data/intermediate/patient_demographics2.pkl'
    # cleanDemogs(in_file, out_file)

    ### Cleaning Visits Data ###
    in_file = '../data/intermediate/visits_data.pkl'
    out_file = '../data/intermediate/visits_data2.pkl'
    cleanVisits(in_file, out_file)