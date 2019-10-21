import jsonref, pprint
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
import statistics
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