# coding: utf-8

import functions as func
import json
import click
import os
from datetime import datetime as dt


default_db_crawl = 'CrawlDB'
default_collection_crawl = 'crawl_collection'
default_db_products = 'ProductDB'
default_collection_products = 'cpe_products'
default_spacy_model = 'en_core_web_lg'
default_phrase_matcher = True
default_topn = 10
default_post_win = 0

ner_model_path = os.path.join('models', 'ner_model')


@click.group()
def main():
    pass


@main.command()
@click.option(
    '--post_window',
    type=click.INT,
    default=default_post_win
)
@click.option(
    '--topn',
    type=click.INT,
    default=default_topn
)
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
    '--db_products',
    type=click.STRING,
    default=default_db_products,
    help="The name of the Product Database"
)
@click.option(
    '--collection_products',
    type=click.STRING,
    default=default_collection_products,
    help="The name of the Product mongoDB collection"
)
@click.option(
    '--spacy_model',
    type=click.STRING,
    default=default_spacy_model,
    help="The sepected pre-trained spaCy model"
)
@click.option(
    '--phrase_matcher',
    type=click.BOOL,
    default=default_phrase_matcher,
    help="Toggle between the use of spaCy's PhraseMatcher"
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
@click.option(
    '--misp_ip',
    type=click.STRING,
    help="The IP where MISP is hosted"
)
@click.option(
    '--misp_key',
    type=click.STRING,
    help="The API key of MISP"
)
@click.option(
    '--iteration',
    type=click.INT,
    help="The iteration number of Named Entity Recognition"
)
def get_ents(post_window, topn, db_crawl, collection_crawl, db_products, collection_products, spacy_model, phrase_matcher, username, password, ip, misp_ip, misp_key, iteration):
    """Identifies the named entities of a document"""
    startTime = dt.now()

    nlp = func.init_ner(model_path=ner_model_path,
                        spacy_model_name=spacy_model,
                        matcher=phrase_matcher)

    swords = nlp.Defaults.stop_words
    score_label = "score{}".format(topn)

    coll = func.connect_to_mongo_collection(
        db_name=db_crawl,
        collection_name=collection_crawl,
        ip=ip,
        username=username,
        password=password
    )

    coll_products = func.connect_to_mongo_collection(
        db_name=db_products,
        collection_name=collection_products,
        ip=ip,
        username=username,
        password=password
    )

    misp = func.misp_init(
        misp_ip=misp_ip,
        misp_key=misp_key
    )

    docs_passed_counter = 0

    for doc in coll.find({'iteration': {'$eq': iteration}}, no_cursor_timeout=True).sort(score_label, -1).limit(post_window):

        if docs_passed_counter < post_window:  # * 0.1:

            id_query = {'_id': doc['_id']}

            if doc['ner'] is False and doc[score_label] > 0.7 and doc['word_coverage'] > 0.1:
                text = func.remove_irrelevant_entities(nlp(doc['raw_text']))

                highlights = func.get_highlights(text, swords)
                ents = func.convert_to_json(text)
                possible_cpes = func.get_possible_cpes(ents, coll_products)

                ner_flag_query = {'$set': {'ner': True}}
                coll.update_one(id_query, ner_flag_query)

                if highlights:
                    poi_query = {'$set': {'highlights': highlights}}
                    coll.update_one(id_query, poi_query)

                named_entities_query = {'$set': ents}
                coll.update_one(id_query, named_entities_query)

                if possible_cpes:
                    possible_cpes_query = {'$set': {'possible_cpes': possible_cpes}}
                    coll.update_one(id_query, possible_cpes_query)

                # print(json.dumps(func.delete_mongo_id(doc), indent=4, sort_keys=False))

                if doc['in_misp'] is False and func.check_ents_eligibility(ents) is True:
                    doc_misp = coll.find_one(id_query)

                    try:
                        func.add_to_misp(
                            misp=misp,
                            doc=doc_misp,
                            topn=topn
                        )

                        misp_flag_query = {'$set': {'in_misp': True}}
                        coll.update_one(id_query, misp_flag_query)

                        print("{} goes in MISP.".format(doc['doc_id']))

                        docs_passed_counter += 1
                    except Exception as e:
                        print(e)
                elif doc['in_misp'] is True:
                    print("{} is already in MISP.".format(doc['doc_id']))
                else:
                    print("{} doesn't go in MISP.".format(doc['doc_id']))
            elif doc['ner'] is True:
                print("{} has already passed through NER.".format(doc['doc_id']))
            else:
                print("{} doesn't qualify for NER.".format(doc['doc_id']))

    print('Runtime: ' + str(dt.now() - startTime))


if __name__ == "__main__":
    main()
