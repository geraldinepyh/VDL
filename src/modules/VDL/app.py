import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash_daq as dqq
from modules.VDL import utils
# import utils

import pickle
import numpy as np
import pandas as pd
from plotly.subplots import make_subplots

# avoid the pandas item deprecation warnings
import warnings
warnings.filterwarnings('ignore') 

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

df = pickle.load(open('../data/intermediate/patient_demographics_sample.pkl','rb'))
visits_data = pickle.load(open('../data/intermediate/visits_data_sample.pkl','rb'))
visit_types_list = list(visits_data.groupby('VisitType')['VisitID'].count().sort_values(ascending=False).index.dropna())
colorsIdx = {val:i+1 for i, val in enumerate(visit_types_list)}
disease_list = visits_data.DiseaseCat.unique().tolist() 
cgi_change_options = ['CGI_Initial','CGI']
period_options = {'Week':7, 'Month':28,'Year':365}
default_filters = {'Sex': None, 'Race': None, 'Age': None,
                    'Medication': 'all', # not added yet. 
                    'DiseaseCat': 'all'}

class patientQ():
    def __init__(self, pid, df=df):
        if type(pid) != int: 
            pid = int(pid)
        self.pid = pid
        self.patientData = visits_data[visits_data.PatientID == self.pid]
        self.cpData = self.getCPData(visits_data)
        self.filteredData = None
        self.filt_values = default_filters.copy()
        self.age = df.loc[df.PatientID == self.pid, 'Age'].item()
        self.sex = df.loc[df.PatientID == self.pid, 'Sex'].item()
        self.race = df.loc[df.PatientID == self.pid, 'Race'].item()
        self.comorbidities = self.patientData.DiseaseCat.unique().tolist()

    def getCPData(self, visits=visits_data):
        # Resets the patient's cpData from the original dataset. 
        return visits_data[visits_data.PatientID != self.pid] 

    def add_filt(self, demog=df, visits=visits_data, age_band=5):
        """For adding demographics filters to the comparative pop dataframe.
        """
        filt_values = self.filt_values
        demog_filters = []
        visit_filters = [visits.PatientID != self.pid]

        for filt, val in filt_values.items():
            if val != None:
                if filt=='Medication' or filt=='DiseaseCat':
                    if not val == 'all':
                        if not isinstance(val, list): val = [val]
                        f = visits[filt].isin(val)
                        visit_filters.append(f)
                    # else: 
                        # visit_filters.append(visits.all(axis=1))
                        
                elif filt=='Age':
                    f = abs(demog['Age']-filt_values['Age'])<=age_band
                    demog_filters.append(f)
                    
                elif filt in ['Sex','Race']: 
                    f = demog[filt]== val
                    demog_filters.append(f)
                    
        if demog_filters != []:           
            demog_pids = demog[pd.concat(demog_filters, axis=1).all(axis=1)]
            visit_filters.append(visits.PatientID.isin(demog_pids.PatientID))

        data_out = visits[pd.concat(visit_filters,axis=1).all(axis=1)] 
        self.cpData = data_out
        
        return data_out
    
# Defining patient instance as global variable for easy refernecing.
initial_pid = df.iloc[0,0] #516
p = patientQ(initial_pid)

####################
###### Layout ######
####################

app.layout = html.Div(style={'backgroundColor':colors['background']},
    children=[
    html.H1(children='VisualDecisionLinc',
            style={'textAlign': 'center', 'color':colors['text']}),
    ## Left side Bar
    html.Div([
        html.H3('Selected Patient: ', style={'color':colors['text']}),
        dcc.Input(id='selected_pid',type='number', value=initial_pid),
        html.Button(id='reset_pid_button', n_clicks=0, children='Update'),
        html.Br(),
        html.Div([
            dcc.Checklist(id ='demog_filt', style={'display': 'inline-block',
                                                    'width' : '35%'}),
            dcc.Dropdown(id ='comorbid_filt', style={'width': '50%',
                                                    'height':'100%',
                                                    'display': 'inline-block'}, 
                                                    multi=True),
            html.Div([html.Button(id='apply_filter', n_clicks=0, children='Apply Filters'),
                    html.Button(id='reset_filter', children='Reset Filters')],
                    style={'float': 'right', 'display': 'inline-block', 'width' : '15%'})
        ]),
        dcc.Loading(id="loading-plot1", children=[dcc.Graph(id='plot1')])
    ],style={'width': '48%', 'float': 'left', 'display': 'inline-block'}),
    dcc.Store(id='filt_values'),
    html.Div([
        html.H3('Comparative Population', style={'color':colors['text']}),
        html.Div('There are {} similar patients in this population.'.format(len(p.cpData.PatientID.unique())),
                id='cpop_count'),
        html.Hr(), 
        dcc.Loading(id="loading-plot2", children=[dcc.Graph(id='plot2')]),
        html.Hr(),
        dcc.Loading(id='loading-plot3',children=[dcc.Graph(id='plot3')]),
        html.Hr(),
        html.Div([
            html.Button(id='view_options',children='Show/Hide Graph Settings', n_clicks=0), 
            html.Br(),
            html.Div([ ## visible only if view_options button is clicked
                dcc.Dropdown(id='comorbid_dropdown',
                     options=[{'label' :d, 'value': d} for d in disease_list],
                     value='major depressive disorder'
                    #  ,style={'width': '50%', 'float':'right', 'display': 'inline-block'}
                     ),
                html.Br(),
                dcc.Dropdown(
                    id='cgi_change_col',
                    options=[{'label': i, 'value': i} for i in cgi_change_options],
                    value='CGI_Initial'
                    #,style={'width': '30%', 'display': 'inline-block'}
                ),
                dcc.Dropdown(
                    id='period_selection',
                    options=[{'label': i, 'value': i} for i in period_options],
                    value='Week'
                    # ,style={'width': '30%', 'display': 'inline-block'}
                ),
                dqq.BooleanSwitch(
                    id='change_in_cgi_toggle',
                    on=True,
                    label='Use Change in CGI',
                    labelPosition='top'
                    # ,style={'width': '30%', 'display': 'inline-block'}
                ), 
                html.Br(), 
                html.Div('Adjust number of Medications to show:'),
                dcc.Input(id='num_meds_to_show', value=5, type='number')
            ], id='hidden_div')
        ])
    ],style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
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
            # return dash.no_update, 'Cannot find Patient {} in the database'.format(pid)
            print('Cannot find Patient {} in the database'.format(pid))
            raise PreventUpdate
        else:
            p = patientQ(pid) # update new selected patient
            return pid

@app.callback(
    Output(component_id='hidden_div', component_property='style'),
    [Input(component_id='view_options', component_property='n_clicks')])
def hide_div_toggle(n_clicks):
    if n_clicks % 2 == 0: # even: turn OFF
        return {'display':'none'}
    else: # odd: turn ON
        return {'display':'inline-block'}

@app.callback(
    Output('demog_filt', 'options'),
    [Input('selected_pid','value')])
def apply_demog_filter(pid):
    global p 
    return [{'label': 'Age: {}'.format( p.age ), 'value':p.age},
            {'label': 'Sex: {}'.format( p.sex ), 'value':p.sex},
            {'label': 'Race: {}'.format( p.race ), 'value': p.race}]

@app.callback(
    Output('comorbid_filt', 'options'),
    [Input('reset_filter','n_clicks'),
    Input('apply_filter','n_clicks')],
    [State('comorbid_dropdown','value')])
def apply_comorbid_filter(reset_filter, apply_filter, selected_diagnosis):
    left = pd.DataFrame(disease_list, columns=['DiseaseCat'])
    right = p.cpData[p.cpData.DiseaseCat!=selected_diagnosis].groupby('DiseaseCat')[['PatientID']].nunique().reset_index()
    tbl = pd.merge(right = right, left = left).fillna(0).set_index('DiseaseCat')
    dropdownlist = [{'label': '{} ({}){}\n'.format(name, count.item(), '*' if name in p.comorbidities else ''),
                    'value':name} for name, count in tbl.iterrows()]
    return dropdownlist

@app.callback(
    [Output('demog_filt','value'),
    Output('comorbid_filt','value')],
    [Input('reset_pid_button','n_clicks'),
    Input('reset_filter','n_clicks')])
def reset_filters(reset_patient, reset_filter):
    """When patient or filters is reset; update the filter values.
    These are States of the filt_values data dictionary, which will then update 
    when either buttons are clicked as well. 
    """
    if reset_patient is None or reset_filter is None:
        raise PreventUpdate
    else:
        return ["","",""], None

@app.callback(
    Output('filt_values', 'data'),
    [Input('reset_filter','n_clicks'),
    Input('apply_filter','n_clicks')], 
    [State('demog_filt', 'value'),
    State('comorbid_filt', 'value')]
    )
def update_filt_values_dict(reset_filter, apply_filter, demogs, comorbids):
    """Data Storage for the dictionary of filter values."""
    global p
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print('=-'*10, 'CHANGING FILTERS', '-='*10,)    
    print('Clicked:', button_id)

    if button_id == 'reset_filter':
        print('Resetting the filters...')
        p.filt_values = default_filters.copy()

    elif button_id == 'apply_filter':
        print('Applying the filters...')
        # Using demog/comorbid filts, update filt_values
        if demogs != None:
            for d in demogs:
                if d == '': 
                    continue
                elif isinstance(d, int): 
                    p.filt_values['Age'] = d
                elif d == 'M' or d == 'F':
                    p.filt_values['Sex'] = d
                else:
                    p.filt_values['Race'] = d
        if comorbids != None and comorbids != p.filt_values['DiseaseCat']:
                p.filt_values['DiseaseCat'] = comorbids

    print('Updated Filters: ',p.filt_values)
    p.cpData = p.add_filt()
    with open('../data/intermediate/temp.pkl','wb') as f:
        pickle.dump(p.cpData, f)
    return p.filt_values

@app.callback(
    Output('cpop_count','children'),
    [Input('filt_values','data')])
def update_cpop_count(dic):
    count = p.cpData.PatientID.nunique()
    count_msg = 'There are {} similar patients in this population.'.format(count)
    print(count_msg)
    return count_msg


#######################
######## Plots ########
#######################

@app.callback(
    Output('plot1', 'figure'),
    [Input('reset_pid_button','n_clicks')],
    [State('selected_pid','value')])
def plot1(n_clicks, pid):
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
    fig1.update_layout(margin=dict(l=20, r=20, t=20, b=20),showlegend=False)
    return fig1
    
@app.callback(
    Output('plot2','figure'),
    [Input('reset_pid_button', 'n_clicks'),
     Input('filt_values', 'data'),
     Input('cgi_change_col', 'value'),
     Input('period_selection', 'value'),
     Input('change_in_cgi_toggle', 'on')])
def plot2(reset_filter, filt_values, col, period, change_in_cgi):
    cp_data = utils.getCGIchangeData(p.cpData, period=period) 
    plot2 = utils.plot_cgi_change(cp_data, col=col, period=period, change_in_cgi=change_in_cgi)
    return plot2

@app.callback(
    Output('plot3','figure'),
    [Input('reset_pid_button', 'n_clicks'),
     Input('filt_values', 'data'),
     Input('num_meds_to_show', 'value')]
    )
def plot3(reset_filter, filt_values, n):
    plot3 = utils.plot_meds_box(p.cpData, n) 
    return plot3



def main(resultsDict):
    print('Starting...')
    app.run_server(debug=True)

# app.run_server(debug=True) # for debugging; so that it updates when i save 
