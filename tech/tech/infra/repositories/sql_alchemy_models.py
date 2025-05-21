from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, create_engine
from sqlalchemy.orm import registry
from datetime import datetime
import enum

table_registry = registry()

class PaymentStatus(enum.Enum):
    """
    Enum representing the status of a payment.
    """
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REFUNDED = "REFUNDED"
    ERROR = "ERROR"


@table_registry.mapped
class SQLAlchemyPayment(object):
    """
    SQLAlchemy mapping for the Payment entity.

    Attributes:
        order_id (int): The unique identifier of the associated order.
        amount (float): The total amount for the payment.
        status (PaymentStatus): The current status of the payment.
        created_at (datetime): The timestamp when the payment was created.
        updated_at (datetime): The timestamp when the payment was last updated.
    """
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(Enum(PaymentStatus), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)