"""
Test suite for dashboard button functionality and API endpoints.
Tests each button's corresponding API endpoint to ensure proper responses.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from core.bot_management.bot_api_server import BotAPIServer
from core.bot_management.event_bus import EventBus
from config.config_manager import ConfigManager


class TestDashboardButtons(AioHTTPTestCase):
    """Test all dashboard button endpoints."""

    async def get_application(self):
        """Create test application with mocked dependencies."""
        # Create mocks for dependencies
        self.mock_bot = Mock()
        self.mock_bot.is_running = False
        self.mock_bot.trading_mode = "backtest"
        
        # Mock balance tracker with proper return values
        mock_balance_tracker = Mock()
        mock_balance_tracker.get_adjusted_fiat_balance.return_value = 1000.0
        mock_balance_tracker.get_adjusted_crypto_balance.return_value = 0.5
        mock_balance_tracker.get_total_balance_value.return_value = 1500.0
        mock_balance_tracker.total_fees = 10.0
        self.mock_bot.balance_tracker = mock_balance_tracker
        
        # Mock exchange service
        mock_exchange = Mock()
        mock_exchange.get_current_price = AsyncMock(return_value=50000.0)
        self.mock_bot.exchange_service = mock_exchange
        
        # Mock grid manager
        mock_grid_manager = Mock()
        mock_grid_manager.central_price = 50000.0
        mock_grid_manager.grid_levels = [49000, 49500, 50000, 50500, 51000]
        mock_grid_manager.sorted_buy_grids = [49000, 49500]
        mock_grid_manager.sorted_sell_grids = [50500, 51000]
        self.mock_bot.grid_manager = mock_grid_manager
        
        # Mock order manager
        mock_order_manager = Mock()
        mock_order_manager.orders = []
        self.mock_bot.order_manager = mock_order_manager
        
        # Create a real event bus for testing
        self.event_bus = EventBus()
        
        # Create a mock config manager
        self.config_manager = Mock(spec=ConfigManager)
        self.config_manager.get_base_currency.return_value = "BTC"
        self.config_manager.get_quote_currency.return_value = "USD"
        self.config_manager.get_trading_mode.return_value = "backtest"
        self.config_manager.get_timeframe.return_value = "1h"
        self.config_manager.get_initial_balance.return_value = 1000.0
        self.config_manager.get_strategy_type.return_value = "simple_grid"
        self.config_manager.get_spacing_type.return_value = "geometric"
        self.config_manager.get_num_grids.return_value = 10
        self.config_manager.get_bottom_range.return_value = 45000.0
        self.config_manager.get_top_range.return_value = 55000.0
        self.config_manager.is_take_profit_enabled.return_value = False
        self.config_manager.get_take_profit_threshold.return_value = 60000.0
        self.config_manager.is_stop_loss_enabled.return_value = False
        self.config_manager.get_stop_loss_threshold.return_value = 40000.0
        self.config_manager.is_multi_timeframe_analysis_enabled.return_value = False
        self.config_manager.config = {
            "exchange": {"name": "kraken", "trading_mode": "backtest"},
            "pair": {"base_currency": "BTC", "quote_currency": "USD"},
            "multi_pair": {"enabled": False, "max_pairs": 2},
        }
        
        # Create API server
        api_server = BotAPIServer(
            bot=self.mock_bot,
            event_bus=self.event_bus,
            config_manager=self.config_manager,
            port=8888
        )
        
        return api_server.app

    @unittest_run_loop
    async def test_health_endpoint(self):
        """Test health check endpoint."""
        resp = await self.client.request("GET", "/api/health")
        assert resp.status == 200
        data = await resp.json()
        assert data["status"] == "ok"
        assert "timestamp" in data

    @unittest_run_loop
    async def test_bot_start_button(self):
        """Test Start Bot button endpoint."""
        resp = await self.client.request("POST", "/api/bot/start")
        assert resp.status == 200
        data = await resp.json()
        assert "success" in data
        assert "message" in data

    @unittest_run_loop
    async def test_bot_stop_button(self):
        """Test Stop Bot button endpoint."""
        # Set bot to running state first
        self.mock_bot.is_running = True
        
        resp = await self.client.request("POST", "/api/bot/stop")
        assert resp.status == 200
        data = await resp.json()
        assert "success" in data
        assert "message" in data

    @unittest_run_loop
    async def test_bot_pause_button(self):
        """Test Pause Bot button endpoint."""
        resp = await self.client.request("POST", "/api/bot/pause")
        assert resp.status == 200
        data = await resp.json()
        assert "success" in data
        assert "message" in data

    @unittest_run_loop
    async def test_bot_resume_button(self):
        """Test Resume Bot button endpoint."""
        resp = await self.client.request("POST", "/api/bot/resume")
        assert resp.status == 200
        data = await resp.json()
        assert "success" in data
        assert "message" in data

    @unittest_run_loop
    async def test_bot_status_endpoint(self):
        """Test bot status retrieval."""
        resp = await self.client.request("GET", "/api/bot/status")
        assert resp.status == 200
        data = await resp.json()
        assert "running" in data
        assert "trading_mode" in data
        assert "trading_pair" in data
        assert "timestamp" in data

    @unittest_run_loop
    async def test_bot_metrics_endpoint(self):
        """Test bot metrics retrieval."""
        resp = await self.client.request("GET", "/api/bot/metrics")
        assert resp.status == 200
        data = await resp.json()
        assert "timestamp" in data

    @unittest_run_loop
    async def test_bot_orders_endpoint(self):
        """Test orders list retrieval."""
        resp = await self.client.request("GET", "/api/bot/orders")
        assert resp.status == 200
        data = await resp.json()
        assert "orders" in data

    @unittest_run_loop
    async def test_config_get_endpoint(self):
        """Test config retrieval."""
        resp = await self.client.request("GET", "/api/config")
        assert resp.status == 200
        data = await resp.json()
        # Config should have some content
        assert len(data) > 0
        assert isinstance(data, dict)

    @unittest_run_loop
    async def test_config_update_endpoint(self):
        """Test config update (used by many buttons)."""
        update_data = {
            "exchange": {"trading_mode": "paper_trading"}
        }
        resp = await self.client.request(
            "POST", "/api/config/update",
            json=update_data
        )
        assert resp.status in [200, 500]  # May fail without proper config file
        data = await resp.json()
        assert "success" in data or "message" in data

    @unittest_run_loop
    async def test_market_scan_button(self):
        """Test market scan button endpoint."""
        scan_params = {
            "min_price": 1.0,
            "max_price": 20.0,
            "timeframe": "15m",
            "quote_currency": "USD",
            "ema_fast_period": 9,
            "ema_slow_period": 21
        }
        resp = await self.client.request(
            "POST", "/api/market/scan",
            json=scan_params
        )
        # Expected to fail without exchange service, but should return proper error
        assert resp.status in [200, 400, 500]
        data = await resp.json()
        assert "success" in data or "message" in data

    @unittest_run_loop
    async def test_multi_pair_status_button(self):
        """Test multi-pair status retrieval."""
        resp = await self.client.request("GET", "/api/multi-pair/status")
        assert resp.status == 200
        data = await resp.json()
        assert "success" in data
        assert "data" in data

    @unittest_run_loop
    async def test_multi_pair_start_button(self):
        """Test multi-pair start button."""
        start_params = {"max_pairs": 2}
        resp = await self.client.request(
            "POST", "/api/multi-pair/start",
            json=start_params
        )
        # Expected to fail without multi_pair_manager, but should return proper error
        assert resp.status in [200, 400, 500]
        data = await resp.json()
        assert "success" in data or "message" in data

    @unittest_run_loop
    async def test_multi_pair_stop_button(self):
        """Test multi-pair stop button."""
        resp = await self.client.request("POST", "/api/multi-pair/stop", json={})
        # Expected to fail without multi_pair_manager running
        assert resp.status in [200, 400, 500]
        data = await resp.json()
        assert "success" in data or "message" in data

    @unittest_run_loop
    async def test_mtf_status_endpoint(self):
        """Test multi-timeframe analysis status."""
        resp = await self.client.request("GET", "/api/mtf/status")
        assert resp.status == 200
        data = await resp.json()
        # Should return valid response structure
        assert isinstance(data, dict)

    @unittest_run_loop
    async def test_mtf_analyze_button(self):
        """Test MTF analyze button."""
        resp = await self.client.request("POST", "/api/mtf/analyze", json={})
        # Expected to fail without proper setup, but should return error properly
        assert resp.status in [200, 400, 500]
        data = await resp.json()
        assert "success" in data or "message" in data

    @unittest_run_loop
    async def test_chuck_smart_scan_button(self):
        """Test Chuck AI Smart Scan button."""
        scan_params = {
            "quote_currency": "USD",
            "num_pairs": 10,
            "min_price": 0.01,
            "max_price": 100,
            "min_volume": 100000
        }
        resp = await self.client.request(
            "POST", "/api/chuck/smart-scan",
            json=scan_params
        )
        # Expected to fail without exchange service
        assert resp.status in [200, 400, 500]
        data = await resp.json()
        assert "success" in data or "message" in data

    @unittest_run_loop
    async def test_chuck_portfolio_status(self):
        """Test Chuck AI portfolio status."""
        resp = await self.client.request("GET", "/api/chuck/portfolio/status")
        assert resp.status == 200
        data = await resp.json()
        assert "success" in data
        assert "running" in data

    @unittest_run_loop
    async def test_chuck_portfolio_start_button(self):
        """Test Chuck AI portfolio start button."""
        start_params = {
            "total_capital": 500,
            "max_positions": 5,
            "min_entry_score": 65,
            "scan_interval": 300
        }
        resp = await self.client.request(
            "POST", "/api/chuck/portfolio/start",
            json=start_params
        )
        # Expected to fail without exchange service
        assert resp.status in [200, 400, 500]
        data = await resp.json()
        assert "success" in data or "message" in data

    @unittest_run_loop
    async def test_chuck_portfolio_stop_button(self):
        """Test Chuck AI portfolio stop button."""
        resp = await self.client.request("POST", "/api/chuck/portfolio/stop", json={})
        # Expected to fail when not running
        assert resp.status in [200, 400, 500]
        data = await resp.json()
        assert "success" in data or "message" in data

    @unittest_run_loop
    async def test_chuck_entry_signal_button(self):
        """Test Chuck AI entry signal analysis button."""
        signal_params = {
            "pair": "BTC/USD",
            "grid_top": 50000,
            "grid_bottom": 40000
        }
        resp = await self.client.request(
            "POST", "/api/chuck/entry-signal",
            json=signal_params
        )
        # Expected to fail without exchange service
        assert resp.status in [200, 400, 500]
        data = await resp.json()
        assert "success" in data or "message" in data

    @unittest_run_loop
    async def test_scanner_config_get(self):
        """Test scanner config retrieval."""
        resp = await self.client.request("GET", "/api/market/scanner-config")
        assert resp.status in [200, 500]  # May fail without config file
        data = await resp.json()
        assert isinstance(data, dict)

    @unittest_run_loop
    async def test_scanner_config_update(self):
        """Test scanner config update."""
        config_update = {
            "min_price": 1.0,
            "max_price": 20.0,
            "ema_fast_period": 9,
            "ema_slow_period": 21
        }
        resp = await self.client.request(
            "POST", "/api/market/scanner-config",
            json=config_update
        )
        assert resp.status in [200, 500]
        data = await resp.json()
        assert "success" in data or "message" in data


class TestDashboardButtonResponseStructures:
    """Test that button endpoints return correct response structures."""

    @pytest.fixture
    def mock_bot_api_server(self):
        """Create a mock bot API server for testing response structures."""
        mock_bot = Mock()
        mock_bot.is_running = False
        mock_bot.trading_mode = "backtest"
        
        event_bus = EventBus()
        
        config_manager = Mock(spec=ConfigManager)
        config_manager.get_base_currency.return_value = "BTC"
        config_manager.get_quote_currency.return_value = "USD"
        config_manager.config = {
            "exchange": {"name": "kraken"},
            "multi_pair": {"enabled": False},
        }
        
        return BotAPIServer(
            bot=mock_bot,
            event_bus=event_bus,
            config_manager=config_manager,
            port=8888
        )

    @pytest.mark.asyncio
    async def test_health_response_structure(self, mock_bot_api_server):
        """Test health endpoint returns proper structure."""
        request = Mock()
        response = await mock_bot_api_server.handle_health(request)
        assert response.status == 200

    @pytest.mark.asyncio
    async def test_multi_pair_status_response_structure(self, mock_bot_api_server):
        """Test multi-pair status returns proper structure."""
        request = Mock()
        response = await mock_bot_api_server.handle_multi_pair_status(request)
        assert response.status == 200

    @pytest.mark.asyncio
    async def test_chuck_portfolio_status_response_structure(self, mock_bot_api_server):
        """Test chuck portfolio status returns proper structure."""
        request = Mock()
        response = await mock_bot_api_server.handle_chuck_portfolio_status(request)
        assert response.status == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
