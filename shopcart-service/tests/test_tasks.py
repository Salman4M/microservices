import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.shopcart_service.core.db import Base
from src.shopcart_service import models, crud, tasks


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


class TestVerifyProductExists:
    """Tests for verify_product_exists function in tasks"""
    
    @patch('src.shopcart_service.tasks.requests.get')
    def test_verify_product_exists_success(self, mock_get):
        """Test successful product verification"""
        variation_id = uuid4()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "product": {"is_active": True},
            "amount": 10
        }
        mock_get.return_value = mock_response
        
        result = tasks.verify_product_exists(variation_id)
        
        assert result is not None
        assert result["amount"] == 10
        assert result["is_active"] is True
    
    @patch('src.shopcart_service.tasks.requests.get')
    def test_verify_product_not_found(self, mock_get):
        """Test product not found returns None"""
        variation_id = uuid4()
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = tasks.verify_product_exists(variation_id)
        
        assert result is None
    
    @patch('src.shopcart_service.tasks.requests.get')
    def test_verify_product_service_error(self, mock_get):
        """Test service error returns None"""
        variation_id = uuid4()
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        result = tasks.verify_product_exists(variation_id)
        
        assert result is None
    
    @patch('src.shopcart_service.tasks.requests.get')
    def test_verify_product_timeout(self, mock_get):
        """Test timeout handling"""
        variation_id = uuid4()
        
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")
        
        result = tasks.verify_product_exists(variation_id)
        
        assert result is None
    
    @patch('src.shopcart_service.tasks.requests.get')
    def test_verify_product_connection_error(self, mock_get):
        """Test connection error handling"""
        variation_id = uuid4()
        
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        result = tasks.verify_product_exists(variation_id)
        
        assert result is None


class TestSyncCartStock:
    """Tests for sync_cart_stock Celery task"""
    
    @patch('src.shopcart_service.tasks.SessionLocal')
    @patch('src.shopcart_service.tasks.verify_product_exists')
    def test_sync_cart_stock_no_items(self, mock_verify, mock_session_local, db_session):
        """Test sync with no cart items"""
        mock_session_local.return_value = db_session
        
        result = tasks.sync_cart_stock()
        
        assert result["status"] == "success"
        assert result["total_items"] == 0
        assert result["message"] == "No items to process"
    
    @patch('src.shopcart_service.tasks.SessionLocal')
    @patch('src.shopcart_service.tasks.verify_product_exists')
    def test_sync_cart_stock_update_quantity(self, mock_verify, mock_session_local, db_session):
        """Test sync updates quantity when stock is lower"""
        mock_session_local.return_value = db_session
        
        # Setup: Create cart with item
        user_uuid = uuid4()
        cart = crud.create_cart(db_session, user_uuid)
        product_var_id = uuid4()
        item = crud.add_item_to_cart(db_session, product_var_id, cart.id, MagicMock())
        item_id = item.id
        item.quantity = 10  # Set high quantity
        db_session.commit()
        
        # Mock product service: only 5 items available
        mock_verify.return_value = {
            "amount": 5,
            "is_active": True
        }
        
        result = tasks.sync_cart_stock()
        
        assert result["status"] == "success"
        assert result["updated"] == 1
        
        # Query the item fresh from database
        updated_item = db_session.query(models.CartItem).filter(
            models.CartItem.id == item_id
        ).first()
        assert updated_item.quantity == 5
    
    @patch('src.shopcart_service.tasks.SessionLocal')
    @patch('src.shopcart_service.tasks.verify_product_exists')
    def test_sync_cart_stock_delete_out_of_stock(self, mock_verify, mock_session_local, db_session):
        """Test sync deletes items that are out of stock"""
        mock_session_local.return_value = db_session
        
        # Setup
        user_uuid = uuid4()
        cart = crud.create_cart(db_session, user_uuid)
        product_var_id = uuid4()
        item = crud.add_item_to_cart(db_session, product_var_id, cart.id, MagicMock())
        item_id = item.id
        
        # Mock: Out of stock
        mock_verify.return_value = {
            "amount": 0,
            "is_active": True
        }
        
        result = tasks.sync_cart_stock()
        
        assert result["status"] == "success"
        assert result["deleted"] == 1
        
        # Verify item was deleted
        deleted_item = db_session.query(models.CartItem).filter(
            models.CartItem.id == item_id
        ).first()
        assert deleted_item is None
    
    @patch('src.shopcart_service.tasks.SessionLocal')
    @patch('src.shopcart_service.tasks.verify_product_exists')
    def test_sync_cart_stock_delete_inactive_product(self, mock_verify, mock_session_local, db_session):
        """Test sync deletes items for inactive products"""
        mock_session_local.return_value = db_session
        
        # Setup
        user_uuid = uuid4()
        cart = crud.create_cart(db_session, user_uuid)
        product_var_id = uuid4()
        item = crud.add_item_to_cart(db_session, product_var_id, cart.id, MagicMock())
        item_id = item.id
        
        # Mock: Product is inactive
        mock_verify.return_value = {
            "amount": 10,
            "is_active": False
        }
        
        result = tasks.sync_cart_stock()
        
        assert result["status"] == "success"
        assert result["deleted"] == 1
        
        # Verify item was deleted
        deleted_item = db_session.query(models.CartItem).filter(
            models.CartItem.id == item_id
        ).first()
        assert deleted_item is None
    
    @patch('src.shopcart_service.tasks.SessionLocal')
    @patch('src.shopcart_service.tasks.verify_product_exists')
    def test_sync_cart_stock_delete_product_not_found(self, mock_verify, mock_session_local, db_session):
        """Test sync deletes items when product not found"""
        mock_session_local.return_value = db_session
        
        # Setup
        user_uuid = uuid4()
        cart = crud.create_cart(db_session, user_uuid)
        product_var_id = uuid4()
        item = crud.add_item_to_cart(db_session, product_var_id, cart.id, MagicMock())
        item_id = item.id
        
        # Mock: Product not found
        mock_verify.return_value = None
        
        result = tasks.sync_cart_stock()
        
        assert result["status"] == "success"
        assert result["deleted"] == 1
        
        # Verify item was deleted
        deleted_item = db_session.query(models.CartItem).filter(
            models.CartItem.id == item_id
        ).first()
        assert deleted_item is None
    
    @patch('src.shopcart_service.tasks.SessionLocal')
    @patch('src.shopcart_service.tasks.verify_product_exists')
    def test_sync_cart_stock_unchanged(self, mock_verify, mock_session_local, db_session):
        """Test sync leaves items unchanged when stock is sufficient"""
        mock_session_local.return_value = db_session
        
        # Setup
        user_uuid = uuid4()
        cart = crud.create_cart(db_session, user_uuid)
        product_var_id = uuid4()
        item = crud.add_item_to_cart(db_session, product_var_id, cart.id, MagicMock())
        item_id = item.id
        item.quantity = 5
        db_session.commit()
        
        # Mock: Plenty of stock
        mock_verify.return_value = {
            "amount": 20,
            "is_active": True
        }
        
        result = tasks.sync_cart_stock()
        
        assert result["status"] == "success"
        assert result["unchanged"] == 1
        
        # Query the item fresh from database
        unchanged_item = db_session.query(models.CartItem).filter(
            models.CartItem.id == item_id
        ).first()
        assert unchanged_item.quantity == 5
    
    @patch('src.shopcart_service.tasks.SessionLocal')
    @patch('src.shopcart_service.tasks.verify_product_exists')
    def test_sync_cart_stock_multiple_items(self, mock_verify, mock_session_local, db_session):
        """Test sync handles multiple items correctly"""
        mock_session_local.return_value = db_session
        
        # Setup: Multiple items with different scenarios
        user_uuid = uuid4()
        cart = crud.create_cart(db_session, user_uuid)
        
        # Item 1: Should be updated
        prod1 = uuid4()
        item1 = crud.add_item_to_cart(db_session, prod1, cart.id, MagicMock())
        item1.quantity = 10
        
        # Item 2: Should be deleted (out of stock)
        prod2 = uuid4()
        item2 = crud.add_item_to_cart(db_session, prod2, cart.id, MagicMock())
        
        # Item 3: Should be unchanged
        prod3 = uuid4()
        item3 = crud.add_item_to_cart(db_session, prod3, cart.id, MagicMock())
        item3.quantity = 3
        
        db_session.commit()
        
        # Mock different responses for each product
        def mock_verify_side_effect(variation_id):
            if variation_id == prod1:
                return {"amount": 5, "is_active": True}  # Update to 5
            elif variation_id == prod2:
                return {"amount": 0, "is_active": True}  # Delete
            elif variation_id == prod3:
                return {"amount": 10, "is_active": True}  # Unchanged
        
        mock_verify.side_effect = mock_verify_side_effect
        
        result = tasks.sync_cart_stock()
        
        assert result["status"] == "success"
        assert result["total_items"] == 3
        assert result["updated"] == 1
        assert result["deleted"] == 1
        assert result["unchanged"] == 1
    
    @patch('src.shopcart_service.tasks.SessionLocal')
    def test_sync_cart_stock_error_handling(self, mock_session_local):
        """Test sync handles database errors gracefully"""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")
        mock_session_local.return_value = mock_db
        
        result = tasks.sync_cart_stock()
        
        assert result["status"] == "error"
        assert "Database error" in result["message"]


class TestTestDbConnection:
    """Tests for test_db_connection Celery task"""
    
    @patch('src.shopcart_service.tasks.SessionLocal')
    def test_db_connection_success(self, mock_session_local, db_session):
        """Test successful database connection"""
        mock_session_local.return_value = db_session
        
        # Create test data
        user_uuid = uuid4()
        cart = crud.create_cart(db_session, user_uuid)
        product_var_id = uuid4()
        crud.add_item_to_cart(db_session, product_var_id, cart.id, MagicMock())
        
        result = tasks.test_db_connection()
        
        assert result["status"] == "success"
        assert result["carts"] == 1
        assert result["items"] == 1
    
    @patch('src.shopcart_service.tasks.SessionLocal')
    def test_db_connection_empty_database(self, mock_session_local, db_session):
        """Test connection with empty database"""
        mock_session_local.return_value = db_session
        
        result = tasks.test_db_connection()
        
        assert result["status"] == "success"
        assert result["carts"] == 0
        assert result["items"] == 0
    
    @patch('src.shopcart_service.tasks.SessionLocal')
    def test_db_connection_error(self, mock_session_local):
        """Test database connection error handling"""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Connection failed")
        mock_session_local.return_value = mock_db
        
        result = tasks.test_db_connection()
        
        assert result["status"] == "error"
        assert "Connection failed" in result["message"]