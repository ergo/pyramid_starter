import decimal
import json
from datetime import datetime, date, timedelta

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%f"


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return {"__type__": "__datetime__", "iso": obj.strftime(DATE_FORMAT)}
        elif isinstance(obj, date):
            return {"__type__": "__date__", "iso": obj.strftime(DATE_FORMAT)}
        elif isinstance(obj, timedelta):
            return {"__type__": "__timedelta__", "seconds": obj.total_seconds()}
        if isinstance(obj, decimal.Decimal):
            return {"__type__": "__decimal__", "decimal": str(obj)}
        else:
            return json.JSONEncoder.default(self, obj)


def date_decoder(dct):
    if "__type__" in dct:
        if dct["__type__"] == "__datetime__":
            return datetime.strptime(dct["iso"], DATE_FORMAT)
        elif dct["__type__"] == "__date__":
            return datetime.strptime(dct["iso"], DATE_FORMAT).date()
        elif dct["__type__"] == "__timedelta__":
            return timedelta(seconds=dct["seconds"])
        elif dct["__type__"] == "__decimal__":
            return decimal.Decimal(dct["decimal"])
    return dct


def json_dumps(obj):
    return json.dumps(obj, cls=DateEncoder)


def json_loads(obj):
    return json.loads(obj, object_hook=date_decoder)
