#################################################
# Technicals ingest
#################################################
# This script pulls raw technical data from schwab
#   and ingests them into the database

# from ameritrade_auth import schwab_auth

class tech_ingest():
    def __init__(self, auth):
        self.auth = auth
        self.resource_url = 'https://api.schwabapi.com/marketdata/v1'
    
    def get_token(self):
        aut = 'Bearer ' + self.auth.access_token
        header = {'Authorization': aut, \
            "Content-Type":"application/json"} 
        auth = {'apikey': self.auth.consumer_key}
        return header, auth

    def get_price_history(self,varargin):
        # args are Ticker, periodType<year>, period<5>,
        # frequencyType<daily>, frequency<1>, needExtendedHoursData<true>
        # This method won't bother to validate inputs, so make sure
        # arguments are in the right order and of the right format!!
        # ex:
        # md.get_price_history('B','PeriodType','year','period','5','frequencyType','minute','frequency','1')
        header, param = self.get_token()
        if len(varargin)==9:
            data = self.auth.get_req(url=self.resource_url + '/' + varargin[0] + '/pricehistory', \
                                 params=param.update({'apikey':self.auth.consumer_key, \
                varargin[1]: varargin[2], \
                varargin[3]: varargin[4], \
                varargin[5]: varargin[6], \
                varargin[7]: varargin[8]}), \
                headers=header)  #The number of periods to show in each candle
            
    def get_quotes(self,tickers: list):
        header, param = self.get_token()
        
        delim = ','
        data = self.auth.get_req(url=self.resource_url + '/quotes', \
        params=param.update({'symbol': delim.join(tickers)}), \
        headers=header)
        if not data.ok:
            msg='tda_market_data: get_quotes data call failed'
            print(msg)
            self.auth.log(msg)
        else:
            self.auth.log(['tda_market_data: Downloaded quotes for ' + varargin[0] + '.'])
        return data

    def get_quote(self,tick: str):
        # len(varargin) must be 2. varargin[0] is a ticker symbol
        header, param = self.get_token()
        
        data = self.auth.get_req(url=self.resource_url + '/' + tick + '/quotes', \
        params=param, headers=header)
        
        if not data.ok:
            msg=f"tda_market_data: data request for get_quote" + \
            f"failed.({data.status_code}: Request {data.request})" + \
            f"Headers: {data.headers}"
            print(msg)
        else:
            self.auth.log(['tda_market_data: Downloaded quote for ' + tick + '.'])
        return data