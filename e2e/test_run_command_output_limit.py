#!/usr/bin/env python3

"""Tests for the output limitation in RunCommand."""

import os
import unittest

from codemcp.common import MAX_LINES_TO_READ, START_CONTEXT_LINES
from codemcp.testing import MCPEndToEndTestCase


class RunCommandOutputLimitTest(MCPEndToEndTestCase):
    """Test the output limitation in RunCommand."""

    async def test_verbose_output_truncation(self):
        """Test that RunCommand truncates verbose output to a reasonable size."""
        # Create a test directory
        test_dir = os.path.join(self.temp_dir.name, "test_directory")
        os.makedirs(test_dir, exist_ok=True)

        # Create a script that generates a lot of output
        script_path = os.path.join(self.temp_dir.name, "generate_output.sh")
        with open(script_path, "w") as f:
            f.write(
                """#!/bin/bash
# Generate a lot of output (more than MAX_LINES_TO_READ)
for i in $(seq 1 2000); do
    echo "Line $i: This is a test line to verify output truncation"
done
"""
            )
        os.chmod(script_path, 0o755)  # Make it executable

        # Create a codemcp.toml file
        config_path = os.path.join(self.temp_dir.name, "codemcp.toml")
        with open(config_path, "w") as f:
            f.write(
                """
[project]
name = "test-project"

[commands]
verbose = ["./generate_output.sh"]
"""
            )

        # Add files to git
        await self.git_run(["add", "."])
        await self.git_run(
            ["commit", "-m", "Add test files for output truncation test"]
        )

        async with self.create_client_session() as session:
            # First initialize project to get chat_id
            init_result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                    "user_prompt": "Test initialization for output limit test",
                    "subject_line": "test: initialize for output limit test",
                    "reuse_head_chat_id": False,
                },
            )

            # Extract chat_id from the init result
            chat_id = self.extract_chat_id_from_text(init_result_text)

            # Call the RunCommand tool with the verbose command
            result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "RunCommand",
                    "path": self.temp_dir.name,
                    "command": "verbose",
                    "chat_id": chat_id,
                },
            )

            # Verify the truncation message is present
            self.assertIn("output truncated", result_text)

            # Verify we kept the beginning context
            self.assertIn("Line 1:", result_text)
            self.assertIn(f"Line {START_CONTEXT_LINES}:", result_text)

            # Verify we have content from the end
            self.assertIn("Line 2000:", result_text)

            # Verify the total number of lines is reasonable
            lines = result_text.splitlines()

            # We should have more than START_CONTEXT_LINES but fewer than MAX_LINES_TO_READ + some overhead
            # The overhead accounts for other lines in the output like "Code verbose successful:" etc.
            self.assertGreater(len(lines), START_CONTEXT_LINES)
            self.assertLess(len(lines), MAX_LINES_TO_READ + 20)


if __name__ == "__main__":
    unittest.main()
