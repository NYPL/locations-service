## Installation

Via Docker:

```
docker image build -t patron-services:local .
docker container run -e ENVIRONMENT=local patron-services:local
```

Or for development in OSX:
```
pyenv local 3.10
python3 -m venv localenv
source localenv/bin/activate
python3 -m pip install -r dev-requirements.txt
python3 -m pip install -r requirements.txt
```