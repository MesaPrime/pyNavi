import geopandas
import networkx
import osmnx
from typing import Optional
import shapely


# mapMultiGraph: networkx.MultiDiGraph = osmnx.graph_from_xml(r"../data/test.osm")
mapMultiGraph: networkx.MultiDiGraph = osmnx.graph_from_place("Piedmont, California, USA", network_type="drive")
graph, axis = osmnx.plot_graph(mapMultiGraph, show=False)

gdf_nodes, gdf_edges = osmnx.graph_to_gdfs(mapMultiGraph)
print(gdf_edges.info())
print(gdf_edges.head())

origin: geopandas.geodataframe.GeoDataFrame = gdf_nodes.sample()
desi: geopandas.geodataframe.GeoDataFrame = gdf_nodes.sample()

path = osmnx.k_shortest_paths(mapMultiGraph, origin.iloc[0].name, desi.iloc[0].name, 1)
for _ in path:
    length = osmnx.utils_graph.route_to_gdf(mapMultiGraph, _)['length']
    print(_)
    print(sum(length))


def downloadFile(area: Optional[list], ):
    pass
