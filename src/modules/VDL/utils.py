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
    
    if change_in_cgi: 
        min_cgi = -7
        plot_title = 'Change in Average CGI Progression'
        values_col = 'CGI_Change'
        colorscale = 'YlOrRd'
    else: # actual cgi values
        min_cgi = 0
        plot_title = 'Average CGI Progression'
        values_col = 'CGI'
        colorscale = 'Reds'

    data_crosstab = pd.crosstab(index=data[col],
                                  columns=data[period],
                                  values=data[values_col], 
                                  aggfunc='mean').round(1)
    
    fig = go.Figure(data=go.Heatmap(
                   z=data_crosstab.iloc[:,:num_periods],
                   y=np.arange(1,8),
                   x=np.arange(1, 11),
                    zmin=min_cgi,
                    zmax=7,
                    colorscale=colorscale #, 
                    # reversescale=True
    ))
    
    fig['layout'] = {'title' : plot_title, 
                     'yaxis':{"title": "Initial CGI"},
                    'xaxis' : {"title": period}
                    }
    return fig

    ## To use:
    ## x = getCGIchangeData( getComparativePopulation(9209, visits_data),period='Month')
    ## plotCGIoverTime(x.iloc[:,:100]).show()

# medications boxplot
def getMedsData(cp_data):
    # cp_data = p.cpData
    cpop_meds = cp_data.groupby('Medication').agg({'PatientID':'nunique', 'CGI':'mean'})
    cpop_improved = cp_data.loc[cp_data['CGI']<=2].groupby('Medication').agg({'PatientID':'nunique', 'CGI':['mean','median','var']})
    cpop_all = cpop_meds.merge(cpop_improved, how='left', on='Medication')
    cpop_all.columns = ['Count_All','CGI_All','Count_Improved','CGI_Mean','CGI_Median','CGI_Var']
    cpop_all['Pct_Improved'] = cpop_all.Count_Improved / cpop_all.Count_All * 100 
    return cpop_all

def plot_meds_box(cp_data, n=5):
    # cp_data = p.cpData
    cpop_all = getMedsData(cp_data)
    topNmeds = cpop_all.sort_values(['Count_All'], ascending=False).index[:n]
    topNmeds_cgi = cp_data.loc[cp_data['Medication'].isin(topNmeds)].groupby(['Medication'])['CGI'].apply(list)
    for i, med in enumerate(topNmeds_cgi): 
        topNmeds_cgi[i] = [m for m in topNmeds_cgi[i] if ~np.isnan(m)] #list(filter(None,topNmeds_cgi[i]))
    pct_imp = cpop_all.loc[cpop_all.index.isin(topNmeds),'Pct_Improved']
    
    fig = go.Figure()
    for ix, med_data in enumerate(topNmeds_cgi):
        med_name = topNmeds_cgi.index[ix]
        med_pct = pct_imp[ix]
        fig.add_trace(go.Box(x=med_data, name=f'{med_name} ({round(med_pct,1)}%)'))
    fig['layout'] = {'title':'Treatment Response C.I. of Top {} Prescribed Medications'.format(n),
                     'xaxis': {'title':'CGI Score'},
                     'yaxis': {'title':'Medication & % Patients Improved'},
                    }
    return fig

