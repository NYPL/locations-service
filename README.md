# Locations Service
This is a python API accessible at:
`{PLATFORM_URL}/locations`
It returns location labels and optionally urls, opening hours, and address for the provided `location_codes`. Note that if no `location_codes` are provided, an 500 error will be returned.

### Example valid endpoints
`/locations?location_codes=map99&fields=hours`
`/locations?location_codes=map99`
`/locations?location_codes=map99,mao&fields=hours,url,location`

## Installation
For development in OSX:
```
pyenv local 3.10
python3 -m venv localenv
source localenv/bin/activate
python3 -m pip install -r dev-requirements.txt
python3 -m pip install -r requirements.txt
```

## Testing
`make test`

## Parameters
| Query Parameter | Example | Description |
|-----------------|---------|-------------|
|location_codes (required)| map82,sn| Sierra location codes
|fields (optional)| url,hours,address| If no fields are provided, app defaults to return url and label. If fields are provided, only those fields are returned (ie `?location_codes=ag,fields=hours` will not return url but `?location_codes=ag` will)

## Local Invocation 
```
sam build
sam local invoke -e events/{eventfile}.json
```