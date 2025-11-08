import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from collections import defaultdict
from .models import Order, OrderItem
from order_service.messaging import publisher

logger = logging.getLogger('order_service')


@receiver(post_save, sender=Order)
def order_post_save(sender, instance, created, **kwargs):
    """
    Send 'order.item_variation' events grouped by shop
    when a new order is created.
    """
    if not created:
        return  # Only handle new orders

    try:
        # Get all items of the order
        order_items = OrderItem.objects.filter(order=instance)

        # Group items by shop
        shop_groups = defaultdict(list)
        for item in order_items:
            shop_groups[item.shop.id].append({
                "item_id": str(item.item.id),
                "quantity": item.quantity,
                "variation_data": item.product_variation
            })

        # Publish one message per shop
        for shop_id, items in shop_groups.items():
            publisher.publish_order_items(
                order_id=str(instance.id),
                items=[
                    {
                        "shop_id": str(shop_id),
                        "item_id": item["item_id"],
                        "quantity": item["quantity"],
                        "variation_data": item["variation_data"]
                    }
                    for item in items
                ]
            )
            logger.info(f"Order event published | order={instance.id} shop={shop_id} item_count={len(items)}")

    except Exception as e:
        logger.error(f"Failed to publish order events for order={instance.id}: {e}", exc_info=True)