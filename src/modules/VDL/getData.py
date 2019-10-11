from logs import logDecorator as lD 
import jsonref, pprint
from lib.databaseIO import pgIO

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle

config = jsonref.load(open('../config/config.json'))
logBase = config['logging']['logBase'] + '.modules.VDL.getData'

class Database:
   '''Database static (stateful) class
   Used to manage database session details and contains common database
   pulling code.
   Variables:
       dbName {string} -- Name of the database
       dbVersion {string} -- Operating schema (representing the version
                             of database) to be used
   '''
   projConfig = jsonref.load(open('../config/modules/getData.json'))
   dbName    = projConfig['inputs']['dbName']
   dbVersion = projConfig['inputs']['dbVersion']

   def PullData(self, query, columns, saveData=True, savePath='../data/intermediate', saveName='temp'):
        '''Function for pulling from the database
        [description]
        Arguments:
            query {string} -- Postgre query to be sent to the server.
            columns {list} -- List of strings corresponding to the column
                                names.
        Returns:
            Output -- Returns output data.
        '''
        # Iterator for query
        dataIterator = pgIO.getDataIterator(query, dbName = Database.dbName, chunks=1000)
        # Run through iterator, appending to buffer
        dataBuffer = []
        for data in dataIterator:
            dataBuffer += data
        # Convert data in bufer to dataframe
        dataOut = pd.DataFrame(dataBuffer, columns=columns)

        if saveData:
            if not os.path.exists(savePath):
                os.makedirs(savePath)
            dataOut.to_pickle(os.path.join(savePath,saveName+'.pkl'))
            print(saveName+'.pkl saved.')

        return dataOut

@lD.log(logBase + '.testQuery')
def testQuery(logger):
    q = Database()
    query = f'''
        select pd.patientid, pd.typepatientid, pd.diagnosis
        from rwe_version1_2.pdiagnose pd
        where patientid = 9 
        limit 20
    '''
    data = q.PullData(query, ['PatientID','VisitID', 'Diagnosis'], saveData=False)
    print(data.head())
    print('Data was pulled successfully.')
    
    return 



@lD.log(logBase + '.prepData')
def prepData(logger):
    q = Database()
    cohort_dsm = ('296.20', '296.21',     '296.22',    '296.23',    '296.24',    '296.25',
                '296.26',    'F32.0',    'F32.1',    'F32.2',    'F32.4',
                'F32.5',    'F32.81',    'F32.89',    '296.30',    '296.31',
                '296.32',    '296.33',    '296.34', '296.35',    '296.36',
                'F33.0',    'F33.1',    'F33.2',    'F33.40',    'F33.41',
                'F33.42',    'F33.8',    '311',    'F32.9',    'F33.9',
                '300.4',    'F34.1')
    cohort_query = f"""select
        distinct pd.patientid, pd.typepatientid, tp.days
    from
        rwe_version1_2.pdiagnose pd, rwe_version1_2.typepatient as tp
    where pd.patientid in (
        select
            tp.patientid
        from
            rwe_version1_2.typepatient as tp,
            rwe_version1_2.meds as meds
        where
            tp.typepatientid = meds.typepatientid
        group by
            tp.patientid,
            meds.medication
        having
            max(tp.days) - min(tp.days) >= 120
            and count(distinct tp.typepatientid) >= 3 )
    and
        cast(pd.dsmno as text) in {cohort_dsm}
        and pd.primary_dx = true
        """
    data = q.PullData(cohort_query, 
                    ['PatientID', 'VisitID', 'Days'],
                    saveName='mdd_visitsdays')
    data.head()
    return 


@lD.log(logBase + '.main')
def main(logger, resultsDict):
    print('Starting..')
    prepData()
    print('Done!')