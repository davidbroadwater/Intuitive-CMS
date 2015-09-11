from bs4 import BeautifulSoup as soup
import feedparser
import requests
from readability.readability import Document
from elasticsearch import Elasticsearch
import pickle
import time

es = Elasticsearch()


# Select feed type:

# Google News RSS Feed
# d = feedparser.parse('http://news.google.com/news?q=grants+loans+small+business&output=rss')

# Google Alert RSS Feed
# d = feedparser.parse('https://www.google.com/alerts/feeds/03803877705654670462/4544370163122525742')

# List of Small Business Feeds
sba_feeds = ["http://smallbusiness.foxbusiness.com/home/feed/rss/",
             "http://www.allbusiness.com/feed/",
             "http://feeds.feedburner.com/entrepreneur/latest",
             "http://smallbusiness.foxbusiness.com/home/feed/rss/",
             "http://www.inc.com/rss/blog/staff-blog.xml",
             "http://rss.nytimes.com/services/xml/rss/nyt/SmallBusiness.xml",
             "http://www.cnbc.com/id/44877279/device/rss/rss.html",
             "http://rss.cnn.com/rss/money_smbusiness.rss",
             "http://feeds2.feedburner.com/SmallBusinessTrends"]

# Iterate through feeds and current feed entries
# NOTE: currently doesn't check for duplicates (i.e., may import same
# entries as previously processed); for testing purposes only.

# COMMENT OUT AFTER INITIAL RUN
#last_update_time = dict()

# UNCOMMENT AFTER INITIAL RUN
last_update_time = pickle.load(open("last_update_time.txt", "rb"))

for feed in sba_feeds:

    d = feedparser.parse(feed)

    current_update_time = time.gmtime()

    # COMMENT OUT AFTER INITIAL RUN
    # last_update_time.update([(feed, 0)])

    for entry in d.entries:
        print entry.published_parsed >= last_update_time[feed]
        if entry.published_parsed >= last_update_time[feed]:

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
                        'bool':{
                            'should':[
                                {
                                'terms':{
                                    'text':['small business','small businesses','loans','grant','grants','loan','pay','budget','debt','money', 'save','spend','invest','tax','taxes','dollar','apply','application','paid','credit','interest','bank','debtor','repay','borrow','lend','lender','federal']}
                                }
                                ],
                            'minimum_should_match':2
                        }
                    }
                }
            )

            if result==True:
                print 'MATCH!'
                doc = {"doc": {"article_title": article_title,
                               "article_url": article_url,
                               "article_text": article_text,
                               "published": entry.published}}

                # Insert document into ES (change as necessary)
                es.index(index="news-test",
                         doc_type="rss",
                         body=doc)
                last_update_time.update([(feed, current_update_time)])
    print "Feed Complete!"

pickle.dump(last_update_time, open("last_update_time.txt", "wb"))
