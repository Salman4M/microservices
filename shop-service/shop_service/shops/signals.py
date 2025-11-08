import logging
from django.db.models.signals import pre_save
from django.dispatch import receiver
from shops.models import Shop
from shop_service.messaging import publisher

logger = logging.getLogger('shop_service')


@receiver(pre_save, sender=Shop)
def shop_pre_save(sender, instance, **kwargs):
    """Send event when shop status changes to APPROVED"""
    previous_status = None
    if instance.id:
        try:
            original = Shop.objects.get(id=instance.id)
            previous_status = original.status
        except Shop.DoesNotExist:
            pass
    
    if instance.status == Shop.APPROVED and previous_status != Shop.APPROVED:
        if instance.id:
            try:
                publisher.publish_shop_created(
                    user_uuid=str(instance.user),
                    shop_id=str(instance.id)
                )
                logger.info(
                    f'Shop approved event published | user={instance.user} shop={instance.id}'
                )
            except Exception as e:
                logger.error(f'Failed to publish shop approved event: {e}', exc_info=True)
