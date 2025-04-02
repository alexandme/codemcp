#!/usr/bin/env python3

import difflib
import os

from ..file_utils import (
    async_open_text,
    check_file_path_and_permissions,
    check_git_tracking_for_existing_file,
    write_text_content,
)
from ..git import commit_changes
from ..line_endings import detect_line_endings, detect_repo_line_endings

# Import session_state from edit_file to ensure consistent auto_edit setting
from .edit_file import session_state

__all__ = [
    "write_file_content",
    "apply_write",
]


async def write_file_content(
    file_path: str, content: str, description: str = "", chat_id: str = ""
) -> str:
    """Write content to a file.

    If auto_edit is False (default), this function will generate a diff preview
    and return it with options to apply the change, enable auto mode, or skip.
    If auto_edit is True, changes will be applied immediately.

    Args:
        file_path: The absolute path to the file to write
        content: The content to write to the file
        description: Short description of the change
        chat_id: The unique ID of the current chat session

    Returns:
        A success message or a diff preview with options if auto_edit is False

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

    # If auto_edit is False, generate a diff and return it with options
    if not session_state["auto_edit"]:
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
        
        # Return the diff with options
        return (
            f"Proposed changes for {action} {file_path}:\n\n"
            f"{diff_text}\n\n"
            f"Options:\n"
            f"1. Apply this change\n"
            f"2. Apply this change and enable auto mode for future changes\n"
            f"3. Skip this change"
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
