import uuid
import asyncio
import random
from typing import Dict, Any
from tech.interfaces.payment_provider import PaymentProvider


class MockPaymentProvider(PaymentProvider):
    """
    Implementação mock do PaymentProvider para desenvolvimento e testes.

    Esta classe simula o comportamento de um gateway de pagamento real, permitindo
    testes sem depender de integrações externas.
    """

    async def process_payment(self, order_id: int, amount: float, payment_method: str) -> Dict[str, Any]:
        """
        Simula o processamento de pagamento com aprovação automática.

        Args:
            order_id: ID do pedido associado ao pagamento.
            amount: Valor a ser cobrado.
            payment_method: Método de pagamento a ser utilizado.

        Returns:
            Dicionário contendo detalhes simulados da transação.
        """
        # Simula latência de rede
        await asyncio.sleep(0.5)

        # Gera um ID de transação aleatório
        transaction_id = f"mock_{uuid.uuid4().hex[:16]}"

        # Dicionário de retorno com status APPROVED em vez de pending_confirmation
        return {
            "transaction_id": transaction_id,
            "status": "APPROVED",  # Alterado para aprovação imediata
            "amount": amount,
            "currency": "BRL",
            "order_id": order_id,
            "payment_method": payment_method
        }

    async def refund_payment(self, transaction_id: str, amount: float = None) -> Dict[str, Any]:
        """
        Simula o estorno de um pagamento.

        Args:
            transaction_id: ID da transação a ser estornada.
            amount: Valor a ser estornado. Se None, estorna o valor total.

        Returns:
            Dicionário contendo detalhes simulados do estorno.
        """
        # Simula latência de rede
        await asyncio.sleep(0.5)

        # Gera um ID de estorno aleatório
        refund_id = f"refund_{uuid.uuid4().hex[:16]}"

        # Escolhe aleatoriamente se o estorno foi bem-sucedido
        success = random.random() > 0.1  # 90% de chance de sucesso

        status = "succeeded" if success else "failed"

        return {
            "refund_id": refund_id,
            "transaction_id": transaction_id,
            "status": status,
            "amount": amount,
            "currency": "BRL"
        }