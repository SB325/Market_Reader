from pydantic import BaseModel
from typing import Optional
from enum import Enum

class periodTypeEnum(Enum):
                        # {valid_periods} : default [period_type]
    day = 'day'         # {1, 2, 3, 4, 5, 10} : 10 [minute]
    month = 'month'     # {1, 2, 3, 6} : 1 [daily, weekly]
    year = 'year'       # {1, 2, 3, 5, 10, 15, 20} : 1 [daily, weekly, monthly]
    ytd = 'ytd'         # {1} : 1 [daily, weekly]

    def __str__(self):
        return str.__str__(self.value)

class frequencyTypeValues(Enum):
    minute = 'minute'
    daily = 'daily'
    weekly = 'weekly'
    monthly = 'monthly'

    def __str__(self):
        return str.__str__(self.value)

    
# #frequency_int
# <frequency_type>      {valid_values} : default
# <minute>              {1, 5, 10, 15, 30} : 1
# <daily>               {1} : 1
# <weekly>              {1} : 1
# <monthly>             {1} : 1

class bool_str(Enum):
    true = 'true'
    false = 'false'

    def __str__(self):
        return str.__str__(self.value)
    
class priceHistoryFormat(BaseModel):
    symbol: str
    periodType: periodTypeEnum = 'day' # Enum
    period: Optional[int]  # see comments in periodTypeEnum
    frequencyType: Optional[frequencyTypeValues] = None   # Enum
    frequency: Optional[int] = None   # see frequency_int
    startDate: Optional[int] = None  # posixtime
    endDate: Optional[int] = None # posixtime
    needExtendedHoursData: Optional[bool_str] = None 
    needPreviousClose: Optional[bool_str] = None 

class marketNames(Enum):
    equity = 'equity'
    option = 'option'
    bond = 'bond'
    future = 'future'
    forex = 'forex'

    def __str__(self):
        return str.__str__(self.value)

