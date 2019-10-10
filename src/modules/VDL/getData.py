from logs import logDecorator as lD 
import jsonref, pprint
from lib.databaseIO import pgIO

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle

class Querier():

    def __init__(self, name, fpath='../data/'):
        self.name = name
        self.fpath = fpath
        self.config = jsonref.load(open('../config/config.json'))
        self.logBase = config['logging']['logBase'] + '.modules.VDL.getData'
        self.projConfig = jsonref.load(open('../config/modules/getData.json'))
        self.data = pd.DataFrame()
    
    def saveData(self, savePath, override=False):

        saveFile = f'{savePath}/{self.name}.pkl'
        if not os.path.exists(saveFile) or override:
            if not os.path.exists(savePath):
                os.makedirs(savePath)
            df.to_pickle(saveFile)
            print(saveFile, 'saved.')
        else:
            print('File already exists. Please specify if you want to override.')

    def getData(self, query, cols=[], saveData=True):

        dbName = self.projConfig['inputs']['dbName']
        dbVersion = self.projConfig['inputs']['dbVersion']
        
        data = pgIO.getAllData(query, dbName=dbName)
        df = pd.DataFrame(data)
        if cols != []: df.columns = cols
        if saveData:
            self.saveData(self.fpath, override=True)
        return df
    
    def filterData(self, filterPath):
        # Assuming filter csv has 2 columns only. 
        # e.g. (Actual_Values, Recoded_Values)

        data_filter = pd.read_csv(filterPath, header=None)
        data_filter_query = tuple([mdd for mdd in data_filter[0]])

        return data_filter_query

@lD.log(logBase + '.prepData')
def prepData(logger):
    mdd_q = Querier(mdd_patients, '../data/temp')
    # full_q = Querier(full_data, '../data/temp')

    # 'Filter' to select my patients of interest. (MDD Patients) 
    # Some other way to provide a list of patientIDs for patients i'm interested in? 
    mdd_filter_query = mdd_q.filterData('../data/raw_data/Filters/data_Filter.csv')
    mdd_query = f"""select
                        distinct pd.patientid
                    from
                        rwe_version1_2.pdiagnose pd
                    inner join (
                        select
                            tp.patientid, meds.medication,min(tp.days),
                            max(tp.days), count(distinct tp.typepatientid)
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
                            and count(distinct tp.typepatientid) >= 3 ) pts on
                        pts.patientid = pd.patientid
                    where
                        cast(pd.dsmno as text) in {mdd_filter_query}
                        and pd.primary_dx = true ; """

    mdd_patients = mdd_q.getData(mdd_query, cols=['PatientID'], savePath='intermediate/mdd_patients')
    mdd_pts_list = tuple([pt for pt in mdd_patients['PatientID']])

    queries = {
        "typepatient" : ["patientid", "typepatientid", "visit_name", "visit_type", "age", "days"]
        "background" : ["patientid", "sex", "race"],
        "pdiagnose" : ["patientid", "typepatientid", "diagnosis", "dsmno"],
        "medication" : ["patientid", "typepatientid", "medication", "dose"],
        "cgi" : ["patientid", "typepatientid", "severity"]
    }

    results = {}
    count = 0
    for tbl, cols in queries.items():
        print(tbl)
        results["result"+str(count)] = Querier(tbl, f'../data/temp/{tbl}.pkl')
        data_query = f"""select distinct on ({tbl}.patientid), {col for col in cols}
                        from rwe_version1_2.{tbl}
                        where {tbl}.patientid in {mdd_pts_list}
                        """
        count+=1
    print(results)
    
    return 

@lD.log(logBase + '.getComparativePop')
def getComparativePop(logger, patientID):
    data = prepData()

    return patientData, popData


@lD.log(logBase + '.main')
def main(logger, resultsDict):
    print('Starting..')

    print('Done!')

    # ## Stash
    # @interact
    # def show_meds_CGIbyDays(med=meds_list, x=365):
    #     temp = pop_mdd.loc[pop_mdd.Medication == med].groupby('Days').agg({'CGI-S':'median'})
    #     return temp.loc[temp.index<x]