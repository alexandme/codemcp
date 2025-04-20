"""
Test for the glob_pattern module's pattern matching functionality.
"""

from codemcp import glob_pattern as glob


def test_gitignore_simple_asterisk():
    """Test simple * pattern with gitignore behavior."""
    # * should match anything except slash
    assert glob.match("*.txt", "file1.txt")
    assert glob.match("*.txt", "a.txt")
    assert not glob.match("*.txt", "dir/file.txt")
    assert not glob.match("*.txt", "file.py")


def test_gitignore_question_mark():
    """Test ? pattern with gitignore behavior."""
    # ? should match any single character except slash
    assert glob.match("file?.txt", "file1.txt")
    assert glob.match("file?.txt", "fileA.txt")
    assert not glob.match("file?.txt", "file12.txt")
    assert not glob.match("file?.txt", "file.txt")
    assert not glob.match("file?.txt", "dir/file1.txt")


def test_gitignore_character_class():
    """Test character class patterns with gitignore behavior."""
    # [abc] should match any character in the brackets
    assert glob.match("file[123].txt", "file1.txt")
    assert glob.match("file[123].txt", "file2.txt")
    assert not glob.match("file[123].txt", "file4.txt")

    # [!abc] should match any character not in the brackets
    assert glob.match("file[!123].txt", "file4.txt")
    assert glob.match("file[!123].txt", "fileA.txt")
    assert not glob.match("file[!123].txt", "file1.txt")

    # [a-z] should match any character in the range
    assert glob.match("file[a-z].txt", "filea.txt")
    assert glob.match("file[a-z].txt", "filez.txt")
    assert not glob.match("file[a-z].txt", "file1.txt")
    assert not glob.match("file[a-z].txt", "fileA.txt")


def test_gitignore_leading_double_asterisk():
    """Test leading **/ pattern with gitignore behavior."""
    # **/ should match in all directories
    assert glob.match("**/file.txt", "file.txt")
    assert glob.match("**/file.txt", "a/file.txt")
    assert glob.match("**/file.txt", "a/b/file.txt")
    assert not glob.match("**/file.txt", "file1.txt")
    assert not glob.match("**/file.txt", "a/file1.txt")

    # **/foo/bar should match bar anywhere directly under foo
    assert glob.match("**/a/file.txt", "a/file.txt")
    assert glob.match("**/a/file.txt", "x/a/file.txt")
    assert not glob.match("**/a/file.txt", "a/b/file.txt")


def test_gitignore_trailing_double_asterisk():
    """Test trailing /** pattern with gitignore behavior."""
    # /** should match everything inside
    assert glob.match("a/**", "a/file.txt")
    assert glob.match("a/**", "a/b/file.txt")
    assert glob.match("a/**", "a/b/c/deep.txt")
    assert not glob.match("a/**", "file.txt")
    assert not glob.match("a/**", "x/file.txt")


def test_gitignore_middle_double_asterisk():
    """Test /**/pattern with gitignore behavior."""
    # /**/ should match zero or more directories
    assert glob.match("a/**/file.txt", "a/file.txt")
    assert glob.match("a/**/file.txt", "a/b/file.txt")
    assert glob.match("a/**/file.txt", "a/b/c/file.txt")
    assert not glob.match("a/**/file.txt", "file.txt")
    assert not glob.match("a/**/file.txt", "a/file.py")


def test_editorconfig_braces():
    """Test editorconfig brace expansion."""
    # {s1,s2,s3} should match any of the strings
    assert glob.match("file.{txt,py}", "file.txt", editorconfig=True)
    assert glob.match("file.{txt,py}", "file.py", editorconfig=True)
    assert not glob.match("file.{txt,py}", "file.md", editorconfig=True)

    # {num1..num2} should match any integer in the range
    assert glob.match("file{1..3}.txt", "file1.txt", editorconfig=True)
    assert glob.match("file{1..3}.txt", "file2.txt", editorconfig=True)
    assert glob.match("file{1..3}.txt", "file3.txt", editorconfig=True)
    assert not glob.match("file{1..3}.txt", "file4.txt", editorconfig=True)
    assert not glob.match("file{1..3}.txt", "file0.txt", editorconfig=True)

    # Negative ranges
    assert glob.match("file{-1..1}.txt", "file-1.txt", editorconfig=True)
    assert glob.match("file{-1..1}.txt", "file0.txt", editorconfig=True)
    assert glob.match("file{-1..1}.txt", "file1.txt", editorconfig=True)

    # Braces can be nested
    assert glob.match("file{a,{b,c}}.txt", "filea.txt", editorconfig=True)
    assert glob.match("file{a,{b,c}}.txt", "fileb.txt", editorconfig=True)
    assert glob.match("file{a,{b,c}}.txt", "filec.txt", editorconfig=True)


def test_editorconfig_asterisk():
    """Test editorconfig asterisk behavior."""
    # * should match any string including path separators
    assert glob.match("*.txt", "file.txt", editorconfig=True)
    assert glob.match("*.txt", "dir/file.txt", editorconfig=True)
    assert not glob.match("*.txt", "file.py", editorconfig=True)


def test_editorconfig_double_asterisk():
    """Test editorconfig ** behavior."""
    # ** should match any string
    assert glob.match("**", "file.txt", editorconfig=True)
    assert glob.match("**", "dir/file.txt", editorconfig=True)
    assert glob.match("**", "dir/subdir/file.txt", editorconfig=True)

    # More specific pattern with **
    assert glob.match("a/**/file.txt", "a/file.txt", editorconfig=True)
    assert glob.match("a/**/file.txt", "a/b/file.txt", editorconfig=True)
    assert glob.match("a/**/file.txt", "a/b/c/file.txt", editorconfig=True)


def test_escaped_characters():
    """Test escaped special characters in patterns."""
    # Escaped special characters should be treated as literals
    assert glob.match(r"\*.txt", "*.txt")
    assert not glob.match(r"\*.txt", "a.txt")

    assert glob.match(r"\?.txt", "?.txt")
    assert not glob.match(r"\?.txt", "a.txt")

    assert glob.match(r"\[abc\].txt", "[abc].txt")
    assert not glob.match(r"\[abc\].txt", "a.txt")


def test_combined_features():
    """Test combining different pattern features."""
    # Combining various features
    assert glob.match("**/[a-z]/{file,test}.{txt,py}", "a/file.txt", editorconfig=True)
    assert glob.match(
        "**/[a-z]/{file,test}.{txt,py}", "x/y/z/test.py", editorconfig=True
    )
    assert not glob.match(
        "**/[a-z]/{file,test}.{txt,py}", "1/file.txt", editorconfig=True
    )
    assert not glob.match(
        "**/[a-z]/{file,test}.{txt,py}", "a/other.txt", editorconfig=True
    )


def test_filter_function():
    """Test the filter function."""
    paths = [
        "file1.txt",
        "file2.py",
        "dir/file.txt",
        "dir/file.py",
        "dir/subdir/file.txt",
    ]

    # Filter with a single pattern
    result = glob.filter(["*.txt"], paths)
    assert result == ["file1.txt"]

    # Filter with multiple patterns
    result = glob.filter(["*.txt", "*.py"], paths)
    assert result == ["file1.txt", "file2.py"]

    # Filter with gitignore-specific pattern
    result = glob.filter(["**/file.txt"], paths)
    assert result == ["dir/file.txt", "dir/subdir/file.txt"]


def test_find_function():
    """Test the find function with a list of paths."""
    # Define test paths
    test_paths = [
        "file1.txt",
        "file2.py",
        "a/file.txt",
        "a/file.py",
        "a/b/file.txt",
        "a/b/file.py",
        "a/b/c/deep.txt",
        "a/d/file.txt",
        "a/d/e/deep.py",
        "x/file.txt",
        "x/y/file.py",
        "x/y/z/deep.txt",
    ]

    # Find with a simple pattern
    result = glob.find(["*.txt"], "", paths=test_paths)
    assert len(result) == 1
    assert result[0] == "file1.txt"

    # Find with gitignore-specific pattern
    result = glob.find(["**/file.txt"], "", paths=test_paths)
    # Should find a/file.txt, a/b/file.txt, a/d/file.txt, x/file.txt
    assert len(result) == 4
    assert all(path.endswith("/file.txt") or path == "file.txt" for path in result)

    # Find with combination of patterns
    result = glob.find(["a/**/*.py"], "", paths=test_paths)
    assert len(result) == 3
    assert "a/file.py" in result
    assert "a/b/file.py" in result
    assert "a/d/e/deep.py" in result


def test_make_matcher_function():
    """Test the make_matcher function."""
    # Create a matcher function
    matcher = glob.make_matcher("*.txt")

    # Test the matcher
    assert matcher("file.txt")
    assert not matcher("file.py")
    assert not matcher("dir/file.txt")

    # Create a matcher with gitignore-specific behavior
    matcher = glob.make_matcher("**/file.txt")

    # Test the matcher
    assert matcher("file.txt")
    assert matcher("dir/file.txt")
    assert matcher("dir/subdir/file.txt")
    assert not matcher("file.py")


def test_complex_patterns():
    """Test more complex pattern combinations."""
    # Mix of ** and character classes
    assert glob.match("**/*[0-9].txt", "file1.txt")
    assert glob.match("**/*[0-9].txt", "dir/file2.txt")
    assert glob.match("**/*[0-9].txt", "a/b/c/file3.txt")
    assert not glob.match("**/*[0-9].txt", "file.txt")

    # Multiple ** patterns
    assert glob.match("**/a/**/b/**/c.txt", "a/b/c.txt")
    assert glob.match("**/a/**/b/**/c.txt", "x/a/y/b/z/c.txt")
    assert glob.match("**/a/**/b/**/c.txt", "a/1/2/b/c.txt")
    assert not glob.match("**/a/**/b/**/c.txt", "a/b/d.txt")

    # Combinations with editorconfig features
    assert glob.match("**/{a,b}/**/*.{txt,md}", "a/x/y/file.txt", editorconfig=True)
    assert glob.match("**/{a,b}/**/*.{txt,md}", "b/file.md", editorconfig=True)
    assert not glob.match("**/{a,b}/**/*.{txt,md}", "c/file.txt", editorconfig=True)
    assert not glob.match("**/{a,b}/**/*.{txt,md}", "a/file.py", editorconfig=True)


def test_edge_cases():
    """Test edge cases and corner cases."""
    # Empty pattern
    assert glob.match("", "")
    assert not glob.match("", "file.txt")

    # Empty path
    assert not glob.match("*.txt", "")

    # Just asterisks
    assert glob.match("*", "file.txt")
    assert glob.match("*", "directory")
    assert not glob.match("*", "nested/file.txt")

    # Just double asterisks
    assert glob.match("**", "file.txt")
    assert glob.match("**", "nested/file.txt", editorconfig=True)

    # Pattern with just a slash
    assert glob.match("/", "/")
    assert not glob.match("/", "file.txt")

    # Pattern with trailing slash
    assert glob.match("dir/", "dir/")
    assert not glob.match("dir/", "dir")
    assert not glob.match("dir/", "dir/file.txt")

    # Invalid character class that isn't closed
    assert not glob.match("file[abc.txt", "fileabc.txt")

    # Escaping backslashes
    assert glob.match(r"file\\.txt", "file\\.txt")
    assert not glob.match(r"file\\.txt", "file.txt")
