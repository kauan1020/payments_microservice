from tech.domain.entities.payments import Payment, PaymentStatus
from tech.interfaces.repositories.payment_repository import PaymentRepository
from tech.interfaces.message_broker import MessageBroker
from tech.interfaces.payment_provider import PaymentProvider
from typing import Dict, Any


class ProcessPaymentRequestUseCase:
    """
    Processa requisições de pagamento recebidas pela fila.
    """

    def __init__(
            self,
            payment_repository: PaymentRepository,
            message_broker: MessageBroker,
            payment_provider: PaymentProvider
    ):
        """
        Inicializa o caso de uso com as dependências necessárias.
        """
        self.payment_repository = payment_repository
        self.message_broker = message_broker
        self.payment_provider = payment_provider

    async def execute(self, payment_request: Dict[str, Any]) -> None:
        """
        Executa o processamento da requisição de pagamento.
        """
        import logging
        logger = logging.getLogger("payment_request_worker")

        try:
            logger.info("Iniciando execução do caso de uso")

            order_id = payment_request.get('order_id')
            amount = payment_request.get('amount')

            logger.info(f"Dados do pedido: ID={order_id}, Valor={amount}")

            # Verificar o provider
            logger.info(f"Provider: {self.payment_provider}")
            logger.info(f"Provider type: {type(self.payment_provider)}")
            logger.info(f"Has process_payment: {hasattr(self.payment_provider, 'process_payment')}")

            # Criar pagamento
            payment = Payment(
                order_id=order_id,
                amount=amount,
                status=PaymentStatus.PROCESSING
            )

            logger.info("Salvando pagamento inicial")
            saved_payment = self.payment_repository.add(payment)
            logger.info(f"Pagamento salvo com ID: {saved_payment.id}")

            try:
                logger.info("Chamando provedor de pagamento")
                # Aqui está a chamada que provavelmente está falhando
                transaction_result = await self.payment_provider.process_payment(
                    order_id=order_id,
                    amount=amount,
                    payment_method=payment_request.get('payment_method', 'credit_card')
                )
                logger.info(f"Resultado da transação: {transaction_result}")

                # Resto do código...

            except Exception as e:
                logger.error(f"Erro ao processar pagamento com o provedor: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                raise

        except Exception as e:
            logger.error(f"Erro geral no caso de uso: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise