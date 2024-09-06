import warnings
import contractions
import os
import re
import unicodedata
import logging
import pickle
import numpy as np
import xml.etree.ElementTree as ET
from gensim.models import KeyedVectors, Word2Vec
from gensim.utils import simple_preprocess
from nltk.tokenize import MWETokenizer
from nltk import sent_tokenize
from nltk.corpus import stopwords
from glob2 import glob
from collections import Counter
from pymongo import MongoClient
from bson.binary import Binary
warnings.filterwarnings(action='ignore', category=UserWarning, module='gensim')


logging.basicConfig(
    filename=os.path.join('data', 'training.log'),
    format='%(asctime)s : %(levelname)s : %(message)s',
    level=logging.INFO)


class LoadSentences(object):
    def __init__(self, filename):
        self.filename = filename

    def __iter__(self):
        for line in open(self.filename, encoding='utf-8'):
            try:
                line = line.split()
                yield(line)
            except Exception:
                pass


def update_retrain_all(tagfile, corpusfile, collection_voc, collection_topic_vec, topn, dimensions, window, min_count, workers):
    """Re-runs the entire process of extracting, preprocessing, training & add to collection"""
    xml_extraction()
    mwe = create_multiword_tags(tagfile=tagfile)
    data_process(tokenizer=mwe)
    train(corpusfile=corpusfile, dimensions=dimensions, window=window, min_count=min_count, workers=workers)
    drop_mongo_collection(collection=collection_voc)
    create_topic_dict(tagfile=tagfile, topn=topn, collection=collection_voc)
    compute_topic_vec(collection_voc=collection_voc, collection_topic_vec=collection_topic_vec)


def xml_extraction():
    """Extracts data from the Stack Exchange XML files"""
    tagFiles = glob(os.path.join('data', 'stack-exchange-xml-files', '*_Tags.xml'))
    for tagFile in tagFiles:
        extract_tags_from_xml(tagFile)

    postFiles = glob(os.path.join('data', 'stack-exchange-xml-files', '*_Posts.xml'))
    for postFile in postFiles:
        extract_posts_from_xml(postFile)

    commentFiles = glob(os.path.join('data', 'stack-exchange-xml-files', '*_Comments.xml'))
    for commentFile in commentFiles:
        extract_comments_from_xml(commentFile)

    merge_tags()


def extract_tags_from_xml(filename):
    """Exctracts Tags from XML file"""
    tree = ET.parse(filename)
    root = tree.getroot()

    path, ext = filename.split('.')
    if '/' in path:
        oldDir1, oldDir2, newFilename = path.split('/')
    else:
        oldDir1, oldDir2, newFilename = path.split('\\')
    newFile = open(os.path.join('data', 'corpus', 'tags', newFilename + '.txt'), 'w')

    count = 0
    for row in root.findall('row'):
        tag_name = row.get('TagName')
        newFile.write(tag_name + ' ')
        count += 1
    newFile.close()


def extract_posts_from_xml(filename):
    """Exctracts Posts from XML file"""
    tree = ET.parse(filename)
    root = tree.getroot()

    path, ext = filename.split('.')
    if '/' in path:
        oldDir1, oldDir2, newFilename = path.split('/')
    else:
        oldDir1, oldDir2, newFilename = path.split('\\')
    newFile = open(os.path.join('data', 'corpus', 'text', newFilename + '.txt'), 'wb')

    for row in root.findall('row'):
        post_type = row.get('PostTypeId')
        if post_type == '1':
            title = row.get('Title')
            title = remove_html_tags(title)
            title = remove_usernames(title)
            title = title.splitlines()
            title = ''.join(title)
            body = row.get('Body')
            body = remove_html_tags(body)
            body = body.splitlines()
            body = ''.join(body)
            newFile.write(title.encode('utf-8'))
            if not title.endswith('?'):
                newFile.write('. '.encode('utf-8'))
            else:
                newFile.write(' '.encode('utf-8'))
            newFile.write(body.encode('utf-8'))
            newFile.write(' '.encode('utf-8'))
        elif post_type == '2':
            body = row.get('Body')
            body = remove_html_tags(body)
            body = remove_usernames(body)
            body = body.splitlines()
            body = ''.join(body)
            newFile.write(body.encode('utf-8'))
            newFile.write(' '.encode('utf-8'))
    newFile.close()


def extract_comments_from_xml(filename):
    """Exctracts comments from XML file"""
    tree = ET.parse(filename)
    root = tree.getroot()

    path, ext = filename.split('.')
    if '/' in path:
        oldDir1, oldDir2, newFilename = path.split('/')
    else:
        oldDir1, oldDir2, newFilename = path.split('\\')
    newFile = open(os.path.join('data', 'corpus', 'text', newFilename + '.txt'), 'wb')

    for row in root.findall('row'):
        comment = row.get('Text')
        comment = remove_html_tags(comment)
        comment = remove_usernames(comment)
        comment = comment.splitlines()
        comment = ''.join(comment)
        newFile.write(comment.encode('utf-8'))
        if not comment.endswith('.'):
            newFile.write(' '.encode('utf-8'))
        else:
            newFile.write('. '.encode('utf-8'))
    newFile.close()


def remove_html_tags(text):
    """Removes HTML tags from text"""
    clean = re.compile(r'<.*?>')

    return re.sub(clean, '', text)


def remove_usernames(text):
    """Remove usernames from text"""
    clean = re.compile(r'@\w*')

    return re.sub(clean, '', text)


def data_process(tokenizer):
    """Preprocesses the training files and writes them into a corpus"""
    filenames = glob(os.path.join('data', 'corpus', 'text', '*ts.txt'))

    outfile = open(os.path.join('data', 'corpus', 'text', '__iotsec_corpus.txt'), mode='w+', encoding='utf-8')
    for filename in filenames:
        print('Processing file: ' + str(filename))
        for line in open(filename, encoding='utf-8'):
            line = sent_tokenize(replace_contractions(convert_to_ascii(line)))
            line = [tokenizer.tokenize(simple_preprocess(ln)) for ln in line]
            for sent in line:
                for s in sent:
                    outfile.write(str(s + ' '))
                outfile.write('\n')
    outfile.close()
    print('Corpus created')


def replace_contractions(text):
    """Replace common contractions (e.g. Don't -> Do not)"""
    return contractions.fix(text)


def remove_non_ascii(s):
    """Removes the non-ASCII characters from a text"""
    return ''.join(i for i in s if ord(i) < 128)


def convert_to_ascii(s):
    """Converts non-ASCII accented characters to ASCII equivalent"""
    return ''.join(
        c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn'
    )


def get_tags(tagfile):
    """Extracts the Tags from the Tagfile"""
    tag_file = open(tagfile, encoding='utf-8')
    tags = tag_file.read()
    tags = tags.split()

    return tags


def create_multiword_tags(tagfile):
    """Creates a tokenizer for Tags that are Multi-word Expressions"""
    multiword_tags = []
    tags = get_tags(tagfile=os.path.join('data', 'corpus', 'tags', tagfile))

    for t in tags:
        if '-' in t:
            terms = t.split('-')
            multiword_tags.append(tuple(terms))

    mwe = MWETokenizer(multiword_tags, separator='_')

    return mwe


def merge_tags():
    """Merges the Tags into one file"""
    filenames = glob(os.path.join('data', 'corpus', 'tags', '*Tags.txt'))
    with open(os.path.join('data', 'corpus', 'tags', '_iotsec_tags.txt'), 'w', encoding='utf-8') as file:
        for filename in filenames:
            with open(filename, 'r', encoding='utf-8') as f:
                file.write(f.read() + '\n')


def lookup_tags(tagfile, corpusfile):
    """Checks which Tags are in the corpus and the ones that are not are written in a file"""
    tags = get_tags(tagfile=os.path.join('data', 'corpus', 'tags', tagfile))

    corpus_file = open(corpusfile, encoding='utf-8')
    corpus = corpus_file.read()
    corpus = corpus.split()

    tag_sums = []
    tags_not_in_voc = []

    for t in tags:
        tsum = 0
        tdict = {'word': t, 'sum': tsum}
        if t in corpus:
            tdict['sum'] = 1
        else:
            tags_not_in_voc.append(t)
        tag_sums.append(tdict)

    with open('tags_not_in_voc.txt', 'w') as f:
        for t in tags_not_in_voc:
            f.write("%s " % t)


def train(corpusfile, dimensions, window, min_count, workers):
    """Trains the word2vec model"""
    print('Started training')
    sents = LoadSentences(os.path.join('data', 'corpus', 'text', corpusfile))
    model = Word2Vec(
        sents,
        size=dimensions,
        window=window,
        min_count=min_count,
        workers=workers,
        sg=1
    )
    model.save(os.path.join('data', 'model', 'iotsec_word2vec.model'))
    print('Finished training')


def load_model():
    """Loads the trained model"""
    return KeyedVectors.load(os.path.join('data', 'model', 'iotsec_word2vec.model'), mmap='r')


def check_vocab(tagfile, topn):
    """Checks which Tags are in the model vocabulary. The ones that are not, are written in a file."""
    count_in = 0
    count_out = 0
    terms_not_in_model = []

    tags = get_tags(tagfile=os.path.join('data', 'corpus', 'tags', tagfile))
    model = load_model()

    for t in tags:
        try:
            if model.most_similar(positive=t, topn=topn):
                count_in += 1
        except Exception:
            count_out += 1
            terms_not_in_model.append(t)
            with open('terms_not_in_w2v.txt', 'w') as f:
                for t in terms_not_in_model:
                    f.write('%s ' % t)
    print('count_in  : {0}'.format(count_in))
    print('count_out : {0}'.format(count_out))


def create_topic_dict(tagfile, topn, collection):
    """Creates the topic vocabulary and adds it to a mongoDB collection"""

    tags = get_tags(tagfile=os.path.join('data', 'corpus', 'tags', tagfile))
    model = load_model()

    print('Started adding to mongoDB collection')
    for t in tags:
        try:
            res = model.most_similar(positive=t, topn=topn)
            tmp_dict = {'word': t, 'vectors': [float(item) for item in list(model[t])]}
            add_to_mongo_collection(tmp_dict, collection)
            for i in range(len(res)):
                tmp_dict = {'word': res[i][0], 'vectors': [float(item) for item in list(model[t])]}
                add_to_mongo_collection(tmp_dict, collection)
        except Exception:
            pass
    print('Finished adding to mongoDB collection')


def connect_to_mongo_collection(db_name, collection_name, username, password, ip):
    """Connects to mongoDB collection"""
    # client = MongoClient("mongodb+srv://paris:ClassifierEvaluationProject_1@cluster0-wdtr4.mongodb.net/")
    # client = MongoClient()
    client = MongoClient(
        host=ip,
        username=username,
        password=password
    )
    db = client[db_name]
    collection = db[collection_name]

    return collection


def add_to_mongo_collection(dict, collection):
    "Adds the words of the Topic Vocabulary to mongoDB"
    collection.insert(dict, check_keys=False)


def drop_mongo_collection(collection):
    """Drops a mongo collection"""
    collection.drop()


def get_word_vec(word, model, collection_voc):
    """Gets the Vector for a specific word"""
    out_word = collection_voc.find_one({'word': word})
    out_word = out_word.get('word', '')
    out_vec = np.array(model[out_word])
    return out_vec


def compute_topic_vec(collection_voc, collection_topic_vec):
    """Computes the Vector for the Topic Vocabulary and adds it to a mongoDB collection"""
    model = load_model()
    topic_vec = np.zeros(150)

    for doc in collection_voc.find():
        w_vec = get_word_vec(str(doc.get("word", "")), model, collection_voc)
        topic_vec += w_vec

    tmp_dict = {'vectors': [float(item) for item in topic_vec]}
    print('Started adding to mongoDB collection')
    add_to_mongo_collection(tmp_dict, collection_topic_vec)
    print('Finished adding to mongoDB collection')


def get_topic_vec(collection_topic_vec):
    """Gets the Vector for the Topic Vocabulary"""

    doc = collection_topic_vec.find()
    w_vec = doc[0]['vectors']

    return np.array(w_vec)


def get_post_vec(post, topic_vec, model, collection_voc, tokenizer):
    """Computes the Vector for the Input Post"""
    post = tokenizer.tokenize(simple_preprocess(replace_contractions(post)))
    post_vec = np.zeros(150)
    words_in_topic = []
    w_vecs_in_topic = []
    word_count = 0
    words_in_topic_count = 0

    for word in post:
        word_count += 1
        # if collection_voc.find_one({'word': word}):
        if collection_voc.count_documents({'word': word}, limit=1):
            words_in_topic_count += 1
            words_in_topic.append(word)
            w_vecs_in_topic.append(get_word_vec(word, model, collection_voc))

    if word_count != 0:
        word_coverage = words_in_topic_count / word_count
    else:
        word_coverage = 0

    # print('Words in Topic Vocabulary:', ', '.join(words_in_topic))

    for w_vec in w_vecs_in_topic:
        word_topic_sim = cos_sim(w_vec, topic_vec)
        post_vec += word_topic_sim * w_vec

    return post_vec, word_coverage


def cos_sim(a, b):
    """Computes the cosine similarity of two Word Vectors"""
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    return dot_product / (norm_a * norm_b)


def post_relevance(post, topic_vec, collection_voc, topn, tokenizer):
    """Computes the Similarity Score of an input Post with the Topic Vector"""
    model = load_model()
    # print('Using Top{0} Topic Vocabulary'.format(topn))

    post_vec, word_coverage = get_post_vec(
        post=post,
        topic_vec=topic_vec,
        model=model,
        collection_voc=collection_voc,
        tokenizer=tokenizer
    )

    score = cos_sim(post_vec, topic_vec)

    # print('Similarity Score of post & topic: {0}'.format(score))
    return score, word_coverage
