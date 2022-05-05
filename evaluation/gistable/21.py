import operator
from haystack.query import SearchQuerySet, SQ

query = 'lil way'
sqs = SearchQuerySet().filter(reduce(operator.__and__, [SQ(name=word.strip()) for word in query.split(' ')]))