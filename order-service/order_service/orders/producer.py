# import pika

# params = pika.URLParameters('amqps://xdlegebv:BsvAguzi-lauPeTP4pqU85TJqEzHXDiK@kangaroo.rmq.cloudamqp.com/xdlegebv')

# connection = pika.BlockingConnection(params)

# channel = connection.channel()

# def publish(method, body):
#     properties = pika.BasicProperties(method)
#     channel.basic_publish(exchange='', routing_key='Ecommerce-order-service', body='hello')