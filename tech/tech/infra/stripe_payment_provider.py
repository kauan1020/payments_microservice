import stripe
from typing import Dict, Any, Optional
from tech.interfaces.payment_provider import PaymentProvider


class StripePaymentProvider(PaymentProvider):
    """
    Implementação do PaymentProvider usando a API do Stripe.

    Esta classe encapsula a comunicação com a API do Stripe para processar
    pagamentos e estornos.
    """

    def __init__(self, api_key: str):
        """
        Inicializa o provedor com a chave de API do Stripe.

        Args:
            api_key: Chave secreta da API do Stripe.
        """
        self.api_key = api_key
        stripe.api_key = api_key

    async def process_payment(self, order_id: int, amount: float, payment_method: str) -> Dict[str, Any]:
        """
        Processa um pagamento através do Stripe.

        Cria uma cobrança na API do Stripe e retorna os detalhes da transação.

        Args:
            order_id: ID do pedido associado ao pagamento.
            amount: Valor a ser cobrado (em centavos).
            payment_method: Método de pagamento a ser utilizado.

        Returns:
            Dicionário contendo detalhes da transação, incluindo transaction_id.

        Raises:
            Exception: Se houver erro no processamento do pagamento.
        """
        try:
            # Converter float para centavos (Stripe trabalha com inteiros)
            amount_cents = int(amount * 100)

            # Em um cenário real, payment_method seria um token ou ID de método de pagamento
            # Para simplificar, vamos criar um método de pagamento mockado
            payment_intent = await stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="brl",
                payment_method_types=["card"],
                metadata={"order_id": str(order_id)}
            )

            return {
                "transaction_id": payment_intent.id,
                "status": payment_intent.status,
                "amount": amount,
                "currency": "BRL"
            }

        except stripe.error.StripeError as e:
            # Captura erros específicos do Stripe
            raise Exception(f"Stripe payment processing error: {str(e)}")
        except Exception as e:
            # Captura outros erros
            raise Exception(f"Error processing payment: {str(e)}")

    async def refund_payment(self, transaction_id: str, amount: float = None) -> Dict[str, Any]:
        """
        Solicita o estorno de um pagamento através do Stripe.

        Args:
            transaction_id: ID da transação a ser estornada.
            amount: Valor a ser estornado. Se None, estorna o valor total.

        Returns:
            Dicionário contendo detalhes do estorno.

        Raises:
            Exception: Se houver erro no processamento do estorno.
        """
        try:
            refund_params = {"payment_intent": transaction_id}

            # Se amount for fornecido, converte para centavos
            if amount is not None:
                refund_params["amount"] = int(amount * 100)

            refund = await stripe.Refund.create(**refund_params)

            return {
                "refund_id": refund.id,
                "transaction_id": transaction_id,
                "status": refund.status,
                "amount": amount or (refund.amount / 100)
            }

        except stripe.error.StripeError as e:
            raise Exception(f"Stripe refund processing error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error processing refund: {str(e)}")