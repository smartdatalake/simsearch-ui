import pandas as pd
from shapely.ops import cascaded_union
from geopandas import GeoDataFrame
from hdbscan import HDBSCAN
from shapely.geometry import Point


def compute_clusters(pois):
    # Compute the clusters
    clusterer = HDBSCAN(min_cluster_size=2, min_samples=2, core_dist_n_jobs=-1)
    labels = clusterer.fit_predict(pois)

    tree = clusterer.condensed_tree_.to_pandas()
    cluster_tree = tree[tree.child_size > 1]
    chosen_clusters = clusterer.condensed_tree_._select_clusters()

    eps_per_cluster = cluster_tree[cluster_tree.child.isin(chosen_clusters)].\
        drop("parent", axis=1).drop("child", axis=1).reset_index().drop("index", axis=1)
    eps_per_cluster['lambda_val'] = eps_per_cluster['lambda_val'].apply(lambda x: 1 / x)
    eps_per_cluster.rename(columns={'lambda_val': 'eps', 'child_size': 'cluster_size'}, inplace=True)

    return labels, eps_per_cluster

def prepare(X, Y, C, d):
    return [(c, Point(x,y).buffer(d[c])) for (x, y, c) in zip(X,Y,C)  if c>= 0]

def cluster_shapes(pois, eps_per_cluster=None):
    f = prepare(pois.geometry.x, pois.geometry.y, pois.cluster_id, eps_per_cluster['eps'])
    f = [(k, cascaded_union([y for (x,y) in f if x == k])) for k in dict(f).keys()]
    t1 = pd.DataFrame(f, columns=['cluster_id', 'geometry'])
    t1['size'] = eps_per_cluster['cluster_size'].loc[t1.cluster_id].values
    return GeoDataFrame(t1[['cluster_id', 'size','geometry']], crs='EPSG:4326')
