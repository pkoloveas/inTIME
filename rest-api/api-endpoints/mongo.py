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


def generate_config():

    cwd = os.getcwd()

    os.chdir(os.path.join("..", "..", "mongo-docker"))

    # get settings list and create yaml file
    settings_list = docker_settings.create_docker_compose_settings(
        abs_path=os.getcwd(),
        db_user=helpers.get_keys()['db_user'],
        db_pass=helpers.get_keys()['db_pass'],
        mongo=True
    )

    helpers.create_yaml_file(
        filename="docker-compose.yml",
        settings_list=settings_list,
        type_obj="mongo"
    )

    os.chdir(cwd)
    logging.info("Successfully generated MongoDB config")

    return make_response(
        "CREATED - Successfully generated MongoDB config",
        201
    )


def start():

    print("Starting MongoDB...")

    cwd = os.getcwd()
    os.chdir(os.path.join("..", "..", "mongo-docker"))
    # subprocess.run(["docker-compose up"], shell=True)  # debug
    subprocess.run(["docker-compose up -d"], shell=True)
    os.chdir(cwd)
    logging.info("Successfully started MongoDB")

    return make_response(
        "Successfully started MongoDB",
        200
    )


def stop():

    print("Stopping MongoDB...")

    cwd = os.getcwd()
    os.chdir(os.path.join("..", "..", "mongo-docker"))
    subprocess.run(["docker-compose down"], shell=True)
    os.chdir(cwd)
    logging.info("Successfully stopped MongoDB")

    return make_response(
        "Successfully stopped MongoDB",
        200
    )
