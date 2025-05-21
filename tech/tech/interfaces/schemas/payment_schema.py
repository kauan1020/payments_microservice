from pydantic import BaseModel
from enum import Enum



class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REFUNDED = "REFUNDED"
    ERROR = "ERROR"


class PaymentCreate(BaseModel):
    """
    Schema for creating a payment.

    Attributes:
        order_id (int): The ID of the order for which payment is being created.
    """
    order_id: int



class PaymentStatusResponse(BaseModel):
    """
    Schema for representing the response of a payment status.

    Attributes:
        order_id (int): The ID of the associated order.
        status (PaymentStatusEnum): The current status of the payment.
    """
    order_id: int
    status: PaymentStatus
