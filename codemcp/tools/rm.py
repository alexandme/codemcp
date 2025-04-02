#!/usr/bin/env python3

import logging
import os
import pathlib

from ..common import normalize_file_path
from ..git import get_repository_root
from ..shell import run_command # Keep run_command for git ls-files and git rm

__all__ = [
    "rm_file",
]


async def rm_file(
    path: str,
    description: str,
    chat_id: str = "",
) -> str:
    """Remove a file using git rm.

    Args:
        path: The path to the file to remove (can be absolute or relative to repository root)
        description: Short description of why the file is being removed
        chat_id: The unique ID of the current chat session

    Returns:
        A string containing the result of the removal operation
    """
    # Use the directory from the path as our starting point
    file_path = normalize_file_path(path)
    dir_path = os.path.dirname(file_path) if os.path.dirname(file_path) else "."

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File does not exist: {path}")

    if not os.path.isfile(file_path):
        raise ValueError(f"Path is not a file: {path}")

    # Get git repository root
    git_root = await get_repository_root(dir_path)
    # Ensure paths are absolute and resolve any symlinks
    file_path_resolved = os.path.realpath(file_path)
    git_root_resolved = os.path.realpath(git_root)

    # Use pathlib to check if the file is within the git repo
    # This handles path traversal correctly on all platforms
    try:
        # Convert to Path objects
        file_path_obj = pathlib.Path(file_path_resolved)
        git_root_obj = pathlib.Path(git_root_resolved)

        # Check if file is inside the git repo using Path.relative_to
        # This will raise ValueError if file_path is not inside git_root
        file_path_obj.relative_to(git_root_obj)
    except ValueError:
        msg = f"Path {file_path} is not within the git repository at {git_root}"
        logging.error(msg)
        raise ValueError(msg)

    # Get the relative path using pathlib
    rel_path = os.path.relpath(file_path_resolved, git_root_resolved)
    logging.info(f"Using relative path: {rel_path}")

    # Check if the file is tracked by git from the git root
    await run_command(
        ["git", "ls-files", "--error-unmatch", rel_path],
        cwd=git_root_resolved,
        check=True,
        capture_output=True,
        text=True,
    )

    # If we get here, the file is tracked by git, so we can remove it
    await run_command(
        ["git", "rm", rel_path],
        cwd=git_root_resolved,
        check=True,
        capture_output=True,
        text=True,
    )

    # Since git rm already stages the change, we just need to inform the user.
    return (
        f"Successfully removed file {rel_path}. Changes staged. Use CommitChanges tool to commit."
    )
