import pika
import json

def setup_queue(queue_names, host='localhost'):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
    channel = connection.channel()

    # This makes the queue persistent
    for queue_name in queue_names:
        channel.queue_declare(queue=queue_name, durable=True)

    return connection, channel


def publish_message(channel, queue_name, message):
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # makes the message persistent
        ))