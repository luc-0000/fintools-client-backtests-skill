"""
Global variables for FastAPI application

This module provides a global dictionary to store application-wide state,
such as database connections and configuration.
"""

# Global variable dictionary
global_var = {}


def get_global_var():
    """Get the global variable dictionary"""
    return global_var


def set_global_var(key, value):
    """Set a value in the global variable dictionary"""
    global_var[key] = value


def init_global_vars(config=None):
    """
    Initialize global variables

    Args:
        config: Optional configuration dictionary
    """
    if config:
        for key, value in config.items():
            global_var[key] = value

    # Initialize with empty db if not already set
    if 'db' not in global_var:
        global_var['db'] = None

    return global_var