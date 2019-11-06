from logs import logDecorator as lD 
import jsonref, pprint
from lib.databaseIO import pgIO

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
from ast import literal_eval as make_tuple

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
   patientsFilter = '../data/intermediate/filtered_patients.pkl'
   visitsFilter = '../data/intermediate/filtered_visits.pkl'
   diagnoses_dsmno = pd.read_csv('../data/raw_data/dsmno_regex.csv')

   def getData(self, query, columns=None, saveData=True, savePath='../data/intermediate', saveName='temp'):
       
        data = pgIO.getAllData(query, dbName = self.dbName)
        df = pd.DataFrame(data)
        if columns != None: df.columns = columns
        if saveData:
            if not os.path.exists(savePath):
                os.makedirs(savePath)
            dataOut.to_pickle(os.path.join(savePath,saveName+'.pkl'))
            print(saveName+'.pkl saved.')
        return dfmake

   def PullData(self, query, columns, saveData=True, savePath='../data/intermediate', saveName='temp'):
        '''Function for pulling from the database
        [description]
        Arguments:
            query {string} -- PostgreSQL query to be sent to the server.
            columns {list} -- List of strings corresponding to the column names.
        Returns:
            Output {pandas DataFrame} -- Returns output data.
        '''
        # Iterator for query
        dataIterator = pgIO.getDataIterator(query, dbName = self.dbName, chunks=1000)
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


@lD.log(logBase + '.getPatientCohort')
def getPatientCohort(logger, disease_cat):
    q = Database()
    cohort_dsm = make_tuple(diagnoses_dsmno.loc[diagnoses_dsmno['disorders']==disease_cat,'dsmno'].item())
    cohort_query = f"""select
        distinct pd.patientid, pd.typepatientid, tp.days
    from
        rwe_version1_2.pdiagnose pd, rwe_version1_2.typepatient as tp
    where pd.typepatientid = tp.typepatientid
        and pd.patientid in (
            select
                tp.patientid
            from
                rwe_version1_2.typepatient tp,
                rwe_version1_2.meds meds, 
                rwe_version1_2.pdiagnose pd
            where
                tp.typepatientid = meds.typepatientid
                and tp.typepatientid = pd.typepatientid
            group by
                tp.patientid,
                pd.dsmno, 
                meds.medication
            having
                max(tp.days) - min(tp.days) >= 120
                and count(distinct tp.typepatientid) >= 3 
                and cast(pd.dsmno as text) in {cohort_dsm}
                )
            and cast(pd.dsmno as text) in {cohort_dsm}
        """
    data = q.PullData(cohort_query, 
                    ['PatientID', 'VisitID', 'Days'],
                    saveName='filtered_patients')
    print(data.head())
    return data

@lD.log(logBase + '.getDemographics')
def getDemographics(logger, patientList=None):
    
    q = Database()
    # if patientList == None:
    #     patientList = pickle.load(open(q.patientsFilter, 'rb'))['PatientID'].unique()
    patientTuple = tuple(patientList)

    query = f'''
        select bg.patientid, bg.sex, bg.race, temp.age
        from rwe_version1_2.background bg
        left join ( select tp.patientid, max(tp.age) as age
                from rwe_version1_2.typepatient tp
                where tp.patientid in {patientTuple}
                group by tp.patientid
        ) temp on bg.patientid = temp.patientid
        where bg.patientid in {patientTuple}
    '''
    data = q.PullData(query, ['PatientID','Sex', 'Race', 'Age'], saveName='patient_demographics')

    # Clean Race/Sex using Filter Tables

    print(data.head())
    print('Data was pulled successfully.')
    
    return data

@lD.log(logBase + '.getTripsData')
def getTripsData(logger, visit_list=None):
    '''This function's method of Select Distinct works faster than separate indexing.
    '''
    
    q = Database()
    # if visit_list == None:
        # visit_list = pickle.load(open(q.visitsFilter, 'rb'))['VisitID'].unique()
    visitTuple = tuple(visit_list)

    # Should use group by tp.patientid, tp.typepatientid, tp.days
    # and (max(cgi.severity) + min(cgi.severity))/ 2 
    # but will need to make it a subquery because i dont want to group by for the medications table.
    query = f"""select distinct on (tp.patientid, tp.typepatientid, tp.days, meds.medication )
                    tp.patientid, tp.typepatientid, tp.days, tp.visit_type, 
                    cgi.severity, meds.medication, meds.dose, meds.regimen,
                    pd.diagnosis, pd.dsmno
                from 
                    rwe_version1_2.typepatient tp, 
                    rwe_version1_2.cgi cgi, 
                    rwe_version1_2.meds meds,
                    rwe_version1_2.pdiagnose pd
                where tp.typepatientid = cgi.typepatientid
                    and tp.typepatientid = meds.typepatientid
                    and tp.typepatientid = pd.typepatientid
                    and tp.typepatientid in {visitTuple}
            """
    data = q.PullData(query, 
                    ['PatientID','VisitID','Days', 'VisitType', 'CGI','Medication','Dose','Regimen', 'Diagnosis','DSMNo'], 
                    saveName='visits_data')

    # Recode dsmno's into disease categories. 
    for i, (disorders, counts, regex, dsmno) in diagnosis_dsmno.iterrows():
        if disorders != 'others':
            data.loc[data.DSMNo.str.contains(regex), 'DiseaseCat'] = disorders

    data.loc[data.DiseaseCat.str.contains('[0-9]|code'), 'DiseaseCat'] = 'others'

    print(data.head())
    print('Data was pulled successfully.')
    
    return data

@lD.log(logBase + '.testQuery')
def testQuery(logger):
    q = Database()
    query = f"""select
        pd.patientid, count(distinct pd.typepatientid), count(distinct tp.days)
    from
        rwe_version1_2.pdiagnose pd, rwe_version1_2.typepatient as tp
    where pd.typepatientid = tp.typepatientid
    group by pd.patientid        
        """
    data = q.PullData(query, 
                    columns=['PatientID','VisitsCount','DaysCount'],
                    saveName='test')
    print(data.head())
    return data

@lD.log(logBase + '.main')
def main(logger, resultsDict):
    print('Starting..')
    ## get pt/visit/days data ##
    disease_cat = 'major depressive disorders'
    data = getPatientCohort(disease_cat)
    # data = pickle.load(open('../data/intermediate/filtered_patients.pkl','rb'))
    # data = pickle.load(open('../data/intermediate/cohort_visitsdays.pkl','rb'))
    
    ## get List of unique patients and their demographics data ## 
    patient_list = data.PatientID.unique()
    patients_data = getDemographics(patient_list)
    # patients_data = pickle.load(open('../data/intermediate/patient_demographics.pkl','rb'))

    ## get TRIPS:cgi/meds/diagnosis data for all patients in list ##
    visit_list = data.VisitID.unique()
    vists_data = getTripsData(visit_list) 
    # vists_data = pickle.load(open('../data/intermediate/visitsdata.pkl','rb'))

    print('Done!')