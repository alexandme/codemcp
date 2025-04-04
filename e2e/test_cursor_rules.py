#!/usr/bin/env python3

import os
import unittest
from pathlib import Path

from codemcp.rules import (
    find_applicable_rules,
    match_file_with_glob,
)
from codemcp.testing import MCPEndToEndTestCase


class TestCursorRulesE2E(MCPEndToEndTestCase):
    async def asyncSetUp(self):
        # Call the parent setUp to initialize git repo and environment
        await super().asyncSetUp()

        self.repo_root = Path(self.temp_dir.name)

        # Create .cursor/rules directory structure
        self.rules_dir = self.repo_root / ".cursor" / "rules"
        os.makedirs(self.rules_dir, exist_ok=True)

        # Create a subdirectory structure for testing
        self.src_dir = self.repo_root / "src"
        self.components_dir = self.src_dir / "components"
        self.utils_dir = self.src_dir / "utils"
        self.tests_dir = self.repo_root / "tests"

        os.makedirs(self.components_dir, exist_ok=True)
        os.makedirs(self.utils_dir, exist_ok=True)
        os.makedirs(self.tests_dir, exist_ok=True)

        # Create some test files
        with open(self.components_dir / "Button.jsx", "w") as f:
            f.write("// Button component")

        with open(self.components_dir / "Input.tsx", "w") as f:
            f.write("// Input component")

        with open(self.utils_dir / "helpers.js", "w") as f:
            f.write("// Helper functions")

        with open(self.utils_dir / "date.js", "w") as f:
            f.write("// Date utilities")

        with open(self.tests_dir / "test_button.js", "w") as f:
            f.write("// Button tests")

        with open(self.repo_root / "config.json", "w") as f:
            f.write('{"name": "test-repo"}')

        # Create some test rule files
        self._create_rule(
            "jsx_components.mdc",
            "JSX Component Rule",
            ["**/*.jsx", "src/components/*.jsx"],
            False,
            "## JSX Component Guidelines\n\nUse functional components with hooks.",
        )

        self._create_rule(
            "js_files.mdc",
            "JavaScript Files Rule",
            ["*.js", "**/*.js"],
            False,
            "## JavaScript Guidelines\n\nUse ES6 features.",
        )

        self._create_rule(
            "config_rule.mdc",
            "Config Files Rule",
            ["*.json", "*.yaml", "*.yml"],
            False,
            "## Config Files Guidelines\n\nUse consistent formatting.",
        )

        self._create_rule(
            "all_files.mdc",
            "Global Rule",
            [],
            True,
            "## Global Guidelines\n\nFollow project conventions.",
        )

        # Create nested rules directory
        nested_dir = self.rules_dir / "typescript"
        os.makedirs(nested_dir, exist_ok=True)

        with open(nested_dir / "tsx_rule.mdc", "w") as f:
            f.write(
                """---
description: TypeScript JSX Rule
globs: *.tsx, **/*.tsx
alwaysApply: false
---
## TypeScript JSX Guidelines

Use interfaces for props."""
            )

        # Add all files to git so they're tracked
        await self.git_run(["add", "."])
        await self.git_run(["commit", "-m", "Add test files and rules"])

    def _create_rule(self, file_name, description, globs, always_apply, content):
        """Helper to create a rule file"""
        globs_str = ", ".join(globs)
        always_apply_str = "true" if always_apply else "false"

        with open(self.rules_dir / file_name, "w") as f:
            f.write(
                f"""---
description: {description}
globs: {globs_str}
alwaysApply: {always_apply_str}
---
{content}"""
            )

    async def test_match_file_with_glob_patterns(self):
        """Test various glob patterns with the match_file_with_glob function"""
        # Test basic extension matching
        self.assertTrue(match_file_with_glob("test.js", "*.js"))
        self.assertTrue(match_file_with_glob("helpers.js", "*.js"))

        # Get relative paths for testing to ensure more consistent matching
        button_jsx_path = os.path.relpath(
            str(self.components_dir / "Button.jsx"), self.repo_root
        )
        helpers_js_path = os.path.relpath(
            str(self.utils_dir / "helpers.js"), self.repo_root
        )
        config_json_path = os.path.relpath(
            str(self.repo_root / "config.json"), self.repo_root
        )

        # Test patterns with /**/
        self.assertTrue(match_file_with_glob(button_jsx_path, "**/*.jsx"))
        self.assertTrue(match_file_with_glob(helpers_js_path, "**/*.js"))

        # Make sure the relative paths work as expected
        self.assertTrue(button_jsx_path.startswith("src/components/"))
        self.assertTrue(helpers_js_path.startswith("src/utils/"))

        # Test directory-specific patterns
        self.assertTrue(match_file_with_glob(button_jsx_path, "src/components/*.jsx"))
        self.assertFalse(match_file_with_glob(helpers_js_path, "src/components/*.js"))

        # Test patterns with /**/
        self.assertTrue(match_file_with_glob(button_jsx_path, "src/**/*.jsx"))
        self.assertTrue(match_file_with_glob(helpers_js_path, "src/**/*.js"))

        # Test non-matching patterns
        self.assertFalse(match_file_with_glob(button_jsx_path, "*.js"))
        self.assertFalse(match_file_with_glob(helpers_js_path, "*.jsx"))

        # Test patterns with trailing /**
        self.assertTrue(match_file_with_glob(helpers_js_path, "src/**"))
        self.assertTrue(match_file_with_glob(button_jsx_path, "src/**"))
        self.assertFalse(match_file_with_glob(config_json_path, "src/**"))

    async def test_find_applicable_rules(self):
        """Test finding applicable rules based on file path"""
        # Test finding rules for a JSX file
        jsx_file_path = str(self.components_dir / "Button.jsx")
        applicable_rules, suggested_rules = find_applicable_rules(
            str(self.repo_root), jsx_file_path
        )

        # Should find the JSX component rule and the global rule
        self.assertEqual(len(applicable_rules), 2)
        rule_descriptions = [rule.description for rule in applicable_rules]
        self.assertIn("JSX Component Rule", rule_descriptions)
        self.assertIn("Global Rule", rule_descriptions)

        # Test finding rules for a JavaScript file
        js_file_path = str(self.utils_dir / "helpers.js")
        applicable_rules, suggested_rules = find_applicable_rules(
            str(self.repo_root), js_file_path
        )

        # Should find the JavaScript files rule and the global rule
        self.assertEqual(len(applicable_rules), 2)
        rule_descriptions = [rule.description for rule in applicable_rules]
        self.assertIn("JavaScript Files Rule", rule_descriptions)
        self.assertIn("Global Rule", rule_descriptions)

        # Test finding rules for a TSX file
        tsx_file_path = str(self.components_dir / "Input.tsx")
        applicable_rules, suggested_rules = find_applicable_rules(
            str(self.repo_root), tsx_file_path
        )

        # Should find the TypeScript JSX rule and the global rule
        self.assertEqual(len(applicable_rules), 2)
        rule_descriptions = [rule.description for rule in applicable_rules]
        self.assertIn("TypeScript JSX Rule", rule_descriptions)
        self.assertIn("Global Rule", rule_descriptions)

        # Test finding rules for a config file
        config_file_path = str(self.repo_root / "config.json")
        applicable_rules, suggested_rules = find_applicable_rules(
            str(self.repo_root), config_file_path
        )

        # Should find the config files rule and the global rule
        self.assertEqual(len(applicable_rules), 2)
        rule_descriptions = [rule.description for rule in applicable_rules]
        self.assertIn("Config Files Rule", rule_descriptions)
        self.assertIn("Global Rule", rule_descriptions)

        # Test finding rules with no file path (only always_apply rules)
        applicable_rules, suggested_rules = find_applicable_rules(str(self.repo_root))

        # Should only find the global rule
        self.assertEqual(len(applicable_rules), 1)
        self.assertEqual(applicable_rules[0].description, "Global Rule")

        # Should have suggested rules for all other rule files
        self.assertEqual(len(suggested_rules), 4)


if __name__ == "__main__":
    unittest.main()
