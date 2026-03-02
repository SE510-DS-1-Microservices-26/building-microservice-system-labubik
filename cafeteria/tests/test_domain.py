from app.core.domain import Order, OrderStatus
import pytest


def make_order():
    return Order("Sofiia", "Salad", 1, 150.50)


def test_order_created_with_created_status():
    order = make_order()
    assert order.status == OrderStatus.CREATED


def test_order_raises_if_customer_name_empty():
    with pytest.raises(ValueError, match="Customer name cannot be empty!"):
        Order(" ", "Salad", 1, 150.50)


def test_order_raises_if_quantity_not_positive():
    with pytest.raises(ValueError, match="Quantity must be positive!"):
        Order("Sofiia", "Salad", 0, 150.50)


def test_order_raises_if_price_not_positive():
    with pytest.raises(ValueError, match="Price must be positive!"):
        Order("Sofiia", "Salad", 1, 0.0)


def test_start_processing_moves_to_pending():
    order = make_order()
    order.start_processing()
    assert order.status == OrderStatus.PENDING


def test_start_processing_raises_if_not_created_status():
    order = make_order()
    order.start_processing()
    with pytest.raises(ValueError, match="Order was already processed!"): order.start_processing()


def test_confirm_moves_to_confirmed():
    order = make_order()
    order.start_processing()
    order.confirm()
    assert order.status == OrderStatus.CONFIRMED


def test_confirm_raises_if_not_pending_status():
    order = make_order()
    with pytest.raises(ValueError, match="Cannot confirm order"): order.confirm()


def test_cancel_moves_to_cancelled():
    order = make_order()
    order.cancel()
    assert order.status == OrderStatus.CANCELLED


def test_cancel_raises_if_already_cancelled():
    order = make_order()
    order.cancel()
    with pytest.raises(ValueError, match="Order was already cancelled!"): order.cancel()


def test_change_status_to_pending():
    order = make_order()
    order.change_status(OrderStatus.PENDING)
    assert order.status == OrderStatus.PENDING


def test_change_status_to_confirmed():
    order = make_order()
    order.change_status(OrderStatus.PENDING)
    order.change_status(OrderStatus.CONFIRMED)
    assert order.status == OrderStatus.CONFIRMED


def test_change_status_to_cancelled():
    order = make_order()
    order.change_status(OrderStatus.CANCELLED)
    assert order.status == OrderStatus.CANCELLED


def test_change_status_raises_if_invalid():
    order = make_order()
    with pytest.raises(ValueError, match="Cannot change status to"): order.change_status(OrderStatus.CREATED)
