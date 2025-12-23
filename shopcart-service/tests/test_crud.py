import pytest
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.shopcart_service.core.db import Base
from src.shopcart_service import schemas, crud


# Test database setup
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture
def db_session():
    """Create a fresh database session for each test"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


class TestCreateCart:
    """Tests for create_cart function"""
    
    def test_create_cart_success(self, db_session):
        """Test successful cart creation"""
        user_uuid = uuid4()
        cart = crud.create_cart(db_session, user_uuid)
        
        assert cart is not None
        assert cart.id is not None
        assert cart.user_uuid == user_uuid
        assert len(cart.items) == 0
    
    def test_create_cart_duplicate(self, db_session):
        """Test that creating duplicate cart returns None"""
        user_uuid = uuid4()
        
        # Create first cart
        cart1 = crud.create_cart(db_session, user_uuid)
        assert cart1 is not None
        
        # Try to create duplicate
        cart2 = crud.create_cart(db_session, user_uuid)
        assert cart2 is None


class TestGetUserByUuid:
    """Tests for get_user_by_uuid function"""
    
    def test_get_existing_cart(self, db_session):
        """Test retrieving existing cart by UUID"""
        user_uuid = uuid4()
        created_cart = crud.create_cart(db_session, user_uuid)
        
        retrieved_cart = crud.get_user_by_uuid(db_session, user_uuid)
        
        assert retrieved_cart is not None
        assert retrieved_cart.id == created_cart.id
        assert retrieved_cart.user_uuid == user_uuid
    
    def test_get_nonexistent_cart(self, db_session):
        """Test retrieving non-existent cart returns None"""
        user_uuid = uuid4()
        cart = crud.get_user_by_uuid(db_session, user_uuid)
        
        assert cart is None


class TestGetCart:
    """Tests for get_cart function"""
    
    def test_get_cart_success(self, db_session):
        """Test successful cart retrieval"""
        user_uuid = uuid4()
        crud.create_cart(db_session, user_uuid)
        
        cart = crud.get_cart(db_session, user_uuid)
        
        assert cart is not None
        assert cart.user_uuid == user_uuid
    
    def test_get_cart_not_found(self, db_session):
        """Test getting cart that doesn't exist"""
        user_uuid = uuid4()
        cart = crud.get_cart(db_session, user_uuid)
        
        assert cart is None


class TestAddItemToCart:
    """Tests for add_item_to_cart function"""
    
    def test_add_new_item(self, db_session):
        """Test adding new item to cart"""
        user_uuid = uuid4()
        cart = crud.create_cart(db_session, user_uuid)
        product_var_id = uuid4()
        
        item_data = schemas.CartItemCreate()
        item = crud.add_item_to_cart(db_session, product_var_id, cart.id, item_data)
        
        assert item is not None
        assert item.product_variation_id == product_var_id
        assert item.quantity == 1
        assert item.shop_cart_id == cart.id
    
    def test_add_existing_item_increments_quantity(self, db_session):
        """Test that adding existing item increments quantity"""
        user_uuid = uuid4()
        cart = crud.create_cart(db_session, user_uuid)
        product_var_id = uuid4()
        item_data = schemas.CartItemCreate()
        
        # Add item first time
        item1 = crud.add_item_to_cart(db_session, product_var_id, cart.id, item_data)
        assert item1.quantity == 1
        
        # Add same item again
        item2 = crud.add_item_to_cart(db_session, product_var_id, cart.id, item_data)
        assert item2.quantity == 2
        assert item2.id == item1.id  # Same item object


class TestUpdateCart:
    """Tests for update_cart function"""
    
    def test_update_cart_item_quantity(self, db_session):
        """Test updating cart item quantity"""
        user_uuid = uuid4()
        cart = crud.create_cart(db_session, user_uuid)
        product_var_id = uuid4()
        
        # Add item
        item_data = schemas.CartItemCreate()
        item = crud.add_item_to_cart(db_session, product_var_id, cart.id, item_data)
        
        # Update quantity
        update_data = schemas.CartItemUpdate(quantity=5)
        updated_item = crud.update_cart(db_session, item.id, cart.id, update_data)
        
        assert updated_item is not None
        assert updated_item.quantity == 5
        assert updated_item.id == item.id
    
    def test_update_nonexistent_item(self, db_session):
        """Test updating non-existent item returns None"""
        user_uuid = uuid4()
        cart = crud.create_cart(db_session, user_uuid)
        
        update_data = schemas.CartItemUpdate(quantity=3)
        updated_item = crud.update_cart(db_session, 999, cart.id, update_data)
        
        assert updated_item is None
    
    def test_update_item_wrong_cart(self, db_session):
        """Test updating item from different cart returns None"""
        user1_uuid = uuid4()
        user2_uuid = uuid4()
        cart1 = crud.create_cart(db_session, user1_uuid)
        cart2 = crud.create_cart(db_session, user2_uuid)
        
        # Add item to cart1
        product_var_id = uuid4()
        item_data = schemas.CartItemCreate()
        item = crud.add_item_to_cart(db_session, product_var_id, cart1.id, item_data)
        
        # Try to update item using cart2's id
        update_data = schemas.CartItemUpdate(quantity=5)
        updated_item = crud.update_cart(db_session, item.id, cart2.id, update_data)
        
        assert updated_item is None


class TestDeleteCartItem:
    """Tests for delete_cart_item function"""
    
    def test_delete_item_success(self, db_session):
        """Test successful item deletion"""
        user_uuid = uuid4()
        cart = crud.create_cart(db_session, user_uuid)
        product_var_id = uuid4()
        
        # Add item
        item_data = schemas.CartItemCreate()
        item = crud.add_item_to_cart(db_session, product_var_id, cart.id, item_data)
        
        # Delete item
        deleted_item = crud.delete_cart_item(db_session, item.id, cart.id)
        
        assert deleted_item is not None
        assert deleted_item.id == item.id
        
        # Verify item is deleted
        cart_after = crud.get_cart(db_session, user_uuid)
        assert len(cart_after.items) == 0
        
    def test_delete_nonexistent_item(self, db_session):
        """Test deleting non-existent item returns None"""
        user_uuid = uuid4()
        cart = crud.create_cart(db_session, user_uuid)
        
        deleted_item = crud.delete_cart_item(db_session, 999, cart.id)
        
        assert deleted_item is None
    
    def test_delete_item_wrong_cart(self, db_session):
        """Test deleting item from wrong cart returns None"""
        user1_uuid = uuid4()
        user2_uuid = uuid4()
        cart1 = crud.create_cart(db_session, user1_uuid)
        cart2 = crud.create_cart(db_session, user2_uuid)
        
        # Add item to cart1
        product_var_id = uuid4()
        item_data = schemas.CartItemCreate()
        item = crud.add_item_to_cart(db_session, product_var_id, cart1.id, item_data)
        
        # Try to delete using cart2's id
        deleted_item = crud.delete_cart_item(db_session, item.id, cart2.id)
        
        assert deleted_item is None


class TestDeleteCartForUser:
    """Tests for delete_cart_for_user function"""
    
    def test_delete_cart_with_items(self, db_session):
        """Test deleting cart that has items"""
        user_uuid = uuid4()
        cart = crud.create_cart(db_session, user_uuid)
        
        # Add multiple items
        for _ in range(3):
            product_var_id = uuid4()
            item_data = schemas.CartItemCreate()
            crud.add_item_to_cart(db_session, product_var_id, cart.id, item_data)
        
        # Delete cart
        result = crud.delete_cart_for_user(db_session, user_uuid)
        
        assert result is True
        
        # Verify cart is deleted
        deleted_cart = crud.get_cart(db_session, user_uuid)
        assert deleted_cart is None
    
    def test_delete_nonexistent_cart(self, db_session):
        """Test deleting non-existent cart returns False"""
        user_uuid = uuid4()
        result = crud.delete_cart_for_user(db_session, user_uuid)
        
        assert result is False
    
    def test_delete_empty_cart(self, db_session):
        """Test deleting empty cart"""
        user_uuid = uuid4()
        crud.create_cart(db_session, user_uuid)
        
        result = crud.delete_cart_for_user(db_session, user_uuid)
        
        assert result is True
        
        # Verify deletion
        cart = crud.get_cart(db_session, user_uuid)
        assert cart is None