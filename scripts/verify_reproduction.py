"""Compare two sets of model results without hiding missing estimates."""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd


def compare_csv(reference, reproduced):
    left, right = pd.read_csv(reference), pd.read_csv(reproduced)
    assert list(left.columns) == list(right.columns), (reference.name, 'columns')
    assert left.shape == right.shape, (reference.name, 'shape')
    differences = {}
    for col in left:
        if pd.api.types.is_numeric_dtype(left[col]):
            a,b=left[col].to_numpy(float),right[col].to_numpy(float)
            assert np.array_equal(np.isnan(a),np.isnan(b)),(reference.name,col,'missing')
            assert np.allclose(a,b,rtol=1e-9,atol=1e-10,equal_nan=True),(reference.name,col)
            valid=np.isfinite(a)&np.isfinite(b)
            differences[col]=float(np.max(np.abs(a[valid]-b[valid]))) if valid.any() else None
        else:
            assert left[col].fillna('<NA>').equals(right[col].fillna('<NA>')),(reference.name,col)
    return {'file':reference.name,'rows':len(left),'max_numeric_difference':max([x for x in differences.values() if x is not None],default=0)}


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--reproduced',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    files=sorted(a.reference.glob('*.csv'))
    files=[x for x in files if x.name not in {'analysis_station_daily.csv','analysis_weather_daily.csv'}]
    checks=[compare_csv(x,a.reproduced/x.name) for x in files]
    a.report.parent.mkdir(parents=True,exist_ok=True)
    result={'passed':True,'file_count':len(checks),'checks':checks,'tolerance':{'rtol':1e-9,'atol':1e-10}}
    a.report.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':main()
