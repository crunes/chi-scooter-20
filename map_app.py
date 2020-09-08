import json
import os

import boto3
from boto3 import session
from botocore.exceptions import ClientError

from dotenv import load_dotenv
load_dotenv()

import geopandas as gpd
from geopandas import GeoDataFrame
from shapely.geometry import Point

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from urllib.request import urlopen
import plotly.graph_objects as go

import dash
import dash_core_components as dcc
import dash_html_components as html

import pandas as pd
import numpy as np

from time import ctime



client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

zip_boundaries = gpd.read_file("https://data.cityofchicago.org/resource/unjd-c2ca.geojson")
ca_boundaries = gpd.read_file("https://data.cityofchicago.org/resource/igwz-8jzy.geojson")
ward_boundaries = gpd.read_file("https://data.cityofchicago.org/resource/k9yb-bpqx.geojson")

geographies = {'zip':
                   {'path': '../data/Boundaries - ZIP Codes.geojson',
                    'gdf': zip_boundaries},
               'ward':
                   {'path': '../data/Boundaries - Wards (2015-).geojson',
                    'gdf': ward_boundaries},
               'community':
                   {'path': '../data/Boundaries - Community Areas (current).geojson',
                    'gdf': ca_boundaries}}

def get_data():
    '''
    Returns a dictionary of scooter snapshot data
    '''
    snapshots = {}
    providers = ['lime','bird']

    for org in providers:
        i = 0
        if org not in snapshots:
            snapshots[org] = []

        for snapshot in client.list_objects_v2(
        Bucket=os.getenv("S3_BUCKET"), Prefix=org+"/2020/09/08/19", MaxKeys=1000)["Contents"]:
        # Ignore irrelevant keys
            if "samplestring" not in snapshot["Key"]:
                #print("Valid key", i)
                snapshot_obj = client.get_object(Bucket=os.getenv("S3_BUCKET"), Key=snapshot["Key"])
                snapshot_data = json.load(snapshot_obj["Body"])
                snapshots[org].append(snapshot_data)
                i+=1

        print(f"Loaded {len(snapshots[org])} for {org}")

    return snapshots


def extract_time(json_obj):
    '''
    Check if a JSON object has time
    '''
    try:
        return int(json_obj['last_updated'])

    except KeyError:
        return 0


def sort_by_time(list_json):
    '''
    Sort a list of JSON objects by a certain key

    Inputs:
    - list_json (list): a list of JSON objects

    Returns: a sorted list
    '''
    return list_json.sort(key=extract_time)


def build_df_dict():
    '''
    TK
    '''
    df_dict = {}

    for org in providers:
        i = 0
        print("Working with...", org.capitalize())
        if org not in df_dict.keys():
            df_dict[org] = {'df': None, 'color': None, 'time': None}

        while i < len(snapshots[org]):
            if 'bikes' in snapshots[org][i]['data']:
                break
            i += 1

        print("    Looking at", i, "in list")

        df_dict[org]['df'] = snapshots[org][i]['data']['bikes']
        df_dict[org]['time'] = snapshots[org][i]['last_updated']

        if org == 'lime':
            df_dict[org]['color'] = 'gold'
        elif org == 'bird':
            df_dict[org]['color'] = 'steelblue'

    return df_dict


def build_gdf_list(df_dict):
    '''
    Builds a GeoDataFrame given a dictionary of pandas DataFrames,
    where each DataFrame contains lat/lon columns

    Inputs:
    - df_dict (dict): a dictionary of pandas DataFrames

    Returns a list of tuples of the provider and corresponding GeoDataFrame
    '''
    gdfs = []
    for provider in df_dict:
        current = df_dict[provider] # This is a dictionary

        # Initialize new keys
        current['geo_df'] = None
        current['str_time'] = None

        # Create Point objects
        df = pd.DataFrame(current['df']) # CONVERT TO A DATAFRAME

        # Make sure lat/lon are numeric
        long = pd.to_numeric(df.lon)
        lat = pd.to_numeric(df.lat)

        #print("Converting lat/lon to Point objects...")
        geometry = [Point(xy) for xy in zip(long, lat)]
        df = df.drop(['lon', 'lat'], axis=1)

        crs = {'init': 'epsg:4326'}

        # Add values to new keys
        current['geo_df'] = GeoDataFrame(df, crs=crs, geometry=geometry)
        current['str_time'] = ctime(current['time'])

        gdfs.append((provider, current['geo_df']))

    return gdfs


def count_by_provider(df_dict):
    '''
    Creates a new GeoDataFrame with all scooters by provider
    '''
    gdfs = build_gdf_list(df_dict)
    all_scooters = pd.DataFrame()

    for provider, gdf in gdfs:
        #scooters = gpd.GeoDataFrame(gdf)
        print("Number of", provider.capitalize(), "scooters:", gdf.shape[0])
        gdf['provider'] = provider

        if provider == 'lime':
            gdf = gdf.drop('vehicle_type', axis=1)

        all_scooters = all_scooters.append(gdf)

    print("Total number of scooters:", all_scooters.shape[0])

    return all_scooters


def open_geojson(filepath):
    '''
    Given a filepath to a GeoJSON object, return the GeoJSON object

    Inputs:
    - filepath (str): path to GeoJSON object

    Returns: a GeoJSON object
    '''
    with open(filepath) as f:
        geojson = json.load(f)

        return geojson


def get_count_by(geo_str, geo_dict):
    '''
    Returns a pandas DataFrame with the coutns of scooters by the given geographic level

    Inputs:
    - geo_str (str): geographic level i.e., 'zip', 'ward', 'comarea'
    - geo_dict (dict): stores path filename of corresponding GeoJSON and
                       GeoDataFrame

    Returns corresponding pandas DataFrame and a GeoJSON
    '''
    geojson = open_geojson(geo_dict[geo_str]['path'])

    scooters_by = gpd.sjoin(all_scooters, geo_dict[geo_str]['gdf'], how="right", op='within')
    n_by = scooters_by.groupby(geo_str).size().reset_index(name='count')

    print("Minimum scooters:", n_by['count'].min())
    print("Maximum scooters:", n_by['count'].max())

    return geojson, n_by


def construct_locations(geo_str, geojson, df):
    '''
    Defines a 'locations' variable in both GeoJSON and DataFrame objects

    Inputs:
    - geo_str (str): geographic level i.e., 'zip', 'ward', 'community'
    - geojson (GeoJSON): corresponding GeoJSON (output from get_count_by function)
    - df (pandas DataFrame): corresponding DataFrame (output from get_count_by function)

    Returns None, updates geojson and df in place

    '''
    if geo_str == 'community':
        df['locations'] = df[geo_str]
        for feature in geojson['features']:
            feature['properties']['locations'] = feature['properties'][geo_str]

    else:
        df['locations'] = geo_str.upper() + ' ' + df[geo_str]
        for feature in geojson['features']:
            feature['properties']['locations'] = geo_str.upper() + ' ' + feature['properties'][geo_str]

    return None


def plot_scooters(geo_str, geo_dict):
    '''
    Produces a plotly.graph_object counting the number of scooters at the given
    geographic level

    Inputs:
    - geo_str (str): geographic level i.e., 'zip', 'ward', 'community'
    - geo_dict (dict): stores path filename of corresponding GeoJSON and
                       GeoDataFrame

    Returns a plotly Figure
    '''

    geojson, df = get_count_by(geo_str, geo_dict)
    construct_locations(geo_str, geojson, df)

    fig = go.Figure(data=go.Choropleth(
                            locations=df['locations'], geojson=geojson,
                            #featureidkey='properties.'+geo_str,
                            featureidkey='properties.locations',
                            z=df['count'].astype(float),
                            colorscale='Blues',
                            autocolorscale=False,
                            #text=df['text'],
                            marker_line_color='white',
                            colorbar_title="Number of scooters"
                            ))

    fig.update_geos(fitbounds='locations', visible=False)

    if geo_str == 'community':
        title_sub = 'community area'
    elif geo_str == 'zip':
        title_sub = geo_str.upper() + ' code'
    else:
        title_sub = geo_str

    fig.update_layout(
        #margin={"r":0,"t":0,"l":0,"b":0},
        title_text='Number of scooters by ' + title_sub
    )
    #fig.show()

    return fig



app = dash.Dash(__name__, external_stylesheets='https://codepen.io/charmaine-runes/pen/ZEWvdyd.css'
app.layout = html.Div([
    dcc.Tabs([
        dcc.Tab(label="Ward", children=dcc.Graph(figure=fig_ward)),
        dcc.Tab(label="ZIP Code", children=dcc.Graph(figure=fig_zip)),
        dcc.Tab(label="Community Area", children=dcc.Graph(figure=fig_ca)),
    ])
])


if __name__ == '__main__':

    snapshots = get_data()
    for provider, data in snapshots.items():
        sort_by_time(data)
    df_dict = build_df_dict()
    all_scooters = count_by_provider(df_dict)

    fig_ward = plot_scooters('ward', geographies)
    fig_zip = plot_scooters('zip', geographies)
    fig_ca = plot_scooters('community', geographies)

    app.run_server(debug=True)
