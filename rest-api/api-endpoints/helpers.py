import yaml
import json
import os
from pymongo import MongoClient
from requests import get
from requests.exceptions import MissingSchema, ConnectionError
from urllib import parse
from bs4 import BeautifulSoup
import logging

logging.basicConfig(
    format='%(asctime)s \t %(message)s',
    level=logging.INFO,
    datefmt='%d-%m-%Y %H:%M:%S',
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)


def get_keys():

    return {
        "db_crawl": os.getenv('DB_CRAWL'),
        "db_prod": os.getenv('DB_PRODUCTS'),
        "coll_crawl": os.getenv('COLLECTION_CRAWL'),
        "coll_voc": os.getenv('COLLECTION_VOCABULARY'),
        "coll_topic_vec": os.getenv('COLLECTION_TOPIC_VECTORS'),
        "coll_prod": os.getenv('COLLECTION_PRODUCTS'),
        "db_ip": os.getenv('MONGO_DB_IP'),
        "db_user": os.getenv('MONGO_DB_USER'),
        "db_pass": os.getenv('MONGO_DB_PASS'),
        "misp_ip": os.getenv('MISP_IP'),
        "misp_key": os.getenv('MISP_KEY')
    }


def create_yaml_file(filename, settings_list, type_obj):

    settings = [s['obj'] for s in settings_list if s['type'] == type_obj]

    with open(filename, 'w') as file:
        yaml.dump(
            data=settings[0],
            stream=file,
            sort_keys=False
        )


def get_yaml_data(type_obj):

    filename = type_obj + ".yml"

    with open(filename) as file:
        settings = yaml.load(
            stream=file,
            Loader=yaml.FullLoader
        )
        print(json.dumps(settings, sort_keys=True, indent=4))
        print('----------------------------------------------------------------')


def delete_line(original_file, line_number):

    is_skipped = False
    current_index = 0
    dummy_file = original_file + '.bak'

    with open(original_file, 'r') as read_obj, open(dummy_file, 'w') as write_obj:

        for line in read_obj:
            if current_index != line_number:
                write_obj.write(line)
            else:
                is_skipped = True
            current_index += 1

    if is_skipped:
        os.remove(original_file)
        os.rename(dummy_file, original_file)
    else:
        os.remove(dummy_file)


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


def print_json(item):
    print(json.dumps(delete_mongo_id(item), indent=4, sort_keys=True))


def delete_mongo_id(item):

    del item['_id']
    return item


def fill_training_folders(crawler_id, pos_f, neg_f):
    any(make_http_request(crawler_id, url, 1) for url in read_urls(crawler_id, pos_f))
    any(make_http_request(crawler_id, url, 0) for url in read_urls(crawler_id, neg_f))


def read_urls(crawler_id, infile):
    urls = []
    with open(infile) as fp:
        urls = [line.strip() for line in fp]

    return urls


def get_folder_text(folder_code):
    return "positive" if folder_code else "negative"


def make_http_request(crawler_id, url, folder_code):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36"}

    try:
        logging.info("Getting URL: {}".format(url))
        req = get(url, headers=headers)
        status = req.status_code
        logging.info("Status: {}".format(status))

        if status == 200:
            write_html(url, folder_code, content=req.content)
    except MissingSchema as ms:
        try:
            logging.info("Missing \"http://\". Trying: {}{}...".format("http://", url))
            req = get("{}{}".format("http://", url), headers=headers)
            status = req.status_code
            logging.info("Status: {}".format(status))

            if status == 200:
                write_html(url, folder_code, content=req.content)
        except Exception as e:
            logging.info("Invalid URL: {}. Skipping...\n".format(url))
            pass
    except Exception as e:
        logging.info("Invalid URL: {}. Skipping...\n".format(url))
        pass


def write_html(url, folder_code, content):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36"}

    try:
        soup = BeautifulSoup(content, "html.parser")

        logging.info("Writing file...")

        title = parse.quote(url, safe='')
        folder = get_folder_text(folder_code)

        with open(os.path.join("training_data", folder, title), "w+", encoding='utf-8') as outfile:
            outfile.write(str(soup))
    except Exception as e:
        pass
