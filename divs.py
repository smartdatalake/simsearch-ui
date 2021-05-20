import dash_core_components as dcc
import dash_html_components as html
from styles import style_div, style_drop_list, active_color, active_light_color, active_dark_color
import dash_table
import os


def make_store_plots(attr, w):
    """Init value for caching plots"""
    fields = {'NUMBER': ['Histogram', 'Boxplot'],
              'DATE_TIME': ['Histogram', 'Boxplot'],
              'GEOLOCATION': ['Clustered POIS', 'HeatMap', 'Clustered Wordclouds'], 
              'KEYWORD_SET': ['WordCloud', 'Top-10 Histogram']}
    
    stats = [[None]*w, [None]*3]
    plots = [ [[None]*w]*len(fields[v]) for k, v in attr.items()]
    
    return [stats, plots]


def make_full_sliders(attr=[]):
    """Create dynamic sliders for all fields"""
    s = [html.Span(id='shrink', title='Remove Weight Combination', children=[html.I(className="fas fa-minus-circle ml-2")], style={'padding-top': '40px', 'color':'grey'})]
    t = [html.Div(children=[html.P(id={'index': f'pw_{no+1}', 'type':'slider_title'}, children=t.capitalize()) for no, t in enumerate(attr)], style={'margin-left':'20px', 'color':'gray'})]
    w = [__make_sliders(no, len(attr)) for no in range(4)] 
    e = [html.Span(id='expand', title='Add Weight Combination', children=[html.I(className="fas fa-plus-circle ml-2")], style={'padding-top': '40px', 'color': active_color})]
    return s + t + w + e

def __make_sliders(no, f):
    """Create dynamic sliders for a specific field"""
    style = {'width':'20%', 'display': 'none'}
    return html.Div(id={'index': f'Slider_{no}', 'type':'slider'}, 
                    children=[__make_slider(no, i) for i in range(1,f+1)], style=style)

def __make_slider(no1, no2):
    """Create single dynamic slider for a specific field"""
    return html.Div(children=[
        dcc.RangeSlider(id={'index': f'Slider_{no1}_{no2}', 'type': 'slider_value', 'col':no1},
                        disabled=True, className='slider',
                        min=0, max=1, step=0.01, value=[1.0],
                        marks= {i/10: str(i/10) for i in range(0, 11, 2)}),
        ], style=style_div)


def make_input(no, text, input_type=None, val=None):
    """Create dynamic input for a specific field type"""
    p = html.Div(children=html.P(id={'index': f'p_{no}', 'type':'input_title'}, 
                                 children=text), style=style_div)
    
    if no == 0:
        if val is None:
            val = '50'
        c = dcc.Input(id={'index': f'Input_{no}', 'type':'input0'},
                       value=val, type='text', pattern='\d*?',
                       style={'width':'50%', 'margin-left':'25%'})
        style={'display':'block', 'width':'10%', 'margin-left': '20px'}
        c = html.Div(c)
    elif input_type == 'NUMBER':
        c = dcc.Input(id={'index': f'Input_{no}', 'type':'input'},
                      type='text', pattern='\d*?',
                      style={'width':'70%', 'margin-left':'15%'})
        style={'display':'block', 'width':'10%', 'margin-left': '20px'}
        c = html.Div(c)
    elif input_type == 'GEOLOCATION':
        c = [dcc.Input(id={'index': f'Input_{no}_1', 'type':'input'},
                       debounce=True, type='text', pattern='\d*\.?\d*',
                       style={'width':'40%', 'margin-right':'5px'}),
             dcc.Input(id={'index': f'Input_{no}_2', 'type':'input'},
                       debounce=True, type='text', pattern='\d*\.?\d*',
                       style={'width':'40%'}),
             html.Span(id={'index': f'Input_{no}_3', 'type':'geoBtn'},
                       title="Pick from map", 
                       children=[html.I(className="fas fa-globe ml-2")],
                       style={'color':active_color}),
             dcc.Input(id={'index': f'Input_{no}_4', 'type':'geoSub1'}, 
                       type='text', style={'display':'none'}),
             dcc.Input(id={'index': f'Input_{no}_5', 'type':'geoSub2'},
                       type='text', style={'display':'none'}),
             dcc.Input(id={'index': f'Input_{no}_6', 'type':'geoSub3'},
                       value=0, type='text', style={'display':'none'})
             ]
        style={'display':'block', 'width':'15%', 'margin-left': '20px'}
        c = html.Div(c)
    elif input_type == 'KEYWORD_SET':
        c = [dcc.Input(id={'index': f'Input_{no}', 'type':'input'},
                      type='text', pattern='.*?', style={'width':'100%'}),
             html.Span(id={'index': f'Input_{no}', 'type':'kwdBtn'},
                       title="Expand keyword set", 
                       children=[html.I(className="fas fa-expand-arrows-alt ml-2")],
                       style={'color':active_color})]
        style={'display':'block', 'width':'25%', 'margin-left': '20px'}
        c = html.Div(children=c, style={'display':'flex'})
    elif input_type == 'DATE_TIME':
        c = dcc.DatePickerSingle(id={'index': f'Input_{no}_1', 'type':'inputDate'},
                                  #date=date.today(),
                                  display_format="DD/MM/YYYY",
                                  clearable=True,
                                  ),
        style={'display':'block', 'width':'10%', 'margin-left': '20px', 
               'margin-right': '20px'}
        c = html.Div(c)
            

        
    return html.Div(children=[p, c], style=style)

def make_advanced(no, text, text2="", input_type=None):
    """Create advanced settings"""
    children = [html.Div(children=[html.P(children=text, style={'margin-right':'10px'}),
                html.Span(title=text2, children=[html.I(className="fas fa-info-circle fa-xs info")],
                          style={'color':active_color})],
                style={'display':'flex', 'justify-content': 'center', 'width':'40%'})]
    if input_type == 'number':
        pattern = '\d*?'
    else:
        pattern = '.*?'
    
    if no == 0:
        d = './settings/'
        options = options=[{'label' : f.split('.')[0], 'value': d+f}
                           for f in os.listdir(d)]
        
        children += [html.Div(children=dcc.Dropdown(id='Advanced_0', clearable=False, searchable=False, 
                                                    #options=[{'label' : 'Default', 'value': "./creds.json"},
                                                    #         ],
                                                    options=options,
                                                    value="./settings/Default.json",
                                                    style={'width':'100%'}),
                              style={'width':'30%', 'margin-bottom':'5px'})]        
    elif no == 1:
        children += [html.Div(children=dcc.Dropdown(id='Advanced_1', clearable=False, searchable=False, 
                                                    options=[], style={'width':'100%'}),
                              style={'width':'30%', 'margin-bottom':'5px'})]     
    elif no == 2:
        children += [html.Div(children=dcc.Input('Advanced_2', value='50', type='text', pattern=pattern, style={'width':'25%'}), style={'margin-bottom':'5px'})]
    elif no == 3:
        children += [html.Div(children=dcc.Input('Advanced_3', type='text', pattern=pattern, style={'width':'30%'}), style={'margin-bottom':'5px'})]
    elif no == 4:
        children += [html.Div(children=dcc.Dropdown(id='Advanced_4', clearable=False, searchable=False, 
                                                    options=[{'label' : 'Threshold', 'value': "threshold"},
                                                             {'label' : 'Partial Random Access', 'value': "partial_random_access"},
                                                             {'label' : 'No Random Access', 'value': "no_random_access"},
                                                             {'label' : 'Pivot Based', 'value': "pivot_based"}
                                                             ],
                                                    value="threshold", style={'width':'100%'}),
                              style={'width':'30%', 'margin-bottom':'5px'})]
    elif no == 5:
        children += [html.Div(children=dcc.Input('Advanced_5', type='text', pattern=pattern, style={'width':'100%'}), style={'margin-bottom':'5px'})]        
    return html.Div(children=children, style={'display':'flex', 'width':'100%'})


def make_tabs():
    """Create tabs for navigation"""
    return dcc.Tabs(id='tabs', value='listings', children=[__make_listings_tab(), 
                                                           __make_statistics_tab(),
                                                           __make_visualizations_tab()],
                    style={'display':'none'})

def __make_listings_tab():
    """Create tab 1 for listings"""    
    table = dash_table.DataTable(id='table', data=[], style_table={'width':'90%', 'margin-left':'5%'},
                                 sort_action="native", page_action="none", row_selectable="single", 
                                 #style_cell={'whiteSpace': 'normal','height': 'auto',},
                                 style_cell={'maxWidth': 0},
                                 style_data_conditional=[{'if': {'row_index': 'odd'},'backgroundColor': 'rgb(230, 230, 230)'}],
                                 style_header={'backgroundColor': active_dark_color,'fontWeight': 'bold', 
                                               'color': '#ffffff', 'whiteSpace': 'normal', 'height': 'auto',
                                               'overflow': 'auto'},
                                 #fixed_rows = {'headers': True, 'data': 0}
                                 css=[{'selector': '.dash-spreadsheet td div',
                                       'rule': '''
                                           line-height: 15px;
                                           max-height: 30px; min-height: 30px; height: 30px;
                                           display: block;
                                           overflow-y: hidden;
                                           '''
                                     }],
                                 tooltip_duration=None,
                                 )
    
    
    
    tab = dcc.Tab(id='tab_1', label='Listings', value="0",
                      children= [
                          html.P(id='raw_body_input', style={'display':'none'}),
                          html.Div(children=[dcc.Dropdown(id='weight_comb_sel', clearable=False, searchable=False,
                                    options=[{'label' : '', 'value': "0"}], value="0",
                                    style={'width':'40%', 'margin-right':'10px'}),
                                             html.Span(id='save', title='Save Listing', children=[html.I(className="fas fa-save ml-2")], style={'color':active_color})],
                                   style=style_drop_list),
                              dcc.Loading(table)
                              ], style={'border-top-color': active_light_color})
    return tab

def __make_statistics_tab():
    """Create tab 2 for statistic plots"""    
    tab = dcc.Tab(id='tab_2', label='Statistics', value="1",
                  children=[
                      html.Div(children=[html.H2('Intra-Correlations', style=style_div),
                                         dcc.Loading(html.Div(id='intra_div', children=[],
                                             style={'display':'flex'})),
                                         html.H2('Inter-Correlations', style=style_div),
                                         dcc.Loading(html.Div(children=[
                                             html.Div(style={'width':'33%'}, children=dcc.Graph(id={'index': f'fig_2_2_{i}', 'type':'interplot'}, style={'width':'100%'})) for i in range(1,4)], 
                                             style={'display':'flex'})
                                         )])
                      
                      
                      ])
    return tab

def fill_intra(no):
    """Create dynamic plots for statistics"""    
    p = f'{100 // no}%'
    return [html.Div(style={'width':p}, children=dcc.Graph(id={'index': f'fig_2_1_{i}', 'type':'intraplot'},
                                                           style={'width':'100%'})) for i in range(no)]

def __make_visualizations_tab():
    """Create tab 3 for field plots"""    
    tab = dcc.Tab(id='tab_3', label='Visualizations', value="2",
                  children=[])
        
    return tab

def fill_visualizations_tab(query, attr, no):
    """Create dynamic plots for fields"""   
    fields = {'NUMBER': ['Histogram', 'Boxplot'],
              'DATE_TIME': ['Histogram', 'Boxplot'],
              'GEOLOCATION': ['Clustered POIS', 'HeatMap', 'Clustered Wordclouds'], 
              'KEYWORD_SET': ['WordCloud', 'Top-10 Histogram']}
    
    total_children = []
    #for i, (key, val) in enumerate(attr.items()):
    for i, item in enumerate(query):
        key = item['column']
        val = attr[key]
        field = key.capitalize()
        
        header = html.H2(id={'index': f'title_3_{i}', 'type':'title'},
                         children=field.capitalize(), style=style_div)
        dropdown = dcc.Dropdown(
                                id={'type':'sel', 'field': i}, 
                                #id={'index': f'sel_3_{i}', 'type':'sel', 'field': i}, 
                                clearable=False, searchable=False,
                                options=[{'label' : v, 'value': str(vi)} for vi,v in enumerate(fields[val])],
                                value="0", style={'width':'40%', 'margin-left':'20px'})
        children = [html.Div(children= [header, dropdown], style=style_div)]
        if val != 'GEOLOCATION':
            p = f'{100 // no}%'
            children += [dcc.Loading(html.Div([html.Div(style={'width':p}, children=dcc.Graph(id={'index': j, 'field': i, 'type':'plot2'}, style={'width':'100%'})) for j in range(no)], style={'display':'flex'}))]
        else:
            p = f'{1200 // no}px'
            children += [dcc.Loading(html.Div([html.Div(children=html.Iframe(id={'index': j, 'field': i, 'type':'plot1'}, width=p, height='300px'), style={'margin-left': '15px'}) for j in range(no)], style={'display':'flex'}))]
        children += [html.Hr()]
        total_children += [html.Div(id=f'div_3_{i}', children=children)]
    
    return html.Div(total_children) 

