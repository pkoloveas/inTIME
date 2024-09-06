# coding: utf-8

from functions import Watcher
import functions as func
import click

default_db_crawl = 'CrawlDB'
default_collection_crawl = 'crawl_collection'


@click.group()
def main():
    pass


@main.command()
@click.option(
    '--db_crawl',
    type=click.STRING,
    default=default_db_crawl,
    help="The name of the Crawl Database"
)
@click.option(
    '--collection_crawl',
    type=click.STRING,
    default=default_collection_crawl,
    help="The name of the Crawl mongoDB collection"
)
@click.option(
    '--crawler_id',
    type=click.STRING,
    help="The ID of the Crawler related to this Watcher"
)
@click.option(
    '--crawler_type',
    type=click.STRING,
    help="The Type of the Crawler that is being watched"
)
@click.option(
    '--directory',
    type=click.STRING,
    help="The Directory of the Crawler to be watched"
)
@click.option(
    '--username',
    type=click.STRING,
    help="The username to connect to mongoDB"
)
@click.option(
    '--password',
    type=click.STRING,
    help="The password to connect to mongoDB"
)
@click.option(
    '--ip',
    type=click.STRING,
    help="The IP where mongoDB is hosted"
)
def start_watcher(db_crawl, collection_crawl, crawler_id, crawler_type, directory, username, password, ip):
    """Start the process of Directory Watching for a specified Crawler"""
    # startTime = dt.now()

    w = Watcher(
        # directory='../ache-crawlers/foc2/data-ache/default/data_pages'
        db_crawl=db_crawl,
        collection_crawl=collection_crawl,
        directory=directory,
        crawler_id=crawler_id,
        crawler_type=crawler_type,
        username=username,
        password=password,
        ip=ip
    )
    w.run()
    # print('Runtime: ' + str(dt.now() - startTime))


if __name__ == "__main__":
    main()
