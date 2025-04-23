"""
Session state management with type safety and efficient access patterns.
This module provides a centralized interface for managing Streamlit session state
with proper abstraction, type hints, and default values.
"""

import streamlit as st
import logging
from typing import Any, Dict, List, Optional, TypeVar, Generic, Callable, Union, Set

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for generic return type
T = TypeVar('T')

class SessionStateManager:
    """
    Efficient session state management with type hints and defaults.
    Provides a centralized interface for accessing and modifying session state.
    """
    
    @staticmethod
    def initialize() -> None:
        """
        Initialize session state with default values.
        Call this at the beginning of the application to ensure all required
        state variables are properly initialized.
        """
        defaults = {
            # Authentication
            'client': None,
            'authenticated': False,
            'auth_method': None,
            'user_info': {},
            
            # Navigation
            'current_page': 'home',
            'previous_page': None,
            'navigation_history': [],
            
            # File browser
            'current_folder_id': '0',  # Root folder
            'folder_path': [],
            'selected_files': [],
            'file_cache': {},
            
            # Metadata templates
            'metadata_templates': {},
            'selected_template': None,
            'template_cache': {},
            
            # Processing
            'extraction_results': {},
            'processing_status': {},
            'batch_progress': 0,
            'current_batch_id': None,
            'processing_mode': 'sequential',
            
            # Configuration
            'settings': {
                'batch_size': 10,
                'concurrent_requests': 5,
                'confidence_threshold': 0.7,
                'auto_apply': False,
                'cache_enabled': True,
                'cache_ttl': 3600,
                'show_debug': False
            },
            
            # UI state
            'sidebar_expanded': True,
            'show_advanced': False,
            'theme': 'light',
            
            # Background jobs
            'jobs': {},
            'active_job_id': None
        }
        
        # Initialize all default values if not already set
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    @staticmethod
    def get(key: str, default: T = None) -> T:
        """
        Get a value from session state with default fallback.
        
        Args:
            key: Session state key
            default: Default value if key doesn't exist
            
        Returns:
            Value from session state or default
        """
        if key not in st.session_state:
            SessionStateManager.set(key, default)
        return st.session_state[key]
    
    @staticmethod
    def set(key: str, value: Any) -> None:
        """
        Set a value in session state.
        
        Args:
            key: Session state key
            value: Value to set
        """
        st.session_state[key] = value
    
    @staticmethod
    def delete(key: str) -> None:
        """
        Delete a key from session state if it exists.
        
        Args:
            key: Session state key to delete
        """
        if key in st.session_state:
            del st.session_state[key]
    
    @staticmethod
    def has(key: str) -> bool:
        """
        Check if a key exists in session state.
        
        Args:
            key: Session state key to check
            
        Returns:
            bool: True if key exists, False otherwise
        """
        return key in st.session_state
    
    @staticmethod
    def update(key: str, update_func: Callable[[T], T]) -> T:
        """
        Update a value in session state using a function.
        
        Args:
            key: Session state key
            update_func: Function that takes current value and returns new value
            
        Returns:
            Updated value
        """
        current_value = SessionStateManager.get(key)
        new_value = update_func(current_value)
        SessionStateManager.set(key, new_value)
        return new_value
    
    @staticmethod
    def append(key: str, item: Any, max_items: Optional[int] = None) -> List[Any]:
        """
        Append an item to a list in session state.
        
        Args:
            key: Session state key (must be a list)
            item: Item to append
            max_items: Maximum number of items to keep (oldest removed first)
            
        Returns:
            Updated list
        """
        current_list = SessionStateManager.get(key, [])
        
        if not isinstance(current_list, list):
            logger.warning(f"Key '{key}' is not a list, converting to list")
            current_list = [current_list]
        
        current_list.append(item)
        
        # Trim list if max_items specified
        if max_items is not None and len(current_list) > max_items:
            current_list = current_list[-max_items:]
        
        SessionStateManager.set(key, current_list)
        return current_list
    
    @staticmethod
    def add_to_dict(key: str, dict_key: Any, dict_value: Any) -> Dict[Any, Any]:
        """
        Add or update a key-value pair in a dictionary in session state.
        
        Args:
            key: Session state key (must be a dict)
            dict_key: Dictionary key to add/update
            dict_value: Value to set
            
        Returns:
            Updated dictionary
        """
        current_dict = SessionStateManager.get(key, {})
        
        if not isinstance(current_dict, dict):
            logger.warning(f"Key '{key}' is not a dict, converting to dict")
            current_dict = {0: current_dict}
        
        current_dict[dict_key] = dict_value
        SessionStateManager.set(key, current_dict)
        return current_dict
    
    @staticmethod
    def remove_from_dict(key: str, dict_key: Any) -> Dict[Any, Any]:
        """
        Remove a key from a dictionary in session state.
        
        Args:
            key: Session state key (must be a dict)
            dict_key: Dictionary key to remove
            
        Returns:
            Updated dictionary
        """
        current_dict = SessionStateManager.get(key, {})
        
        if not isinstance(current_dict, dict):
            logger.warning(f"Key '{key}' is not a dict")
            return {}
        
        if dict_key in current_dict:
            del current_dict[dict_key]
        
        SessionStateManager.set(key, current_dict)
        return current_dict
    
    @staticmethod
    def toggle(key: str) -> bool:
        """
        Toggle a boolean value in session state.
        
        Args:
            key: Session state key (must be a boolean)
            
        Returns:
            New boolean value
        """
        current_value = SessionStateManager.get(key, False)
        
        if not isinstance(current_value, bool):
            logger.warning(f"Key '{key}' is not a boolean, converting to boolean")
            current_value = bool(current_value)
        
        new_value = not current_value
        SessionStateManager.set(key, new_value)
        return new_value
    
    @staticmethod
    def increment(key: str, amount: Union[int, float] = 1) -> Union[int, float]:
        """
        Increment a numeric value in session state.
        
        Args:
            key: Session state key (must be numeric)
            amount: Amount to increment by
            
        Returns:
            New numeric value
        """
        current_value = SessionStateManager.get(key, 0)
        
        if not isinstance(current_value, (int, float)):
            logger.warning(f"Key '{key}' is not numeric, converting to numeric")
            try:
                current_value = float(current_value)
            except (ValueError, TypeError):
                current_value = 0
        
        new_value = current_value + amount
        SessionStateManager.set(key, new_value)
        return new_value
    
    @staticmethod
    def clear_all() -> None:
        """Clear all session state variables."""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
    
    @staticmethod
    def get_all() -> Dict[str, Any]:
        """
        Get all session state variables.
        
        Returns:
            dict: All session state variables
        """
        return dict(st.session_state)
    
    @staticmethod
    def get_keys() -> Set[str]:
        """
        Get all session state keys.
        
        Returns:
            set: All session state keys
        """
        return set(st.session_state.keys())
    
    @staticmethod
    def create_callback(key: str, value: Any) -> Callable[[], None]:
        """
        Create a callback function that sets a session state value.
        Useful for Streamlit widgets that use callbacks.
        
        Args:
            key: Session state key
            value: Value to set
            
        Returns:
            Callback function
        """
        def callback():
            SessionStateManager.set(key, value)
        return callback

# Alias for shorter usage
SSM = SessionStateManager
