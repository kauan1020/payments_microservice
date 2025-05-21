from abc import ABC, abstractmethod
from typing import Dict, Any


class PaymentProvider(ABC):
    """
    Interface para provedores de serviços de pagamento externos.

    Esta interface define o contrato para comunicação com gateways de pagamento
    externos como PayPal, Stripe, PagSeguro, etc., mantendo o domínio da aplicação
    independente de implementações específicas.
    """

    @abstractmethod
    async def process_payment(self, order_id: int, amount: float, payment_method: str) -> Dict[str, Any]:
        """
        Processa um pagamento através do provedor externo.

        Args:
            order_id: ID do pedido associado ao pagamento.
            amount: Valor a ser cobrado.
            payment_method: Método de pagamento a ser utilizado (cartão, boleto, etc).

        Returns:
            Dicionário contendo detalhes da transação, incluindo transaction_id.

        Raises:
            Exception: Se houver erro no processamento do pagamento.
        """
        pass

    @abstractmethod
    async def refund_payment(self, transaction_id: str, amount: float = None) -> Dict[str, Any]:
        """
        Solicita o estorno de um pagamento.

        Args:
            transaction_id: ID da transação a ser estornada.
            amount: Valor a ser estornado. Se None, estorna o valor total.

        Returns:
            Dicionário contendo detalhes do estorno.

        Raises:
            Exception: Se houver erro no processamento do estorno.
        """
        pass