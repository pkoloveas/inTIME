FROM python:3.7

RUN mkdir /content-ranking
WORKDIR /content-ranking
COPY . /content-ranking

RUN pip3 install -r requirements.txt
RUN pip3 install paramiko
RUN python3 -c "import nltk;nltk.download('punkt')"

ENTRYPOINT ["python3", "content_rank.py"]

