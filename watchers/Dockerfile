FROM python:3.7

RUN mkdir /watchers
WORKDIR /watchers
COPY . /watchers

RUN pip3 install -r requirements.txt

ENTRYPOINT ["python3", "watcher.py"]