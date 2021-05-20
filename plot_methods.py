import pandas as pd
import plotly.express as px
from wordcloud import WordCloud, STOPWORDS
from geopandas import GeoDataFrame
from shapely.geometry import box
from folium.plugins import MarkerCluster, Fullscreen
import folium
from folium import IFrame
from folium.plugins import HeatMap
import re
from clustering import cluster_shapes, compute_clusters
import base64
from io import BytesIO
import matplotlib.pyplot as plt
from numpy import around
from shapely.geometry import Point
from collections import Counter
from numpy import ones
import scipy
import dash
import json
from plotly.io import from_json, to_json
from filelock import FileLock


def fetch_map():
    """Method for generating folium map with custom event for clicking inside."""
    home_m = folium.Map(location=[41.8902142, 12.4900369], zoom_start=5, width=550, height=350)
    home_m.add_child(folium.LatLngPopup())
    home_m = home_m.get_root().render()
    home_p = [r.start() for r in re.finditer('}', home_m)][-1]
    hide_s = """var myCustomData = { Latitude: e.latlng.lat.toFixed(4), Longitude: e.latlng.lng.toFixed(4) }
                var event = new CustomEvent('myEvent', { detail: myCustomData })
                window.parent.document.dispatchEvent(event)"""
    home_m = '{}\n{}\n{}'.format(home_m[:home_p], hide_s, home_m[home_p:])
    return home_m


def __fetch_star(no):
    """Method that generates a ranking system for entities for spatial plots."""
    r = around(no, 1) / 0.2
    s = ""
    i = 0
    while r > 0:
        if r >= 1.0:
            s += '<span class="fa fa-star checked"></span>'
        else:
            s += '<span class="fa fa-star-half-o checked"></span>'
        i+=1
        r -= 1.0
    s += '<span class="fa fa-star-o checked"></span>' * (5-i)
    return s

def __prepare_popup(r):
    """Method that generates the popup that will contain the raking system for spatial plots."""
    pop = '<table style="width:200px"> <tr> <th colspan="3" style="text-align:center" >{}</th> </tr>'.format(r['name'])
    for key in r.keys():
        if key.endswith('score'):
            pop += '<tr> <td> {} </td> <td> {} </td> <td> {:.2f}</td> </tr>'.format(key, __fetch_star(r[key]), r[key])
            
    return folium.Popup(pop, width=300)

def return_var_plot(result, attr_name, attr_type, option=0):
    """Method that generates the corresponding plot for each attribute, based 
    on the type and the selection of the user."""
    aval = f'{attr_name}_value'
    if attr_type == 'NUMBER' or attr_type == 'DATE_TIME':
        if aval not in result[0].keys():
            return None
        vals = [r[aval] for r in result]
        if option == 0:
            fig = px.histogram(x=vals)
            fig.update_yaxes(title='Frequency')
        elif option == 1:
            fig = px.box(x=vals)
        fig.update_xaxes(title=attr_name.capitalize())            
        return fig
    elif attr_type == 'GEOLOCATION': #location
        if aval not in result[0].keys():
            return None    
    
        pois = [tuple(map(float, r[aval][7:-1].split(' '))) for r in result]
        x, y = zip(*pois)
        minx, miny, maxx, maxy = min(x), min(y), max(x), max(y)
        
        bb = box(minx, miny, maxx, maxy)
        map_center = [bb.centroid.y, bb.centroid.x]
        m = folium.Map(location=map_center, tiles='OpenStreetMap', width='100%', height='100%')
        m.fit_bounds(([bb.bounds[1], bb.bounds[0]], [bb.bounds[3], bb.bounds[2]]))
        m.add_child(Fullscreen())
        
        if option == 0:
            coords, popups = [], []
            poi_layer = folium.FeatureGroup(name='pois')
            for r, yy, xx in zip(result, y, x):
                coords.append([yy, xx])
                popups.append(__prepare_popup(r))
            poi_layer.add_child(MarkerCluster(locations=coords, popups=popups))
            m.add_child(poi_layer)    
            folium.GeoJson(bb).add_to(m)
        elif option == 1:
            scores = [r['score'] for r in result]
            HeatMap(zip(y,x,scores), radius=10).add_to(m)  
        elif option == 2:
            if 'keywords_value' not in result[0].keys():
                return None
            
            
            kwds = [r['keywords_value'] for r in result]
            scores = [r['score'] for r in result]
            

            labels, eps = compute_clusters(pois)
            
            pois = [Point(poi) for poi in pois]
            d = {'geometry': pois, 'kwd': kwds, 'score': scores, 'cluster_id': labels}
            gdf = GeoDataFrame(d, crs="EPSG:4326")
            gdf = gdf[gdf.cluster_id >= 0]
            
            aois = cluster_shapes(gdf, eps).set_index('cluster_id')
            
            means = gdf.groupby('cluster_id').agg({'score': 'mean', 'kwd': lambda x: ' '.join(x)})
            clustered_keys = pd.concat([aois, means], axis=1).reset_index(drop=False)
            
            bins = list(clustered_keys['score'].quantile([0, 0.25, 0.5, 0.75, 1]))
            
            folium.Choropleth(geo_data=clustered_keys, data=clustered_keys,
                              columns=['cluster_id','score'], bins=bins,
                              key_on='feature.properties.cluster_id',
                              fill_color='YlOrRd', fill_opacity=0.6,
                              line_opacity=0.5).add_to(m)
            
            wc = WordCloud(width = 200, height = 150, random_state=1,
                       background_color='salmon', colormap='Pastel1',
                       collocations=False, stopwords = STOPWORDS)
            
            for index, row in clustered_keys.iterrows():
                c = Counter(row['kwd'])
                s = wc.generate_from_frequencies(c)
                plt.imshow(s, interpolation='bilinear')
                plt.axis("off")
                buf = BytesIO()
                plt.savefig(buf, format='png', bbox_inches='tight')
                # Include image popup to the marker
                html = '<img src="data:image/PNG;base64,{}" style="width:100%; height:100%; display:block">'.format
                encoded = base64.b64encode(buf.getvalue()).decode()
                iframe = IFrame(html(encoded), width=300, height=150)
                popup = folium.Popup(iframe, min_width=300, max_width=300, parse_html=True) # max_width=2650
                buf.close()
                
                folium.GeoJson(row['geometry']).add_child(popup).add_to(m)
        return m.get_root().render()
    
    
    elif attr_type == 'KEYWORD_SET':
        if aval not in result[0].keys():
            return None    
    
        wc = WordCloud(width = 400, height = 300, random_state=1,
                       background_color='salmon', colormap='Pastel1',
                       collocations=False, stopwords = STOPWORDS)
        
        c = Counter()
        for r in result:
            c.update(r[aval])
        s = wc.generate_from_frequencies(c)
        
        if option == 0:
            fig = px.imshow(s, labels={})
            fig.update_xaxes(showticklabels=False)
            fig.update_yaxes(showticklabels=False)
            fig.update_traces(hovertemplate=None, hoverinfo='skip' )
            return fig
        elif option == 1:
            df = pd.DataFrame(c.most_common(10), columns=['Word', 'Frequency'])
            df = df.sort_values('Frequency', ascending=True)
            fig = px.bar(df, x="Frequency", y="Word", orientation='h')
            fig.update_yaxes(title=None)
            return fig
        
def return_stat_plot(data, sel, no):
    """Method that generates the general plots of the results."""
    if sel == 1:
        if 'similarityMatrix' not in data[no]:
            return {}
        s = pd.DataFrame(data[no]['similarityMatrix']).drop_duplicates().pivot(index='left', columns='right', values='score')
        s = s.reset_index(drop=True)
        s.columns = range(s.columns.shape[0])
            
        fig = px.imshow(s, labels=dict(x="Results", y="Results", color="Score"),)
        fig.update_layout(title_text='Weight Combination {}'.format(no+1), title_x=0.5)
        return fig
    elif sel == 2:
        df2 = pd.concat([pd.DataFrame([[x['id'],x['score']] for x in data[i]['rankedResults']]).set_index(0)[1] for i in range(no)],
                        axis=1, keys=range(no))

        pearsonr = ones((no, no))
        spearmanr = ones((no, no))
        kendalltau = ones((no, no))
        
        for i in range(no):
            for j in range(i+1,no):
                z = df2[[i, j]].dropna(how='all').fillna(0).values.T
                pearsonr[i,j] = pearsonr[j,i] = scipy.stats.pearsonr(z[0], z[1])[0]
                spearmanr[i,j] = spearmanr[j,i] = scipy.stats.spearmanr(z[0], z[1])[0]
                kendalltau[i,j] = kendalltau[j,i] = scipy.stats.kendalltau(z[0], z[1])[0]
        
        
        
        t1 = '<a href = "https://en.wikipedia.org/wiki/Pearson_correlation_coefficient/">Pearson Correlation</a>'
        t2 = '<a href = "https://en.wikipedia.org/wiki/Spearman%27s_rank_correlation_coefficient/">Spearman Correlation</a>'
        t3 = '<a href = "https://en.wikipedia.org/wiki/Kendall_rank_correlation_coefficient/">Kendall Correlation</a>'
        
        
        fig1 = px.imshow(pearsonr, labels=dict(x="Listing", y="Listing", color="Score"))
        fig1.update_xaxes(showticklabels=False)
        fig1.update_yaxes(showticklabels=False)
        fig1.update_layout(title_text=t1, title_x=0.5)
        
        fig2 = px.imshow(spearmanr, labels=dict(x="Listing", y="Listing", color="Score"))
        fig2.update_xaxes(showticklabels=False)
        fig2.update_yaxes(showticklabels=False)
        fig2.update_layout(title_text=t2, title_x=0.5)
        
        fig3 = px.imshow(kendalltau, labels=dict(x="Listing", y="Listing", color="Score"))
        fig3.update_xaxes(showticklabels=False)
        fig3.update_yaxes(showticklabels=False)
        fig3.update_layout(title_text=t3, title_x=0.5)  
        
        return [fig1, fig2, fig3]
        
 
def update_plots_general(sel, field, attr_name, attr_type, session_id):
    """Method that returns or generates a general plot."""
    with open('output/plots_{}.json'.format(session_id), 'r') as f:
        plots = json.load(f)
    if plots[1][field][sel][0] is not None:
        return [fig_from_json(fig) for fig in plots[1][field][sel]]
    
    with open('output/data_{}.json'.format(session_id)) as f:
        data = json.load(f)
    no = len(data)
    figs = []
    for w in range(no):
        fig = return_var_plot(data[w]['rankedResults'], attr_name, attr_type, sel)
        figs.append(fig if fig is not None else dash.no_update)


    lock = FileLock("output/locks_{}.lock".format(session_id))
    with lock:
        with open('output/plots_{}.json'.format(session_id), 'r') as f:
            plots = json.load(f)
        plots[1][field][sel] = [fig_to_json(fig) for fig in figs]
        with open('output/plots_{}.json'.format(session_id), 'w') as f:
            json.dump(plots, f, indent=4)
        
    return figs

def fig_to_json(fig):
    """Method that transforms a plot from json."""
    if isinstance(fig, str):
        return fig
    elif fig == dash.no_update:
        return None
    else:
        return to_json(fig, pretty=True)
    
def fig_from_json(fig):
    """Method that transforms a plot to json."""
    if fig == None:
        return dash.no_update
    else:
        try:
            fig = from_json(fig)
        except:
            pass
        finally:
            return fig
