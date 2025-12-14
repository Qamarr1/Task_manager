import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config, DevelopmentConfig, ProductionConfig, config


def test_base_config():
    """Test base configuration class"""
    config_obj = Config()
    assert hasattr(config_obj, 'SECRET_KEY')
    assert hasattr(config_obj, 'DB_TYPE')
    assert hasattr(config_obj, 'ENVIRONMENT')


def test_development_config():
    """Test development configuration"""
    dev_config = DevelopmentConfig()
    assert dev_config.DEBUG is True
    assert dev_config.DB_TYPE == 'sqlite'


def test_production_config():
    """Test production configuration"""
    prod_config = ProductionConfig()
    assert prod_config.DEBUG is False
    assert prod_config.DB_TYPE == 'azure_sql'


def test_config_dictionary():
    """Test configuration dictionary"""
    assert 'development' in config
    assert 'production' in config
    assert 'default' in config
    assert config['default'] == DevelopmentConfig


def test_config_environment_defaults():
    """Test configuration reads environment variables with defaults"""
    config_obj = Config()
    # Should have default values when env vars not set
    # In CI/CD, database might be :memory: for testing
    assert config_obj.SQLITE_DATABASE in ['tasks.db', ':memory:', 'test_tasks.db']
    assert config_obj.ENVIRONMENT in ['development', 'production']


def test_development_environment():
    """Test development environment selection"""
    dev = config['development']
    assert dev.DEBUG is True
    assert dev.DB_TYPE == 'sqlite'


def test_production_environment():
    """Test production environment selection"""
    prod = config['production']
    assert prod.DEBUG is False
    assert prod.DB_TYPE == 'azure_sql'
