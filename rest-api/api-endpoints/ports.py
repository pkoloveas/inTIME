import helpers
from flask import make_response, abort
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
    collection_name='ports',
    ip=helpers.get_keys()['db_ip'],
    username=helpers.get_keys()['db_user'],
    password=helpers.get_keys()['db_pass']
)


def check_availability(available):

    ports = []

    for port in collection.find({}):
        if port['available'] is available:
            ports.append(port['port_no'])

    logging.info("Successfully retrieved ports")

    return ports


def change_port_availability(port_no):

    check_port = {'port_no': port_no}

    if collection.find_one(check_port) and port_no is not None:
        port = collection.find_one(check_port)

        if port['available'] is True:
            collection.update_one(
                check_port,
                {
                    '$set': {
                        'available': False
                    }
                }
            )

        logging.info("Port availability updated succesfully")

        return make_response("Port availability updated succesfully", 201)
    else:
        logging.info("Port with number '{port_no}' does not exist".format(port_no=port_no))
        abort("Port with number '{port_no}' does not exist".format(port_no=port_no), 404)
