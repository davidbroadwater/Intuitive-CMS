from bs4 import BeautifulSoup as soup
import feedparser
import requests
from readability.readability import Document
from elasticsearch import Elasticsearch

es = Elasticsearch()

# Select feed type:

# Google News RSS Feed
#d=feedparser.parse('http://finance.yahoo.com/news/;_ylt=A0LEVj6L1vFViEcA0CsnnIlQ;_ylu=X3oDMTEyYmI0bWNyBGNvbG8DYmYxBHBvcwMxBHZ0aWQDQjA3MDBfMQRzZWMDc3I-?format=rss')
d = feedparser.parse('https://news.google.com/news?q=%22small%20businesses%22%20OR%20%22small%20business%22%20AND%20loan%20OR%20grant%20OR%20loans%20OR%20grant%20OR%20tax%20OR%20taxes&output=rss')
print d.feed.link
# Google Alert RSS Feed
# d = feedparser.parse('https://www.google.com/alerts/feeds/03803877705654670462/4544370163122525742')

# Iterate through current feed entries 
# NOTE: currently doesn't check for duplicates (i.e., may import same 
# entries as previously processed); for testing purposes only.
for entry in d.entries:
    #print entry
	# SELECT ONE (based on feed type):

	# Google News RSS Entry Link
    r = requests.get(entry.link)
    # Google Alert RSS Entry Link
    # r = requests.get(entry.links[0].href)

    # Extract article text, title, and url
    readable_article = Document(r.text).summary()
    article_html = soup(readable_article, 'lxml')
    article_text = article_html.get_text(" ").encode('utf-8')
    article_url = r.url
    article_title = Document(r.text).short_title().encode('utf-8')
    print article_title
    # Place relevant info into document for easy ES insertion.
	# NOTE: "published" field is not currently processed; date format 
	# differs between Google News and Alert feeds
    es.index(index='temp2',
                 doc_type='temp2',
                 id=1,
                 refresh=True,
                 body={
                     "text": article_text,
                     "title":article_title
                 })
    result=es.search_exists(
        index='temp2',
        doc_type='temp2',
        body={
            'query':{
                #'query_string':{
                #    'default_field':'message',
                #    'query':'small business', 'loan',' pay budget debt money save spend invest tax dollar apply application paid credit interest bank debtor repay borrow lend lender federal job'
                #},
                'bool':{
                    # 'must':[
                    #     {
                    #     'terms':{
                    #         'text':['small business','small businesses'],
                    #         'minimum_should_match': 1}
                    #     }
                    # ],
                    'should':[
                        {
                        'terms':{
                            'text':['loans','grant','grants','loan','pay','budget','debt','money', 'save','spend','invest','tax','taxes','dollar','apply','application','paid','credit','interest','bank','debtor','repay','borrow','lend','lender','federal']}
                            #'title': ['loans','grant','grants','loan','pay','budget','debt','money', 'save','spend','invest','tax','taxes','dollar','apply','application','paid','credit','interest','bank','debtor','repay','borrow','lend','lender','federal']}
                        }
                        ],
                    'minimum_should_match':1
                }
            }
        }
    )

    if result==True:
        print "MATCH!"
        doc = {"article_title": article_title,
               "article_url": article_url,
               "article_text": article_text,
               "published": entry.published}
        # Insert document into ES (change as necessary)
        es.index(index="news-test",
                  doc_type="rss",
                  body=doc)