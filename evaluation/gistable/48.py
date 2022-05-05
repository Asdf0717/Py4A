import os
import math
import re
import pandas as pd
from collections import Counter
from sklearn.datasets import fetch_20newsgroups

#get a subset of the dataset

categories = [
        'alt.atheism',
        'talk.religion.misc',
        'comp.graphics',
        'sci.space',
    ]
docs_data = fetch_20newsgroups(subset='train', categories=categories,
                                shuffle=True, random_state=42,
                                remove=('headers', 'footers', 'quotes'))
                                
#build a pandas dataframe using the filename and data of each post
docs =  pd.DataFrame({
            'filename' : docs_data.filenames, 
            'data': docs_data.data
})
#grab the corpus size(we'll use this later for IDF)
corpus_size = len(docs)

#no let's do some basic cleaning up of the text, make everything lower case and strip out all non-letters
docs['words'] = docs.data.apply(lambda doc: re.sub("[\W\d]", " ", doc.lower().strip()).split())

#let's calculate the word frequencies for each document (Bag of words)
docs['frequencies'] = docs.words.apply(lambda words: Counter(words))

#cool, now we can calculate TF, the log+1 of the frequency of each word
docs['log_frequencies'] = docs.frequencies.apply(lambda d: dict([(k,math.log(v) + 1) for k, v in d.iteritems()]))

#now let's build up a lookup list of document frequencies
#first we build a vocabulary for our corpus(set of unique words)
corpus_vocab = set([word for words in docs.words for word in words])

#now use the vocabulary to find the document frequency for each word
df = lambda word: len(docs[docs.words.apply(lambda w: word in w)])
corpus_vocab_dfs = dict([(word,math.log(corpus_size / df(word))) for word in corpus_vocab])

#phew! no let's put it all together. let's calculate tf*idf for each term
tfidf = lambda tfs: dict([(k,v * corpus_vocab_dfs[k]) for k, v  in tfs.iteritems()])
docs['tfidf'] = docs.log_frequencies.apply(tfidf)

#finally we can grab the top 5 weighted terms to get keywords for each document
sorted(docs.tfidf[0], key=docs.tfidf[0].get, reverse=True)[0:5]
docs['keywords'] = docs.tfidf.apply(lambda t: sorted(t, key=t.get, reverse=True)[0:5])