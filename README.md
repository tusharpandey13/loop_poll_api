# My FastAPI App

## Setup

1. Install the dependencies:

```
pip install -r requirements.txt
```

2. Run the application:

```
uvicorn app.main:app --reload
```

## Usage

The application has two endpoints:

/echo/{message}: Returns the input string.
/poll/poll_compute: Performs a computation in the background and returns a random string instantly.
/poll/generate_csv: Generates a CSV file with the given input string as the filename.

## Testing

To run the tests, use the following command:

```
pytest
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)