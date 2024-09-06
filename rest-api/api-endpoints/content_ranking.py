import os
from datetime import datetime as dt
from flask import make_response, abort
import helpers
import docker_settings
import subprocess
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
    collection_name='content_ranking_config',
    ip=helpers.get_keys()['db_ip'],
    username=helpers.get_keys()['db_user'],
    password=helpers.get_keys()['db_pass']
)


def add_config(content_ranking_config):

    config = collection.find_one({})

    if not config:
        cr_config_props = {
            "classifier_type": content_ranking_config["classifier_type"],
            "dimensions": content_ranking_config["dimensions"],
            "window": content_ranking_config["window"],
            "min_count": content_ranking_config["min_count"],
            "top_n": content_ranking_config["top_n"],
            "number_of_docs": content_ranking_config["number_of_docs"],
            "iteration": 0
        }

        # insert to mongo
        collection.insert(cr_config_props, check_keys=False)
        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "content-ranking"))

        # get settings list and create yaml file
        settings_list = docker_settings.create_docker_compose_settings(
            abs_path=os.getcwd(),
            db_ip=helpers.get_keys()['db_ip'],
            db_user=helpers.get_keys()['db_user'],
            db_pass=helpers.get_keys()['db_pass'],
            db_crawl=helpers.get_keys()['db_crawl'],
            coll_crawl=helpers.get_keys()['coll_crawl'],
            coll_voc=helpers.get_keys()['coll_voc'],
            coll_topic_vec=helpers.get_keys()['coll_topic_vec'],
            cr_config=content_ranking_config
        )

        helpers.create_yaml_file(
            filename="docker-compose.yml",
            settings_list=settings_list,
            type_obj="content_ranking"
        )

        os.chdir(cwd)
        logging.info("Successfully added Content Ranking config")

        return make_response(
            "CREATED - Successfully added Content Ranking config",
            201
        )
    else:
        logging.info("Content Ranking config already exists")
        abort(
            409,
            "Content Ranking Config already exists"
        )


def read_config():

    config = collection.find_one({})

    if config:
        logging.info("Successfully retrieved Content Ranking config")

        return helpers.delete_mongo_id(config)
    elif not config:
        logging.info("Content Ranking config does not exist")
        abort(
            404,
            "NOT FOUND - Content Ranking config does not exist"
        )


def read_classifier():

    config = collection.find_one({})

    if config:
        logging.info("Successfully retrieved classifier type")

        return config["classifier_type"]
    elif not config:
        logging.info("Content Ranking config does not exist")
        abort(
            404,
            "NOT FOUND - Content Ranking config does not exist"
        )


def read_number_of_docs():

    config = collection.find_one({})

    if config:
        logging.info("Successfully retrieved number of documents to be evaluated with Content Ranking")

        return config["number_of_docs"]
    elif not config:
        logging.info("Content Ranking config does not exist")
        abort(
            404,
            "NOT FOUND - Content Ranking config does not exist"
        )


def read_iteration_number():

    config = collection.find_one({})

    if config:
        logging.info("Successfully retrieved iteration number of Content Ranking")

        return config["iteration"]
    elif not config:
        logging.info("Content Ranking config does not exist")
        abort(
            404,
            "NOT FOUND - Content Ranking config does not exist"
        )


def change_config(content_ranking_config):

    config = collection.find_one({})

    if config:
        content_ranking_config["iteration"] = read_iteration_number()
        collection.update_one(
            {},
            {
                '$set': {
                    "classifier_type": content_ranking_config["classifier_type"],
                    "dimensions": content_ranking_config["dimensions"],
                    "window": content_ranking_config["window"],
                    "min_count": content_ranking_config["min_count"],
                    "top_n": content_ranking_config["top_n"],
                    "number_of_docs": content_ranking_config["number_of_docs"],
                    "iteration": content_ranking_config["iteration"]
                }
            }
        )

        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "content-ranking"))

        # get settings list and create yaml file
        settings_list = docker_settings.create_docker_compose_settings(
            abs_path=os.getcwd(),
            db_ip=helpers.get_keys()['db_ip'],
            db_user=helpers.get_keys()['db_user'],
            db_pass=helpers.get_keys()['db_pass'],
            db_crawl=helpers.get_keys()['db_crawl'],
            coll_crawl=helpers.get_keys()['coll_crawl'],
            coll_voc=helpers.get_keys()['coll_voc'],
            coll_topic_vec=helpers.get_keys()['coll_topic_vec'],
            cr_config=content_ranking_config
        )

        helpers.create_yaml_file(
            filename="docker-compose.yml",
            settings_list=settings_list,
            type_obj="content_ranking"
        )

        os.chdir(cwd)
        logging.info("Successfully updated Content Ranking config")

        return make_response(
            "OK - Successfully updated Content Ranking config",
            200
        )
    elif not config:
        logging.info("Content Ranking config does not exist")
        abort(
            404,
            "NOT FOUND - Content Ranking config does not exist"
        )


def change_classifier(classifier_type):

    config = collection.find_one({})

    if config:
        collection.update_one(
            {},
            {
                '$set': {
                    "classifier_type": classifier_type
                }
            }
        )

        content_ranking_config = read_config()
        content_ranking_config["classifier_type"] = classifier_type
        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "content-ranking"))

        # get settings list and create yaml file
        settings_list = docker_settings.create_docker_compose_settings(
            abs_path=os.getcwd(),
            db_ip=helpers.get_keys()['db_ip'],
            db_user=helpers.get_keys()['db_user'],
            db_pass=helpers.get_keys()['db_pass'],
            db_crawl=helpers.get_keys()['db_crawl'],
            coll_crawl=helpers.get_keys()['coll_crawl'],
            coll_voc=helpers.get_keys()['coll_voc'],
            coll_topic_vec=helpers.get_keys()['coll_topic_vec'],
            cr_config=content_ranking_config
        )

        helpers.create_yaml_file(
            filename="docker-compose.yml",
            settings_list=settings_list,
            type_obj="content_ranking"
        )

        os.chdir(cwd)
        logging.info("Successfully updated classifier type")

        return make_response(
            "OK - Successfully updated classifier type",
            201
        )
    elif not config:
        logging.info("Content Ranking config does not exist")
        abort(
            404,
            "NOT FOUND - Content Ranking config does not exist"
        )


def change_number_of_docs(number_of_docs):

    config = collection.find_one({})

    if config:
        collection.update_one(
            {},
            {
                '$set': {
                    "number_of_docs": number_of_docs
                }
            }
        )

        content_ranking_config = read_config()
        content_ranking_config["number_of_docs"] = number_of_docs
        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "content-ranking"))

        # get settings list and create yaml file
        settings_list = docker_settings.create_docker_compose_settings(
            abs_path=os.getcwd(),
            db_ip=helpers.get_keys()['db_ip'],
            db_user=helpers.get_keys()['db_user'],
            db_pass=helpers.get_keys()['db_pass'],
            db_crawl=helpers.get_keys()['db_crawl'],
            coll_crawl=helpers.get_keys()['coll_crawl'],
            coll_voc=helpers.get_keys()['coll_voc'],
            coll_topic_vec=helpers.get_keys()['coll_topic_vec'],
            cr_config=content_ranking_config
        )

        helpers.create_yaml_file(
            filename="docker-compose.yml",
            settings_list=settings_list,
            type_obj="content_ranking"
        )

        os.chdir(cwd)
        logging.info("Successfully updated number of documents to be evaluated with Content Ranking")

        return make_response(
            "OK - Successfully updated number of documents to be evaluated with Content Ranking",
            201
        )
    elif not config:
        logging.info("Content Ranking config does not exist")
        abort(
            404,
            "NOT FOUND - Content Ranking config does not exist"
        )


def update_iteration_number():

    config = collection.find_one({})

    if config:
        content_ranking_config = read_config()
        content_ranking_config["iteration"] += 1

        collection.update_one(
            {},
            {
                '$set': {
                    "iteration": content_ranking_config["iteration"]
                }
            }
        )

        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "content-ranking"))

        # get settings list and create yaml file
        settings_list = docker_settings.create_docker_compose_settings(
            abs_path=os.getcwd(),
            db_ip=helpers.get_keys()['db_ip'],
            db_user=helpers.get_keys()['db_user'],
            db_pass=helpers.get_keys()['db_pass'],
            db_crawl=helpers.get_keys()['db_crawl'],
            coll_crawl=helpers.get_keys()['coll_crawl'],
            coll_voc=helpers.get_keys()['coll_voc'],
            coll_topic_vec=helpers.get_keys()['coll_topic_vec'],
            cr_config=content_ranking_config
        )

        helpers.create_yaml_file(
            filename="docker-compose.yml",
            settings_list=settings_list,
            type_obj="content_ranking"
        )

        os.chdir(cwd)
        logging.info("Successfully updated iteration number of Content Ranking")

        return make_response(
            "OK - Successfully updated iteration number of Content Ranking",
            201
        )
    elif not config:
        logging.info("Content Ranking config does not exist")
        abort(
            404,
            "NOT FOUND - Content Ranking config does not exist"
        )


def reset_iteration_number():

    config = collection.find_one({})

    if config:
        content_ranking_config = read_config()
        content_ranking_config["iteration"] = 0

        collection.update_one(
            {},
            {
                '$set': {
                    "iteration": content_ranking_config["iteration"]
                }
            }
        )

        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "content-ranking"))

        # get settings list and create yaml file
        settings_list = docker_settings.create_docker_compose_settings(
            abs_path=os.getcwd(),
            db_ip=helpers.get_keys()['db_ip'],
            db_user=helpers.get_keys()['db_user'],
            db_pass=helpers.get_keys()['db_pass'],
            db_crawl=helpers.get_keys()['db_crawl'],
            coll_crawl=helpers.get_keys()['coll_crawl'],
            coll_voc=helpers.get_keys()['coll_voc'],
            coll_topic_vec=helpers.get_keys()['coll_topic_vec'],
            cr_config=content_ranking_config
        )

        helpers.create_yaml_file(
            filename="docker-compose.yml",
            settings_list=settings_list,
            type_obj="content_ranking"
        )

        os.chdir(cwd)
        logging.info("Successfully reset iteration number of Content Ranking")

        return make_response(
            "OK - Successfully reset iteration number of Content Ranking",
            201
        )
    elif not config:
        logging.info("Content Ranking config does not exist")
        abort(
            404,
            "NOT FOUND - Content Ranking config does not exist"
        )


def start():

    update_iteration_number()

    logging.info("Starting Content Ranking...")
    cwd = os.getcwd()
    os.chdir(os.path.join("..", "..", "content-ranking"))
    # subprocess.run(["docker-compose up"], shell=True)  # debug
    subprocess.run(["docker-compose up -d"], shell=True)
    os.chdir(cwd)
    logging.info("Successfully started Content Ranking")

    return make_response(
        "Starting Content Ranking",
        200
    )


def stop():

    logging.info("Stopping Content Ranking...")
    cwd = os.getcwd()
    os.chdir(os.path.join("..", "..", "content-ranking"))
    subprocess.run(["docker-compose down"], shell=True)
    os.chdir(cwd)
    logging.info("Successfully stopped Content Ranking")

    return make_response(
        "Stopping Content Ranking",
        200
    )
