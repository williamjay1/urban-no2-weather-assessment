"""Verbatim aggregate from wasp_weather_alignment.py; no retrieval code.
See provenance/aggregation_source.json for source identity.
"""
import numpy as np
import pandas as pd

def aggregate(hourly, offset, accumulation_shift=True):
    h=hourly.copy()
    instant=pd.to_datetime(h.time)+pd.Timedelta(hours=offset)
    h['date']=instant.dt.floor('D')
    d=h.groupby('date').agg(temperature_2m_max=('temperature_2m','max'),wind_speed_10m_mean=('wind_speed_10m','mean'),relative_humidity_2m_mean=('relative_humidity_2m','mean'),n_instant=('time','size'))
    angle=np.deg2rad(h.wind_direction_10m)
    h['wind_u']=h.wind_speed_10m*np.sin(angle);h['wind_v']=h.wind_speed_10m*np.cos(angle)
    uv=h.groupby('date')[['wind_u','wind_v']].mean()
    d['wind_direction_10m_dominant']=np.mod(np.rad2deg(np.arctan2(uv.wind_u,uv.wind_v)),360)
    h['accum_date']=(instant-pd.Timedelta(hours=1 if accumulation_shift else 0)).dt.floor('D')
    acc=h.groupby('accum_date').agg(precipitation_sum=('precipitation','sum'),shortwave_radiation_sum=('shortwave_radiation','sum'),n_accum=('time','size'))
    acc['shortwave_radiation_sum']*=.0036
    d=d.join(acc)
    d=d.loc['2019-01-01':'2025-12-31']
    assert len(d)==2557 and d.n_instant.eq(24).all() and d.n_accum.eq(24).all()
    return d.drop(columns=['n_instant','n_accum']).reset_index()
