import requests
from indicators.models import Indicator, IndicatorData

def save(indicator, save_data):
   save_data.update({"indicator":indicator})
   IndicatorData(**save_data).save()

def save_json(indicator, json):
   indicator_api = indicator.api
   path = indicator_api.json.split(".")
   result = json
   if len(path) == 1:
      if path[0] == u"":
         pass
      else:
         for p in path:
            result = result[p]
   else:
      for p in path:
         result = result[p]
   
   if type(result).__name__ == 'dict':
      save_data = {}
      for json_key in indicator_api.json_keys:
         save_data.update({json_key.indicator_data_key: result[json_key.json_key]})
      save(indicator, save_data)
   else:
      for i in result:
         save_data = {}
         for json_key in indicator_api.json_keys:
            save_data.update({json_key.indicator_data_key: i[json_key.json_key]})
         save(indicator, save_data)

def save_api(indicator):
   indicator_api = indicator.api
   IndicatorData.objects.filter(indicator=indicator).delete()
   for param_set in indicator_api.url_param_sets:
       payload = {}
       for param in param_set.param.all():
           payload.update({param.key: param.value})
       r = requests.get(indicator_api.url, params=payload)
       print "GET", r.url
       save_json(indicator, r.json())

