
from nltk.corpus import wordnet as wn
from nltk.stem.porter import PorterStemmer
from sklearn.preprocessing import LabelEncoder
from nltk.corpus import stopwords
from nltk import word_tokenize
import string

from transformers import pipeline

import newspaper
import pandas as pd
import pickle
import os
import sys


# add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import create_session, Article, Cluster

class Scraper():
    def __init__(self):
        news = pd.read_csv(
            "scraper/classifier/training_dataset.csv", names=["id", "text", "category"]
        )

        # load the label encoder to decode category numbers
        self.encoder = LabelEncoder()
        self.encoder.fit_transform(news["category"])

        # load the text classifer
        self.text_clf = open("scraper/classifier/nb_classifier.pkl", "rb")
        self.text_clf = pickle.load(self.text_clf)

        self.porter = PorterStemmer()

        # load the summarization model
        self.summarizer = pipeline("summarization", model="philschmid/flan-t5-base-samsum")

        # prevents odd nltk error
        # https://stackoverflow.com/questions/27433370/what-would-cause-wordnetcorpusreader-to-have-no-attribute-lazycorpusloader
        wn.ensure_loaded()

        self.session = create_session()

    
    def scrape_article(self, article):

        # check if article already exists in db
        if self.session.query(Article).filter_by(title=article.title).first():
            return None

        try:
            user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
            config = newspaper.Config()
            config.browser_user_agent = user_agent

            newspaper_article = newspaper.Article(article.url, language="en", config=config)
            newspaper_article.download()
            newspaper_article.parse()
        except Exception as e:
            print("error parsing article")
            print(e)
            pass

        if(newspaper_article):
            article.text = str.join(" ", newspaper_article.text.splitlines())[:9999]
            article.cleaned_text = self.clean_text(article.text)
            article.category = self.categorize(article.cleaned_text)
            #article.summary = self.summarize_article(article.text)

            if(len(article.text) < 300):
                return None
            
            allowed_categories = ["U.S.", "Business", "World", "Technology", "Science"]
            if not article.category in allowed_categories:
                return None

            if not hasattr(article, 'img_url'):
                article.img_url = newspaper_article.top_image
            
            article.desc = " ".join(article.text.split()[:50]) + "..."


            return article
        else:
            return None

    def summarize_article(self, text):
        text = self.summarizer(" ".join(text.split()[:512]), min_length=150, max_length=250)
        print(text)
        return text


    def categorize(self, text):
        prediction = self.text_clf.predict([text])
        predicted_category = self.encoder.inverse_transform(prediction)

        return predicted_category[0].strip()

    def clean_text(self, text):
        """
        Remove stopwords from, tokenize, and stem the text
        """
        stop = stopwords.words("english") + list(string.punctuation)
        words = word_tokenize(text.lower())
        # words = [w for w in words if not w in stop]
        words = [self.porter.stem(w) for w in words if not w in stop]

        return " ".join(words)

        


def scraper_process(input_queue, output_queue):
    """
    Scrapes articles from the scraper queue
    Uploads articles to db
    Sends to cluster queue
    """

    scraper = Scraper()

    for article in iter(input_queue.get, "STOP"):
        article = scraper.scrape_article(article)

        if article:
            # TODO: upload article to db


            #article_num = len(os.listdir('scraper/articles'))

            # save article to csv file
            #with open("scraper/articles/" + str(article_num) + ".txt", "w") as f:
            #    f.write(article.title + "\n" + article.text)

            output_queue.put(article)
        else:
            pass