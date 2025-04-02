#!/usr/bin/env python3

import json
import tempfile
import uuid
from pathlib import Path

# Create a directory for pending changes
PENDING_CHANGES_DIR = Path(tempfile.gettempdir()) / "codemcp_pending_changes"
PENDING_CHANGES_DIR.mkdir(exist_ok=True)

# Dictionary to track pending changes in memory
pending_changes = {}

# Track whether to prompt for commit
commit_prompt_enabled = True

def get_current_change_id(chat_id: str) -> str | None:
    """Get the current change ID for a chat session.
    
    Args:
        chat_id: The chat ID to get the current change for
        
    Returns:
        The change ID if found, None otherwise
    """
    id_file = PENDING_CHANGES_DIR / f"current_{chat_id}.txt"
    if not id_file.exists():
        return None
        
    with open(id_file, "r") as f:
        return f.read().strip()

def set_current_change_id(chat_id: str, change_id: str) -> None:
    """Set the current change ID for a chat session.
    
    Args:
        chat_id: The chat ID to set the current change for
        change_id: The change ID to set
    """
    id_file = PENDING_CHANGES_DIR / f"current_{chat_id}.txt"
    with open(id_file, "w") as f:
        f.write(change_id)

def clear_current_change_id(chat_id: str) -> None:
    """Clear the current change ID for a chat session.
    
    Args:
        chat_id: The chat ID to clear the current change for
    """
    id_file = PENDING_CHANGES_DIR / f"current_{chat_id}.txt"
    if id_file.exists():
        id_file.unlink()

def store_pending_change(change_info: dict) -> str:
    """Store a pending change and return its ID.
    
    Args:
        change_info: Dictionary containing change information
        
    Returns:
        The unique ID of the stored change
    """
    change_id = str(uuid.uuid4())
    
    # Store in memory
    pending_changes[change_id] = change_info
    
    # Store on disk
    change_file = PENDING_CHANGES_DIR / f"{change_id}.json"
    with open(change_file, "w") as f:
        json.dump(change_info, f, indent=2)
        
    return change_id

def get_pending_change(change_id: str) -> dict | None:
    """Get a pending change by ID.
    
    Args:
        change_id: The ID of the change to get
        
    Returns:
        The change information if found, None otherwise
    """
    # First check memory
    if change_id in pending_changes:
        return pending_changes[change_id]
        
    # Then check disk
    change_file = PENDING_CHANGES_DIR / f"{change_id}.json"
    if not change_file.exists():
        return None
        
    with open(change_file, "r") as f:
        return json.load(f)

def remove_pending_change(change_id: str) -> None:
    """Remove a pending change.
    
    Args:
        change_id: The ID of the change to remove
    """
    # Remove from memory
    if change_id in pending_changes:
        del pending_changes[change_id]
        
    # Remove from disk
    change_file = PENDING_CHANGES_DIR / f"{change_id}.json"
    if change_file.exists():
        change_file.unlink()

def set_commit_prompt(enabled: bool = True) -> str:
    """Enable or disable commit prompting.
    
    Args:
        enabled: Whether to enable commit prompting
        
    Returns:
        A confirmation message
    """
    global commit_prompt_enabled
    commit_prompt_enabled = enabled
    
    if enabled:
        return "Commit prompting enabled. You will be asked to confirm before changes are committed."
    else:
        return "Commit prompting disabled. Changes will be committed automatically after approval."

def is_commit_prompt_enabled() -> bool:
    """Check if commit prompting is enabled.
    
    Returns:
        True if commit prompting is enabled, False otherwise
    """
    return commit_prompt_enabled