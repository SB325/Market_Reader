from datetime import datetime
import pdb
import time
from zoneinfo import ZoneInfo
from typing import Union

def to_posix(datestring: str, dateformat_str: str):
    dt = datetime.strptime(datestring, dateformat_str)
    dt.replace(tzinfo=ZoneInfo('US/Eastern'))
    return int(dt.timestamp())

def to_y_m_d(datestring: str, dateformat_str: str):
    latest_date = datetime.strptime(datestring, dateformat_str)
    latest_date.replace(tzinfo=ZoneInfo('US/Eastern'))
    return latest_date.strftime("%Y-%m-%d")

def posix_to_datestr(posixt: Union[int,list], outformat: str = "%Y-%m-%d"):
    if isinstance(posixt, int):
        if len(str(posixt)) > 10:
            # Convert from ms to s
            posixt = int(posixt/1000)
        dt = datetime.fromtimestamp(posixt).replace(tzinfo=ZoneInfo('US/Eastern'))
        return dt.strftime(outformat)
    elif isinstance(posixt, list):
        if len(str(posixt)) > 10:
            # Convert from ms to s
            dt = [ datetime.fromtimestamp(int(dstr/1000)).replace(tzinfo=ZoneInfo('US/Eastern')) 
                for dstr in posixt ]
        else:
            dt = [ datetime.fromtimestamp(dstr).replace(tzinfo=ZoneInfo('US/Eastern')) 
                for dstr in posixt ]
        return [val.strftime(outformat) for val in dt]

def posix_now():
    return int(time.mktime(datetime.now().timetuple()))

def date_now_str(format_string: str):
    datetime_object = datetime.fromtimestamp(posix_now())
    datetime_object.replace(tzinfo=ZoneInfo('US/Eastern'))
    return datetime_object.strftime(format_string)
    