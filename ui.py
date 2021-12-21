#!/usr/bin/env python3
import dash
from dash.dependencies import Input, Output, State, MATCH, ALL
import dash_core_components as dcc
import dash_html_components as html
from plot_methods import fetch_map, return_stat_plot, update_plots_general, fig_to_json, fig_from_json
from data_methods import fetch_input, flatten, fetch_ids, fetch_id, mod_cols
from styles import style_div, active_color
from divs import make_tabs, make_advanced, make_input, make_full_sliders, make_store_plots, fill_visualizations_tab, fill_intra
import requests
import dash_bootstrap_components as dbc
from collections import Counter
import json
import uuid
import plotly.express as px
import pandas as pd
import sys


app = dash.Dash(__name__, title='Top-k SimSearch', update_title=None,
                external_stylesheets=[dbc.themes.BOOTSTRAP, 
                                      "https://use.fontawesome.com/releases/v5.7.2/css/all.css"],
)
app.layout = html.Div([
    
    dcc.Store(id='suggested_names'), dcc.Store(id='stored_attributes'),
    html.Span(id='advanced_go', title='Advanced Search Settings',  children=[html.I(id='menu-bars', className="fas fa-bars ml-2")], style={'color':active_color}),
    html.Div(children=html.H1(id='title', children='Top-k Similarity Search'), style=style_div),
    html.Div(children=html.H2(children='Search Conditions'), style=style_div),
    html.Div(children=[
        
        html.Div(className='autocomplete', 
                 children=dcc.Input(id='search_bar', type='text', 
                                    placeholder='Search for entity...',
                                    debounce=False, autoComplete="off"),
                 style={'width': '60%'}),
        dcc.Input(id='search_bar_2', type='text', placeholder='Search for company...',
                      debounce=False, style={'width': '60%', 'display': 'none'}, autoComplete="off"),
        html.Span(id='search_go', title='Search',  children=[html.I(className="fas fa-search ml-2")], style={'color':active_color}),
        dcc.Store(id='search_selected', data=""),
        html.Span(id='settings_go', title='Search Settings', children=[html.I(className="fas fa-cog ml-2")], style={'color':active_color, 'margin-left': '40px'}),],
         style=style_div),
    dbc.Collapse(id='inputs_collapse',
        children=[html.Div(id='inputs', className='options', children=[
            make_input(0, 'k', 'number'),  
            ], style={'display':'flex', 'margin-top': '20px', 'justify-content': 'center'}),
        html.Hr()]
    ),
    dbc.Modal(centered=True, id="modal", size="lg", children=
        [dbc.ModalHeader("Pick a Location"),
         dbc.ModalBody(html.Iframe(id='Map', srcDoc = fetch_map(), height=355, width=555), style=style_div),
         dbc.ModalFooter(children = [
                dbc.Button("Choose", id="confirmMap"),
                dbc.Button("Cancel", id="cancelMap")]
            )
        ],
    ),
    
    dbc.Modal(centered=True, id="kwd_modal", size="lg", children=
        [dbc.ModalHeader(id="kwd_header", children="Expand field: "),
         dbc.ModalBody([dcc.Textarea(id='kwd_text_area', value="",
                                     style={'width': '100%', 'height': 200}),
                        dcc.Store("kwd_selected")],  style=style_div),
         dbc.ModalFooter(children = [
                dbc.Button("Save", id="kwd_save"),
                dbc.Button("Cancel", id="kwd_cancel")]
            )
        ],
    ),

    html.Div(children=[html.H2(children='Weights'), html.Span(id='weights_go', title='Weights Settings',  children=[html.I(className="fas fa-sliders-h ml-2")], style={'color':active_color, 'margin-top':'7px', 'margin-left':'15px'})], style=style_div),
    dbc.Collapse(id='weights_collapse', children=[
        html.Div(id='weights', className='weights', children=make_full_sliders(), style={'display':'flex'}),
        html.Hr(),]), 
    dbc.Modal(centered=True, id="advanced_menu", size="lg", children=
      [dbc.ModalHeader("Advanced Settings"),
        dbc.ModalBody(html.Div(className='advanced', children=[
            make_advanced(0, 'Source Pool', 'Which source file to read'),
            make_advanced(1, 'Sources', 'Which source to use for queries'),
            make_advanced(2, 'k', 'The default number of top-k results to return', 'number'),
            make_advanced(3, 'Decay Factor', 'A positive double value used as decay factor in ranking of results', 'float'),
            make_advanced(4, 'Algorithm', 'The ranking method to apply in aggregation; if omitted, threshold is used by default'),
            make_advanced(5, 'API Key', 'API Key for SimSearch Instance'),
            #make_advanced(4, 'API Key', 'Specification of API KEY for connecting to an instance of SimSearch service', 'text'),
            ])),
        dbc.ModalFooter(children = [
            dbc.Button("Save", id="saveAdvanced"),
            dbc.Button("Reset", id="resetAdvanced")]
        )], is_open=True
    ),
    dcc.Store(id='advanced_k', data=50), dcc.Store(id='advanced_decay_factor', data=0.01),
    dcc.Store(id='advanced_algorithm', data='threshold'), dcc.Store(id='stored_source', data={}),
    html.Div(id='submit_div', children=[html.Button('Submit', id='submit', style={'border-radius': '10px', 'background-color': active_color, 'color': '#fff', 'padding': '10px 20px', 'font-size': '20px'}),
                                        dcc.Store(id='submit_clicked', data=0),
                                        dcc.Store(id='submit_initialized', data=0),
                                        dcc.Store(id='submit_finalized', data=0)],
                                        style={'display':'flex', 'justify-content': 'center', 'width': '100%', 'margin-bottom':'20px', 'margin-top':'20px'}),
    make_tabs(),
    dbc.Modal([dbc.ModalHeader("Error"),
                dbc.ModalBody(id="message_body", children="This is the content of the modal"),
                dbc.ModalFooter(
                    dbc.Button("OK", id="message_close")
                ),
            ],id="message",),
    dbc.Modal([dbc.ModalHeader("Entity Score Inspection"),
                dbc.ModalBody(id="confirmBody",
                              children=dcc.Graph(id='radarPlot',
                                                 style={'width':'100%'})),
                dbc.ModalFooter(children = [
                    dbc.Button("Set as Query", id="confirmQuery"),
                    dbc.Button("Close", id="cancelQuery")]
                ),
            ],id="confirm",),    
    dcc.Store(id='msg1'), dcc.Store(id='msg2'), dcc.Store(id='msg3'),
    dcc.Loading(dcc.Store(id='session_id')),
    html.Div(id='dump1', style={'display':'none'}), html.Div(id='dump2', style={'display':'none'})
    ])


app.clientside_callback(
    """
    function(data) {
        if (data === undefined)
            return {};
        
        autocomplete(document.getElementById("search_bar"), data);
        
        return {};
    }
    """,
    Output("dump1", "children"),
    [Input("suggested_names", "data")]
) 

@app.callback(
    [Output("suggested_names", "data")],
    [Input("search_bar", "value")],
    State("stored_source", "data")
) 
def suggest_names(value, source):
    """Callback method for fetching suggestions."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return [dash.no_update]
    
    if len(value) < 3:
        return [[]]
        
    res = fetch_ids(value, source)
    if res is None:
        return [[]]
    
    return [[lab for val, lab in res]]


@app.callback(
    [Output("Advanced_{}".format(no), "value") for no in range(2,5)],
    [Input("resetAdvanced", "n_clicks")],
    [State("advanced_k", "data"), State("advanced_decay_factor", "data"), State("advanced_algorithm", "data")]
) 
def reset_advanced(n, k, decay_factor, algorithm):
    """Callback method for resetting advanced settings."""
    return [k, decay_factor, algorithm]


@app.callback(
    [Output({'index':ALL, 'col':ALL, 'type':'slider_value'}, "disabled"),
     Output({'index':ALL, 'type':'slider_title'}, "style")],
    [Input({'index': ALL, 'type':'input'}, "value"), Input({'index': ALL, 'type':'inputDate'}, "date")],
    [State({'index':ALL, 'type':'input_title'}, "children"),
     State("stored_attributes", "data")]
)
def turn_switch(inputs, inputDates, input_titles, attr):
    """Callback method for updating sliders when interacting with input."""
    ctx = dash.callback_context

    if not ctx.triggered:
        return [[dash.no_update]*len(attr)*4, [dash.no_update]*len(attr)]

    changes = {int(json.loads(x['prop_id'].split('.')[0])['index'].split('_')[1]): x['value'] for x in ctx.triggered if 'value' in x}
    changes.update({int(json.loads(x['prop_id'].split('.')[0])['index'].split('_')[1]): x['date'] for x in ctx.triggered if 'date' in x})
    
    ret = [[dash.no_update]*len(attr)*4, [dash.no_update]*len(attr)]
    
    for key, val in changes.items():
        if key == 1 and attr[input_titles[1].lower()] == 'GEOLOCATION':
            null = (inputs[0] is None or inputs[0] =='' ) or (inputs[1] is None or inputs[1] =='')
        else:
            null = val is None or val ==''
        color = 'gray' if null else 'black'
        ret[1][key-1] = {'color':color}
        ret[0][key-1::len(attr)] = [null]*len(ret[0][key-1::len(attr)])
    return ret
        

@app.callback(
    [Output("weight_comb_sel", "options"), Output("table", "columns"),
     Output("table", "data"),  Output("table", "filter_action"),
     Output("table", "tooltip_data"),
    Output({'index': ALL, 'type':'intraplot'}, "figure"), 
    Output({'index': ALL, 'type':'interplot'}, "figure"),
    Output({'type':'sel', 'field': ALL }, "value")],
    [Input("tabs", "value"), Input("weight_comb_sel", "value")],
    [State("session_id", "data"), State("stored_attributes", "data"),
     State({'index': ALL, 'type':'intraplot'}, "figure"), 
     State({'index': ALL, 'type':'interplot'}, "figure"),
     State({'type':'sel', 'field': ALL}, "value"),]
)
def changeTab(tab_selected, weight_combination_selected, session_id, attr,
              intra_plot, inter_plot, plot_sel):
    """Callback method for updating the content when changing tab."""
    ctx = dash.callback_context
    
    ret = [dash.no_update]*5 + [[dash.no_update]*len(intra_plot)] + [[dash.no_update]*len(inter_plot)] + [[dash.no_update]*len(plot_sel)]
    if not ctx.triggered:
        return ret
    
    with open('output/data_{}.json'.format(session_id)) as f:
        data = json.load(f)

    no = len(data)
    
    if tab_selected == "0":
        options = [{'label' : 'Weight Combination {}'.format(i+1), 'value': str(i)} for i in range(no)]
        results = data[int(weight_combination_selected)]['rankedResults']
        columns = mod_cols(results)
        data = results
        
        tooltip_data=[{ column: {'value': str(value), 'type': 'markdown'}
                       for column, value in row.items()}
                      for row in data]
        
        ret[:5] = [options, columns, data, 'native', tooltip_data]
        return ret
    
    elif tab_selected == "1":
        with open('output/plots_{}.json'.format(session_id)) as f:
            plots = json.load(f)
        #### STARTING INTRA HERE ######
        if plots[0][0][0] is None:
            intra_figs = [return_stat_plot(data, 1, i) for i in range(no)]
            #intra_figs += [dash.no_update] * (4-len(intra_figs))
            inter_figs = return_stat_plot(data, 2, no)

            plots[0][0] = [fig_to_json(fig) for fig in intra_figs]
            plots[0][1] = [fig_to_json(fig) for fig in inter_figs]
            with open('output/plots_{}.json'.format(session_id), 'w') as f:
                json.dump(plots, f, indent=4)
        else:
            intra_figs = [fig_from_json(fig) for fig in plots[0][0]]
            inter_figs = [fig_from_json(fig) for fig in plots[0][1]]
        
        ret[5] = intra_figs
        ret[6] = inter_figs
            
        return ret
    
    elif tab_selected == "2":
        ret[7] = ["0"]*len(plot_sel)
        return ret
        #return [dash.no_update]*3 + [dash.no_update]*7 + [["0"]*len(plot_sel)]


@app.callback(
    [Output({'index': ALL, 'field': MATCH, 'type':'plot2'}, "figure")],
    [Input({'field': MATCH, 'type':'sel'}, "value")],
    [State({'index': ALL, 'field': MATCH, 'type':'plot2'}, "id"),
     State("session_id", "data"), State("stored_attributes", "data"),
     State({'index': ALL, 'type':'title'}, "children")]
)
def update_plots_1(sel, plots, session_id, attr, fields):
    """Callback method for updating plots (fig) when selecting from dropdown."""    
    ctx = dash.callback_context
    if not ctx.triggered:
        return [[dash.no_update]*len(plots)]
    
    field = plots[0]['field']
    attr_name = fields[field].lower()
    attr_type = attr[attr_name]
    figs = update_plots_general(int(sel[0]), field, attr_name, attr_type, session_id)
    
    return [figs]

@app.callback(
    [Output({'index': ALL, 'field': MATCH, 'type':'plot1'}, "srcDoc")],
    [Input({'field': MATCH, 'type':'sel'}, "value")],
    [State({'index': ALL, 'field': MATCH, 'type':'plot1'}, "id"),
     State("session_id", "data"), State("stored_attributes", "data"),
     State({'index': ALL, 'type':'title'}, "children")]
)
def update_plots_2(sel, plots, session_id, attr, fields):
    """Callback method for updating plots (map) when selecting from dropdown."""    
    ctx = dash.callback_context
    if not ctx.triggered:
        return [[dash.no_update]*len(plots)]
    
    field = plots[0]['field']
    attr_name = fields[field].lower()
    attr_type = attr[attr_name]
    figs = update_plots_general(int(sel[0]), field, attr_name, attr_type, session_id)
    
    return [figs]

@app.callback(
    [Output("modal", "is_open"), Output({'index': ALL, 'type':'geoSub3'}, "value")],
    [Input({'index': ALL, 'type':'geoBtn'}, "n_clicks"), Input("confirmMap", "n_clicks"), Input("cancelMap", "n_clicks")],
    [State("modal", "is_open"), State({'index': ALL, 'type':'geoSub3'}, "value")]
)
def popMap(n_clicks1, n_clicks2, n_clicks3, is_open, val):
    """Callback method for popping map when in spatial field input."""    
    ctx = dash.callback_context
    
    if not ctx.triggered:
        return [dash.no_update, [dash.no_update]*len(val)]
    
    trig = ctx.triggered[0]['prop_id']
    
    if trig == '{"index":"Input_1_3","type":"geoBtn"}.n_clicks' and n_clicks1[0] is not None:
        return [True, [dash.no_update]]
    elif trig == 'confirmMap.n_clicks':
        return [False, [val[0]+1]]
    elif trig == 'cancelMap.n_clicks':        
        return [False, [dash.no_update]]

    return [dash.no_update, [dash.no_update]*len(val)]
    
@app.callback(
    
    [Output({'type':'slider', 'index': ALL}, "style")] +
    [Output("shrink", "style"), Output("expand", "style")],
    [Input("expand", "n_clicks"), Input("shrink", "n_clicks"),
     Input("submit_finalized", "data")],
    [State({'type':'slider', 'index': ALL}, "style")]
)
def expand(e_clicks, s_clicks, dat, sliders):
    """Callback method for (dis)appearing of sliders."""    
    
    black = {'color': active_color,'padding-top': '40px'}
    grey = {'color': 'grey','padding-top': '40px'}
    max_s = len(sliders)
    
    ret = [[dash.no_update]*max_s, dash.no_update, dash.no_update]
    
    if e_clicks is None and s_clicks is None:
        no = 0
        return ret
    
    ctx = dash.callback_context
    choice = ctx.triggered[0]['prop_id'].split('.')[0]
    no = Counter([s['display'] for s in sliders])['block']
    if choice == 'expand' and no < 4:
        no += 1
    elif choice == 'shrink' and no > 0:
        no -= 1
    elif choice == 'submit_finalized' and no == 0:
        no = 1

    p = '{}%'.format(80 // (no+1))
    show = {'width': p, 'display': 'block'}
    hide = {'width': p, 'display': 'none'}

    ret[0][0:no] = [show]*no
    ret[0][no:max_s+1] = [hide]*(max_s-no)
    if no == 0:
        ret[1], ret[2] = grey, black
    elif no == max_s:
        ret[1], ret[2] = black, grey
    else:
        ret[1], ret[2] = black, black

    return ret

@app.callback(
    [Output("message", "is_open")],
    [Input("message_body", "children"), Input("message_close", "n_clicks")]
)
def updateModal(message, clicked):
    """Callback method for popping modal of notifications."""    
    ctx = dash.callback_context

    if not ctx.triggered:
        return [dash.no_update]
    else:
        trig = ctx.triggered[0]['prop_id']
        if trig == 'message_body.children':
            return [True]
        elif trig == 'message_close.n_clicks':
            return [False]

@app.callback(
    [Output("message_body", "children"),], 
    [Input("msg1", "data"), Input("msg2", "data"), Input("msg3", "data")],
)
def updateMessage(msg1, msg2, msg3):
    """Callback method for changing the body of notifications popup."""    
    ctx = dash.callback_context
    if not ctx.triggered or ctx.triggered[0]['prop_id'] == '.':
        return [dash.no_update]
    else:
        trig = ctx.triggered[0]['prop_id']
        if trig == 'msg1.data':
            return [msg1]
        elif trig == 'msg2.data':
            return [msg2]
        elif trig == 'msg3.data':
            return [msg3]

@app.callback(
    [Output("submit_clicked", "data"), Output('submit_initialized', 'data')],
    [Input("submit", "n_clicks")],
    [State("submit_clicked", "data"), State("submit_initialized", "data")]
)
def submit_clicked(n_clicks, data1, data2):
    """Callback method for triggering after the submission of a query."""    
    ctx = dash.callback_context
    if not ctx.triggered:
        return [dash.no_update]*2
    return [data1+1, data2+1]

@app.callback(
    [Output("tabs", "style"), Output('tabs', 'value')],
    [Input("submit_clicked", "data"), Input("submit_finalized", "data")],
)
def change_tab_display(data1, data2):
    """Callback method for hiding tab content when new submission is made."""
    ctx = dash.callback_context
    if not ctx.triggered or ctx.triggered[0]['prop_id'] == '.':
        return [dash.no_update]*2
    else:
        trigs = [trig['prop_id'] for trig in ctx.triggered]
        if 'submit_finalized.data' in trigs: # takes priority
            return [{'display':'flex'}, "0"]        
        
        if 'submit_clicked.data' in trigs:
            return [{'display':'none'}, dash.no_update]


@app.callback(
    [Output("session_id", "data"), Output("msg1", "data"),
     Output("submit_finalized", "data"), Output("intra_div", "children"),
     Output("tab_3", "children"),
     Output({'index':ALL, 'col':0, 'type':'slider_value'}, "value")],
    [Input("submit_initialized", "data")],
    [State("Advanced_3", "value"), State("Advanced_4", "value"),
     State("Advanced_5", "value"),
     State("submit_finalized", "data"), State("weights", "children"),
     State("inputs", "children"), State("stored_attributes", "data"),
     State("stored_source", "data"),
     State({'index':ALL, 'col':0, 'type':'slider_value'}, "value"),
     State({'index': ALL, 'type':'slider_title'}, "children"),
     State({'index': 'Slider_0', 'type':'slider'}, "style")]
)
def submit_query(submitted, decay_factor, rankMethod, apikey, state, sliders,
                 inputs, attr, source, slider_0_val, slider_titles, slider_0_style):
    """Callback method for submission of a query."""
    ret = [dash.no_update]*5 + [[dash.no_update]*len(slider_0_val)]
    ctx = dash.callback_context
    if not ctx.triggered:    
        return ret
    session_id = str(uuid.uuid4())
    
    ret[0] = session_id
    
    k = inputs[0]['props']['children'][1]['props']['children']['props']['value']
    
    query = [fetch_input(inputs[i]['props']['children'], sliders, 
                         i-1, attr) for i in range(1, len(inputs))]
    query = [q for q in query if q is not None]
    
    if len(query) == 0:
        ret[1] = 'Please check the input you have entered.'
        return ret
    
    if source['api_required']:
        if apikey is None or apikey == '':
            ret[1] = 'This Source requires an API key.'
            return ret
        if source['simsearch_api'] != apikey:
            ret[1] = 'Wrong API Key.'
            return ret    
    
    # params = {'algorithm':rankMethod, 'k':str(k), 'queries': query, 'decay_factor': decay_factor}
    params = {'algorithm':rankMethod, 'k':str(k), 'queries': query, 'decay_factor': decay_factor, "output" : {"extra_columns" : ["name"]},}
    headers = {'api_key' : source['simsearch_api'], 'Content-Type' : 'application/json'}
    
    response = requests.post(source['simsearch_url']+'search/', json=params, headers=headers)
    
    if response.status_code != 200:
        ret[1] = 'Something is wrong with the service. Please try again later.'
        return ret
    j = response.json()
    
    if j[0]['rankedResults'] is None:
        ret[1] = j[0]['notification']
        return ret
   
    no = len(j)
    
    for i in range(len(j)):
        j[i]['rankedResults'] = flatten(j[i]['rankedResults'], attr)
    
    with open('output/data_{}.json'.format(session_id), 'w') as f:
        json.dump(j, f, indent=4)
        
    with open('output/plots_{}.json'.format(session_id), 'w') as f:
        json.dump(make_store_plots(attr, no), f, indent=4)        

    open('output/locks_{}.lock'.format(session_id), 'w')
        
    
    ret[2] = state+1
    ret[3] = fill_intra(no)
    ret[4] = fill_visualizations_tab(query, attr, no)
    
    if slider_0_style['display'] == 'none':
        weights = j[0]['weights']
        for a in weights:
            index = slider_titles.index(a['attribute'].capitalize())
            ret[5][index] = [a['value']]
    
    return ret


@app.callback(
    [Output({'index': ALL, 'type':'input'}, "value"),
     Output({'index': ALL, 'type':'inputDate'}, "date"),
     Output("settings_go", "n_clicks"), Output("msg2", "data")],
    [Input("search_go", "n_clicks"), Input({'index': ALL, 'type':'geoSub3'}, "value"),
     Input('kwd_save', "n_clicks")],
    [State("search_bar", "value"), State("search_selected", "data"),
     State("settings_go", "n_clicks"), State("inputs_collapse", "is_open"),
     State({'index': ALL, 'type':'geoSub1'}, "value"),
     State({'index': ALL, 'type':'geoSub2'}, "value"),
     State({'index': ALL, 'type':'input'}, "value"),
     State({'index': ALL, 'type':'inputDate'}, "value"),
     State("stored_attributes", "data"), State("stored_source", "data"),
     State("kwd_text_area", "value"), State("kwd_selected", "data")]
)
def search_company(n_clicks, geosub3, kwd_save, search_value, search_id, n_clicks_2,
                   is_open, geosub1, geosub2, inputs, inputDates, attr, source,
                   kwd_value, kwd_field):
    """Callback method for autocompleting an entity's values."""
    ctx = dash.callback_context

    ret = [[dash.no_update] * len(inputs), [dash.no_update] * len(inputDates), dash.no_update, dash.no_update]

    if not ctx.triggered:
        return ret
    
    trig = ctx.triggered[0]['prop_id']
    if trig == "search_bar.value" or trig == "search_go.n_clicks":
        result = fetch_id(search_value, search_id, attr, source)
        if result is None:
            ret[3] = 'Company not found.'
            return ret
        
        ret[0], ret[1] = result
        
        val = dash.no_update
        if not is_open:
            if n_clicks_2 is not None:
                val = n_clicks_2 + 1
            else: 
                val = 1
        ret[2] = val
                
        #return list(result)+[val, dash.no_update]
    elif trig == '{"index":"Input_1_6","type":"geoSub3"}.value':
        if ctx.triggered[0]['value'] == 0:
            return ret
        ret[0][0] = geosub1[0]
        ret[0][1] = geosub2[0]
    elif trig == 'kwd_save.n_clicks':
        ret[0][kwd_field] = kwd_value
    
    return ret

@app.callback(
    [Output("confirm", "is_open"), Output("radarPlot", "figure")],
    [Input('table', 'selected_rows'), Input('confirmQuery', 'n_clicks'),
     Input('cancelQuery', 'n_clicks')],
    [State('table', 'data')]
)
def openSelectedData(sel, confirmQuery, cancelQuery, rows):
    """Callback method for showing radar plot and possible selection as query."""
    ctx = dash.callback_context
    
    ret = [dash.no_update, dash.no_update]

    if ctx.triggered:
        trig = ctx.triggered[0]['prop_id']
        if trig == 'table.selected_rows':
            ret[0] = True
            
            r = [(k.split('_')[0],v) for k,v in rows[sel[0]].items() 
                 if k.endswith('_score')]
            
            df = pd.DataFrame(r, columns=['Attribute', 'Score'])
            ret[1] = px.line_polar(df, r='Score', theta='Attribute', line_close=True)
            
        elif trig == 'confirmQuery.n_clicks':
            ret[0] = False
        elif trig == 'cancelQuery.n_clicks':            
            ret[0] = False

    return ret

@app.callback(
    [Output("search_bar", "value"), Output("search_go", "n_clicks"),
     Output("search_selected", "data")],
    [Input('confirmQuery', 'n_clicks'), Input('search_bar_2', 'value')],
    [State('table', 'selected_rows'), State('table', 'data'), State("search_go", "n_clicks")])
def updateSelectedData(ok, val2, sel, rows, go):
    """Callback method for changing query based on selected entity from Listing."""
    ctx = dash.callback_context
    
    ret = [dash.no_update]*3

    if ctx.triggered:
        trig = ctx.triggered[0]['prop_id']
        if sel is None and trig == 'search_bar_2.value':
            ret[0] = val2
        elif trig == 'confirmQuery.n_clicks':
            company = rows[sel[0]]['name']
            
            id = rows[sel[0]]['id'].split('/')[-1][:-1]
            if go is None:
                go = 0
            ret = [company, go+1, id]

    return ret

@app.callback(
    Output("inputs_collapse", "is_open"),
    [Input("settings_go", "n_clicks")],
    [State("inputs_collapse", "is_open")],
)
def inputs_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("weights_collapse", "is_open"),
    [Input("weights_go", "n_clicks")],
    [State("weights_collapse", "is_open")],
)
def weights_collapse(n, is_open):
    """Callback method for showing/hiding weights div."""
    if n:
        return not is_open
    return is_open


@app.callback(
    [Output("advanced_menu", "is_open"), Output({'index': 'Input_0', 'type':'input0'}, "value"),
     Output("stored_attributes", "data"), Output("inputs", "children"),
     Output("weights", "children"), Output("msg3", "data")],
    [Input("advanced_go", "n_clicks"), Input("saveAdvanced", "n_clicks")],
    [State("advanced_menu", "is_open"), State("Advanced_2", "value"),
     State("Advanced_4", "value"), State("stored_source", "data"),
     State("Advanced_5", "value")],
)
def advanced_collapse(n, n2, is_open, k, method, source, apikey):
    """Callback method for showing advanced settings menu & corresponding fetching of fields."""
    ctx = dash.callback_context

    ret = [dash.no_update]*6

    if not ctx.triggered:
        return ret
    
    trig = ctx.triggered[0]['prop_id']
    if trig == 'advanced_go.n_clicks':
        ret[0] = True
    elif trig == 'saveAdvanced.n_clicks':
        if source['api_required']:
            if apikey is None or apikey == '':
                ret[5] = 'This Source requires an API key.'
                return ret
            if source['simsearch_api'] != apikey:
                ret[5] = 'Wrong API Key.'
                return ret
        
        headers = { 'api_key' : source['simsearch_api'], 'Content-Type' : 'application/json'}
        response = requests.post(source['simsearch_url']+'catalog/', json={}, headers=headers)
        d2 = {}
        children = [make_input(0, 'k', 'number', val=k)]
        if response.status_code == 200:
            d = response.json()
            if method == 'pivot_based':
                d = {dd['column']: dd['datatype'] for dd in d if dd['operation'] == 'pivot_based'}
            else:
                d = {dd['column']: dd['datatype'] for dd in d if dd['operation'] != 'pivot_based'}
            
            d2 = {k:v for k,v in d.items() if v == 'GEOLOCATION'}
            d2.update({k:v for k,v in d.items() if v != 'GEOLOCATION'})
            children += [make_input(i+1, key.capitalize(), val) 
                         for i, (key, val) in enumerate(d2.items())]
        
        sliders = make_full_sliders(d2.keys())
            
        ret[0:5] =  [False, k, d2, children, sliders]

    return ret
@app.callback(
    Output("raw_body_input", "children"),
    [Input("save", "n_clicks")],
    [State("weight_comb_sel", "value"), State("session_id", "data")]
)
def update_copy_data(n_clicks, sel, session_id):
    """Callback method for preparing download of Listing."""
    if not n_clicks:
        return dash.no_update
    with open('output/data_{}.json'.format(session_id)) as f:
        data = json.load(f)
    d = json.dumps(data[int(sel)], indent=4)
    return d


@app.callback(
    [Output("Advanced_1", "options"), Output("Advanced_1", "value")],
    [Input("Advanced_0", "value")],
)
def update_sources(file):
    """Callback method for updating the sources options."""
    with open(file) as f:
        j = json.load(f)
    
    return [[{'label' : jj['name'], 'value': jj['name']} for jj in j],
            j[0]['name']]

@app.callback(
    [Output("stored_source", "data")],
    Input("Advanced_1", "value"),
    State("Advanced_0", "value")
)
def store_source(source, file):
    """Callback method for updating the sources selection."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return [{}]
    
    with open(file) as f:
        j = json.load(f)
    
    return [jj for jj in j if jj['name'] == source]


app.clientside_callback(
    """
    function(data, value) {
        if (data === undefined)
            return;

        //Convert JSON string to BLOB.
        json = [data];
        var blob1 = new Blob(json, { type: "text/plain;charset=utf-8" });
        
        var file = "Results_" + value + ".json"
 
        //Check the Browser.
        var isIE = false || !!document.documentMode;
        if (isIE) {
            window.navigator.msSaveBlob(blob1, file);
        } else {
            var url = window.URL || window.webkitURL;
            link = url.createObjectURL(blob1);
            var a = document.createElement("a");
            a.download = file;
            a.href = link;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }        
    }
    """,
    Output('dump2', 'children'),
    Input('raw_body_input', 'children'),
    State("weight_comb_sel", "value")
)    

            
@app.callback(
    [Output("kwd_modal", "is_open"), Output("kwd_header", "children"),
     Output("kwd_text_area", "value"), Output("kwd_selected", "data")],
    [Input({'index': ALL, 'type':'kwdBtn'}, "n_clicks"),
     Input('kwd_save', "n_clicks"), Input('kwd_cancel', "n_clicks")],
    [State({'index': ALL, 'type':'input'}, "value"),
     State({'index': ALL, 'type':'input'}, "id"),
     State({'index': ALL, 'type':'kwdBtn'}, "id"),
     State({'index': ALL, 'type':'input_title'}, "children")]
)
def open_kwd_modal(kwd_n, save_n, cancel_n, input_vals, input_ids, 
                   kwd_btn_ids, field_titles):
    """Callback method for popping the keyword input popup."""
    ctx = dash.callback_context
    
    ret = [dash.no_update]*4
    if not ctx.triggered:
        return ret
    
    trig = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trig == 'kwd_save':
        ret[0] = False
    elif trig == 'kwd_cancel':
        ret[0] = False
        ret[2] = ""
    elif trig.startswith('{'):
        t = json.loads(trig)
        index = kwd_btn_ids.index(t) #find appropriate button clicked
        if kwd_n[index] is not None:
            ret[0] = True
            no = int(t['index'].split("_")[-1])
            ret[1] = 'Expand field: {}'.format(field_titles[no])
            
            in_id = {'index': f'Input_{no}', 'type': 'input'}
            index2 = input_ids.index(in_id)
            body = input_vals[index2]
            ret[2] = body if body is not None else ""
            ret[3] = index2
        
    return ret
            
if __name__ == '__main__':
    if len(sys.argv) == 1:
        port = 8095
    elif len(sys.argv) != 3:
        raise ValueError('Wrong arguments')
    else: 
        if sys.argv[1] not in ['--port', '-p']:
            raise ValueError('Wrong arguments')
        if not sys.argv[2].isnumeric():
            raise ValueError('Wrong arguments')
        port = int(sys.argv[2])
    app.run_server(debug=False, host='0.0.0.0', port=port)