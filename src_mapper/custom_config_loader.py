#!/usr/bin/env python3
# src_mapper/custom_config_loader.py

"""
Module for loading configuration settings, with support for custom overrides.
This allows users to create a custom_config.py file with their own settings
without modifying the original config.py file.
"""

import importlib.util
import sys
from pathlib import Path


def get_config():
    """
    Attempts to load custom configuration if available, 
    otherwise falls back to the default configuration.
    
    Returns:
        module: The loaded configuration module
    """
    # Try to load custom_config.py if it exists
    custom_config_path = Path(__file__).parent / "custom_config.py"
    
    if custom_config_path.exists():
        try:
            # Load the custom config as a module
            spec = importlib.util.spec_from_file_location("custom_config", custom_config_path)
            custom_config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(custom_config)
            print("Using custom configuration from custom_config.py")
            return custom_config
        except Exception as e:
            print(f"Error loading custom configuration: {e}", file=sys.stderr)
            print("Falling back to default configuration", file=sys.stderr)
    
    # Fall back to default config
    from . import config
    return config


if __name__ == "__main__":
    # Simple test to verify module works correctly
    config = get_config()
    print(f"Loaded configuration with {len(config.ALWAYS_INCLUDE_CONTENT_PATTERNS)} prioritized file patterns")
    print(f"Max embedded content: {config.MAX_TOTAL_EMBEDDED_CONTENT_KB} KB")