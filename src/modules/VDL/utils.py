import jsonref, pprint
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
import statistics, math
import re

import plotly.graph_objects as go

def plot_cgi_time(pid, data, colorsIdx, visit_types_list):
    cgi = data.groupby('Days').apply(lambda x: statistics.mean([x['CGI'].max(), x['CGI'].min()]))

    colors = data['VisitType'].map(colorsIdx)
    return go.Scatter(y=cgi.values,#cgi-scores
                      x=cgi.index, #days
                      mode='lines+markers',
                      line=dict(color='lightgray'), 
                      marker=dict(color=colors,
                                  line=dict(width=1, color='darkgray'),
                                  colorbar=dict(title='Visit Type',
                                                tick0=0,
                                                dtick=1,
                                                tickvals=[i+1 for i in np.arange(len(visit_types_list))],
                                               ticktext=visit_types_list),
                                  colorscale='Sunsetdark',
                                  reversescale=True
                                 ))

def plot_meds_time(pid, data):
    """Scatter plot of a patient `pid`'s medication over time.'"""
    
    patient_meds_df = data.groupby('Medication').agg({'Days':['min','max']})
    patient_meds_df = patient_meds_df.reset_index()
    patient_meds_df.columns = patient_meds_df.columns.droplevel()
    patient_meds_df.columns = ['Medication','First','Last']
    patient_meds_df['Duration'] = patient_meds_df['Last'] - patient_meds_df['First'] + 1

    return go.Bar(y=list(patient_meds_df.Medication),
                  x=list(patient_meds_df.Duration),
                  base=list(patient_meds_df.First),
                  orientation='h',
                  )

# heatmap

def getCGIchangeData(cp_data, period='Week',n_periods=7):
    ## Adds the columns of CGI_Initial, Week and CGI_Change 
    ## to a copy of the comparative population dataset. 
    
    periods = {'Week':7, 'Month':28,'Year':365}
    data = cp_data.copy()
    
    data_grouper = data.groupby('PatientID')['Days']
    cp_initialCGI = data.loc[data_grouper.idxmin(),['PatientID','CGI']]
    cp_initialCGI.columns = ['PatientID','CGI_Initial']
    data = pd.merge(data, cp_initialCGI, how='left', on='PatientID')
    data[period] = data_grouper.transform(lambda x: (x - x.min() + 1) / periods[period]).apply(math.floor)
    data['CGI_Change'] = data['CGI'] - data['CGI_Initial'] 
    
    return data

# heatmap
def plot_cgi_change(data, change_in_cgi=True, period='Week', 
                    col='CGI_Initial', num_periods=100):

    if set([col, period, 'CGI_Change']).issubset(data.columns):
        data_crosstab = pd.crosstab(index=data[col],
                                  columns=data[period],
                                  values=data.CGI_Change, 
                                  aggfunc='mean').round(1)
    else:
        print('Error: Column not found in dataframe.')
    
    if change_in_cgi: 
        min_cgi = -7
        plot_title = 'Change in Average CGI Progression'
    else: # actual cgi values
        min_cgi = 0
        plot_title = 'Average CGI Progression'
    
    fig = go.Figure(data=go.Heatmap(
                   z=data_crosstab.iloc[:,:num_periods],
                   y=np.arange(1,8),
                   x=np.arange(1, 11),
                    zmin=min_cgi,
                    zmax=7,
                    colorscale='RdBu', reversescale=True
    ))
    
    fig['layout'] = {'title' : plot_title, 
                     'yaxis':{"title": "Initial CGI"},
                    'xaxis' : {"title": period}
                    }
    return fig

    ## To use:
    ## x = getCGIchangeData( getComparativePopulation(9209, visits_data),period='Month')
    ## plotCGIoverTime(x.iloc[:,:100]).show()
