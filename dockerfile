FROM python:3.9

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

EXPOSE 8000

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

