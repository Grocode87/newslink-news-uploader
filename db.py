from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, BLOB
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    name = Column(String(128))
    sitemap_url = Column(String(256))
    bias_ranking = Column(Integer)


class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True)
    articles = relationship("Article", back_populates="cluster")
    centroid = Column(BLOB)
    is_processed = Column(Integer, default=0)

class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True)
    title = Column(String(256))
    text = Column(String(10000))
    url = Column(String(256))
    cluster_id = Column(Integer, ForeignKey('clusters.id'))
    cluster = relationship("Cluster", back_populates="articles")

    source_id = Column(Integer, ForeignKey('sources.id'))
    embedding = Column(BLOB)

def create_session():
    engine = create_engine("mysql://ntadmin:AVNS_FqUsDPVpZuQc5AkkbIA@db-mysql-tor1-52068-do-user-704416-0.b.db.ondigitalocean.com:25060/neuraltimes")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    
    return Session()