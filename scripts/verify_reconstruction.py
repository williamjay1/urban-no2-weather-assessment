"""Verify site and weather data rebuilt from source files."""
from pathlib import Path
import argparse
import hashlib
import json
from verify_reproduction import compare_csv


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--reference',type=Path,required=True)
    p.add_argument('--rebuilt',type=Path,required=True)
    p.add_argument('--report',type=Path,required=True)
    a=p.parse_args()
    names=['stations/station_daily.csv','weather/weather_daily.csv']
    checks=[compare_csv(a.reference/n,a.rebuilt/n) for n in names]
    result={'passed':True,'checks':checks,'reference_sha256':{n:hashlib.sha256((a.reference/n).read_bytes()).hexdigest() for n in names}}
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':main()
