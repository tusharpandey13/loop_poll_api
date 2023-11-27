# Take home interview - Store Monitoring

This app generates uptime reports of restaurants. It features a trigger/poll architecture for getting the reports.  
* The data manipulation is done via pandas.  
* It uses FastAPI for api.  
* It uses Redis to store report generation status.  
* It uses PSQL as a data source for the poll data.  
* It writes the output CSV files to an S3 bucket and gives the url of that file in the poll response.  
* It is capable of horizontal scaling on kubernetes as a single remote redis instance is used to track the report generation status across app instances.  


In my tests, generation of 1 report of poll data of 7 days took ~3minutes on my macbook. This time can be further reduced by using parallel pandas features.


> NOTE: the ipynb file is present in the sample_data directory


## API
/echo/{message}: Returns the input string.

`/trigger_report` endpoint that will trigger report generation from the data provided.  
Response:
```
{
    "report_id": "06757268c878488d846aee30a8101cae"
}
```

`/get_report` endpoint that will return the status of the report or the csv.  
Running Response:
```
{
    "status": "Running"
}
```
Completed Response:
```
{
    "url": "https://loopbucket1.s3.amazonaws.com/%240f8f1a89f83f43cebcbbd6e5b2c0c6e0.csv?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIATTXRLV5J3BSGF4QR%2F20231127%2Feu-north-1%2Fs3%2Faws4_request&X-Amz-Date=20231127T104141Z&X-Amz-Expires=86400&X-Amz-SignedHeaders=host&X-Amz-Signature=9d7ca85ce80131acaee23aa506c26481544d126e0db63fb07599cb05c02bcb56",
    "status": "Complete"
}
```
This url url when opened downloads the report CSV from S3.


## Data Analysis and Manipulation
Please check the attached ipynb file for complete steps.  
The data manipulation of the poll data consists of following steps:  
* Load the data
* Normalize the store hours data to UTC, recalculate day-of-week due to time normalization
* Filter the poll data according to store opening/closing hours. Entries lying outside the open hours are discarded.
* Resample the poll data to hour boundaries.
* Extrapolate the missing values by using a rolling window that takes into account the mode of the window values (majority of active/inactive). This also fills the missing intervals with what was the last known status before that time.
* Perform this operation for all store_ids and generate the result dataframe
* Export the result to csv

## Extrapolation of missing data
In the case of missing data, a simple extrapolation technique is used that takes the status of the last known status as the contious status throughout the missing time interval. No prediction is used to generate missing information as it is not reliable for uptime data.  
In real life, uptime information of well known websites (openai, google, slack, youtube) is consistent with this technique.  
In hours where multiple data points are present, a majority filter is used to calculate the majority value of that hour.
The majority only affects the hour values, it does not affect neighbouring hour's values. They are determined by last known value.

## Architecture
The app uses a redis cache to act as central place to poll for report generation status. The actual report generation task on the server is done parallely on a seperate thread and thus the server can handle more requests.  
For scaling, the load balancer can be configured at istio level to use a round-robin method of allocating report generation requests.  
Sample DestinationRule:
```
apiVersion: networking.istio.io/v1alpha3
kind: DestinationRule
metadata:
  name: my-destination-rule
spec:
  host: my-svc
  trafficPolicy:
    loadBalancer:
      simple: RANDOM
  subsets:
  - name: poll_handler
    labels:
      version: v1
  - name: report_genration_handler
    labels:
      version: v2
    trafficPolicy:
      loadBalancer:
        simple: ROUND_ROBIN
```
Here, the report genreation traffic is distributed across the pods in a round robin fashion ensuring that no single pod is choked at a time. The poll requests can be distributed randomly as they are not CPU intensive.
## Setup

1. Install the dependencies:

```
pip install -r requirements.txt
```

2. Run the application:

```
uvicorn app.main:app --reload
```

Docker:
```
docker-compose build
docker-compose up -d
```