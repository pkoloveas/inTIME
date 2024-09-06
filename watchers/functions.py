import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pymongo import MongoClient
import os
from urllib import parse
from lxml import html
import unicodedata
from hashlib import md5
import json
from htmlmin import minify
from datetime import datetime as dt
import re
import logging

logging.basicConfig(
    format='%(asctime)s \t %(message)s',
    level=logging.INFO,
    datefmt='%d-%m-%Y %H:%M:%S'
)

# ######################################################
# #################### DOC TEMPLATE ####################
# {
#   "doc_id": "",
#   "discovered_by": "",
#   "discovery_timestamp": "2020-06-03T00:00:00",
#   "title": "",
#   "hashed_title": "",
#   "raw_text": "",
#   "hashed_text": "",
#   "source_url": "",
#   "hashed_source_url": "",
#   "raw_html": "",
#   "hashed_html": ""
# }
# ######################################################


class Watcher:

    def __init__(self, db_crawl, collection_crawl, crawler_id, crawler_type, directory, username, password, ip):
        self.observer = Observer()
        self.directory_to_watch = directory
        self.crawler_id = crawler_id
        self.crawler_type = crawler_type
        self.collection = connect_to_mongo_collection(
            db_name=db_crawl,
            collection_name=collection_crawl,
            ip=ip,
            username=username,
            password=password
        )
        self.last_doc_id = get_last_doc_id(self.collection, self.crawler_id)

    def run(self):
        # time.sleep(15)
        event_handler = Handler(self.collection, self.crawler_id, self.crawler_type, self.last_doc_id)
        self.observer.schedule(event_handler, self.directory_to_watch, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except Exception as e:
            self.observer.stop()
            logging.info("Error")

        self.observer.join()


class Handler(FileSystemEventHandler):

    def __init__(self, collection, crawler_id, crawler_type, last_doc_id):
        self.collection = collection
        self.crawler_id = crawler_id
        self.crawler_type = crawler_type
        self.last_doc_id = last_doc_id
        self.doc_id_num = self.last_doc_id

    # @staticmethod
    def on_any_event(self, event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':

            logging.info("Created file %s" % event.src_path)
            try:

                title, content, source_url, html_page, hashed_title, hashed_content, hashed_source_url, hashed_html_page = lxml_parser(event.src_path)

                if content is None:
                    logging.info("No content in document. Skipping...")
                    pass
                else:
                    self.doc_id_num += 1
                    doc_id = "cti_{}_{}".format(self.crawler_id, self.doc_id_num)
                    discovery_timestamp = dt.now().isoformat(sep='T', timespec='auto')
                    doc = create_doc(
                        doc_id=doc_id,
                        title=title,
                        content=content,
                        source_url=source_url,
                        html_page=html_page,
                        hashed_title=hashed_title,
                        hashed_content=hashed_content,
                        hashed_source_url=hashed_source_url,
                        hashed_html_page=hashed_html_page,
                        crawler_id=self.crawler_id,
                        crawler_type=self.crawler_type,
                        discovery_timestamp=discovery_timestamp
                    )

                    self.collection.insert_one(doc)

                    logging.info("Added document \"{}\" to DB".format(doc_id))

                if os.path.isfile(event.src_path):
                    os.remove(event.src_path)

            except Exception as e:
                logging.info(e)

        elif event.event_type == 'deleted':
            logging.info("Deleted file %s" % event.src_path)


def lxml_parser(filename):

    try:
        with open(file=filename, mode='r', encoding='utf-8') as f:
            html_page = f.read()
            hashed_html_page = get_md5_hash(html_page)

        tree = html.fromstring(minify(html_page))

        source_url = parse.unquote(filename.split("/")[-1])
        hashed_source_url = get_md5_hash(source_url)

        title = text_extractor(tree, '//title/text()')
        hashed_title = get_md5_hash(title)

        headings = text_extractor(tree, "//h1/text() | //h2/text()")
        paragraphs = text_extractor(tree, "//p/text()")
        body_text = text_extractor(tree, "//div[contains(@id, 'content')]//text()")

        if (headings.strip() == "\"\"" or paragraphs.strip() == "\"\"") and body_text.strip() == "\"\"":
            content = None
            hashed_content = None
        else:
            content = "{}. {}. {}".format(headings, paragraphs, body_text)
            hashed_content = get_md5_hash(content)

        # print(' '.join([p for p in tree.xpath("//div[contains(@id, 'content')]//text()") if p != 'undefined']))
        # print(convert_to_ascii(' '.join([p for p in tree.xpath('/html/body/main/div/div[1]/div/div/div/div/div/div/text()') if p != 'undefined'])).strip())
        # print(content)
        return title, content, source_url, html_page, hashed_title, hashed_content, hashed_source_url, hashed_html_page
    except Exception as e:
        logging.info(e)
        pass


def create_doc(doc_id, title, content, source_url, html_page, hashed_title, hashed_content, hashed_source_url, hashed_html_page, crawler_id, crawler_type, discovery_timestamp):

    doc = {
        "doc_id": doc_id,
        "discovered_by": crawler_id,
        "discovery_timestamp": discovery_timestamp,
        "crawler_type": crawler_type,
        "title": title,
        "hashed_title": hashed_title,
        "raw_text": content,
        "hashed_text": hashed_content,
        "source_url": source_url,
        "hashed_source_url": hashed_source_url,
        "raw_html": html_page,
        "hashed_html": hashed_html_page
    }

    return doc


def get_md5_hash(text):
    return md5(text.encode("utf-8")).hexdigest()


def text_extractor(tree, pattern):
    return json.dumps(remove_tabs_newlines(remove_non_ascii(' '.join([p for p in tree.xpath(pattern) if p != 'undefined']))))


def remove_html_tags(text):
    """Removes HTML tags from text"""
    clean = re.compile(r'<.*?>')

    return re.sub(clean, '', text)


def convert_to_ascii(s):
    """Converts non-ASCII accented characters to ASCII equivalent"""
    return ''.join(
        c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'
    )


def remove_non_ascii(s):
    """Removes non-ASCII characters"""
    return s.encode("ascii", "ignore").decode()


def remove_tabs_newlines(s):
    """Removes tabs and newline characters"""
    return re.sub(r"\s+", " ", s)


def get_keys():

    return {
        "db_ip": os.getenv('MONGO_DB_IP'),
        "db_user": os.getenv('MONGO_DB_USER'),
        "db_pass": os.getenv('MONGO_DB_PASS'),
        "misp_ip": os.getenv('MISP_IP'),
        "misp_key": os.getenv('MISP_KEY')
    }


def connect_to_mongo_collection(db_name, collection_name, ip, username, password):
    """Connects to mongoDB collection"""
    # client = MongoClient()
    client = MongoClient(
        host=ip,
        username=username,
        password=password
    )
    db = client[db_name]
    collection = db[collection_name]

    return collection


def get_last_doc_id(collection, crawler_id):
    """Retrieves the doc_id of the last document added to mongoDB"""

    last_doc_id = []
    query_where = {
        "discovered_by": {
            "$eq": crawler_id
        }
    }
    query_select = {
        "_id": 0,
        "doc_id": 1
    }

    for doc in collection.find(query_where, query_select):
        last_doc_id.append(doc)

    if len(last_doc_id) > 0:
        last_doc_id = int(last_doc_id[-1]['doc_id'].split('_')[-1])
    else:
        last_doc_id = 0

    return last_doc_id
