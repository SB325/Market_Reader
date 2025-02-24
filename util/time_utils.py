from datetime import datetime
import pdb
import time

def to_posix(datestring: str, dateformat_str: str):
    dt = datetime.strptime(datestring, dateformat_str)
    return int(dt.timestamp())

def to_y_m_d(datestring: str, dateformat_str: str):
    latest_date = datetime.strptime(datestring, dateformat_str)
    return latest_date.strftime("%Y-%m-%d")

def posix_to_datestr(posixt: int, outformat: str = "%Y-%m-%d"):
    dt = datetime.fromtimestamp(posixt)
    return dt.strftime(outformat)

def posix_now():
    return int(time.mktime(datetime.now().timetuple()))

def date_now_str(format_string: str):
    datetime_object = datetime.fromtimestamp(posix_now())
    return datetime_object.strftime(format_string)
    