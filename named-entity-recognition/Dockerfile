FROM python:3.7

RUN mkdir /named-entity-recognition
WORKDIR /named-entity-recognition
COPY . /named-entity-recognition

RUN pip3 install -r requirements.txt

# RUN pip3 show pymisp

COPY ./data/crawled_obj /usr/local/lib/python3.7/site-packages/pymisp/data/misp-objects/objects/crawled_obj

# RUN file="$(ls -1 /usr/local/lib/python3.7/site-packages/pymisp/data/misp-objects/objects/crawled_obj)" && echo $file

RUN python3 -m spacy download en_core_web_sm
RUN python3 -m spacy download en_core_web_md
RUN python3 -m spacy download en_core_web_lg

ENTRYPOINT ["python3", "ner.py"]