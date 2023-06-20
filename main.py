import multiprocessing
import time
import signal

from crawler.crawler import crawler_process
from scraper.scraper import scraper_process
from clusterer.clusterer import cluster_process

from db import create_session

class SignalHandler:
    def __init__(self):
        self.terminate = False
        signal.signal(signal.SIGINT, self.set_terminate_flag)

    def set_terminate_flag(self, signum, frame):
        print('SIGINT received. Shutting down...')
        self.terminate = True

class WorkerPool:
    def __init__(self, worker_fn, min_workers, max_workers, input_queue, output_queue):
        self.worker_fn = worker_fn
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.input_queue = input_queue
        self.output_queue = output_queue
        self.workers = []

    def add_worker(self):
        p = multiprocessing.Process(target=self.worker_fn, args=(self.input_queue, self.output_queue))
        p.start()
        self.workers.append(p)

    def remove_worker(self):
        self.workers.pop().terminate()

    def adjust_workers(self):
        current_workers = len(self.workers)
        
        if current_workers < self.min_workers:
            for i in range(self.min_workers - current_workers):
                self.add_worker()

        if self.input_queue == None:
            return

        queue_size = self.input_queue.qsize()
        
        if queue_size < 10 and current_workers > self.min_workers:
            self.remove_worker()

        # If the queue is greater than 100, add a worker
        elif queue_size > 100 and current_workers < self.max_workers:
            self.add_worker()

    def terminate(self):
        for p in self.workers:
            p.terminate()
            p.join()


def manager():
    crawler_to_scraper_queue = multiprocessing.Queue()
    scraper_to_clusterer_queue = multiprocessing.Queue()

    queues = {"crawler_to_scraper": crawler_to_scraper_queue, 
              "scraper_to_clusterer": scraper_to_clusterer_queue}

    crawler_pool = WorkerPool(crawler_process, 1, 1, None, crawler_to_scraper_queue)
    scraper_pool = WorkerPool(scraper_process, 1, 5, crawler_to_scraper_queue, scraper_to_clusterer_queue)
    clusterer_pool = WorkerPool(cluster_process, 1, 1, scraper_to_clusterer_queue, None)

    pools = {"crawlers": crawler_pool,
             "scrapers":  scraper_pool,
             "clusterers": clusterer_pool}

    while True:
        for pool in pools:
            pools[pool].adjust_workers()
        
        print("\n\n2----")
        print('--- Queues sizes ---')
        for name, queue in queues.items():
            print(f'{name}: {queue.qsize()}')
        
        print('\n--- Pool process counts ---')
        for name, worker_pool in pools.items():
            print(f'{name}: {len(worker_pool.workers)}')
        print("------------------------")


        # Break condition - all workers have stopped and queues are empty
        if all(not pools[pool].workers for pool in pools) and all(queues[q].empty() for q in queues):
            break

        time.sleep(5)

    for pool in pools:
        pool.terminate()



if __name__ == '__main__':
    manager()