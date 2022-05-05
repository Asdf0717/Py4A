# preliminaries
from pymongo import MongoClient
from nltk.corpus import stopwords
from string import ascii_lowercase
import pandas as pd
import gensim, os, re, pymongo, itertools, nltk, snowballstemmer

# set the location where we'll save our model
savefolder = '/data'

# grab data from database and convert to pandas dataframe
client = MongoClient()
db = client.target_database # access target database
collection = db.target_collection # access target collection within the target database
data = pd.DataFrame(list(collection.find())) # each row is one document; the raw text of the document should be in the 'text_data' column

# initialize stemmer
stemmer = snowballstemmer.EnglishStemmer()

# grab stopword list, extend it a bit, and then turn it into a set for later
stop = stopwords.words('english')
stop.extend(['may','also','zero','one','two','three','four','five','six','seven','eight','nine','ten','across','among','beside','however','yet','within']+list(ascii_lowercase))
stoplist = stemmer.stemWords(stop)
stoplist = set(stoplist)
stop = set(sorted(stop + list(stoplist))) 

# remove characters and stoplist words, then generate dictionary of unique words
data['text_data'].replace('[!"#%\'()*+,-./:;<=>?@\[\]^_`{|}~1234567890’”“′‘\\\]',' ',inplace=True,regex=True)
wordlist = filter(None, " ".join(list(set(list(itertools.chain(*data['text_data'].str.split(' ')))))).split(" "))
data['stemmed_text_data'] = [' '.join(filter(None,filter(lambda word: word not in stop, line))) for line in data['text_data'].str.lower().str.split(' ')]

# remove all words that don't occur at least 5 times and then stem the resulting docs
minimum_count = 5
str_frequencies = pd.DataFrame(list(Counter(filter(None,list(itertools.chain(*data['stemmed_text_data'].str.split(' '))))).items()),columns=['word','count'])
low_frequency_words = set(str_frequencies[str_frequencies['count'] < minimum_count]['word'])
data['stemmed_text_data'] = [' '.join(filter(None,filter(lambda word: word not in low_frequency_words, line))) for line in data['stemmed_text_data'].str.split(' ')]
data['stemmed_text_data'] = [" ".join(stemmer.stemWords(re.sub('[!"#%\'()*+,-./:;<=>?@\[\]^_`{|}~1234567890’”“′‘\\\]',' ', next_text).split(' '))) for next_text in data['stemmed_text_data']]

# run word2vec model and then save it
texts_stemmed = filter(None, [next_text.strip(' ').split(' ') for next_text in data['stemmed_text_data']])
w2vmodel_stemmed = gensim.models.Word2Vec(texts_stemmed, size=100, window=5, min_count=5, workers=4)
w2vmodel_stemmed.save(savefolder+'w2v_stemmed_model')