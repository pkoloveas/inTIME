from datetime import datetime as dt
from flask import make_response, abort
from connexion import request
from urllib import parse
import subprocess
import os
import csv
import helpers
import docker_settings
import ports
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


collection = helpers.connect_to_mongo_collection(
    db_name='Crawler_meta',
    collection_name='crawlers',
    ip=helpers.get_keys()['db_ip'],
    username=helpers.get_keys()['db_user'],
    password=helpers.get_keys()['db_pass']
)


def read_all():

    logging.info("Successfully retrieved all crawlers")

    return [helpers.delete_mongo_id(crawler) for crawler in collection.find({})]


def read_one(crawler_id):

    check_id = {'crawler_id': crawler_id}
    crawler = collection.find_one(check_id)

    if crawler:
        logging.info("Successfully retrieved crawler {crawler_id}".format(crawler_id=crawler_id))
        return helpers.delete_mongo_id(crawler)
    elif not crawler:
        logging.info("Crawler {crawler_id} does not exist".format(crawler_id=crawler_id))
        abort(
            404, "Crawler {crawler_id} does not exist".format(crawler_id=crawler_id)
        )


def create_crawler(crawler_id, crawler_config):

    check_id = {'crawler_id': crawler_id}
    crawler = collection.find_one(check_id)

    if not crawler:

        crawler_type = crawler_config.get("crawler_type", None)
        crawler_port = crawler_config.get("port", None)

        if crawler_type == "focused":

            # insert to memory
            crawler_props = {
                "crawler_id": crawler_id,
                "crawler_type": crawler_type,
                "crawler_port": crawler_port,
                "SeedFinder": {
                    "exists": False,
                    "query": ""
                },
                "seeds": [],
                "positive_urls": [],
                "negative_urls": []
            }

            # insert to mongo
            collection.insert(crawler_props, check_keys=False)

            # change port availability
            ports.change_port_availability(crawler_props["crawler_port"])

            cwd = os.getcwd()

            os.chdir(os.path.join("..", "..", "ache-crawlers"))

            if not os.path.isdir(crawler_id):
                os.mkdir(crawler_id)
            os.chdir(crawler_id)

            # get settings list and create file tree and yaml files depending on crawler type
            settings_list = docker_settings.create_docker_compose_settings(
                port=crawler_port,
                abs_path=os.getcwd(),
                db_ip=helpers.get_keys()['db_ip'],
                db_user=helpers.get_keys()['db_user'],
                db_pass=helpers.get_keys()['db_pass'],
                db_crawl=helpers.get_keys()['db_crawl'],
                coll_crawl=helpers.get_keys()['coll_crawl'],
                crawler_id=crawler_id,
                crawler_type=crawler_type
            )

            helpers.create_yaml_file(
                filename="docker-compose.yml",
                settings_list=settings_list,
                type_obj=crawler_type
            )

            helpers.create_yaml_file(
                filename="ache.yml",
                settings_list=settings_list,
                type_obj="ache_focused"
            )
            if not os.path.isdir("model"):
                os.mkdir("model")
            os.chdir("model")

            helpers.create_yaml_file(
                filename="docker-compose.yml",
                settings_list=settings_list,
                type_obj="model_1"
            )

            helpers.create_yaml_file(
                filename="pageclassifier.yml",
                settings_list=settings_list,
                type_obj="model_2"
            )

            os.mkdir("training_data")
            os.chdir("training_data")
            os.mkdir("positive")
            os.mkdir("negative")

            os.chdir(os.path.join("..", ".."))
            os.mkdir("data-ache")
            os.chdir("data-ache")
            os.mkdir("default")
            os.chdir("default")
            os.mkdir("data_pages")

            os.chdir(cwd)
            os.chdir(os.path.join("..", "..", "watchers", "watcher_data"))
            if not os.path.isdir(crawler_id):
                os.mkdir(crawler_id)
            os.chdir(crawler_id)

            helpers.create_yaml_file(
                filename="docker-compose.yml",
                settings_list=settings_list,
                type_obj="watchers"
            )

            os.chdir(cwd)
        elif crawler_type == "indepth_clear":

            # insert to memory
            crawler_props = {
                "crawler_id": crawler_id,
                "crawler_type": crawler_type,
                "crawler_port": crawler_port,
                "link_filters": False,
                "status": False,
                "seeds": [],
                "session_cookie": {
                    "domain": None,
                    "cookies": None,
                    "user_agent": None
                }
            }

            # insert to mongo
            collection.insert(crawler_props, check_keys=False)

            # change port availability
            ports.change_port_availability(crawler_props["crawler_port"])

            cwd = os.getcwd()

            os.chdir(os.path.join("..", "..", "ache-crawlers"))

            if not os.path.isdir(crawler_id):
                os.mkdir(crawler_id)
            os.chdir(crawler_id)

            # get settings list and create file tree and yaml files depending on crawler type
            settings_list = docker_settings.create_docker_compose_settings(
                port=crawler_port,
                abs_path=os.getcwd(),
                db_ip=helpers.get_keys()['db_ip'],
                db_user=helpers.get_keys()['db_user'],
                db_pass=helpers.get_keys()['db_pass'],
                db_crawl=helpers.get_keys()['db_crawl'],
                coll_crawl=helpers.get_keys()['coll_crawl'],
                crawler_id=crawler_id,
                crawler_type=crawler_type
            )

            helpers.create_yaml_file(
                filename="docker-compose.yml",
                settings_list=settings_list,
                type_obj=crawler_type
            )

            helpers.create_yaml_file(
                filename="ache.yml",
                settings_list=settings_list,
                type_obj="ache_indepth"
            )

            os.mkdir("data-ache")
            os.chdir("data-ache")
            os.mkdir("default")
            os.chdir("default")
            os.mkdir("data_pages")

            os.chdir(cwd)
            os.chdir(os.path.join("..", "..", "watchers", "watcher_data"))
            if not os.path.isdir(crawler_id):
                os.mkdir(crawler_id)
            os.chdir(crawler_id)

            helpers.create_yaml_file(
                filename="docker-compose.yml",
                settings_list=settings_list,
                type_obj="watchers"
            )

            os.chdir(cwd)
        elif crawler_type == "indepth_dark":

            # insert to memory
            crawler_props = {
                "crawler_id": crawler_id,
                "crawler_type": crawler_type,
                "crawler_port": crawler_port,
                "link_filters": False,
                "status": False,
                "seeds": [],
                "session_cookie": {
                    "domain": None,
                    "cookies": None,
                    "user_agent": None
                }
            }

            # insert to mongo
            collection.insert(crawler_props, check_keys=False)

            # change port availability
            ports.change_port_availability(crawler_props["crawler_port"])

            cwd = os.getcwd()

            os.chdir(os.path.join("..", "..", "ache-crawlers"))

            if not os.path.isdir(crawler_id):
                os.mkdir(crawler_id)
            os.chdir(crawler_id)

            # get settings list and create file tree and yaml files depending on crawler type
            settings_list = docker_settings.create_docker_compose_settings(
                port=crawler_port,
                abs_path=os.getcwd(),
                db_ip=helpers.get_keys()['db_ip'],
                db_user=helpers.get_keys()['db_user'],
                db_pass=helpers.get_keys()['db_pass'],
                db_crawl=helpers.get_keys()['db_crawl'],
                coll_crawl=helpers.get_keys()['coll_crawl'],
                crawler_id=crawler_id,
                crawler_type=crawler_type
            )

            helpers.create_yaml_file(
                filename="docker-compose.yml",
                settings_list=settings_list,
                type_obj=crawler_type
            )

            helpers.create_yaml_file(
                filename="ache.yml",
                settings_list=settings_list,
                type_obj="ache_indepth"
            )

            os.mkdir("data-ache")
            os.chdir("data-ache")
            os.mkdir("default")
            os.chdir("default")
            os.mkdir("data_pages")

            os.chdir(cwd)
            os.chdir(os.path.join("..", "..", "watchers", "watcher_data"))
            if not os.path.isdir(crawler_id):
                os.mkdir(crawler_id)
            os.chdir(crawler_id)

            helpers.create_yaml_file(
                filename="docker-compose.yml",
                settings_list=settings_list,
                type_obj="watchers"
            )

            os.chdir(cwd)

        logging.info("{crawler_type} crawler with id: {crawler_id} successfully created in port {crawler_port}".format(
            crawler_type=crawler_type,
            crawler_id=crawler_id,
            crawler_port=crawler_port
        ))

        return make_response(
            "{crawler_type} crawler with id: {crawler_id} successfully created in port {crawler_port}".format(
                crawler_type=crawler_type,
                crawler_id=crawler_id,
                crawler_port=crawler_port
            ),
            201
        )
    elif crawler:
        logging.info("Crawler {crawler_id} already exists".format(crawler_id=crawler_id))
        abort(
            409, "Crawler {crawler_id} already exists".format(crawler_id=crawler_id)
        )


def add_seedFinder_query(crawler_id, seedFinder_obj):

    check_id = {'crawler_id': crawler_id}
    crawler = collection.find_one(check_id)

    if crawler and crawler["crawler_type"] == "focused":

        crawler_port = crawler["crawler_port"]

        # update in mongo
        collection.update_one(
            check_id,
            {
                '$set': {
                    "SeedFinder": {
                        "exists": True,
                        "query": seedFinder_obj["seedFinder_query"]
                    },
                }
            }
        )

        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "ache-crawlers", crawler_id))

        # get settings list and create file tree and yaml files
        settings_list = docker_settings.create_docker_compose_settings(
            port=crawler_port,
            abs_path=os.getcwd(),
            seedFinder_query=seedFinder_obj["seedFinder_query"]
        )

        if not os.path.isdir("seedFinder"):
            os.mkdir("seedFinder")
        os.chdir("seedFinder")

        helpers.create_yaml_file(
            filename="docker-compose.yml",
            settings_list=settings_list,
            type_obj="seedFinder"
        )
        os.chdir(cwd)
        logging.info("Successfully added seedFinder query: {seedFinder_query}".format(
            seedFinder_query=seedFinder_obj["seedFinder_query"]
        ))

        return make_response(
            "Successfully added seedFinder query: {seedFinder_query}".format(
                seedFinder_query=seedFinder_obj["seedFinder_query"]
            ),
            201
        )
    elif not crawler:
        logging.info("Crawler {crawler_id} does not exist".format(crawler_id=crawler_id))
        abort(
            404, "Crawler {crawler_id} does not exist".format(crawler_id=crawler_id)
        )
    elif not crawler["crawler_type"] == "focused":
        logging.info("Functionality not permitted for crawler type: {crawler_type}".format(crawler_type=crawler["crawler_type"]))
        abort(
            405, "Functionality not permitted for crawler type: {crawler_type}".format(crawler_type=crawler["crawler_type"])
        )


def read_seedFinder_query(crawler_id):

    check_id = {'crawler_id': crawler_id}
    crawler = collection.find_one(check_id)

    if crawler and crawler["crawler_type"] == "focused":
        logging.info("Successfully retrieved Seedinder query: {seedfinder_query}".format(seedfinder_query=crawler["SeedFinder"]))

        return crawler["SeedFinder"]
    elif not crawler:
        logging.info("Crawler {crawler_id} does not exist".format(crawler_id=crawler_id))
        abort(
            404, "Crawler {crawler_id} does not exist".format(crawler_id=crawler_id)
        )
    elif not crawler["crawler_type"] == "focused":
        logging.info("Functionality not permitted for crawler type: {crawler_type}".format(crawler_type=crawler["crawler_type"]))
        abort(
            405, "Functionality not permitted for crawler type: {crawler_type}".format(crawler_type=crawler["crawler_type"])
        )


def add_seed_single(crawler_id, seed_obj):

    check_id = {'crawler_id': crawler_id}
    crawler = collection.find_one(check_id)

    if crawler:

        # insert to mongo
        collection.update_one(
            check_id,
            {
                '$push': {
                    'seeds': seed_obj["seed_url"]
                }
            }
        )

        # create seeds.txt file
        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "ache-crawlers", crawler_id))
        with open("seeds.txt", 'a+') as file:
            # insert to file
            file.write(seed_obj["seed_url"] + '\n')
        os.chdir(cwd)
        logging.info("Successfully added seed URL: {seed_url}".format(seed_url=seed_obj["seed_url"]))

        return make_response(
            "Successfully added seed URL: {seed_url}".format(
                seed_url=seed_obj["seed_url"]
            ),
            201
        )
    elif not crawler:
        logging.info("Crawler {crawler_id} does not exist".format(crawler_id=crawler_id))
        abort(
            404, "Crawler {crawler_id} does not exist".format(crawler_id=crawler_id)
        )


def add_seed_file(crawler_id, seed_file):

    check_id = {'crawler_id': crawler_id}
    crawler = collection.find_one(check_id)

    if crawler:
        in_file = request.files["seed_file"]

        # create seeds.txt file
        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "ache-crawlers", crawler_id))
        with open("seeds.txt", 'a+') as file:

            for line in in_file.readlines():
                line = line.decode("utf-8").rstrip()

                # insert to mongo
                collection.update_one(
                    check_id,
                    {
                        '$push': {
                            'seeds': line
                        }
                    }
                )

                # insert to file
                file.write(line + '\n')
        os.chdir(cwd)
        logging.info("Successfully added seed file")

        return make_response(
            "Successfully added seed file",
            201
        )
    elif not crawler:
        logging.info("Crawler {crawler_id} does not exist".format(crawler_id=crawler_id))
        abort(
            404, "Crawler {crawler_id} does not exist".format(crawler_id=crawler_id)
        )


def read_seed_urls(crawler_id):

    check_id = {'crawler_id': crawler_id}
    crawler = collection.find_one(check_id)

    if crawler:
        logging.info("Successfully retrieved seed URLs")

        return crawler["seeds"]
    elif not crawler:
        logging.info("Crawler {crawler_id} does not exist".format(crawler_id=crawler_id))
        abort(
            404, "Crawler {crawler_id} does not exist".format(crawler_id=crawler_id)
        )


def delete_seed_url(crawler_id, offset):

    check_id = {'crawler_id': crawler_id}
    crawler = collection.find_one(check_id)

    if crawler and offset <= len(crawler["seeds"]):

        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "ache-crawlers", crawler_id))
        print(len(crawler["seeds"]))

        # delete from file
        helpers.delete_line("seeds.txt", offset - 1)

        # delete from mongo
        url = crawler["seeds"][offset - 1]
        collection.update_one(
            check_id,
            {
                '$pull': {
                    'seeds': url
                }
            }
        )
        os.chdir(cwd)
        logging.info("Seed in position: {offset} was successfully deleted".format(offset=offset))

        return make_response(
            "Seed in position: {offset} was successfully deleted".format(offset=offset),
            200
        )
    elif crawler and not offset <= len(crawler["seeds"]):
        logging.info("Offset: {offset} is not valid".format(offset=offset))
        abort(
            400, "Offset: {offset} is not valid".format(offset=offset)
        )
    elif not crawler:
        logging.info("Crawler {crawler_id} does not exist".format(crawler_id=crawler_id))
        abort(
            404, "Crawler {crawler_id} does not exist".format(crawler_id=crawler_id)
        )


def add_training_url_single(crawler_id, url_type, training_obj):

    check_id = {'crawler_id': crawler_id}
    crawler = collection.find_one(check_id)

    if crawler and crawler["crawler_type"] == "focused":

        url_type = str(url_type + "_urls")

        # insert to mongo
        collection.update_one(
            check_id,
            {
                '$push': {
                    url_type: training_obj["training_url"]
                }
            }
        )

        # create positive_urls.txt/negative_urls.txt file
        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "ache-crawlers", crawler_id, 'model'))
        with open(url_type + ".txt", 'a+') as file:
            # insert to file
            file.write(training_obj["training_url"] + '\n')
        os.chdir(cwd)
        logging.info("Successfully added {url_type} training URL: {training_url}".format(
            url_type=url_type,
            training_url=training_obj["training_url"]
        ))

        return make_response(
            "Successfully added {url_type} training URL: {training_url}".format(
                url_type=url_type,
                training_url=training_obj["training_url"]
            ),
            201
        )
    elif not crawler:
        logging.info("Crawler {crawler_id} does not exist".format(crawler_id=crawler_id))
        abort(
            404, "Crawler {crawler_id} does not exist".format(crawler_id=crawler_id)
        )
    elif not crawler["crawler_type"] == "focused":
        logging.info("Functionality not permitted for crawler type: {crawler_type}".format(crawler_type=crawler["crawler_type"]))
        abort(
            405, "Functionality not permitted for crawler type: {crawler_type}".format(crawler_type=crawler["crawler_type"])
        )


def add_training_file(crawler_id, url_type, training_file):

    check_id = {'crawler_id': crawler_id}
    crawler = collection.find_one(check_id)

    if crawler and crawler["crawler_type"] == "focused":

        url_type = str(url_type + "_urls")
        in_file = request.files["training_file"]

        # create positive_urls.txt/negative_urls.txt file
        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "ache-crawlers", crawler_id, "model"))

        with open(url_type + ".txt", 'a+') as file:

            for line in in_file.readlines():
                line = line.decode("utf-8").rstrip()

                # insert to mongo
                collection.update_one(
                    check_id,
                    {
                        '$push': {
                            url_type: line
                        }
                    }
                )

                # insert to file
                file.write(line + '\n')

        os.chdir(cwd)
        logging.info("Successfully added training file")

        return make_response(
            "Successfully added training file",
            201
        )
    elif not crawler:
        logging.info("Crawler {crawler_id} does not exist".format(crawler_id=crawler_id))
        abort(
            404, "Crawler {crawler_id} does not exist".format(crawler_id=crawler_id)
        )
    elif not crawler["crawler_type"] == "focused":
        logging.info("Functionality not permitted for crawler type: {crawler_type}".format(crawler_type=crawler["crawler_type"]))
        abort(
            405, "Functionality not permitted for crawler type: {crawler_type}".format(crawler_type=crawler["crawler_type"])
        )


def read_training_urls(crawler_id, url_type):

    check_id = {'crawler_id': crawler_id}
    crawler = collection.find_one(check_id)

    if crawler and crawler["crawler_type"] == "focused":
        url_type = str(url_type + "_urls")
        logging.info("Successfully retrieved training URLs")

        return crawler[url_type]
    elif not crawler:
        logging.info("Crawler {crawler_id} does not exist".format(crawler_id=crawler_id))
        abort(
            404, "Crawler {crawler_id} does not exist".format(crawler_id=crawler_id)
        )
    elif not crawler["crawler_type"] == "focused":
        logging.info("Functionality not permitted for crawler type: {crawler_type}".format(crawler_type=crawler["crawler_type"]))
        abort(
            405, "Functionality not permitted for crawler type: {crawler_type}".format(crawler_type=crawler["crawler_type"])
        )


def delete_training_url(crawler_id, url_type, offset):

    check_id = {'crawler_id': crawler_id}
    crawler = collection.find_one(check_id)
    url_type_init = url_type
    url_type = str(url_type + "_urls")

    if crawler and offset <= len(crawler[url_type]) and crawler["crawler_type"] == "focused":

        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "ache-crawlers", crawler_id, 'model'))

        # delete from file
        helpers.delete_line(url_type + ".txt", offset - 1)

        # delete from mongo
        url = crawler[url_type][offset - 1]
        collection.update_one(
            check_id,
            {
                '$pull': {
                    url_type: url
                }
            }
        )

        # delete from file system if it exists
        os.chdir(os.path.join("training_data", url_type_init))

        url_escaped_text = parse.quote(url, safe='')
        if os.path.isfile(url_escaped_text):
            os.remove(url_escaped_text)
        else:
            pass

        os.chdir(cwd)
        logging.info("{url_type} training URL in position: {offset} was successfully deleted".format(url_type=url_type_init, offset=offset))

        return make_response(
            "{url_type} training URL in position: {offset} was successfully deleted".format(url_type=url_type_init, offset=offset),
            200
        )
    elif crawler and crawler["crawler_type"] == "focused" and not offset <= len(crawler[url_type]):
        logging.info("Offset: {offset} is not valid".format(offset=offset))
        abort(
            400, "Offset: {offset} is not valid".format(offset=offset)
        )
    elif not crawler:
        logging.info("Crawler {crawler_id} does not exist".format(crawler_id=crawler_id))
        abort(
            404, "Crawler {crawler_id} does not exist".format(crawler_id=crawler_id)
        )
    elif not crawler["crawler_type"] == "focused":
        logging.info("Functionality not permitted for crawler type: {crawler_type}".format(crawler_type=crawler["crawler_type"]))
        abort(
            405, "Functionality not permitted for crawler type: {crawler_type}".format(crawler_type=crawler["crawler_type"])
        )


def add_link_filters_file(crawler_id, link_filters_file):

    check_id = {'crawler_id': crawler_id}
    crawler = collection.find_one(check_id)

    if crawler and (crawler["crawler_type"] == "indepth_clear" or crawler["crawler_type"] == "indepth_dark"):
        in_file = request.files["link_filters_file"]

        # insert to mongo
        collection.update_one(
            check_id,
            {
                '$set': {
                    'link_filters': True
                }
            }
        )

        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "ache-crawlers", crawler_id))

        # create link_filters.yml file
        with open("link_filters.yml", 'a+') as file:
            for line in in_file.readlines():
                line = line.decode("utf-8").rstrip()
                file.write(line + '\n')

        os.chdir(cwd)
        logging.info("Successfully added link filters file")

        return make_response(
            "Successfully added link filters file",
            201
        )
    elif not crawler:
        logging.info("Crawler {crawler_id} does not exist".format(crawler_id=crawler_id))
        abort(
            404, "Crawler {crawler_id} does not exist".format(crawler_id=crawler_id)
        )
    elif not crawler["crawler_type"] == "indepth_clear" or not crawler["crawler_type"] == "indepth_dark":
        logging.info("Functionality not permitted for crawler type: {crawler_type}".format(crawler_type=crawler["crawler_type"]))
        abort(
            405, "Functionality not permitted for crawler type: {crawler_type}".format(crawler_type=crawler["crawler_type"])
        )


def add_cookies(crawler_id, cookie_obj):

    check_id = {'crawler_id': crawler_id}
    crawler = collection.find_one(check_id)

    if crawler and (crawler["crawler_type"] == "indepth_clear" or crawler["crawler_type"] == "indepth_dark"):

        collection.update_one(
            check_id,
            {
                "$set": {
                    "session_cookie": {
                        "domain": cookie_obj["domain"],
                        "cookies": cookie_obj["cookies"],
                        "user_agent": cookie_obj["user_agent"]
                    }
                }
            }
        )
        logging.info("Successfully added Session Cookies")

        return make_response(
            "Successfully added Session Cookies",
            201
        )
    elif not crawler:
        logging.info("Crawler {crawler_id} does not exist".format(crawler_id=crawler_id))
        abort(
            404, "Crawler {crawler_id} does not exist".format(crawler_id=crawler_id)
        )
    elif not crawler["crawler_type"] == "indepth_clear" or not crawler["crawler_type"] == "indepth_dark":
        logging.info("Functionality not permitted for crawler type: {crawler_type}".format(crawler_type=crawler["crawler_type"]))
        abort(
            405, "Functionality not permitted for crawler type: {crawler_type}".format(crawler_type=crawler["crawler_type"])
        )


def start_crawl(crawler_id):

    check_id = {'crawler_id': crawler_id}
    crawler = collection.find_one(check_id)

    if crawler and crawler["crawler_type"] == "focused":

        logging.info("Starting Focused crawler initialization processes...")
        if len(crawler["positive_urls"]) and len(crawler["negative_urls"]):

            logging.info("Training URLs exist")
            cwd = os.getcwd()
            os.chdir(os.path.join("..", "..", "ache-crawlers", crawler_id, "model"))

            logging.info("Retrieving training data")
            helpers.fill_training_folders(
                crawler_id=crawler_id,
                pos_f='positive_urls.txt',
                neg_f='negative_urls.txt'
            )

            logging.info("Starting page classifier training")
            subprocess.run(["docker-compose up"], shell=True)
            os.chdir(cwd)

            if crawler["SeedFinder"]["exists"]:
                logging.info("Starting SeedFinder")
                os.chdir(os.path.join("..", "..", "ache-crawlers", crawler_id, "seedFinder"))
                subprocess.run(["docker-compose up"], shell=True)
                os.chdir(cwd)
            else:
                pass

            os.chdir(os.path.join("..", "..", "ache-crawlers", crawler_id))
            subprocess.run(["docker-compose up -d"], shell=True)
            os.chdir(os.path.join(cwd, "..", "..", "watchers", "watcher_data", crawler_id))
            subprocess.run(["docker-compose up -d"], shell=True)
            os.chdir(cwd)

            logging.info("Successfully started crawler with id: {crawler_id}".format(crawler_id=crawler_id))

            return make_response(
                "Starting crawler with id: {crawler_id}".format(
                    crawler_id=crawler_id
                ),
                200
            )
        elif len(crawler["positive_urls"]) and not len(crawler["negative_urls"]):
            logging.info("Crawler {crawler_id} is missing negative training URLs".format(crawler_id=crawler_id))
            abort(
                404, "Crawler {crawler_id} is missing negative training URLs".format(crawler_id=crawler_id)
            )
        elif not len(crawler["positive_urls"]) and len(crawler["negative_urls"]):
            logging.info("Crawler {crawler_id} is missing positive training URLs".format(crawler_id=crawler_id))
            abort(
                404, "Crawler {crawler_id} is missing positive training URLs".format(crawler_id=crawler_id)
            )
        else:
            logging.info("Crawler {crawler_id} is missing positive and negative training URLs".format(crawler_id=crawler_id))
            abort(
                404, "Crawler {crawler_id} is missing positive and negative training URLs".format(crawler_id=crawler_id)
            )
    elif crawler and (crawler["crawler_type"] == "indepth_clear" or crawler["crawler_type"] == "indepth_dark"):

        logging.info("Starting Indepth crawler initialization processes...")
        cwd = os.getcwd()

        os.chdir(os.path.join("..", "..", "ache-crawlers", crawler_id))
        subprocess.run(["docker-compose up -d"], shell=True)
        os.chdir(os.path.join(cwd, "..", "..", "watchers", "watcher_data", crawler_id))
        subprocess.run(["docker-compose up -d"], shell=True)
        os.chdir(cwd)

        logging.info("Successfully started crawler with id: {crawler_id}".format(crawler_id=crawler_id))

        return make_response(
            "Starting crawler with id: {crawler_id}".format(
                crawler_id=crawler_id
            ),
            200
        )
    elif not crawler:
        logging.info("Crawler {crawler_id} does not exist".format(crawler_id=crawler_id))
        abort(
            404, "Crawler {crawler_id} does not exist".format(crawler_id=crawler_id)
        )


def stop_crawl(crawler_id):

    check_id = {'crawler_id': crawler_id}
    crawler = collection.find_one(check_id)

    if crawler:
        logging.info("Stopping crawl...")
        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "ache-crawlers", crawler_id))
        subprocess.run(["docker-compose down"], shell=True)
        os.chdir(os.path.join(cwd, "..", "..", "watchers", "watcher_data", crawler_id))
        subprocess.run(["docker-compose down"], shell=True)
        os.chdir(cwd)

        logging.info("Successfully stopped crawler")

        return make_response(
            "Stopping crawler with id: {crawler_id}".format(
                crawler_id=crawler_id
            ),
            200
        )
    elif not crawler:
        logging.info("Crawler {crawler_id} does not exist".format(crawler_id=crawler_id))
        abort(
            404, "Crawler {crawler_id} does not exist".format(crawler_id=crawler_id)
        )


def read_crawled_pages(crawler_id, page_type):

    check_id = {'crawler_id': crawler_id}
    crawler = collection.find_one(check_id)

    if crawler:

        file = page_type + "pages.csv"
        page_type = page_type + "_pages"
        path_to_pages = os.path.join("..", "..", "ache-crawlers", crawler_id, "data-ache", "default", "data_monitor")
        pages = []

        with open(os.path.join(path_to_pages, file)) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter="\t")
            for row in csv_reader:
                pages.append(row[0])

        logging.info("Successfully retrieved crawled pages")

        return pages
    elif not crawler:
        logging.info("Crawler {crawler_id} does not exist".format(crawler_id=crawler_id))
        abort(
            404, "Crawler {crawler_id} does not exist".format(crawler_id=crawler_id)
        )
