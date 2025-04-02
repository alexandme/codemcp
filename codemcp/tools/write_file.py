#!/usr/bin/env python3

import os
from pathlib import Path

from ..file_utils import (
    async_open_text,
    check_file_path_and_permissions,
    check_git_tracking_for_existing_file,
    write_text_content,
)
from ..line_endings import detect_line_endings, detect_repo_line_endings
from ..shell import run_command # Import run_command for git add

__all__ = [
    "write_file_content",
]


async def write_file_content(
    file_path: str, content: str, description: str = "", chat_id: str = "", preview: bool = False # Preview removed
) -> str:
    """Write content to a file.


    Args:
        file_path: The absolute path to the file to write
        content: The content to write to the file
        description: Short description of the change
        chat_id: The unique ID of the current chat session
        preview: (Deprecated) This parameter is ignored. Changes are always applied directly.

    Returns:
        A success message indicating changes are staged.

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

    # Write the content with UTF-8 encoding and proper line endings
    await write_text_content(file_path, content, "utf-8", line_endings)

    # Stage the changes
    await run_command(
        ["git", "add", file_path],
        cwd=os.path.dirname(file_path),
        check=True,
        capture_output=True,
        text=True,
    )
    git_message = "\nChanges staged. Use CommitChanges tool to commit."

    return f"Successfully wrote to {file_path}{git_message}"
