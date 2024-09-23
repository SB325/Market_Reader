import json
from marshmallow import Schema, fields
from sqlalchemy.dialects.postgresql import JSONB

class JSON(fields.Field):
    def _deserialize(self, value, attr, data, **kwargs):
        if value:
            try:
                return json.loads(value)
            except ValueError:
                return None

        return None
  
class sSymbols(Schema):
    cik_str = fields.String()
    ticker = fields.String()
    title = fields.String()

    # calling_number = fields.String()
    # imsi = fields.String()
    # imei = fields.Integer()
    # called_number = fields.String()
    # called_imsi = fields.Integer()
    # call_duration = fields.Float()
    # cgi = fields.String()
    # geo_lat = fields.Float()
    # geo_lon = fields.Float()
    # radius = fields.Float()
    
