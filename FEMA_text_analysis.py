__author__ = 'elisabethpaulson'

import json
import pandas as pd
from nltk.corpus import stopwords
import re
from collections import defaultdict
from gensim import corpora, models, similarities
from pprint import pprint

# MUST RUN SCRAPY SPIDER FIRST TO GENERATE JSON FILE
file="FEMA-web-content.json"
myfile=open(file,'r').read()
#print(myfile)
results=json.loads(myfile)
data=pd.DataFrame.from_dict(results,orient='columns')

descriptions=data.description
descriptions=map(str,descriptions)
links=data.link
links=map(str,links)

standard_descriptions=[]
standard_links=[]

# STANDARDIZE LINKS AND DESCRIPTIONS
m=0
for x in descriptions:
    y = x.replace('/',' ').replace('-',' ').replace('&','').replace('.\'',' ').replace(',','').replace('\[0-9]','').replace('.',' ').upper()  #split / and - into separated words
    y=''.join([i for i in y if not i.isdigit()])
    y=y.replace('[','').replace(']','').replace('U\'','').replace('\'',' ')
    y=re.sub(r'[\w]*[\\\.\-\&\/\(\)\"\:]+[\w]*', r'', y)
    if y!='':
        standard_descriptions.append(y)
        standard_links.append(links[m])
    m=m+1

# DELETE STOPWORDS
texts=[[word for word in sentences.lower().split() if word not in stopwords.words("english")] for sentences in standard_descriptions]


# ONLY KEEP WORKS THAT APPEAR MORE THAN ONCE
frequency=defaultdict(int)
for text in texts:
    for token in text:
        frequency[token]+=1
#sorted=sorted(frequency.items(),key=operator.itemgetter(1),reverse=True)

texts=[[token for token in text if frequency[token]>1] for text in texts]

# SAVE DICTIONARY
dictionary=corpora.Dictionary(texts)
dictionary.save("FEMA.dict")
#print(dictionary)
#print(dictionary.token2id)

# SAVE CORPUS OF DESCRIPTIONS
corpus=[dictionary.doc2bow(text) for text in texts]
corpora.MmCorpus.serialize('FEMA.mm',corpus)
corpus=corpora.MmCorpus("FEMA.mm")

# TF-IDF
tfidf=models.TfidfModel(corpus)
corpus_tfidf=tfidf[corpus]

# LSI Model
lsi=models.LsiModel(corpus_tfidf,id2word=dictionary,num_topics=100)
corpus_lsi=lsi[corpus_tfidf]
pprint(lsi.print_topics(5))

# LDA Model
lda=models.LdaModel(corpus,id2word=dictionary,num_topics=100)
corpus_lda=lda[corpus]
#pprint(lda.print_topics(50))

#for doc in corpus_lsi:
#    doc=sorted(doc,key=lambda  item: -item[1])
#    print(doc)

# FIND WHAT TOPIC BEST MATCHES TERM
doc="flood prevention" #Make up query term
vec_bow=dictionary.doc2bow(doc.lower().split())
vec_lsi=lsi[vec_bow]
print(vec_lsi) # print vector that scores each document according to how well it matches query

# WHICH WHICH DOCUMENT BEST MATCHES TERM
index=similarities.MatrixSimilarity(lsi[corpus])
index.save('FEMA.index')
index=similarities.MatrixSimilarity.load('FEMA.index')

# PRINT TOP 5 FEMA DOCUMENTS THAT BEST MATCH QUERY TERM
sims=index[vec_lsi]
sims=sorted(enumerate(sims),key=lambda  item: -item[1])
#pprint(sims[:5])
for i in sims[:5]:
    print(standard_descriptions[i[0]])
    print(standard_links[i[0]])




#print(data.description)