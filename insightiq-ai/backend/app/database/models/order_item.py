"""SQLAlchemy Model for Order Items (Line Items)."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.database.models.order import Order
    from app.database.models.product import Product


class OrderItem(Base):
    """Line-item entity representing individual products purchased within an order."""

    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_order_item_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="chk_order_item_unit_price_non_negative"),
        Index("ix_order_items_order_product", "order_id", "product_id"),
    )

    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("orders.order_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.product_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # N:1 relationship with Order
    order: Mapped[Order] = relationship("Order", back_populates="items")

    # N:1 relationship with Product
    product: Mapped[Product] = relationship("Product", back_populates="order_items")

    @property
    def total_price(self) -> Decimal:
        """Computes subtotal for this line item."""
        return self.quantity * self.unit_price

    def __repr__(self) -> str:
        return (
            f"<OrderItem(id={self.item_id}, order_id={self.order_id}, "
            f"product_id={self.product_id}, qty={self.quantity}, price={self.unit_price})>"
        )
