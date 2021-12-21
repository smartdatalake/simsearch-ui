import dash
from dash_table.Format import Format, Scheme
from elasticsearch import Elasticsearch
from itertools import islice
from dateutil.parser import parse

def fetch_input(inputs, sliders, i, attr):
    """Method for returning input value with corresponding weights for the submission query."""
    name = inputs[0]['props']['children']['props']['children'].lower()
    dtype = attr[name]
    
    if dtype == 'NUMBER':
        if 'value' not in inputs[1]['props']['children']['props']:
            return None
        val = inputs[1]['props']['children']['props']['value']
        if val is None or val == '':
            return None
        val = str(val)
    elif dtype == 'KEYWORD_SET':
        if 'value' not in inputs[1]['props']['children'][0]['props']:
            return None        
        val = inputs[1]['props']['children'][0]['props']['value']
        if val is None or val == '':
            return None
    elif dtype == 'GEOLOCATION':
        if 'value' not in inputs[1]['props']['children'][0]['props'] or 'value' not in inputs[1]['props']['children'][1]['props']:
            return None
        lon = inputs[1]['props']['children'][0]['props']['value']
        lat = inputs[1]['props']['children'][1]['props']['value']
        if lon is None or lon == '' or lat is None or lat == '':
            return None
        val = 'POINT ({} {})'.format(lon, lat)
    elif dtype == 'DATE_TIME':
        if 'date' not in inputs[1]['props']['children'][0]['props']:
            return None        
        val = inputs[1]['props']['children'][0]['props']['date']
        if val is None or val == '':
            return None        
    else:
        return None

    return {'column': name, 'value': val, 'weights': create_weights(sliders, i)}


def create_weights(sliders, i):
    """Method for returning the weights of a specific input."""
    w = []
    for sl in sliders[2:-1]:
        p = sl['props']['children'][i]['props']['children'][0]['props']
        if sl['props']['style']['display'] != 'none' and not p['disabled']:
            w.append(p['value'][0])
    return w


def transform_field(x, attr_type):
    """Method for transforming a field from the returned entities to the corresponding format."""
    if x is None or x == 'NaN':
        return None
    if attr_type == 'KEYWORD_SET':
        return x
    if attr_type == 'NUMBER':
        val = int(float(x)) if x != '' else 0
        return val
    if attr_type == 'GEOLOCATION' or attr_type == 'DATE_TIME':
        return x
    if attr_type == 'id':
        if x.startswith('http'):
            return '[{}]({})'.format(x, x)
        else:
            return x

def flatten(results, attr):
    """Method that flattens the response json into the appropriate format for internal manipulation."""
    final = []
    seen = set()
    for r in results:
        d = {}
        
        if r['id'] in seen:
            continue
        seen.add(r['id'])
        
        d['id'] = transform_field(r['id'], "id")
        #d['name'] = name
        # d['name'] = r['name']
        d['name'] = r['extraAttributes']['name']
        for key in ['score', 'rank', 'exact']:
            d[key] = r[key]
        for a in r['attributes']:
            name = a['name']
            d['{}_value'.format(name)] = transform_field(a['value'], attr[name])
            d['{}_score'.format(name)] = a['score']
        final.append(d)
    return final


def mod_cols(results):
    """Method that modifies the format of the columns of the datatable."""
    
    order = ['rank', 'name', 'score', 'id']
    for i in results[0].keys():
        if i.endswith('_value'):
            order.append(i)
    
    cols = []
    for i in order:
        if i != 'id':
            name = i[:-6] if i.endswith('_value') else i
            if isinstance(results[0][i], str):
                cols.append({"name": name, "id": i, "type":'text'})
            elif isinstance(results[0][i], float):
                cols.append({"name": name, "id": i, "type":'numeric', "format": Format(precision=2, scheme=Scheme.fixed)})
            elif isinstance(results[0][i], int):    
                cols.append({"name": name, "id": i, "type":'numeric', "format": Format()})
            elif isinstance(results[0][i], list):
                cols.append({"name": name, "id": i})
        else:
            cols.append({"name": i, "id": i, 'presentation':'markdown'})
    return cols

def fetch_ids(name, source):
    """Method that fetches suggestions from an ElasticSearch Index."""
    if name is None or name == '' or 'es_url' not in source:
        return None

    client = Elasticsearch(hosts=source['es_url'])
    field = source['es_field']
    
    names = name.lower().split(' ')
    query = {"track_scores":"true",
             "_source": [field, 'id'],
             "query" : {"bool" : {
                     "must" : {"prefix": {field: names[0]}},
                     "filter" : [{"bool" : {"should" : [{"prefix" : {field : w}} for w in names[1:]]}}]
                     }}}
    
    response = client.search(index=source['es_index'], body=query)
    
    d = ((hit['_source']['id'], hit['_source'][field]) for hit in response['hits']['hits'])
    d = list(islice(d, 10))
    return d


def fetch_id(name, id, attr, source):
    """Method that fetches a specific entity from an ElasticSearch Index,
    with all the appropriate fields."""
    if name is None or name == '' or 'es_url' not in source:
        return None

    client = Elasticsearch(hosts=source['es_url'])

    field = source['es_field']
    fields = [field] + list(attr.keys())

    query = {"track_scores":"true",
             "_source": fields,
             "query": {"bool" : {"must" : {"match" : { field : name}},
                                 "should": {"prefix" : { "id" : id }}}}}

    response = client.search(index=source['es_index'], body=query)
    for hit in response['hits']['hits']:
        break
    
    d1, d2 = [], []
    for key in attr:
        if key in hit['_source']:
            if attr[key] == 'GEOLOCATION':
                d1.append(float(hit['_source'][key].split(',')[1]))
                d1.append(float(hit['_source'][key].split(',')[0]))
            elif attr[key] == 'DATE_TIME':
                d2.append(parse(hit['_source'][key]).date())
            elif attr[key] == 'NUMBER':         
                val = hit['_source'][key]
                val = int(float(hit['_source'][key])) if val is not None else None
                d1.append(val)
            else:
                d1.append(','.join(set(hit['_source'][key].split(','))))
        else:
            if attr[key] == 'GEOLOCATION':
                d1.append(dash.no_update)
                d1.append(dash.no_update)
            elif attr[key] == 'DATE_TIME':
                d2.append(dash.no_update)
            else:
                d2.append(dash.no_update)
    
    return d1, d2