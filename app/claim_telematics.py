import configparser
import os
import re
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import teleroot
from typing import Optional
from teleroot.trip import normalize
from teleroot.utilities import timeseries
from teleroot.utilities import general_utilities
from teleroot.utilities import time_utilities
import boto3
import datetime
import warnings
import datetime
from geopy.distance import geodesic
import folium
from datetime import timedelta
import sys
from app.utils import *

warnings.filterwarnings("ignore")
MIN_DISPLAY_SPEED_MPS = -2
MAX_DISPLAY_SPEED_MPS = 50
XLIM_DISPLAY_BUFFER = 0.025
def download_file(data_file_name):
    try:
        return boto3.resource('s3').Bucket('root-production-telematics').Object(data_file_name).get()['Body']
    except:
        return None

def get_trip(trip_file):
    trip=download_file(trip_file)
    if trip is None:
        return None
    try:
        trip = normalize.Trip(trip)
        trip.clean()
        trip.preprocess()
    except:
        return(None)
    return trip


def plot_multiple_trip(trip_list,
                 show_map=True,
                 start_end = True,
                 accident_location = None,
                 **kwargs):


    def _plot_dataframe_intervals_on_map(trip, map_object, left, right, trip_num, dataframe: pd.DataFrame, **kwargs):
        for i, row in dataframe.iterrows():
            if row['start'] >= left or row['end'] <= right:
                folium.PolyLine(list(zip(trip.gps.latitude.loc[max(row['start'], left):min(row['end'], right)],
                                         trip.gps.longitude.loc[max(row['start'], left):min(row['end'], right)])),
                                **kwargs).add_to(map_object)


    def _plot_map():
        colors = ['red', 'blue', 'green', 'purple', 'orange', 
                  'darkred', 'lightred', 'darkblue', 'darkgreen', 'cadetblue', 
                  'darkpurple', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']
        
        trip = trip_list[0]
        time_offset = trip.gps.timestamp.min()
        left = trip.gps.timestamp.min()
        right = max(trip.gps.timestamp.loc[trip.gps.timestamp<trip.meta['end_timestamp']])
        window_width = (right - left).total_seconds()
        window_xlims = ((left - time_offset).total_seconds() - window_width * XLIM_DISPLAY_BUFFER,
                    (right - time_offset).total_seconds() + window_width * XLIM_DISPLAY_BUFFER)

        plt.figure(figsize=kwargs.get('figsize', (12, 12)))
        if trip.has_gps and 'latitude' in trip.gps.columns and 'longitude' in trip.gps.columns:
            m = folium.Map(location=[trip.gps.latitude.loc[left:right].median(),
                                        trip.gps.longitude.loc[left:right].median()],
                            tiles="OpenStreetMap", zoom_start=kwargs.get('zoom_start', 13))
            folium.PolyLine(list(zip(trip.gps.latitude.loc[left:right],
                                        trip.gps.longitude.loc[left:right])), color='black').add_to(m)
            if trip.trip_end < right:
                folium.PolyLine(list(zip(trip.gps.latitude.loc[trip.trip_end:right],
                                            trip.gps.longitude.loc[trip.trip_end:right])), color='gray', weight=3.0).add_to(m)
        for i in range(1,len(trip_list)):
            trip = trip_list[i]
            time_offset = trip.gps.timestamp.min()
            left = trip.gps.timestamp.min()
            right = max(trip.gps.timestamp.loc[trip.gps.timestamp<trip.meta['end_timestamp']])
            window_width = (right - left).total_seconds()
            window_xlims = ((left - time_offset).total_seconds() - window_width * XLIM_DISPLAY_BUFFER,
                        (right - time_offset).total_seconds() + window_width * XLIM_DISPLAY_BUFFER)

            if trip.has_gps and 'latitude' in trip.gps.columns and 'longitude' in trip.gps.columns:
                folium.PolyLine(list(zip(trip.gps.latitude.loc[left:right],
                                         trip.gps.longitude.loc[left:right])), color=colors[i%len(colors)]).add_to(m)
                if trip.trip_end < right:
                    folium.PolyLine(list(zip(trip.gps.latitude.loc[trip.trip_end:right],
                                             trip.gps.longitude.loc[trip.trip_end:right])), color='gray', weight=3.0).add_to(m)
                #_plot_dataframe_intervals_on_map(trip, m, left, right, i, trip.stops, color='red', weight=3.0)
                #_plot_dataframe_intervals_on_map(trip, m, left, right, i, trip.turns[trip.turns.direction == 'left'], color='blue', weight=3.0)
                #_plot_dataframe_intervals_on_map(trip, m, left, right, i, trip.turns[trip.turns.direction == 'right'], color='green', weight=3.0)
                if start_end and i != (len(trip_list)-1):
                    continue
        if accident_location is not None:
            folium.Marker(accident_location, popup='<i>'+str(right)+'</i>', tooltip = 'Accident Site', icon=folium.Icon(color='black')).add_to(m)
        return m

    return _plot_map()



def get_data_file_name(id_list, trip_id = True):
    if trip_id:
        data_file_name_list = []
        for trip_id in id_list:
            data_file_name = pd.read_sql_query(
             ''' 
            select data_file_name from telematics_public.trips where id = '%s'
            '''%trip_id,connection


                )
            data_file_name_list.append(data_file_name.iloc[0,0])
        return(data_file_name_list)
    else:
        data_file_name_list = []
        for user_id in id_list:
            data_file_name = pd.read_sql_query(
                ''' 
            WITH temp1(telematics_user_id, trip_count, start_time, end_time, duration) AS
  (SELECT t1.telematics_user_id,
          count(t1.data_file_name),
          min(t1.start) AS start_time,
          max(t1.end) AS end_time,
          max(t1.end) - min(t1.start) AS duration
   FROM telematics_public.trips t1
   WHERE t1.gps_coordinates_disabled != 'true'
     AND t1.start > 2015
     AND t1.end < CURRENT_DATE
   GROUP BY t1.telematics_user_id
   HAVING DATEDIFF(DAY, start_time, end_time)>=21 and telematics_user_id = '%s')
SELECT t1.telematics_user_id,
       t1.id,
       t1.start,
       t1.end,
       t1.data_file_name
FROM telematics_public.trips t1
INNER JOIN temp1 ON t1.telematics_user_id = temp1.telematics_user_id
WHERE t1.end < temp1.end_time
  AND DATEDIFF(DAY, t1.start, temp1.end_time)<=7
  AND t1.distance != ''
ORDER BY t1.end ASC
            '''%user_id,connection


                )
            data_file_name_list.append(data_file_name.iloc[:,4])
        return(data_file_name_list)

import geopy
def min_dist_to_location(trip, location):
    def f(x):
        return geopy.distance.vincenty((x[0], x[1]), location).miles
    
    if location is None:
        return np.nan
    return trip.gps[['latitude','longitude']].apply(f, axis=1).min()


def get_trip_list(claim_number, start_date, end_date):
    connection = db_connection('production_follower')
    connection.autocommit = True
    telematics_user_id = pd.read_sql_query(
    ''' select 
           telematics_user_id 
        from claims
        join policies on policies.id = claims.policy_id
        join users on users.account_id = policies.account_id
        where claims.number = '%s'
    '''%claim_number,
    connection
    )

    connection = db_connection('DB')
    connection.autocommit = True

    in_condition = "('" + "','".join(telematics_user_id['telematics_user_id']) + "')"
    sql_query = '''
        select
            telematics_user_id,
            id as trip_id,
            trips.start,
            telematics_public.trips.end,
            distance,
            data_file_name
        from telematics_public.trips
        where telematics_user_id in %s
    '''%in_condition

    trip_info = pd.read_sql_query(sql_query, connection)

    trip_info = trip_info.sort_values(by = 'start').reset_index(drop = True)
    trip_info.data_file_name[0]

    trip = get_trip(trip_info.data_file_name[0])
    time_zone_offset = timedelta(hours=trip.meta['time_zone_offset'].components.hours-24)
    trip_info['start_time_local'] = trip_info['start'] + time_zone_offset
    trip_info['end_time_local'] = trip_info['end'] + time_zone_offset

    interested_trips = trip_info.loc[trip_info.start_time_local >= start_date].loc[trip_info.start_time_local <= end_date]
    return interested_trips


def plot_trips(interested_trips, location=None):
    trip_list = []
    interested_trips['min_dist'] = np.nan
    interested_trips['has_gps'] = False
    #for i,data_file_name in enumerate(interested_trips.data_file_name):
    for i, data_file_name in enumerate(["9dd089f1-93a8-4bd2-a15c-247a39788f8e.json.gz"]):
        trip = get_trip(data_file_name)
        if trip is not None:
            if trip._has_gps:
                interested_trips['has_gps'].iloc[i] = True
                interested_trips['min_dist'].iloc[i] = min_dist_to_location(trip, location)
                trip_list.append(trip)
        break
    print(trip_list)
    plots = plot_multiple_trip(trip_list, accident_location=location)
    print("done plotting")
    return plots
