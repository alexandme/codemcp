#!/usr/bin/env python3

import difflib
import os
import json
import uuid
from pathlib import Path

from ..file_utils import (
    async_open_text,
    check_file_path_and_permissions,
    check_git_tracking_for_existing_file,
    write_text_content,
)
from ..git import commit_changes
from ..line_endings import detect_line_endings, detect_repo_line_endings

# Use the same pending changes system as edit_file
from .edit_file import PENDING_CHANGES_DIR, pending_changes

__all__ = [
    "write_file_content",
]


async def write_file_content(
    file_path: str, content: str, description: str = "", chat_id: str = "", preview: bool = True
) -> str:
    """Write content to a file.

    In preview mode (default), this function generates a diff of the proposed changes
    without applying them. A change_id is created and returned which can be used with
    approve_change or reject_change to apply or discard the changes.

    If preview is False, changes are applied immediately.

    Args:
        file_path: The absolute path to the file to write
        content: The content to write to the file
        description: Short description of the change
        chat_id: The unique ID of the current chat session
        preview: Whether to preview changes without applying them (default: True)

    Returns:
        A success message or a diff preview in preview mode

    Note:
        This function allows creating new files that don't exist yet.
        For existing files, it will reject attempts to write to files that are not tracked by git.
        Files must be tracked in the git repository before they can be modified.

    """
    # Validate file path and permissions
    is_valid, error_message = await check_file_path_and_permissions(file_path)
    if not is_valid:
        raise ValueError(error_message)

    # Check git tracking for existing files
    is_tracked, track_error = await check_git_tracking_for_existing_file(
        file_path, chat_id
    )
    if not is_tracked:
        raise ValueError(track_error)

    # Determine line endings
    old_file_exists = os.path.exists(file_path)

    # Get the current content for diff if file exists
    current_content = ""
    if old_file_exists:
        line_endings = await detect_line_endings(file_path)
        current_content = await async_open_text(file_path, encoding="utf-8")
    else:
        line_endings = detect_repo_line_endings(os.path.dirname(file_path))
        # Ensure directory exists for new files
        directory = os.path.dirname(file_path)
        os.makedirs(directory, exist_ok=True)

    # If in preview mode, generate a diff and store for later approval
    if preview:
        # Generate the diff
        current_lines = current_content.splitlines() if current_content else []
        new_lines = content.splitlines()
        
        diff = list(difflib.unified_diff(
            current_lines,
            new_lines,
            fromfile=f"a/{os.path.basename(file_path)}",
            tofile=f"b/{os.path.basename(file_path)}",
            lineterm="",
        ))
        
        diff_text = "\n".join(diff)
        
        action = "updating" if old_file_exists else "creating"
        
        # Create a unique ID for this change
        change_id = str(uuid.uuid4())
        
        # Store the change in memory and on disk
        change_info = {
            "type": "write",
            "file_path": file_path,
            "content": content,
            "description": description,
            "chat_id": chat_id,
            "line_endings": line_endings
        }
        
        pending_changes[change_id] = change_info
        
        # Also store to disk for persistence
        change_file = PENDING_CHANGES_DIR / f"{change_id}.json"
        with open(change_file, "w") as f:
            json.dump(change_info, f, indent=2)
        
        # Return the diff with instructions on how to approve or reject
        return (
            f"Proposed changes for {action} {file_path}:\n\n"
            f"{diff_text}\n\n"
            f"To apply this change, use: approve_change(\"{change_id}\")\n"
            f"To reject this change, use: reject_change(\"{change_id}\")\n"
            f"Change ID: {change_id}"
        )

    # Write the content with UTF-8 encoding and proper line endings
    await write_text_content(file_path, content, "utf-8", line_endings)

    # Commit the changes
    git_message = ""
    success, message = await commit_changes(file_path, description, chat_id)
    if success:
        git_message = f"\nChanges committed to git: {description}"
    else:
        git_message = f"\nFailed to commit changes to git: {message}"

    return f"Successfully wrote to {file_path}{git_message}"


async def apply_write(
    file_path: str, 
    content: str, 
    description: str = "", 
    chat_id: str = ""
) -> str:
    """Apply a previously proposed write operation to a file.

    This function is called after write_file_content when the user approves a change.
    It performs the same write operation but skips the diff generation and approval step.

    Args:
        file_path: The absolute path to the file to write
        content: The content to write to the file
        description: Short description of the change
        chat_id: The unique ID of the current chat session

    Returns:
        A success message
    """
    # Temporarily set auto_edit to True
    original_auto_edit = session_state["auto_edit"]
    session_state["auto_edit"] = True
    
    try:
        result = await write_file_content(
            file_path,
            content,
            description,
            chat_id,
        )
    finally:
        # Restore original auto_edit setting
        session_state["auto_edit"] = original_auto_edit
    
    return result
