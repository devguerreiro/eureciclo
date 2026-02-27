import pika
import json


class AMQPPublisher:
    def __init__(self, amqp_url: str, queue_name: str):
        # CLEAN CODE: Centralizado as configurações.
        # Se mudar o endereço do servidor, só precisa mexer aqui.
        self.amqp_url = amqp_url
        self.queue_name = queue_name

    def publish_batch(self, data_list: list):
        """Publica uma lista de mensagens de forma eficiente."""
        # CONEXÃO: Abre a conexão uma única vez para todo o lote.
        params = pika.URLParameters(self.amqp_url)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()

        # RESILIÊNCIA: durable=True garante que a fila não suma se o RabbitMQ reiniciar.
        channel.queue_declare(queue=self.queue_name, durable=True)

        for item in data_list:
            # DESIGN DECISION: Publica item por item para permitir o processamento paralelo por múltiplos workers
            # e garantir que a falha de um único XML não invalide o processamento de todo o lote,
            # seguindo as melhores práticas de sistemas fracamente acoplados.
            channel.basic_publish(
                exchange="",
                routing_key=self.queue_name,
                body=item.model_dump_json(),  # Transforma o dicionário em texto JSON
                properties=pika.BasicProperties(
                    delivery_mode=2,  # PERSISTÊNCIA: Grava a mensagem no disco do broker
                    content_type="application/json",
                ),
            )

        # PERFORMANCE: Fechar a conexão é vital para não deixar "sockets" pendentes no servidor.
        connection.close()
