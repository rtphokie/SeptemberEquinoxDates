import unittest
import statistics
import os
from pprint import pprint
from skyfield import almanac
from skyfield.api import load_file, load
from pytz import timezone
from contextlib import contextmanager

bspcachedir='/var/data'
ephfiles={f'de440s.bsp': (1850,2148), #1849-12-25T23:59:18Z - 2150-01-21T23:58:51Z
          f'de440.bsp': (1550,2639), #1549-12-30T23:59:18Z - 2650-01-24T23:58:51Z
          f'de422.bsp': (-2999,2999), #-3000-11-12T23:59:18Z - 3000-01-29T23:58:51Z
          }

ts = load.timescale()

@contextmanager
def cwd(path):
    oldpwd=os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)

def seasons(startyear, endyear, tzstr='US/Eastern', showdeltas=False):
    for fn, yearrange in sorted(ephfiles.items()):
        if yearrange[0] <= startyear and yearrange[1] >= endyear:
            filename = fn
    if fn is None:
        raise ValueError(f"year range must fall between {yearrange}")

    with cwd(bspcachedir):
        eph = load(filename)
    print(f"using {filename} covering { ts.tt_jd(eph.spk.segments[0].start_jd).utc_iso()} - {ts.tt_jd(eph.spk.segments[-1].end_jd).utc_iso()}")
    t0 = ts.utc(startyear, 1, 1)
    t1 = ts.utc(endyear, 12, 31)
    t, y = almanac.find_discrete(t0, t1, almanac.seasons(eph))

    metrics={'UTC': {}, tzstr: {}}
    prevval=None
    deltas=[]
    for yi, ti in zip(y, t):
        if yi == 2:
            for x in ['UTC', tzstr] :
                tz = timezone(tzstr)
                day = ti.utc_datetime().astimezone(timezone(x)).strftime("%d")
                year = ti.utc_datetime().astimezone(timezone(x)).strftime("%Y")
                val = int(ti.utc_datetime().astimezone(timezone(x)).strftime("%d"))
                val += int(ti.utc_datetime().astimezone(timezone(x)).strftime("%-H"))/24.0
                val += int(ti.utc_datetime().astimezone(timezone(x)).strftime("%-M"))/1440.0
                val += int(ti.utc_datetime().astimezone(timezone(x)).strftime("%-S"))/86400.0
                if x == 'UTC' and prevval is not None:
                    delta = val-prevval
                    if delta < 0:
                        delta+=1
                    if showdeltas:
                        print(f"{year} {24*(delta):12.4f}")
                    deltas.append(24*delta)
                if x == 'UTC':
                    prevval=val
                if day not in metrics[x].keys():
                    metrics[x][day]=0
                metrics[x][day]+=1
            # print(yi, almanac.SEASON_EVENTS[yi], ti.utc_datetime().strftime('%x'), ti.utc_datetime().astimezone(tz).strftime("%x"))
    print(f"between {yearrange[0]} and {yearrange[1]} in the {tzstr} timezone")
    print(f"the September equinox arrives ~{statistics.median(deltas):.2f} hours later each year")
    for d,c in metrics[tzstr].items():
        print(f"{d} {c/sum(metrics[tzstr].values())*100:.2f}%")


if __name__ == '__main__':
    seasons(1583, 2021, tzstr='US/Eastern')
