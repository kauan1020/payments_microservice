from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

class PaymentStatus(Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REFUNDED = "REFUNDED"
    ERROR = "ERROR"

@dataclass
class Payment:
    order_id: int
    amount: float
    status: PaymentStatus
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    transaction_id: Optional[str] = None
    error_message: Optional[str] = None
    payment_method: Optional[str] = None