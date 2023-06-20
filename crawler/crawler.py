import time
import requests
from xml.etree import ElementTree

import sys
import os
import pika

sys.path.append(os.path.abspath("../"))
from article import Article

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import create_session, Source

from message_broker import setup_queue, publish_message  # import the setup_queue function
from constants import crawler_to_scraper_queue
from article import Article

connection, channel = setup_queue([crawler_to_scraper_queue])


def crawler_process():
    """
    Crawls news website sitemaps and finds articles to pass into the scraper queue
    """

    while True:
        session = create_session()

        sources = session.query(Source).all()

        print("found ", str(len(sources)), " sources")

        for source in sources[0:]:
            try:
                print("parsing: ", source.name)
                articles = parse_sitemap(source)

                print("sucessfuly parsed sitemap: ", source.name, " with ", len(articles), " articles")
                for article in articles:
                    # send to queue
                    publish_message(channel=channel, queue_name=crawler_to_scraper_queue, message=article.to_json())

            except Exception as e:
                print("could not read sitemap: ", source.name)
                print(e)

        while True:
            pass
        # sleep for 10 minutes
        #time.sleep(10 * 60)


ns = {"news": "http://www.google.com/schemas/sitemap-news/0.9", 
      "sitemap": "http://www.sitemaps.org/schemas/sitemap/0.9", 
      "image": "http://www.google.com/schemas/sitemap-image/1.1"}


def parse_sitemap(source):
    response = requests.get(source.sitemap_url, headers={'User-Agent': 'Googlebot-News'})
    root = ElementTree.fromstring(response.content)

    articles = []
    for url in root.findall('sitemap:url', ns):
        article = Article()

        news = url.find('news:news', ns)

        if(news):
            article.url = url.find('sitemap:loc', ns).text
            article.title = news.find('news:title', ns).text
            article.pubDate = news.find('news:publication_date', ns).text

            publication = news.find('news:publication', ns)
            if(publication):
                article.language = publication.find('news:language', ns).text

            article.source = {
                "id": source.id,
                "name": source.name,
                "bias_ranking": source.bias_ranking,
            }
            
            image = url.find('image:image', ns)
            if(image):
                article.img_url = image.find('image:loc', ns).text

            if article.language and article.language == "en":
                articles.append(article)
    
    return articles


if __name__ == "__main__":
    crawler_process()