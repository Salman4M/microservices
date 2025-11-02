# import pika

# params = pika.URLParameters('amqps://xdlegebv:BsvAguzi-lauPeTP4pqU85TJqEzHXDiK@kangaroo.rmq.cloudamqp.com/xdlegebv')

# connection = pika.BlockingConnection(params)

# channel = connection.channel()

# channel.queue_declare(queue='Ecommerce-order-service')

# def callback(ch, method, properties, body):
#     pass

# channel.basic_consume(queue='Ecommerce-order-service', on_message_callback=callback)

# print('Started Consuming')

# channel.start_consuming()

# channel.close()