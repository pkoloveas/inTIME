import spacy
import os
import json
from spacy.pipeline import EntityRuler
from spacy.tokens import Span
from spacy.language import Language
from spacy.matcher import PhraseMatcher
from spacy.tokenizer import Tokenizer
from pymongo import MongoClient
from xml.etree import ElementTree as ET
from pymisp import ExpandedPyMISP
from pymisp import PyMISP
from pymisp import MISPObject
from pymisp import MISPEvent
from pymisp import MISPObjectAttribute
from pymisp import MISPAttribute
from pymisp.tools import GenericObjectGenerator


class EntityMatcher(object):
    name = 'entity_matcher'

    def __init__(self, nlp, term_list, labels):
        for terms, label in zip(term_list, labels):
            patterns = [nlp.make_doc(text) for text in terms]
            self.matcher = PhraseMatcher(nlp.vocab)
            self.matcher.add(label, patterns)

    def __call__(self, doc):
        matches = self.matcher(doc)
        spans = []
        try:
            for label, start, end in matches:
                entity = Span(doc, start, end, label=label)
                spans.append(entity)

                doc.ents = list(doc.ents) + [entity]
        except Exception:
            pass
        return doc


def connect_to_mongo_collection(db_name, collection_name, ip, username, password):
    """Connects to mongoDB collection"""

    client = MongoClient(
        host=ip,
        username=username,
        password=password
    )
    db = client[db_name]
    collection = db[collection_name]

    return collection


def get_list_from_file(filename):
    with open(os.path.join('data', 'phrase_matcher', filename + '.txt'), mode='r', encoding='utf-8') as f:
        data = f.readlines()
        data = [d.replace('\n', '') for d in data]
        data = [d for d in data if len(d) > 1]

        return list(set(data))


def show_entities(doc):

    if doc.ents:
        for ent in doc.ents:
            print('{} - {} - [{},{}]'.format(ent.text, ent.label_, str(ent.start), str(ent.end)))
    else:
        print('No entities found')
    print()


def remove_irrelevant_entities(doc):

    #   !!! PERSON !!!                 | People, including fictional.
    #   !!! NORP !!!                   | Nationalities or religious or political groups.
    #   !!! FAC !!!                    | Buildings, airports, highways, bridges, etc.
    #   ORG                            | Copanies, agencies, institutions, etc.
    #   !!! GPE !!!                    | Countries, cities, states.
    #   !!! LOC !!!                    | Non-GPE locations, mountain ranges, bodies of water.
    #   PRODUCT                        | Objects, vehicles, foods, etc.
    #   !!! EVENT !!!                  | Named hurricanes, battles, wars, sports events, etc.
    #   !!! WORK_OF_ART !!!            | Titles of books, songs, etc.
    #   !!! LAW !!!                    | Named documents made into laws.
    #   !!! LANGUAGE !!!               | Any named language.
    #   DATE                           | Absolute or relative dates or periods.
    #   TIME                           | Times smaller than a day.
    #   !!! PERCENT !!!                | Percentage, including "%".
    #   MONEY                          | Monetary values, including unit.
    #   !!! QUANTITY !!!               | Measurements, as of weight or distance.
    #   !!! ORDINAL !!!                | "first", "second", etc.
    #   !!! CARDINAL !!!               | Numerals that do not fall under another type.
    #   CVE                            | Common Vulnerabilities and Exposures (CVE) identifier.
    #   CPE                            | Common Platform Enumeration (CPE) identifier.
    #   CWE                            | Common Weakness Enumeration (CWE) identifier.
    #   IP                             | IP address.
    #   VERSION                        | Software version.
    #   FILE                           | Filename or file extension.
    #   COMMAND/FUNCTION/CONFIG        | Shell command/code function/configuration setting.
    #   CVSS2_VECTOR                   | Common Vulnerability Scoring System (CVSS) v2.
    #   CVSS3_VECTOR                   | Common Vulnerability Scoring System (CVSS) v3.0-v3.1.

    unwanted_ents = [
        "PERSON",
        "NORP",
        "FAC",
        "GPE",
        "LOC",
        "EVENT",
        "WORK_OF_ART",
        "LAW",
        "LANGUAGE",
        "PERCENT",
        "QUANTITY",
        "ORDINAL",
        "CARDINAL"
    ]

    doc.ents = [ent for ent in list(doc.ents) if ent.label_ not in unwanted_ents]

    return doc


def convert_to_json(doc):
    matches = []

    if doc.ents:
        for ent in doc.ents:
            tmp_ent = dict([('text', ent.text), ('entity', ent.label_), ('start', ent.start), ('end', ent.end)])
            matches.append(tmp_ent)
    return dict([('ner_entities', matches)])


def custom_tokenizer(nlp):
    cve = r'(cve|CVE)-\d{4}-\d+'
    cpe = r'(cpe|CPE):/[ahoAHO]:\w+:[\.\w]+'
    cwe = r'(cwe|CWE)-\d+'
    ver = r'\b((v|ver)?\d+\.(\d+|x)(\.\d+\.x|\.\d+\.\d+(\-\d+)?|\.\d+\.\d+\-\d+(\-\d+)?|\.x|\.\d+(\-\d+)?|(\-\d+)?)\+?)|(Android\-(\d\d?\.\d\.\d|\d\d?\.\d))\b'
    file = r'([\w\/\-])+\.\w+'
    ip = r'\b(?:(?:\d){1,3}\.){3}(?:\d){1,3}\b'
    product_with_number = r'((?:[a-zA-Z_]+[0-9]|[0-9]+[a-zA-Z])[a-zA-Z0-9_]*)'
    cvss = r'(AV:(\w)/AC:(\w)/Au:(\w)/C:(\w)/I:(\w)/A:(\w))|(CVSS:3\.(\d)/AV:(\w)/AC:(\w)/PR:(\w)/UI:(\w)/S:(\w)/C:(\w)/I:(\w)/A:(\w))'
    command = r'(\w+\(\))|(\w+\_\w+)|((?<=\s)(\w+(\_|::|#))+\w+)'
    currency = r'\b(\d+(\.\d+)?)\s(BTC|ETH|ETC|XRP|BCH|GRC|LTC|XBT|DASH|DOGE|XDG|EOS|ZEC|XVG|XPM|XMR|XLM|XEM|VTC|USDT|USDC|TIT|PPC|POT|NXT|NMC|NEO|Nano|MZC|USD|EUR|GBP|JPY|AUD|QAR|SAR|RUB)\b'

    # prefixes_re = spacy.util.compile_prefix_regex(tuple(list(nlp.Defaults.prefixes) + [cve] + [cpe] + [cwe] + [currency] + [ver] + [file] + [ip] + [product_with_number] + [cvss] + [command]))
    # infix_re = spacy.util.compile_infix_regex(nlp.Defaults.infixes)

    prefixes_re = spacy.util.compile_prefix_regex(nlp.Defaults.prefixes)
    infix_re = spacy.util.compile_infix_regex(tuple(list(nlp.Defaults.prefixes) + [cve] + [cpe] + [cwe] + [currency] + [ver] + [file] + [ip] + [product_with_number] + [cvss] + [command]))
    suffix_re = spacy.util.compile_suffix_regex(nlp.Defaults.suffixes)

    return Tokenizer(nlp.vocab,
                     rules=nlp.Defaults.tokenizer_exceptions,
                     prefix_search=prefixes_re.search,
                     infix_finditer=infix_re.finditer,
                     suffix_search=suffix_re.search,
                     token_match=None)


def get_matcher_lists():

    matcher_list = []
    label_list = ['ORG', 'PRODUCT']

    matcher_list.append(get_list_from_file('vendors'))
    matcher_list.append(get_list_from_file('products'))

    return matcher_list, label_list


def get_highlights(doc, stopwords):

    highlights = []

    for noun_chunk in doc.noun_chunks:
        chunk_tok = [word for word in noun_chunk.text.split(' ') if word not in stopwords]
        chunk_str = ' '.join(chunk_tok)
        if len(chunk_tok) >= 4:
            highlights.append(chunk_str)

    return highlights


def init_ner(model_path, spacy_model_name, matcher=True):

    nlp = spacy.load(spacy_model_name)
    nlp.tokenizer = custom_tokenizer(nlp)

    ruler = EntityRuler(nlp).from_disk(os.path.join("data", "patterns.jsonl"))
    nlp.add_pipe(ruler, before='ner')

    if matcher is True:
        matcher_list, label_list = get_matcher_lists()

        entity_matcher = EntityMatcher(nlp, term_list=matcher_list, labels=label_list)
        nlp.add_pipe(entity_matcher, after='entity_ruler')

    merge_ents = nlp.create_pipe("merge_entities")
    nlp.add_pipe(merge_ents)

    if not os.path.isdir(model_path):
        nlp.to_disk(model_path)

    return nlp


def extract_from_rdf(filename, collection):

    tree = ET.parse(filename)
    root = tree.getroot()
    children = root.getchildren()

    vendors = children[0]

    for vendor in vendors:
        for product in vendor:
            prod_name = product.get('pname')
            cpe = product.get('cpe')

            dict_entry = {
                "cpe": cpe,
                "product_name": prod_name,
                "product_ngrams": ' '.join(make_ngrams(prod_name))
            }

            collection.insert_one(dict_entry)


def make_ngrams(word, min_size=5):

    length = len(word)
    size_range = range(min_size, max(length, min_size) + 1)
    return list(set(
        word[i:i + size]
        for size in size_range
        for i in range(0, max(0, length - size) + 1)
    ))


def add_index(collection):

    collection.create_index(
        [(
            "product_ngrams", "text"
        )],
        name="search_product_ngrams",
        weights={
            "product_ngrams": 100
        }
    )


def add_cpe_products(filename, collection):

    extract_from_rdf(filename=filename, collection=collection)
    add_index(collection)


def read_products(ents):

    results = []

    for ent in ents['ner_entities']:
        if ent['entity'] == "PRODUCT":
            results.append(ent['text'])

    return results


def lookup_cpes(query, collection):

    result = collection.find(
        {
            "$text": {
                "$search": ' '.join(make_ngrams(query))
            }
        },
        {
            "product_name": True,
            "cpe": True,
            "score": {
                "$meta": "textScore"
            }
        }
    ).sort([("score", {"$meta": "textScore"})])

    cpes = []
    for res in result.limit(10):
        cpes.append({
            'cpe': res['cpe'],
            'score': res['score']
        })

    if not cpes:
        return None
    else:
        cpe_object = {
            'name': query,
            'CPEs': cpes
        }
        # print(json.dumps(cpe_object, indent=4, sort_keys=False))

        return cpe_object


def get_possible_cpes(entities, collection):

    products = []
    possible_cpes = []

    for ent in entities['ner_entities']:
        if ent['entity'] == "PRODUCT":
            products.append(ent['text'])

    for ent in products:
        possible_cpe = lookup_cpes(ent, collection)
        if possible_cpe:
            possible_cpes.append(possible_cpe)

    return possible_cpes


def delete_mongo_id(item):

    del item['_id']
    return item


def check_ents_eligibility(entities):

    eligible_entities = [
        "ORG",
        "PRODUCT",
        "CVE",
        "CPE",
        "CWE",
        "CVSS2_VECTOR",
        "CVSS3_VECTOR"
    ]

    entity_types = [ent["entity"] for ent in entities["ner_entities"]]

    if len(list(set(entity_types) & set(eligible_entities))) != 0 and len(entity_types) > 3:
        return True


def misp_init(misp_ip, misp_key):

    misp = ExpandedPyMISP(misp_ip, misp_key, False, debug=False)

    return misp


def add_to_misp(doc, topn, misp):

    # misp = misp_init(misp_ip, misp_key)  # ExpandedPyMISP(misp_ip, misp_key, False, debug=False)

    # doc = read_json(filename='doc.json')
    rs_label = "score" + str(topn)

    doc_misp = process_doc_for_misp(doc, rs_label)

    try:
        event = MISPEvent()
        event.info = doc['doc_id']
        event.distribution = 0
        event.threat_level_id = 4
        event.analysis = 2
        event = misp.add_event(event)
        event_id = event["Event"]["id"]

        misp_object = GenericObjectGenerator("crawled_obj")
        misp_object.generate_attributes(json.loads(doc_misp))
        misp.add_object(event_id, misp_object)
    except Exception as e:
        print(e)


def process_doc_for_misp(doc, rs_label):

    doc_misp = [
        {"id": {"value": doc['doc_id']}},
        {"title": {"value": doc['title']}},
        {"hashed_title": {"value": doc['hashed_title']}},
        {"raw_text": {"value": doc['raw_text']}},
        {"hashed_text": {"value": doc['hashed_text']}},
        {"source_url": {"value": doc['source_url']}},
        {"hashed_url": {"value": doc['hashed_url']}},
        {"discovered_by": {"value": doc['discovered_by']}},
        {"discovery_timestamp": {"value": doc['discovery_timestamp']}},
        {"crawler_type": {"value": doc['crawler_type']}},
        {"relevance_score": {"value": doc[rs_label]}},
    ]

    if 'highlights' in doc:
        for highlight in doc['highlights']:
            doc_misp.append({
                "highlight": {
                    "value": highlight
                }
            })

    if 'ner_entities' in doc:
        for ent in doc['ner_entities']:
            if ent['entity'] == "CPE":
                ent['entity'] = "vulnerable_configuration"
            else:
                ent['entity'] = "{}_entity".format(ent['entity'].lower().replace('/', '_'))
            doc_misp.append({
                ent['entity']: {
                    "value": ent['text'],
                    "comment": "Position: [{}-{}]".format(ent['start'], ent['end'])
                }
            })

    if 'possible_cpes' in doc:
        for prod in doc['possible_cpes']:
            for cpe in prod['CPEs']:
                doc_misp.append({
                    "possible_cpe": {
                        "value": cpe['cpe'],
                        "comment": "{} [{}]".format(prod['name'], cpe['score'])
                    }
                })

    doc_misp.append({"credit": {"value": "crawler"}})

    # print(json.dumps(doc_misp, indent=4, sort_keys=False))

    doc_misp = str(doc_misp)

    doc_misp = doc_misp.replace("\"", "\\\"")
    doc_misp = doc_misp.replace("{'", "{\"")
    doc_misp = doc_misp.replace("'}", "\"}")
    doc_misp = doc_misp.replace("': '", "\": \"")
    doc_misp = doc_misp.replace("':", "\":")
    doc_misp = doc_misp.replace("', '", "\", \"")
    doc_misp = doc_misp.replace("\", '", "\", \"")
    doc_misp = doc_misp.replace("\\\", \"", "\", \"")
    doc_misp = doc_misp.replace("\\\", \\\"", "\", \"")
    doc_misp = doc_misp.replace("\", \\\"", "\", \"")
    doc_misp = doc_misp.replace("', \"", "\", \"")
    doc_misp = doc_misp.replace("\\'", "'")
    doc_misp = doc_misp.replace(": \\\"", ": \"")
    doc_misp = doc_misp.replace("\\\"}", "\"}")

    # print()
    # print(doc_misp)

    return doc_misp
