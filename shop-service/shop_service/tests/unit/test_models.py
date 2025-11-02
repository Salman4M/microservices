import pytest
import uuid
from django.core.exceptions import ValidationError
from shops.models import *
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.django_db
def test_shop_creation():
    user = uuid.uuid4()
    shop = Shop.objects.create(user=user, name="Test Shop", about="Some info about shop")
    
    assert shop.name == "Test Shop"
    assert shop.about == "Some info about shop"
    assert shop.user == user
    assert shop.is_active is True
    assert shop.is_verified is False
    assert isinstance(shop.id, uuid.UUID)
    assert str(shop) == "Test Shop"
    assert shop.get_slug_source() == shop.name


@pytest.mark.django_db
def test_shop_branch_creation():
    user = uuid.uuid4()
    shop = Shop.objects.create(user=user, name="Shop With Branch")
    branch = ShopBranch.objects.create(shop=shop, name="Main Branch", latitude=40.123456, longitude=49.654321)
    
    assert branch.shop == shop
    assert branch.name == "Main Branch"
    assert branch.is_active is True
    assert branch.latitude == 40.123456
    assert branch.longitude == 49.654321
    assert str(branch) == f"{shop.id}: Main Branch"


@pytest.mark.django_db
def test_shop_comment_clean_validation():
    user = uuid.uuid4()
    shop = Shop.objects.create(user=user, name="Shop For Comment")  

    comment = ShopComment(user=user, shop=shop)  
    with pytest.raises(ValidationError):
        comment.clean()

    comment.text = "Nice shop"
    comment.clean()

    comment.rating = 4
    comment.clean()

    assert comment.text == "Nice shop"
    assert comment.rating == 4
    assert comment.is_active is True


@pytest.mark.django_db
def test_shop_comment_str():
    user = uuid.uuid4()
    shop = Shop.objects.create(user=user, name="Shop Str Test")  
    comment = ShopComment.objects.create(user=user, shop=shop, text="Great", rating=5)

    assert str(comment) == f"{user} add comment to {shop.id}"


@pytest.mark.django_db
def test_shop_media_creation():
    user = uuid.uuid4()
    shop = Shop.objects.create(user=user, name="Shop Media")
    
    image = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
    media = ShopMedia.objects.create(shop=shop, image=image, alt_text="Alt text")
    
    assert media.shop == shop
    assert media.alt_text == "Alt text"
    assert str(media) == str(media.id)


@pytest.mark.django_db
def test_shop_social_media_creation():
    user = uuid.uuid4()
    shop = Shop.objects.create(user=user, name="Shop Social")
    
    sm = ShopSocialMedia.objects.create(shop=shop, media_name="Instagram", media_url="https://instagram.com/shop")
    
    assert sm.shop == shop
    assert sm.media_name == "Instagram"
    assert sm.media_url == "https://instagram.com/shop"
    assert str(sm) == f"{shop.id}: Instagram"
