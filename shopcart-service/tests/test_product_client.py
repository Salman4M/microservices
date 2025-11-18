import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException
import httpx
from src.shopcart_service.core.product_client import ProductServiceDataCheck


@pytest.fixture
def product_client():
    """Create ProductServiceDataCheck instance"""
    with patch.dict('os.environ', {'PRODUCT_SERVICE': 'http://product-service:8000'}):
        return ProductServiceDataCheck()


@pytest.fixture
def product_data():
    """Sample product data response"""
    return {
        "id": str(uuid4()),
        "product": {
            "id": str(uuid4()),
            "name": "Test Product",
            "is_active": True
        },
        "amount": 10,
        "price": 99.99
    }


class TestVerifyProductExists:
    """Tests for verify_product_exists method"""
    
    @pytest.mark.asyncio
    async def test_verify_product_exists_success(self, product_client, product_data):
        """Test successful product verification"""
        variation_id = uuid4()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = product_data
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            result = await product_client.verify_product_exists(variation_id)
            
            assert result is not None
            assert result["amount"] == 10
            assert result["product"]["is_active"] is True
    
    @pytest.mark.asyncio
    async def test_verify_product_not_found(self, product_client):
        """Test product not found returns 404"""
        variation_id = uuid4()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await product_client.verify_product_exists(variation_id)
            
            assert exc_info.value.status_code == 404
            assert "Product not found" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_verify_product_inactive(self, product_client, product_data):
        """Test inactive product raises exception"""
        variation_id = uuid4()
        product_data["product"]["is_active"] = False
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = product_data
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await product_client.verify_product_exists(variation_id)
            
            assert exc_info.value.status_code == 400
            assert "Product unavailable" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_verify_product_service_unavailable(self, product_client):
        """Test handling service unavailable response"""
        variation_id = uuid4()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 503
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await product_client.verify_product_exists(variation_id)
            
            assert exc_info.value.status_code == 503
            assert "Product service unavailable" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_verify_product_connection_error(self, product_client):
        """Test handling connection errors"""
        variation_id = uuid4()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.RequestError("Connection refused")
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await product_client.verify_product_exists(variation_id)
            
            assert exc_info.value.status_code == 503
            assert "Cannot connect to product service" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_verify_product_timeout(self, product_client):
        """Test handling timeout errors"""
        variation_id = uuid4()
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Request timeout")
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await product_client.verify_product_exists(variation_id)
            
            assert exc_info.value.status_code == 503


class TestVerifyStock:
    """Tests for verify_stock method"""
    
    @pytest.mark.asyncio
    async def test_verify_stock_success(self, product_client, product_data):
        """Test successful stock verification"""
        variation_id = uuid4()
        quantity = 5
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = product_data
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            result = await product_client.verify_stock(variation_id, quantity)
            
            assert result is not None
            assert result["amount"] >= quantity
    
    @pytest.mark.asyncio
    async def test_verify_stock_insufficient(self, product_client, product_data):
        """Test insufficient stock raises exception"""
        variation_id = uuid4()
        quantity = 20  # More than available (10)
        product_data["amount"] = 5
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = product_data
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await product_client.verify_stock(variation_id, quantity)
            
            assert exc_info.value.status_code == 400
            assert "5 items available" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_verify_stock_zero(self, product_client, product_data):
        """Test zero stock raises exception"""
        variation_id = uuid4()
        quantity = 1
        product_data["amount"] = 0
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = product_data
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await product_client.verify_stock(variation_id, quantity)
            
            assert exc_info.value.status_code == 400
            assert "0 items available" in exc_info.value.detail
    
    @pytest.mark.asyncio
    async def test_verify_stock_exact_amount(self, product_client, product_data):
        """Test stock verification with exact available amount"""
        variation_id = uuid4()
        quantity = 10
        product_data["amount"] = 10
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = product_data
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            result = await product_client.verify_stock(variation_id, quantity)
            
            assert result["amount"] == quantity
    
    @pytest.mark.asyncio
    async def test_verify_stock_product_not_found(self, product_client):
        """Test stock verification when product doesn't exist"""
        variation_id = uuid4()
        quantity = 1
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404
            
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await product_client.verify_stock(variation_id, quantity)
            
            assert exc_info.value.status_code == 404


class TestProductClientConfiguration:
    """Tests for ProductServiceDataCheck configuration"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        with patch.dict('os.environ', {'PRODUCT_SERVICE': 'http://fastapi_app:8000'}):
            client = ProductServiceDataCheck()
            
            assert client.base_url == 'http://fastapi_app:8000'
            assert client.timeout == 30.0
    
    def test_custom_timeout(self):
        """Test client respects timeout setting"""
        with patch.dict('os.environ', {'PRODUCT_SERVICE': 'http://fastapi_app:8000'}):
            client = ProductServiceDataCheck()
            client.timeout = 10.0
            
            assert client.timeout == 10.0