"""SQLAlchemy Model for Orders."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.customer import Customer
    from app.database.models.order_item import OrderItem


class Order(Base):
    """Transactional order entity."""

    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_order_date_status", "order_date", "status"),
    )

    order_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("customers.customer_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    order_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="completed",
        index=True,
    )

    # N:1 relationship with Customer
    customer: Mapped[Customer] = relationship("Customer", back_populates="orders")

    # 1:N relationship with OrderItems
    items: Mapped[List[OrderItem]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Order(id={self.order_id}, customer_id={self.customer_id}, date='{self.order_date}', status='{self.status}')>"
