import os


from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sklearn.cluster import Birch
from sklearn.decomposition import IncrementalPCA
from transformers import AutoTokenizer, AutoModel

from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

import torch
import numpy as np
import os
import sys
import glob
import requests
import json

import joblib

# add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import create_session, Article, Cluster

Base = declarative_base()




class NewsArticleClusterer:
    def __init__(self):
        self.model = SentenceTransformer('all-mpnet-base-v2')
        self.model.max_seq_length = 512

        self.session = create_session()

        
        # initialize clusters
        # get all clusters from database
        print("Initializing clusters")
        clusters = self.session.query(Cluster).all()

        self.cluster_centroids = [np.frombuffer(cluster.centroid, dtype=np.float32) for cluster in clusters]
        self.cluster_id_lookup = {i: cluster.id for i, cluster in enumerate(clusters)}
        self.session.close()


    def _embed_article(self, text):
        embedding = self.model.encode(text)
        return embedding


    def send_to_backend(self, cluster_id, articles):
        """
        Sends articles to backend
        """

        texts = " ".join([article.text[:5000] for article in articles])
        sources = "\n".join([article.url for article in articles])

        data = {
            "topicinformation": texts,
            "sources": sources,
            "password": '2f2cfe47e0ed9b85b834b9e042948833'
        }

        print(texts)
        print(sources)
        
        headers = {'Content-Type': 'application/json'}

        # send to backend
        response = requests.post("http://35.87.34.222/add", headers=headers, data=json.dumps(data))


        # set cluster to processed
        cluster = self.session.query(Cluster).get(cluster_id)
        cluster.is_processed = 1
        self.session.commit()

        
        print("sent story to backend")
        print(response)
        
        pass



    def cluster_article(self, title, text, source, url):
        # Generate embeddings for article
        embedding = self._embed_article(text)

        threshold = 0.74  # define the threshold here

        if len(self.cluster_centroids) > 0:
            similarities = cosine_similarity([embedding], self.cluster_centroids)[0]
            max_similarity_index = np.argmax(similarities)
            max_similarity = similarities[max_similarity_index]


        if len(self.cluster_centroids) > 0 and max_similarity > threshold:
            # If similarity is greater than threshold, assign to existing cluster
            cluster_id = self.cluster_id_lookup[max_similarity_index]
            cluster = self.session.query(Cluster).get(cluster_id)

            # Update centroid
            old_centroid = self.cluster_centroids[max_similarity_index]
            new_centroid = np.mean(np.array([old_centroid, embedding]), axis=0)
            
            self.cluster_centroids[max_similarity_index] = new_centroid
            cluster.centroid = new_centroid.tobytes()


            # Assigned to existing cluster, check if enough articles and bias ranking good, and send to writer
            print("found matching article")
            print("Article: ", title)
            print("\nAdding to cluster with articles:")
            for article in cluster.articles:
                print(article.title.strip())

            print("\n")

            if(len(cluster.articles) > 6):
                if not cluster.is_processed:
                    self.send_to_backend(cluster.id, cluster.articles)
        else:
            # If similarity is not greater than threshold, create a new cluster
            print("creating a new cluster\n")
            new_cluster = Cluster()
            self.session.add(new_cluster)
            self.session.commit()  # Ensure we commit so that new_cluster has an ID

            cluster_id = new_cluster.id
            new_cluster.centroid = embedding.tobytes()  # The centroid of the new cluster is the new article's embedding

            self.cluster_centroids.append(embedding)
            self.cluster_id_lookup[len(self.cluster_centroids) - 1] = cluster_id

        # Store article and its embedding in database
        article = Article(title=title, text=text, url=url, cluster_id=cluster_id, source_id=source['id'], embedding=embedding.tobytes())
        self.session.add(article)
        self.session.commit()

        return cluster_id


def cluster_process(input_queue, output_queue):
    """
    Clusters articles from the cluster queue
    """

    clusterer = NewsArticleClusterer()

    print("starting cluster process")
    for article in iter(input_queue.get, "STOP"):
        clusterer.cluster_article(article.title, article.text, article.source, article.url)