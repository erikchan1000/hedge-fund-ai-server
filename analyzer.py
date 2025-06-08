# load test.json
import json

with open('./test.json') as file:
    data = json.load(file)

data = data['series']
print(data)
annual_keys = data['annual'].keys()
print("Annual Keys: ", annual_keys)
ttm_keys = data['quarterly'].keys()
print("Quarterly Keys: ", ttm_keys)
