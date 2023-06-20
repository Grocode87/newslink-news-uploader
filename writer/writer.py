def writer_process(input_queue, output_queue):
    # takes in a cluster object
    # uses chatgpt to write an article based on the article in the cluster

    for cluster in iter(input_queue, "STOP"):
        
        articles = cluster.articles
        article_texts = [article.summary for article in articles]

    

