"""
Representation of an article to be scraped and added to the database
"""
import datetime
import pytz

import json
from dateutil import parser


class Article:
    def __init__(self, json_rep=None, **kwargs):
        if not json_rep:
            self.db_id = -1
            self.title = kwargs.get("title", "")
            self.desc = kwargs.get("desc", "")
            self.source = kwargs.get("source", "")
            self.text = kwargs.get("text", "")
            self.cleaned_text = kwargs.get("cleaned_text", "")
            self.url = kwargs.get("url", "")
            self.img_url = kwargs.get("img_url", "")
            self.entities = kwargs.get("entities", [])
            self.category = kwargs.get("category", "")
            self.language = kwargs.get("language", "")
            self.pubDate = kwargs.get(
                "pubDate", datetime.datetime.now(datetime.timezone.utc)
            )
        else:
            self.db_id = json_rep["db_id"]
            self.title = json_rep["title"]
            self.desc = json_rep["desc"]
            self.source = json_rep["source"]
            self.text = json_rep["text"]
            self.url = json_rep["url"]
            self.img_url = json_rep["img_url"]
            self.category = json_rep["category"]
            self.cleaned_text = json_rep["cleaned_text"]
            self.pubDate = parser.parse(json_rep["pubDate"])

    def mirror_db_model(self, article_db_model):
        self.db_id = article_db_model.id
        self.title = article_db_model.title
        self.desc = article_db_model.description
        self.source = article_db_model.source
        self.text = article_db_model.content
        self.cleaned_text = article_db_model.cleaned_content
        self.img_url = article_db_model.image_url
        self.url = article_db_model.url
        self.category = article_db_model.category
        self.pubDate = article_db_model.date_created.replace(tzinfo=pytz.utc)

    def to_json(self):
        return json.dumps(
            {
                "db_id": self.db_id,
                "title": self.title,
                "desc": self.desc,
                "source": self.source,
                "text": self.text,
                "cleaned_text": self.cleaned_text,
                "url": self.url,
                "img_url": self.img_url,
                "category": self.category,
                "pubDate": str(self.pubDate),
            }
        )
    """
    def get_db_instance(self):
        return ArticleModel(
            title=self.title,
            description=self.desc,
            source=self.source,
            content=self.text,
            cleaned_content=self.cleaned_text,
            url=self.url,
            image_url=self.img_url,
            category=self.category,
            date_created=self.pubDate,
        )
    """


    def fallback_value(self, value, fallback):
        if value is None:
            return fallback
        return value
