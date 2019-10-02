from logs import logDecorator as lD 
import jsonref, pprint
from lib.databaseIO import pgIO

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import pickle

config = jsonref.load(open('../config/config.json'))
logBase = config['logging']['logBase'] + '.modules.module1.module1'
projConfig = jsonref.load(open('../config/modules/module1.json'))

@lD.log(logBase + '.getData')
def getData(logger):
    '''get data from mindlinc
    
    This function gets some data from the mindlinc database.
    
    Parameters
    ----------
    logger : {logging.Logger}
        The logger used for logging error information
    '''
    dbName = projConfig['inputs']['dbName']
    dbVersion = projConfig['inputs']['dbVersion']
    cohortWindow = [0, 1000]
    daysWindow = [0, 365]

    # get CGI data - target
    cgi_query = '''
                SELECT distinct on (severity, {0}.cgi.patientid, days) severity, {0}.cgi.patientid, days
                from 
                (
                    select * from {0}.typepatient
                        where age is not null 
                        and patientid >= {1} and patientid <= {2}
                        and days >= {3} and days <= {4} 
                ) as temp1
                inner join {0}.cgi
                on {0}.cgi.typepatientid = temp1.typepatientid  
                '''.format( dbVersion, cohortWindow[0], cohortWindow[1], daysWindow[0], daysWindow[1])
    cgi_data = pgIO.getAllData(cgi_query, dbName=dbName)
    cgi_df = pd.DataFrame(cgi_data, columns=['cgi', 'patientID', 'days'])
    if not os.path.exists('../data/raw_data/cgi.pkl'): cgi_df.to_pickle('../data/raw_data/cgi.pkl')

    # get meds data - Features
    meds_query = '''
                SELECT distinct on (medication, {0}.meds.patientid, days) medication, {0}.meds.patientid, days from 
                (
                    select * from {0}.typepatient
                        where age is not null 
                        and patientid >= {1} and patientid <= {2}
                        and days >= {3} and days <= {4} 
                ) as temp1
                inner join {0}.meds
                on {0}.meds.typepatientid = temp1.typepatientid    
                '''.format( dbVersion, cohortWindow[0], cohortWindow[1], daysWindow[0], daysWindow[1])
    meds_data = pgIO.getAllData(meds_query, dbName=dbName)
    meds_df = pd.DataFrame(meds_data, columns=['meds', 'patientID', 'days'])
    if not os.path.exists('../data/raw_data/meds.pkl'): meds_df.to_pickle('../data/raw_data/meds.pkl')

    cgiOut = cgi_df.drop('days', axis=1).groupby(['patientID'], sort=False, as_index=False)['cgi'].mean()

    medsOut = meds_df.drop('days', axis=1).groupby('patientID', sort=False, as_index=False).agg(lambda x: list(x.unique()))
    medsOut = medsOut['meds'].str.join('|').str.get_dummies().join(medsOut[['patientID']])

    dataOut = pd.merge(medsOut, cgiOut, how='inner', on='patientID')
    dataOut.set_index('patientID', inplace=True)
    if not os.path.exists('../data/raw_data/combined.pkl'): dataOut.to_pickle('../data/raw_data/combined.pkl')
    # print(dataOut.describe())

    return dataOut


@lD.log(logBase + '.main')
def main(logger, resultsDict):
    '''main function for module1
    
    This function finishes all the tasks for the
    main function. This is a way in which a 
    particular module is going to be executed. 
    
    Parameters
    ----------
    logger : {logging.Logger}
        The logger used for logging error information
    '''

    df = getData()
    x_train, x_test, y_train, y_test = train_test_split(df.iloc[:,:-1], df.iloc[:,-1], test_size=0.25, random_state=2019)
    model = LinearRegression()

    model.fit(x_train, y_train)
    r_sq = model.score(x_test, y_test)
    print(r_sq)
    print(model.intercept_)
    print(model.coef_)
    print('-'*30)

    y_pred = model.predict(x_test)
    # plt.scatter(x_test, y_test, color='black')
    plt.plot(x_test, y_pred, color='blue', linewidth=3)
    # plt.show()
    plt.savefig('../results/fig1.png')

    return

