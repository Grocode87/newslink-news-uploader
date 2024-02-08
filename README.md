## About

This is the backend of my News API

This program consists of multiple different microservices that each interact with a rabbitmq queue in order to crawl, scrape, and cluster news articles.

The output of this program is a database with articles and story clusters - groups of articles about the same story

## Microservices

### Crawler
Crawls a list of predefined sitemaps from a list of the top news sources around the world. It then extracts the basic content from the article using the newspaper library, and passes that content into the rabbitMQ queue

### Scraper
This service takes the articles from the crawler, and furthur processes them. It extracts the languge and content of the article, clusters them into catagories (world, us, etc) using a custom clasifier i created, extracts named entities from the article,  and then pases them back into the queue

### Clusterer
THis service takes the scraped article, and clusters it into a story cluster using a modified DBScan algorithm. Each story cluster then consists of individual articles about a specific topic
