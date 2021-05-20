# SimSearch UI

## Overview
SimSearch UI is an open-source system that utilizes existing [SimSearch](https://github.com/smartdatalake/simsearch) Instances for finding, exploring and navigating similar entities.

### Install
To install SimSearch UI you will need to install some necessary libraries as well, such as [Dash](https://dash.plotly.com/), [Folium](http://python-visualization.github.io/folium/) and [ElasticSearch Python Client](https://elasticsearch-py.readthedocs.io/en/v7.12.1/). The latter is necessary only for the suggestions of entities, but it can be ommited if the user does not want to utilize this feature.

### Run Service
To run the SimSearch UI, the user has to execute the `python ui.py -p 8095` or `python ui.py --port 8095`. If no arguments are passed, then the service will be executed by default on the `8095` port.

### How to include a new Source
The SimSearch UI works dynamically, since for each new Source new corresponding input fields & plots will be created, based on each field type. However, the administrator is responsible for creating the appropriate [SimSearch](https://github.com/smartdatalake/simsearch) instances in the first place. To embed them in the UI, the administrator can modify the `settings/Default.json.example` or create a new json file in the same directory. The content of each file should be a json containing one or more sources with the following format:

```json
[
   {
      "name":"Source Name",
      "simsearch_url":"http://...",
      "simsearch_api":"API_KEY",
      "api_required": false,
      "es_url":"http://...",
      "es_index":"source_index",
      "es_field":"query_field"
   }
]
```

- name: Name of the source for convenience, **required**
- simsearch_url: URL of the existing SimSearch instance, **required**
- simsearch_api: API Key for the specific source in the existing SimSearch instance, **required**
- api_required": boolean value [true,false] on whether this source is public and API Key is actually required in the UI, **required**
- es_url: Link for an ElasticSearch DB that contains the data of the source. Used for suggestions, **optional**
- es_index: Name of the specific index in the ElasticSearch, **required if** es_url is well-defined
- es_field: Name of the specific field in the index to query upon, **required if** es_url is well-defined
   

## Usage
After both the SimSearch Service and the SimSearch UI Service is on, the user can use the SimSearch UI.

### Settings
The first thing that the user will see when opening the service is a menu of general options. From there, the user can select from a pool of Sources, set the API Key manually (if data are not open) and other optional parameters for the SimSearch instances.

### Search
To search for similar entities:
- If the ElasticSearch Index with the corresponding data is on, then the user can search in the search bar for an entity, hit the search button and the input fields will be auto-completed. After that, the user can add extra weight-combinations (or none and the system will automatically calculate the best weight combination) and hit the submit button.
- Otherwise, the user can manually insert values into the input fields and search for the corresponding similar entities.

### Navigation
After the retrieval of the results, the user can navigate into the 3 tabs: the listings, the statistics plots & the individual field plots. More information on that can also be found [here](https://simplify2021.imsi.athenarc.gr/papers/SIMPLIFY_2021_paper_11.pdf).

You can try a live demo [here](http://simsearch-demo.magellan.imsi.athenarc.gr/).

***

## License

The contents of this project are licensed under the [Apache License 2.0](https://github.com/SLIPO-EU/loci/blob/master/LICENSE).

***

## Acknowledgement

This software is being developed in the context of the [SmartDataLake](https://smartdatalake.eu/) project. This project has received funding from the European Union’s [Horizon 2020 research and innovation programme](https://ec.europa.eu/programmes/horizon2020/en) under grant agreement No 825041.
