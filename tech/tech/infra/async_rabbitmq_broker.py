import json
import asyncio
from typing import Dict, Any, Callable, Optional
from tech.interfaces.message_broker import MessageBroker
from tech.infra.rabbitmq_broker import RabbitMQBroker


class AsyncRabbitMQBroker(MessageBroker):
    """
    Implementação assíncrona de MessageBroker usando RabbitMQ.

    Esta classe adapta os métodos síncronos do RabbitMQBroker para serem
    usados em contextos assíncronos.
    """

    def __init__(self, host: str, port: int, user: str, password: str):
        """
        Inicializa o adaptador assíncrono para RabbitMQBroker.

        Args:
            host: Endereço do host RabbitMQ
            port: Porta do serviço RabbitMQ
            user: Nome de usuário para autenticação
            password: Senha para autenticação
        """
        self.sync_broker = RabbitMQBroker(
            host=host,
            port=port,
            user=user,
            password=password
        )

    def publish(self, queue: str, message: Dict[str, Any]) -> None:
        """
        Método síncrono de publicação para compatibilidade com a interface.
        Redireciona para o broker síncrono.

        Args:
            queue: Nome da fila para publicar a mensagem
            message: Mensagem a ser publicada
        """
        self.sync_broker.publish(queue, message)

    async def publish_async(self, queue: str, message: Dict[str, Any]) -> None:
        """
        Publica uma mensagem de forma assíncrona.

        Usa um executor para não bloquear o loop de eventos durante a
        operação de publicação.

        Args:
            queue: Nome da fila para publicar a mensagem
            message: Mensagem a ser publicada
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.sync_broker.publish(queue, message)
        )

    def consume(self, queue: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Método síncrono de consumo para compatibilidade com a interface.
        Redireciona para o broker síncrono.

        Args:
            queue: Nome da fila para consumir
            callback: Função a ser chamada quando uma mensagem for recebida
        """
        self.sync_broker.consume(queue, callback)

    def close(self) -> None:
        """
        Fecha a conexão com o RabbitMQ.

        Redireciona para o método de fechamento do broker síncrono.
        """
        self.sync_broker.close()

    async def close_async(self) -> None:
        """
        Fecha a conexão com o RabbitMQ de forma assíncrona.

        Usa um executor para não bloquear o loop de eventos durante a
        operação de fechamento.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.sync_broker.close()
        )


# Função auxiliar para criar uma instância do adaptador assíncrono
def create_async_rabbitmq_broker(
        host: str,
        port: int,
        user: str,
        password: str
) -> AsyncRabbitMQBroker:
    """
    Cria e retorna uma instância configurada do adaptador assíncrono.

    Args:
        host: Endereço do host RabbitMQ
        port: Porta do serviço RabbitMQ
        user: Nome de usuário para autenticação
        password: Senha para autenticação

    Returns:
        Uma instância configurada de AsyncRabbitMQBroker
    """
    return AsyncRabbitMQBroker(
        host=host,
        port=port,
        user=user,
        password=password
    )