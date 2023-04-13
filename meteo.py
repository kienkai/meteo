
import streamlit as st
import pandas as pd
import datetime

import re
from urllib import request
import gzip
import shutil
import os
import numpy as np
import matplotlib
SITE = 7005
HOUR = "1200"

def kelvin_to_celsius(temp):
    try:
        return float(temp) -  273.15
    except ValueError:
        return np.nan
    
def get_temp_values(csv_filepath,date_start,date_end):
    pd_synop = pd.read_csv(csv_filepath,delimiter = ';')

    pd_synop.set_index('numer_sta',inplace=True)
    pd_orly = pd_synop.loc[SITE]
    pd_orly['hour'] = pd_orly['date'].astype(str).str[8:12]
    pd_orly_hour = pd_orly[pd_orly['hour'] == HOUR]
    pd_orly_hour['t_celsius'] = pd_orly_hour['t'].apply(lambda x :kelvin_to_celsius(x))
    pd_orly_temp = pd_orly_hour.set_index('date')[['t_celsius']]
    #print(pd_orly_temp)
    return(pd_orly_temp)

def get_temperatures(date_start,date_end):
    if not os.path.exists("temp"):
        os.makedirs("temp")
    if not os.path.exists("meteo_txt_files"):
        os.makedirs("meteo_txt_files")
    year_start= date_start.year
    year_end= date_end.year
    month_start= date_start.month
    month_end= date_end.month
    monthes = (year_end-year_start) * 12 + (month_end-month_start) + 1
    pd_orly_temp_all = pd.DataFrame()

    for month in range(monthes):
        year_download = (month -1 + month_start) // 12 + year_start
        month_download =  (month - 1 + month_start) % 12 + 1
        year_month = f'{year_download:4d}{month_download:02d}'
        print(year_month)
        url1 = f'https://donneespubliques.meteofrance.fr/donnees_libres/Txt/Synop/Archive/synop.{year_month}.csv.gz'
        print(url1)
        file_name1 = re.split(pattern='/', string=url1)[-1]
        gz_filepath = os.path.join("temp",file_name1)

        r1 = request.urlretrieve(url=url1, filename=gz_filepath)
        txt1 = re.split(pattern=r'\.', string=file_name1)[0] + year_month + ".csv"
        csv_filepath = os.path.join("meteo_txt_files",txt1)
        with gzip.open(gz_filepath, 'rb') as f_in:
            with open(csv_filepath, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        pd_orly_temp = get_temp_values(csv_filepath,date_start,date_end)
        pd_orly_temp_all = pd.concat([pd_orly_temp_all, pd_orly_temp])
    return pd_orly_temp_all

date_start = None
date_end = None
st.header("Température à Paris Orly (site = 7005) à midi")
dts = st.date_input(
    label="Intervalle de dates ",
    value=(datetime.datetime.now(), datetime.datetime.now()),
    key="#date_range",
    help="Date de début ET date de fin ",
)
if dts and len(dts) == 2:
    date_start = dts[0]
    date_end = dts[1]
# if start_dt and end_dt:
#     start_date = start_dt.strftime("%Y-%m-%d")
#     end_date = end_dt.strftime("%Y-%m-%d")

# date_start = datetime.date(2011,5,6)
# date_end = datetime.date(2023,3,30)
if date_start and date_end:
    pd_orly_temp_all = get_temperatures(date_start,date_end)
    pd_orly_temp_all.reset_index(inplace=True)
    pd_orly_temp_all['datetime'] = pd.to_datetime(pd_orly_temp_all['date'].astype(str).str[0:8])
    pd_orly_temp_all.set_index('datetime',inplace=True)
    #lines = pd_orly_temp_all[['t_celsius']].plot.line()
    st.line_chart(pd_orly_temp_all[['t_celsius']])
    csv = pd_orly_temp_all[['t_celsius']].to_csv()
    st.download_button(
     label="Télécharger en fichier CSV",
     data=csv,
     file_name='temperatures.csv',
     mime='text/csv',
 )
#print(pd_orly_temp_all)

