import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import utils

import pickle
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

class patientQ():
    def __init__(self, pid, demog_df=df):
        if type(pid) != int: 
            pid = int(pid)
        self.pid = pid
        self.age = df.loc[df.PatientID == pid, 'Age'].item()
        self.sex = df.loc[df.PatientID == pid, 'Sex'].item()
        race = df.loc[df.PatientID == pid, 'Race'].item()
        if race != "":
            self.race = race
        else:
            self.race = None # Race not specified.

    def getPatientData(self):
        patient_data = visits_data[visits_data.PatientID == self.pid]
        return patient_data
    
    def getComparativeData(self):
        comp_data = visits_data[visits_data.PatientID != self.pid]
        return patient_data

def generate_table(dataframe, max_rows=10):
    return html.Table(
        [html.Tr([html.Th(col) for col in dataframe.columns])] +

        # Body
        [html.Tr([
            html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
        ]) for i in range(min(len(dataframe), max_rows))],
        style={'color':colors['text']}
    )

def generate_graph():
    return dcc.Graph(
        id='example-graph',
        figure={
            'data': [
                {'x': [1, 2, 3], 'y': [4, 1, 2], 'type': 'bar', 'name': 'SF'},
                {'x': [1, 2, 3], 'y': [2, 4, 5], 'type': 'bar', 'name': u'Montréal'},
            ],
            'layout': {
                'title': 'Dash Data Visualization',
                'plot_bgcolor': colors['background'],
                'paper_bgcolor': colors['background'],
                'font': {
                    'color': colors['text']
                }
            }
        }
    )

def generate_markdown(id, text):
    # Text must be in markdown format.
    return dcc.Markdown(id=id, children=text, style={'color':colors['text']})

demog_options = {'Age':'12', 'Sex': 'F','Race': 'x'}

####################
###### Layout ######
####################

app.layout = html.Div(style={'backgroundColor':colors['background']},
    children=[
    html.H1(children='VisualDecisionLinc',
            style={'textAlign': 'center', 'color':colors['text']}),
    dcc.Input(id='reset_pid',type='number', value=9209),
    html.Button(id='reset_pid_button', n_clicks=0, children='Update'),
    html.Hr(),

    html.Div('Selected Patient: ', style={'color':colors['text']}),
    html.Div(id='selected_pid', #children=pid,
            style={'color':colors['text_selected']}),
    
    dcc.Checklist(id ='demog_filt',
                # options = [{'label': k, 'value': k} for k in demog_options.keys()]
                # options=[{'label': f'Age: { p.age }', 'value':'Age'},
                #         {'label': f'Sex: { p.sex }', 'value':'Sex'},
                #         {'label': f'Race: { p.race }', 'value':'Race'}],
                style={'color':colors['text']}),

    # generate_table(df),
    generate_markdown('filter_description',f'''
    **Filters Applied:**'''),
    html.Div(id='selected_filts', style={'color':colors['text']}),
    # generate_graph()

    dcc.Graph(id='plot1'),

    html.Hr()
])

###############################
###### Reactive Elements ######
###############################

@app.callback(
    Output('selected_pid', 'children'),
    [Input('reset_pid_button','n_clicks')],
    [State('reset_pid','value')]
)
def reset_patient(n_clicks, pid):
    # only changes the pid if button is clicked. 
    if n_clicks is None: 
        raise PreventUpdate
    else:
        if pid not in df.PatientID.unique():
            print('Error: Patient not found.')
            return None
        else:
            return pid

@app.callback(
    Output('demog_filt', 'options'),
    [Input('selected_pid','children')]
)
def apply_demog_filter(pid):
    if pid != None:
        p = patientQ(pid)
        return [{'label': f'Age: { p.age }', 'value':'Age'},
                {'label': f'Sex: { p.sex }', 'value':'Sex'},
                {'label': f'Race: { p.race }', 'value':'Race'}]
    else:
        return [{'label': 'Patient not found.','value':'reset_page'}]

@app.callback(
    Output(component_id='selected_filts', component_property='children'),
    [Input(component_id='demog_filt', component_property='value')]
)
def selected_demogs(filters_list):
    txt = f'Demographics: {filters_list}'
    return txt

@app.callback(
    Output('plot1', 'figure'),
    [Input('selected_pid','children')]
)
def plot1(pid):
    p = patientQ(pid)
    patient_data = p.getPatientData()
    fig1 = make_subplots(rows=2, cols=1, shared_xaxes=True)
    fig1.append_trace(utils.plot_cgi_time(pid, patient_data, colorsIdx, visit_types_list), 
                    row=1, col=1)
    fig1.append_trace(utils.plot_meds_time(pid, patient_data), 
                    row=2, col=1)
    fig1.update_xaxes(title_text='Days',
                    showgrid=False, row=1, col=1)
    fig1.update_yaxes(title_text='CGI Severity Score',
                             showgrid=False,
                             range=[0,7],row=1, col=1)
    fig1.update_layout(showlegend=False)
    return fig1

if __name__ == '__main__':
    app.run_server(debug=True)