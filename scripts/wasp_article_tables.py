"""Deterministic manuscript tables from the frozen WASP output, without refitting."""
from pathlib import Path
import argparse
import json
import sys
import numpy as np
import pandas as pd

from release_cli import PACKAGE, disable_network, prepare_output

ANALYSIS=PACKAGE/'results'
CITY_METADATA=PACKAGE/'provenance/city_metadata.json'
OUT=PACKAGE/'reproduced_tables'

def f(v,d=2):
    return 'NA' if pd.isna(v) else f'{v:.{d}f}'.replace('-', '−')

def interval(row,prefix='cross_city_summary'):
    return f(row[prefix+'_lower'])+', '+f(row[prefix+'_upper'])

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(map(str,row))+' |' for row in rows])

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    a=ANALYSIS;audit=json.loads((a/'analysis_audit.json').read_text())
    assert audit['completed'] and audit['models']==20
    OUT.mkdir(exist_ok=True)
    summary=pd.read_csv(a/'model_summary.csv').set_index(['model','contrast'])
    thresholds=pd.read_csv(a/'thresholds.csv').set_index('city')
    cities=list(thresholds.index)
    ev=pd.read_csv(a/'episode_manifest.csv');ev=ev[ev.year.le(2024)]
    support=pd.read_csv(a/'p80_p30_min2_sep7_binary_support_city_year.csv')
    support=support[support.year.le(2024)].groupby(['city','comparator']).sum(numeric_only=True)
    maincity=pd.read_csv(a/'weather_adjusted_city_estimates.csv')
    sitecounts=maincity[maincity.contrast.eq('episode_vs_reference')].set_index('city').n_stations
    tables={};rows=[]
    for city in cities:
        ec=ev[ev.city.eq(city)];t=thresholds.loc[city]
        rows.append([city,int(sitecounts[city]),f(t.heat_c,1),f(t.wind_kmh,3),len(ec),int(ec.duration_days.sum()),
            str(int(support.loc[(city,'neither'),'supported_episode_city_days']))+' / '+str(int(support.loc[(city,'wind_only'),'supported_episode_city_days']))])
    tables['T1']=table(['City','Sites','Heat °C','Wind km h⁻¹','Episodes','Days','Direct N / W days'],rows)
    contrast_names={'episode_vs_reference':'Episode versus neither','wind_only_vs_reference':'Low wind versus neither',
        'heat_only_vs_reference':'High temperature versus neither','other_compound_vs_reference':'Other compound versus neither',
        'episode_vs_wind_only':'Episode versus low wind','episode_vs_heat_only':'Episode versus high temperature'}
    rows=[]
    for key,name in contrast_names.items():
        cal=summary.loc[('calendar_only',key)];adj=summary.loc[('weather_adjusted',key)]
        rows.append([name,f(cal.estimate_ppb)+' ('+interval(cal)+')',f(adj.estimate_ppb)+' ('+interval(adj)+')',interval(adj,'jackknife')])
    tables['T2']=table(['Comparison','Calendar estimate (summary interval)','Adjusted estimate (summary interval)','Adjusted year diagnostic'],rows)
    direct=[('direct_episode_neither','Direct neither','episode_vs_neither'),('direct_episode_wind','Direct low wind','episode_vs_wind_only'),
            ('persistent_wind_comparator','Persistent low wind','episode_vs_persistent_wind_only'),('direct_wind_spline','Direct low wind with wind spline','episode_vs_wind_only')]
    rows=[]
    for mod,label,c in direct:
        r=summary.loc[(mod,c)]
        rows.append([label,int(r.n_strata),int(r.n_episode_station_days),int(r.n_episode_city_days),int(r.n_episodes),str(int(r.n_estimable_cities))+'/11'])
    tables['T3']=table(['Restriction','Strata','Episode site-days','Episode city-days','Events','Estimable cities'],rows)
    names={'compound_vs_reference':'Compound versus neither','heat_only_vs_reference':'High temperature versus neither',
           'wind_only_vs_reference':'Low wind versus neither','compound_vs_wind_only':'Compound versus low wind',
           'compound_vs_heat_only':'Compound versus high temperature','compound_additive_interaction':'Additive interaction'}
    rows=[]
    for key,label in names.items():
        r=summary.loc[('four_weather_regimes',key)]
        rows.append([label,f(r.estimate_ppb),interval(r),interval(r,'jackknife')])
    tables['T4']=table(['Comparison','Estimate','Cross-city summary','Year diagnostic'],rows)
    meta=json.loads(CITY_METADATA.read_text())
    tables['A1']=table(['City','Latitude °N','Longitude °E'],[[m['city'],f(m['lat'],4),f(m['lon'],4)] for m in sorted(meta,key=lambda m:m['city'])])
    ds=pd.read_csv(a/'descriptive_distributions_city_regime.csv')
    ds=ds[ds.period.eq('2019_2024') & ds.classification.eq('regime')].set_index(['city','regime','variable'])
    rows=[]
    for city in cities:
        row=[city]
        for state in ['episode','wind_only','heat_only','neither','other_compound']:
            d=ds.loc[(city,state,'no2_ppb')];row.append(f(d['mean'])+' ['+f(d.q25)+', '+f(d.q75)+']')
        rows.append(row)
    tables['A2']=table(['City','Episode','Low wind','High temperature','Neither','Other compound'],rows)
    runs=pd.read_csv(a/'low_wind_run_manifest.csv')
    runs=runs[runs.year.le(2024) & runs.run_type.eq('pure_wind')]
    rows=[]
    for city in cities:
        rows.append([city,f(ds.loc[(city,'episode','wind_speed_10m_mean'),'mean']),f(ds.loc[(city,'wind_only','wind_speed_10m_mean'),'mean']),
            f(ev[ev.city.eq(city)].duration_days.mean()),f(runs[runs.city.eq(city)].duration_days.mean())])
    tables['A3']=table(['City','Episode wind','Low-wind-only wind','Episode run length','Low-wind-only run length'],rows)
    rows=[]
    city_direct={mod:pd.read_csv(a/(mod+'_city_estimates.csv')).set_index('city') for mod,_,_ in direct}
    for city in cities:rows.append([city]+[f(city_direct[mod].loc[city,'estimate_ppb']) for mod,_,_ in direct])
    tables['B1']=table(['City','Direct neither','Direct low wind','Persistent low wind','Wind spline'],rows)
    year=pd.read_csv(a/'weather_adjusted_leave_year.csv').pivot(index='omitted_year',columns='contrast',values='estimate_ppb')
    factorial=pd.read_csv(a/'four_weather_regimes_leave_year.csv').pivot(index='omitted_year',columns='contrast',values='estimate_ppb')
    rows=[[y,f(year.loc[y,'episode_vs_reference']),f(year.loc[y,'episode_vs_wind_only']),f(factorial.loc[y,'compound_additive_interaction'])] for y in year.index]
    tables['B2']=table(['Omitted year','Episode versus neither','Episode versus low wind','Four-state interaction'],rows)
    bootjobs=([('weather_adjusted','Main neither','episode_vs_reference'),('weather_adjusted','Main low wind','episode_vs_wind_only'),
              ('four_weather_regimes','Four-state interaction','compound_additive_interaction')]+direct+
             [('period_2019_2022','2019–2022 neither','episode_vs_reference'),('period_2019_2022','2019–2022 low wind','episode_vs_wind_only'),
              ('period_2023_2024','2023–2024 neither','episode_vs_reference'),('period_2023_2024','2023–2024 low wind','episode_vs_wind_only'),
              ('p80_p30_min3_sep7','Three-day neither','episode_vs_reference'),('p80_p30_min3_sep7','Three-day low wind','episode_vs_wind_only')])
    rows=[]
    for mod,label,key in bootjobs:
        r=summary.loc[(mod,key)]
        rows.append([label]+[int(r[s+'_failed']) for s in ['hierarchical_city_independent_year','synchronized_year_fixed_cities','synchronized_year_resampled_cities']]+[interval(r,'synchronized_year_fixed_cities_conditional')])
    tables['B3']=table(['Comparison','Hierarchy failed','Fixed cities failed','Resampled cities failed','Fixed-city quantiles'],rows)
    for name,md in tables.items():(OUT/(name+'.md')).write_text(md,encoding='utf-8')
    ledger={'input_audit':audit,'tables':tables,'main':summary.loc['weather_adjusted'].reset_index().replace({np.nan:None}).to_dict('records'),
        'primary_city':maincity[maincity.contrast.isin(['episode_vs_reference','episode_vs_wind_only'])].replace({np.nan:None}).to_dict('records')}
    (OUT/'result_ledger.json').write_text(json.dumps(ledger,indent=2),encoding='utf-8')
    print('\n\n'.join(k+'\n'+v for k,v in tables.items()))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis',type=Path,default=ANALYSIS)
    parser.add_argument('--city-metadata',type=Path,default=CITY_METADATA)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    disable_network()
    ANALYSIS=args.analysis.resolve();CITY_METADATA=args.city_metadata.resolve()
    names=[name+'.md' for name in ('T1','T2','T3','T4','A1','A2','A3','B1','B2','B3')]+['result_ledger.json']
    OUT=prepare_output(args.output,names,(ANALYSIS,CITY_METADATA))
    main()
