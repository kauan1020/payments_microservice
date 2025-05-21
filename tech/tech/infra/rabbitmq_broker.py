import json
import pika
from typing import Callable, Dict, Any
from tech.interfaces.message_broker import MessageBroker


class RabbitMQBroker(MessageBroker):
    """
    Implementação de MessageBroker usando RabbitMQ.
    """

    def __init__(self, host: str, port: int, user: str, password: str):
        """
        Inicializa a conexão com RabbitMQ.
        """
        credentials = pika.PlainCredentials(user, password)
        self.connection_params = pika.ConnectionParameters(
            host=host,
            port=port,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        self.connection = pika.BlockingConnection(self.connection_params)
        self.channel = self.connection.channel()

    def publish(self, queue: str, message: dict) -> None:
        """
        Publica uma mensagem em uma fila RabbitMQ.
        """
        self.channel.queue_declare(queue=queue, durable=True)
        self.channel.basic_publish(
            exchange='',
            routing_key=queue,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistente
                content_type='application/json'
            )
        )

    def consume(self, queue: str, callback: Callable[[dict], None]) -> None:
        """
        Consome mensagens de uma fila RabbitMQ.
        """

        def _callback(ch, method, properties, body):
            message = json.loads(body)
            callback(message)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        self.channel.queue_declare(queue=queue, durable=True)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=queue, on_message_callback=_callback)
        self.channel.start_consuming()

    def close(self) -> None:
        """
        Fecha a conexão com RabbitMQ.
        """
        if self.connection and self.connection.is_open:
            self.connection.close()