You will want to create a virtualenv using python 3.10 or higher (3.11 was used), likely via:
```python3 -m venv venv```
```source venv/bin/activate```
```python -m pip install -r requirements.txt```
```API_TESTING=1 python -m tests``` to run the unit tests
```uvicorn app:app --host 0.0.0.0 --port 8000``` to run the server


At this time there are no background tasks to attain historical altitude data and thus in order to get the data, the server must be queried via the `/stats` API at the respective rate.

