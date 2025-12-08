import uuid
import logging
from datetime import datetime
from decimal import Decimal
from ..product_client import product_client
from ..models import Order, OrderItem

logger = logging.getLogger('analitic.services.analitic_service')


class AnaliticService:

    def process_order_completed(self, data):
        """
        Create analytics record when order is completed
        """
        try:
            print(f"[DEBUG] process_order_completed called with order_id={data.get('id')}, items_count={len(data.get('items', []))}")
            logger.info(f"process_order_completed called with order_id={data.get('id')}, items_count={len(data.get('items', []))}")

            created_at = data["created_at"]
            if isinstance(created_at, str):
                if created_at.endswith('Z'):
                    created_at = created_at.replace('Z', '+00:00')
                created_at = datetime.fromisoformat(created_at)

            # Convert order_id to integer (Order.order_id is BigIntegerField, not UUID)
            order_id = data["id"]
            if not isinstance(order_id, int):
                # If it's a string, try to convert to int
                try:
                    order_id = int(order_id)
                except (ValueError, TypeError):
                    logger.error(f"Invalid order_id format, must be integer. Got: {type(order_id)} - {order_id}")
                    raise ValueError(f"Invalid order_id format: {order_id}")
            
            user_id = data["user_id"]
            if not isinstance(user_id, uuid.UUID):
                user_id = uuid.UUID(str(user_id))

            # Create or update Order
            logger.info(f"Creating/updating Order with order_id={order_id}, user_id={user_id}")
            order, _ = Order.objects.update_or_create(
                order_id=order_id,
                defaults={
                    "user_id": user_id,
                    "created_at": created_at
                }
            )
            logger.info(f"Order created/updated: id={order.id}, order_id={order.order_id}")

            # Process each order item: fetch data from product service and save to DB
            print(f"[DEBUG] Processing {len(data['items'])} order items")
            logger.info(f"Processing {len(data['items'])} order items")
            for item in data["items"]:
                try:
                    variation_id = item["product_variation"]
                    if not isinstance(variation_id, uuid.UUID):
                        variation_id = uuid.UUID(str(variation_id))

                    # Convert item id to integer (OrderItem.id is BigAutoField, not UUID)
                    item_id = item["id"]
                    if not isinstance(item_id, int):
                        # If it's a string, try to convert to int
                        try:
                            item_id = int(item_id)
                        except (ValueError, TypeError):
                            logger.error(f"Order item {item.get('id')}: Invalid item_id format, must be integer. Got: {type(item_id)} - {item_id}")
                            continue

                    # Convert price to Decimal
                    price = item["price"]
                    if not isinstance(price, Decimal):
                        price = Decimal(str(price))

                    # Always fetch shop_id and product_id from product service, not from order
                    shop_id = None
                    product_id = None
                    logger.info(f"Processing order item {item_id}: Fetching data from product service for variation_id={variation_id}")
                    
                    # Fetch variation data from product service
                    logger.info(f"Order item {item_id}: Fetching product variation data for {variation_id}")
                    variation = product_client.get_product_variation_data(variation_id)

                    if not variation:
                        logger.error(f"Order item {item_id}: Failed to get product variation data from product service. Cannot save without shop_id and product_id.")
                        # Skip item if we can't get data from product service
                        continue  

                    # Convert base_price and original_price to Decimal
                    base_price = variation.get("base_price")
                    if base_price is not None and not isinstance(base_price, Decimal):
                        base_price = Decimal(str(base_price))
                    elif base_price is None:
                        base_price = Decimal('1.00')  # Default value
                    
                    original_price = variation.get("original_price")
                    if original_price is not None and not isinstance(original_price, Decimal):
                        original_price = Decimal(str(original_price))

                    # Always get shop_id and product_id from product service (not from order)
                    shop_id = variation.get("shop_id")
                    if shop_id is not None and not isinstance(shop_id, uuid.UUID):
                        shop_id = uuid.UUID(str(shop_id))
                    if shop_id:
                        logger.info(f"Order item {item_id}: Got shop_id from product service: {shop_id}")
                    else:
                        logger.warning(f"Order item {item_id}: shop_id not found in product service response")
                    
                    product_id = variation.get("product_id")
                    if product_id is not None and not isinstance(product_id, uuid.UUID):
                        product_id = uuid.UUID(str(product_id))
                    if product_id:
                        logger.info(f"Order item {item_id}: Got product_id from product service: {product_id}")
                    else:
                        logger.warning(f"Order item {item_id}: product_id not found in product service response")

                    # Save OrderItem to DB
                    order_item_data = {
                        "order": order,
                        "product_variation_id": variation_id,
                        "quantity": item["quantity"],
                        "price": price,
                        # Data fetched from Product API
                        "base_price": base_price,
                        "original_price": original_price,
                        "size": variation.get("size"),
                        "color": variation.get("color"),
                        "product_title": variation.get("product_title"),
                        "product_sku": variation.get("product_sku"),
                        "shop_id": shop_id,
                        "product_id": product_id,
                    }
                    logger.info(f"Order item {item_id}: Saving to DB with shop_id={shop_id}, product_id={product_id}")
                    logger.info(f"Order item {item_id}: Full data keys: {list(order_item_data.keys())}")
                    
                    OrderItem.objects.update_or_create(
                        id=item_id,
                        defaults=order_item_data
                    )
                    logger.info(f"Order item {item_id}: Successfully saved to DB")
                    
                except Exception as e:
                    logger.error(f"Error processing order item {item.get('id', 'unknown')}: {str(e)}", exc_info=True)
                    # Continue with next item instead of failing entire order
                    continue

            return order
        except Exception as e:
            logger.error(f"Error in process_order_completed: {str(e)}", exc_info=True)
            raise
