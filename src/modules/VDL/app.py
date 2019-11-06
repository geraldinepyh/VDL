import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_daq as dqq
from modules.VDL import utils

import pickle
import numpy as np
import pandas as pd
from plotly.subplots import make_subplots

###########################
######### Styling #########
###########################

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
colors = {
    'background': '#f9f7f7',
    'text': '#112d4e',
    'text_selected': '#3f72af'
}

###########################
######### Get Data ########
###########################

df = pickle.load(open('../data/intermediate/patient_demographics.pkl','rb'))
visits_data = pickle.load(open('../data/intermediate/visits_data.pkl','rb'))
visit_types_list = list(visits_data.groupby('VisitType')['VisitID'].count().sort_values(ascending=False).index.dropna())
colorsIdx = {val:i+1 for i, val in enumerate(visit_types_list)}
disease_list = visits_data.DiseaseCat.unique().tolist() 
cgi_change_options = ['CGI_Initial','CGI']
period_options = {'Week':7, 'Month':28,'Year':365}

class patientQ():
    def __init__(self, pid, df=df):
        if type(pid) != int: 
            pid = int(pid)
        self.pid = pid
        self.patientData = visits_data[visits_data.PatientID == self.pid]
        self.cpData = visits_data[visits_data.PatientID != self.pid] # self.getCPData(df, visits_data)
        self.filt_values = {'Sex':None, 'Race':None, 'Age':None, 'Medication':'all', 'DiseaseCat':'all'}
        self.age = df.loc[df.PatientID == self.pid, 'Age'].item()
        self.sex = df.loc[df.PatientID == self.pid, 'Sex'].item()
        race = df.loc[df.PatientID == self.pid, 'Race'].item()
        if race != "":
            self.race = race
        else:
            self.race = None # if Race not specified.

    def add_filt(self, filt_values, demog=df, visits=visits_data, age_band=5):
        """For adding demographics filters to the comparative pop dataframe.
        """
        demog_filters = []
        visit_filters = []
        updated = False

        for filt, val in filt_values.items():
            if val != None:
                if filt=='Medication' or filt=='DiseaseCat':
                    if not val == 'all':
                        if not isinstance(val, list): val = [val]
                        f = visits[filt].isin(val)
                        visit_filters.append(f)
                        updated = True
                    
                elif filt=='Age':
                    f = abs(demog['Age']-filt_values['Age'])<=age_band
                    demog_filters.append(f)
                    updated = True

                else: # Sex/Race
                    f = demog[filt]== val
                    demog_filters.append(f)
                    updated = True
            
        if updated:
            demogs = demog[pd.concat(demog_filters, axis=1).all(axis=1)]
            visit_filters.append(visits.PatientID.isin(demogs.PatientID))
            filteredDF = visits[pd.concat(visit_filters,axis=1).all(axis=1)]
            self.cpData = filteredDF
            return filteredDF
        
    def getCPData(self, demogs, comorbids):
        """ This function updates the comparative population data of the current patient,
            by using two sets of filters (`demogs` and `comorbids`).
        """
        updatedData = self.add_filt(self.filt_values, df, visits_data)
        self.cpData = updatedData
        print('Updated comparative population for patient ' + str(self.pid))
        return updatedData # visits_data[visits_data.PatientID != self.pid]

# Defining patient instance as global variable for easy refernecing.
initial_pid = 92
p = patientQ(initial_pid)

####################
###### Layout ######
####################

app.layout = html.Div(style={'backgroundColor':colors['background']},
    children=[
    html.H1(children='VisualDecisionLinc',
            style={'textAlign': 'center', 'color':colors['text']}),
    html.Div([
        html.Div('Selected Patient: ', style={'color':colors['text']}),
        dcc.Input(id='selected_pid',type='number', value=92),
        html.Button(id='reset_pid_button', n_clicks=0, children='Update'),
        dcc.Dropdown(id='reset_diagnosis',
                     options=[{'label' :d, 'value': d} for d in disease_list],
                     value='major depressive disorder',
                     style={'width': '40%', 'display': 'inline-block'})
    ]),
    html.Hr(),    
    dcc.Checklist(id ='demog_filt', style={'color':colors['text']}),
    dcc.Dropdown(id ='comorbid_filt', style={'color':colors['text'], 'width': '50%','height':'75%'}, multi=True),
    html.Button(id='reset_filter', n_clicks=0, children='Apply Filters'),
    dcc.Store(id='filt_values'), 

    dcc.Loading(id="loading-plot1", children=[dcc.Graph(id='plot1', style={'width': '50%'})]),
    html.Hr(),
    html.Div([
    dcc.Dropdown(
        id='cgi_change_col',
        options=[{'label': i, 'value': i} for i in cgi_change_options],
        value='CGI_Initial',
        style={'width': '35%', 'display': 'inline-block'}
    ),
    dcc.Dropdown(
        id='period_selection',
        options=[{'label': i, 'value': i} for i in period_options],
        value='Week',
        style={'width': '35%', 'display': 'inline-block'}
    ),
    dqq.BooleanSwitch(
        id='change_in_cgi_toggle',
        on=True,
        label='Use Change in CGI',
        labelPosition='top',
        style={'width': '30', 'display': 'inline-block'}
    )]),
    dcc.Loading(id="loading-plot2", children=[dcc.Graph(id='plot2', style={'width': '50%'})]),
    dcc.Slider(
        id='width_slider', # needs to match plot2 
        min=1, #df[period].min(),
        max=1000, #df[period].max(),
        value=100,
        # marks = {i:i for i in np.arange(0,1000,100)}, #df[period].max())}, # causes error.
        step=100
    ),
    html.Hr(),
    dcc.Input(id='num_meds_to_show', value=10, type='number'),
    dcc.Loading(id='loading-plot3',children=[dcc.Graph(id='plot3', style={'width': '50%'})]),
    html.Hr()
])

###############################
###### Reactive Elements ######
###############################

@app.callback(
    Output('selected_pid', 'value'),
    [Input('reset_pid_button','n_clicks')],
    [State('selected_pid','value')])
def reset_patient(n_clicks, pid):
    global p 
    # only changes the pid if button is clicked. 
    if n_clicks is None: 
        raise PreventUpdate
    else:
        if pid not in df.PatientID.unique():
            print('Error: Patient not found.') # turn into some error message
            raise PreventUpdate 
        else:
            p = patientQ(pid) # update new selected patient
            return pid

@app.callback(
    Output('demog_filt', 'options'),
    [Input('selected_pid','value')]
    )
def apply_demog_filter(pid):
    global p 
    return [{'label': 'Age: {}'.format( p.age ), 'value':p.age},
            {'label': 'Sex: {}'.format( p.sex ), 'value':p.sex},
            {'label': 'Race: {}'.format( p.race ), 'value': '' if p.race == None else p.race}]
    
@app.callback(
    Output('comorbid_filt', 'options'),
    [Input('reset_diagnosis','value')])
def apply_comorbid_filter(selected_diagnosis):
    global p 
    cpData = p.cpData

    if selected_diagnosis is None:
        raise preventUpdate
    else:
        tbl = cpData[cpData.DiseaseCat!=selected_diagnosis].groupby('DiseaseCat')[['PatientID']].count()
        return [{'label': '{} ({})\n'.format(name, count.item()), 'value':name} for name, count in tbl.iterrows()]

@app.callback(
    Output('filt_values', 'data'),
    [Input('reset_filter','n_clicks'), 
    Input('demog_filt', 'value'),
    Input('comorbid_filt', 'value')]
    )
def selected_demogs(n_clicks, demogs, comorbids):
    if n_clicks != None:
        global p
        filt_values = p.filt_values # change this? 
        if demogs != None:
            for d in demogs:
                if isinstance(d, int): 
                    filt_values['Age'] = d
                elif d == 'M' or d == 'F':
                    filt_values['Sex'] = d
                else:
                    filt_values['Race'] = d
        if comorbids != None and comorbids != filt_values['DiseaseCat']:
                filt_values['DiseaseCat'] = comorbids

        return filt_values
    else:
        raise PreventUpdate

@app.callback(
    Output('plot1', 'figure'),
    [Input('reset_pid_button','n_clicks'),
    Input('selected_pid','value')])
def plot1(n_clicks, pid):
    if n_clicks is None:
        raise PreventUpdate
    else:
        global p
        patientData = p.patientData

        fig1 = make_subplots(rows=2, cols=1, shared_xaxes=True)
        fig1.append_trace(utils.plot_cgi_time(pid, patientData, colorsIdx, visit_types_list), 
                        row=1, col=1)
        fig1.append_trace(utils.plot_meds_time(pid, patientData), 
                        row=2, col=1)
        fig1.update_xaxes(title_text='Days',
                        showgrid=False, row=1, col=1)
        fig1.update_yaxes(title_text='CGI Severity Score',
                                showgrid=False,
                                range=[0,7],row=1, col=1)
        fig1.update_layout(showlegend=False)
        return fig1
    
@app.callback(
    Output('plot2','figure'),
    [Input('reset_pid_button', 'n_clicks'),
     Input('reset_filter', 'n_clicks'),
     Input('filt_values', 'data'),
     Input('cgi_change_col', 'value'),
     Input('period_selection', 'value'),
     Input('width_slider', 'value'),
     Input('change_in_cgi_toggle', 'on')])
def plot2(pt_reset, filter_reset, filt_values, col, period, num_periods, change_in_cgi):
    if pt_reset is None:
        raise PreventUpdate
    else:
        global p
        if filter_reset != None: 
            cpData = p.add_filt(filt_values)
        else:
            cpData = p.cpData
        cp_data = utils.getCGIchangeData(cpData, period=period)

        return utils.plot_cgi_change(data=cp_data,
                    change_in_cgi=change_in_cgi,
                    period=period,
                    col=col,
                    num_periods=num_periods)
    

@app.callback(
    Output('plot3','figure'),
    [Input('reset_pid_button','n_clicks'),
    Input('reset_filter','n_clicks'),
    Input('filt_values', 'data'),
    Input('num_meds_to_show', 'value')]
    )
def plot3(pt_reset, filter_reset,filt_values, n):
    if pt_reset is None:
        raise PreventUpdate
    else:
        global p
        if filter_reset != None: 
            cpData = p.add_filt(filt_values)
        else:
            cpData = p.cpData

        return utils.plot_meds_box(cpData, n)

def main(resultsDict):
    print('Starting...')
    app.run_server(debug=True)
