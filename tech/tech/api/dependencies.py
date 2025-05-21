from tech.interfaces.payment_provider import PaymentProvider
from tech.infra.mock_payment_provider import MockPaymentProvider
from tech.infra.stripe_payment_provider import StripePaymentProvider
import os


def get_payment_provider() -> PaymentProvider:
    """
    Fornece uma instância do provedor de pagamento.

    Em desenvolvimento, usa o provedor mock.
    Em produção, usa o Stripe com a chave de API do ambiente.
    """
    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        api_key = os.getenv("STRIPE_API_KEY")
        if not api_key:
            raise ValueError("STRIPE_API_KEY environment variable is required in production")
        return StripePaymentProvider(api_key)
    else:
        return MockPaymentProvider()