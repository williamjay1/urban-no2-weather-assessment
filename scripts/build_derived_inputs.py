"""Portable reconstruction from downloaded EPA AQS CSVs and ERA5 JSONs.

Never downloads or modifies source files. Put the seven national AQS daily
CSV files in --aqs-directory and the eleven archived city responses in
--weather-json-directory. Coordinates are in city_metadata.json.
"""
from pathlib import Path
import argparse
import json
import hashlib
import numpy as np
import pandas as pd

FIELDS=['temperature_2m_max','wind_speed_10m_mean','relative_humidity_2m_mean',
        'precipitation_sum','shortwave_radiation_sum','wind_direction_10m_dominant']

def haversine(lat,lon,lat0,lon0):
    a,b=np.deg2rad(lat),np.deg2rad(lon)
    c,d=np.deg2rad(lat0),np.deg2rad(lon0)
    h=np.sin((a-c)/2)**2+np.cos(a)*np.cos(c)*np.sin((b-d)/2)**2
    return 6371.0088*2*np.arcsin(np.sqrt(np.clip(h,0,1)))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--aqs-directory',type=Path,required=True)
    p.add_argument('--weather-json-directory',type=Path,required=True)
    p.add_argument('--city-metadata',type=Path,default=Path(__file__).resolve().parents[1]/'provenance'/'city_metadata.json')
    p.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[1]/'data')
    a=p.parse_args()
    cities=json.loads(a.city_metadata.read_text(encoding='utf-8'))
    out=a.output; (out/'stations').mkdir(parents=True,exist_ok=True); (out/'weather').mkdir(parents=True,exist_ok=True)
    pieces=[]; sources=[]; flow=[]
    columns=['State Code','County Code','Site Num','POC','Latitude','Longitude','Sample Duration','Pollutant Standard','Date Local','Units of Measure','Event Type','Observation Percent','Arithmetic Mean','Observation Count']
    for year in range(2019,2026):
        src=a.aqs_directory/f'daily_42602_{year}.csv'
        raw=pd.read_csv(src,usecols=columns,dtype={'State Code':str,'County Code':str,'Site Num':str},low_memory=False)
        ok=raw['Sample Duration'].eq('1 HOUR')&raw['Units of Measure'].eq('Parts per billion')&raw['Pollutant Standard'].eq('NO2 1-hour 2010')&pd.to_numeric(raw['Observation Percent'],errors='coerce').ge(75)
        r=raw[ok].copy();r['date']=pd.to_datetime(r['Date Local'])
        r['station_id']=r['State Code'].str.zfill(2)+'-'+r['County Code'].str.zfill(3)+'-'+r['Site Num'].str.zfill(4)
        for city in cities:
            z=r.copy();z['distance_km']=haversine(z.Latitude.to_numpy(float),z.Longitude.to_numpy(float),city['lat'],city['lon'])
            z=z[z.distance_km.le(25)].copy();before=len(z)
            z['event_priority']=z['Event Type'].map({'Events Included':0,'None':1,'No Events':1,'Events Excluded':2}).fillna(3)
            z=z.sort_values('event_priority',kind='stable').drop_duplicates(['station_id','POC','date'],keep='first').dropna(subset=['Arithmetic Mean','date'])
            z['weight']=z['Observation Count'].fillna(1).clip(lower=1);z['weighted_value']=z['Arithmetic Mean']*z.weight
            d=z.groupby(['station_id','date'],as_index=False).agg(weighted_value=('weighted_value','sum'),observation_count=('weight','sum'),n_pocs=('POC','nunique'),min_observation_percent=('Observation Percent','min'),latitude=('Latitude','mean'),longitude=('Longitude','mean'),distance_km=('distance_km','mean'))
            d['no2_ppb']=d.weighted_value/d.observation_count;d=d.drop(columns='weighted_value');d.insert(0,'city',city['city']);pieces.append(d)
            flow.append(dict(city=city['city'],year=year,within_radius_rows=before,rows_after_deduplication=len(z),station_days=len(d)))
        sources.append(dict(file=src.name,sha256=hashlib.sha256(src.read_bytes()).hexdigest()))
    station=pd.concat(pieces,ignore_index=True).sort_values(['city','date','station_id'])
    assert not station.duplicated(['city','date','station_id']).any()
    station.to_csv(out/'stations'/'station_daily.csv',index=False)
    weather=[]
    for city in cities:
        src=a.weather_json_directory/(city['slug']+'.json')
        payload=json.loads(src.read_text(encoding='utf-8'));d=pd.DataFrame(payload['daily']).rename(columns={'time':'date'});d['city']=city['city']
        assert len(d)==2557 and d.date.nunique()==2557
        assert set(FIELDS).issubset(d.columns)
        weather.append(d);sources.append(dict(file=src.name,sha256=hashlib.sha256(src.read_bytes()).hexdigest(),timezone=payload['timezone']))
    pd.concat(weather,ignore_index=True).sort_values(['city','date']).to_csv(out/'weather'/'weather_daily.csv',index=False)
    pd.DataFrame(flow).to_csv(out/'stations'/'reconstruction_flow.csv',index=False)
    (out/'reconstruction_sources.json').write_text(json.dumps(sources,indent=2),encoding='utf-8')
    print('Rebuilt',len(station),'station-days and',sum(map(len,weather)),'city weather-days')

if __name__=='__main__': main()
