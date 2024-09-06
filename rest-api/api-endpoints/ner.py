import os
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
    collection_name='ner_config',
    ip=helpers.get_keys()['db_ip'],
    username=helpers.get_keys()['db_user'],
    password=helpers.get_keys()['db_pass']
)


def add_config(ner_config):

    config = collection.find_one({})

    if not config:
        ner_config_props = {
            "spacy_model": ner_config["spacy_model"],
            "phrase_matcher": ner_config["phrase_matcher"],
            "top_n": ner_config["top_n"],
            "number_of_docs": ner_config["number_of_docs"],
            "iteration": 0
        }

        # insert to mongo
        collection.insert(ner_config_props, check_keys=False)
        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "named-entity-recognition"))

        # get settings list and create yaml file
        settings_list = docker_settings.create_docker_compose_settings(
            abs_path=os.getcwd(),
            db_ip=helpers.get_keys()['db_ip'],
            db_user=helpers.get_keys()['db_user'],
            db_pass=helpers.get_keys()['db_pass'],
            misp_ip=helpers.get_keys()['misp_ip'],
            misp_key=helpers.get_keys()['misp_key'],
            db_crawl=helpers.get_keys()['db_crawl'],
            db_prod=helpers.get_keys()['db_prod'],
            coll_crawl=helpers.get_keys()['coll_crawl'],
            coll_prod=helpers.get_keys()['coll_prod'],
            ner_config=ner_config
        )

        helpers.create_yaml_file(
            filename="docker-compose.yml",
            settings_list=settings_list,
            type_obj="ner"
        )

        os.chdir(cwd)
        logging.info("Successfully added Named Entity Recognition config")

        return make_response(
            "CREATED - Successfully added Named Entity Recognition config",
            201
        )
    else:
        logging.info("Named Entity Recognition config already exists")
        abort(
            409,
            "Named Entity Recognition Config already exists"
        )


def read_config():

    config = collection.find_one({})

    if config:
        logging.info("Successfully retrieved Named Entity Recognition config")

        return helpers.delete_mongo_id(config)
    elif not config:
        logging.info("Named Entity Recognition config does not exist")
        abort(
            404,
            "NOT FOUND - Named Entity Recognition config does not exist"
        )


def read_number_of_docs():

    config = collection.find_one({})

    if config:
        logging.info("Successfully retrieved number of documents to be evaluated with Named Entity Recognition")

        return config["number_of_docs"]
    elif not config:
        logging.info("Named Entity Recognition config does not exist")
        abort(
            404,
            "NOT FOUND - Named Entity Recognition config does not exist"
        )


def read_iteration_number():

    config = collection.find_one({})

    if config:
        logging.info("Successfully retrieved iteration number of Named Entity Recognition")

        return config["iteration"]
    elif not config:
        logging.info("Named Entity Recognition config does not exist")
        abort(
            404,
            "NOT FOUND - Named Entity Recognition config does not exist"
        )


def change_config(ner_config):

    config = collection.find_one({})

    if config:
        ner_config["iteration"] = read_iteration_number()
        collection.update_one(
            {},
            {
                '$set': {
                    "spacy_model": ner_config["spacy_model"],
                    "phrase_matcher": ner_config["phrase_matcher"],
                    "top_n": ner_config["top_n"],
                    "number_of_docs": ner_config["number_of_docs"],
                    "iteration": ner_config["iteration"]
                }
            }
        )

        cwd = os.getcwd()

        os.chdir(os.path.join("..", "..", "named-entity-recognition"))

        # get settings list and create yaml file
        settings_list = docker_settings.create_docker_compose_settings(
            abs_path=os.getcwd(),
            db_ip=helpers.get_keys()['db_ip'],
            db_user=helpers.get_keys()['db_user'],
            db_pass=helpers.get_keys()['db_pass'],
            misp_ip=helpers.get_keys()['misp_ip'],
            misp_key=helpers.get_keys()['misp_key'],
            db_crawl=helpers.get_keys()['db_crawl'],
            db_prod=helpers.get_keys()['db_prod'],
            coll_crawl=helpers.get_keys()['coll_crawl'],
            coll_prod=helpers.get_keys()['coll_prod'],
            ner_config=ner_config
        )

        helpers.create_yaml_file(
            filename="docker-compose.yml",
            settings_list=settings_list,
            type_obj="ner"
        )

        os.chdir(cwd)
        logging.info("Successfully updated Named Entity Recognition config")

        return make_response(
            "OK - Successfully updated Named Entity Recognition config",
            200
        )
    elif not config:
        logging.info("Named Entity Recognition config does not exist")
        abort(
            404,
            "NOT FOUND - Named Entity Recognition config does not exist"
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

        ner_config = read_config()
        ner_config["number_of_docs"] = number_of_docs
        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "named-entity-recognition"))

        # get settings list and create yaml file
        settings_list = docker_settings.create_docker_compose_settings(
            abs_path=os.getcwd(),
            db_ip=helpers.get_keys()['db_ip'],
            db_user=helpers.get_keys()['db_user'],
            db_pass=helpers.get_keys()['db_pass'],
            misp_ip=helpers.get_keys()['misp_ip'],
            misp_key=helpers.get_keys()['misp_key'],
            db_crawl=helpers.get_keys()['db_crawl'],
            db_prod=helpers.get_keys()['db_prod'],
            coll_crawl=helpers.get_keys()['coll_crawl'],
            coll_prod=helpers.get_keys()['coll_prod'],
            ner_config=ner_config
        )

        helpers.create_yaml_file(
            filename="docker-compose.yml",
            settings_list=settings_list,
            type_obj="ner"
        )

        os.chdir(cwd)
        logging.info("Successfully updated number of documents to be evaluated with Named Entity Recognition")

        return make_response(
            "OK - Successfully updated number of documents to be evaluated with Named Entity Recognition",
            201
        )
    elif not config:
        logging.info("Named Entity Recognition config does not exist")
        abort(
            404,
            "NOT FOUND - Named Entity Recognition config does not exist"
        )


def update_iteration_number():

    config = collection.find_one({})

    if config:
        ner_config = read_config()
        ner_config["iteration"] += 1

        collection.update_one(
            {},
            {
                '$set': {
                    "iteration": ner_config["iteration"]
                }
            }
        )

        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "named-entity-recognition"))

        # get settings list and create yaml file
        settings_list = docker_settings.create_docker_compose_settings(
            abs_path=os.getcwd(),
            db_ip=helpers.get_keys()['db_ip'],
            db_user=helpers.get_keys()['db_user'],
            db_pass=helpers.get_keys()['db_pass'],
            misp_ip=helpers.get_keys()['misp_ip'],
            misp_key=helpers.get_keys()['misp_key'],
            db_crawl=helpers.get_keys()['db_crawl'],
            db_prod=helpers.get_keys()['db_prod'],
            coll_crawl=helpers.get_keys()['coll_crawl'],
            coll_prod=helpers.get_keys()['coll_prod'],
            ner_config=ner_config
        )

        helpers.create_yaml_file(
            filename="docker-compose.yml",
            settings_list=settings_list,
            type_obj="ner"
        )

        os.chdir(cwd)
        logging.info("Successfully updated iteration number of Named Entity Recognition")

        return make_response(
            "OK - Successfully updated iteration number of Named Entity Recognition",
            201
        )
    elif not config:
        logging.info("Named Entity Recognition config does not exist")
        abort(
            404,
            "NOT FOUND - Named Entity Recognition config does not exist"
        )


def reset_iteration_number():

    config = collection.find_one({})

    if config:
        ner_config = read_config()
        ner_config["iteration"] = 0

        collection.update_one(
            {},
            {
                '$set': {
                    "iteration": ner_config["iteration"]
                }
            }
        )

        cwd = os.getcwd()
        os.chdir(os.path.join("..", "..", "named-entity-recognition"))

        # get settings list and create yaml file
        settings_list = docker_settings.create_docker_compose_settings(
            abs_path=os.getcwd(),
            db_ip=helpers.get_keys()['db_ip'],
            db_user=helpers.get_keys()['db_user'],
            db_pass=helpers.get_keys()['db_pass'],
            misp_ip=helpers.get_keys()['misp_ip'],
            misp_key=helpers.get_keys()['misp_key'],
            db_crawl=helpers.get_keys()['db_crawl'],
            db_prod=helpers.get_keys()['db_prod'],
            coll_crawl=helpers.get_keys()['coll_crawl'],
            coll_prod=helpers.get_keys()['coll_prod'],
            ner_config=ner_config
        )

        helpers.create_yaml_file(
            filename="docker-compose.yml",
            settings_list=settings_list,
            type_obj="ner"
        )

        os.chdir(cwd)
        logging.info("Successfully reset iteration number of Named Entity Recognition")

        return make_response(
            "OK - Successfully reset iteration number of Named Entity Recognition",
            201
        )
    elif not config:
        logging.info("Named Entity Recognition config does not exist")
        abort(
            404,
            "NOT FOUND - Named Entity Recognition config does not exist"
        )


def start():

    update_iteration_number()

    logging.info("Starting Named Entity Recognition...")
    cwd = os.getcwd()
    os.chdir(os.path.join("..", "..", "named-entity-recognition"))
    # subprocess.run(["docker-compose up"], shell=True)  # debug
    subprocess.run(["docker-compose up -d"], shell=True)
    os.chdir(cwd)
    logging.info("Successfully started Named Entity Recognition")

    return make_response(
        "Starting Named Entity Recognition",
        200
    )


def stop():

    logging.info("Stopping Named Entity Recognition...")
    cwd = os.getcwd()
    os.chdir(os.path.join("..", "..", "named-entity-recognition"))
    subprocess.run(["docker-compose down"], shell=True)
    os.chdir(cwd)
    logging.info("Successfully stopped Named Entity Recognition")

    return make_response(
        "Stopping Named Entity Recognition",
        200
    )
