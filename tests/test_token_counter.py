"""Tests for the token counter module."""

import tempfile
from pathlib import Path
import pytest

from ai_context_manager.utils.token_counter import TokenCounter


class TestTokenCounter:
    """Test cases for the TokenCounter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)
        
        # Create test files
        self.create_test_files()
        
        # Create token counter instance
        self.counter = TokenCounter()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def create_test_files(self):
        """Create test files for token counting."""
        # Create Python file
        python_file = self.test_dir / "test.py"
        python_file.write_text('''#!/usr/bin/env python3
"""A test Python file for token counting."""

import os
import sys
from typing import List, Dict

class Calculator:
    """A simple calculator class."""
    
    def __init__(self):
        """Initialize the calculator."""
        self.history = []
    
    def add(self, a: int, b: int) -> int:
        """Add two numbers."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
    
    def multiply(self, a: int, b: int) -> int:
        """Multiply two numbers."""
        result = a * b
        self.history.append(f"{a} * {b} = {result}")
        return result

def main():
    """Main function."""
    calc = Calculator()
    print(calc.add(5, 3))
    print(calc.multiply(4, 7))

if __name__ == "__main__":
    main()
''')
        
        # Create JavaScript file
        js_file = self.test_dir / "test.js"
        js_file.write_text('''/**
 * A test JavaScript file
 */
class UserManager {
    constructor() {
        this.users = [];
    }
    
    addUser(name, email) {
        const user = {
            id: Date.now(),
            name: name,
            email: email,
            createdAt: new Date()
        };
        this.users.push(user);
        return user;
    }
    
    getUser(id) {
        return this.users.find(user => user.id === id);
    }
    
    listUsers() {
        return this.users.map(user => ({
            id: user.id,
            name: user.name,
            email: user.email
        }));
    }
}

// Usage
const manager = new UserManager();
const user1 = manager.addUser("Alice", "alice@example.com");
const user2 = manager.addUser("Bob", "bob@example.com");
console.log(manager.listUsers());
''')
        
        # Create Markdown file
        md_file = self.test_dir / "test.md"
        md_file.write_text('''# Test Documentation

This is a test markdown file for token counting purposes.

## Features

- Feature 1: Basic functionality
- Feature 2: Advanced features
- Feature 3: Integration capabilities

## Code Example

```python
def hello_world():
    print("Hello, World!")
    return True
```

## API Reference

### Function: `process_data`

Processes input data according to specified parameters.

**Parameters:**
- `data`: Input data to process
- `format`: Output format (default: "json")

**Returns:**
Processed data in the specified format.

## Conclusion

This concludes our test documentation.
''')
        
        # Create plain text file
        txt_file = self.test_dir / "test.txt"
        txt_file.write_text('''This is a plain text file.
It contains simple text without any special formatting.
The purpose is to test token counting on plain text.

Line 1: Hello world
Line 2: This is a test
Line 3: Token counting works
Line 4: For all file types
Line 5: Including plain text
''')
        
        # Create empty file
        empty_file = self.test_dir / "empty.py"
        empty_file.write_text("")
    
    def test_token_counter_initialization(self):
        """Test TokenCounter initialization."""
        counter = TokenCounter()
        assert counter.encoding_name == "cl100k_base"
        assert counter.encoding is not None
    
    def test_count_tokens_python(self):
        """Test token counting for Python file."""
        file_path = str(self.test_dir / "test.py")
        token_count = self.counter.count_tokens_in_file(file_path)
        
        assert isinstance(token_count, int)
        assert token_count > 0
        assert 100 < token_count < 300  # Reasonable range for this file
    
    def test_count_tokens_javascript(self):
        """Test token counting for JavaScript file."""
        file_path = str(self.test_dir / "test.js")
        token_count = self.counter.count_tokens_in_file(file_path)
        
        assert isinstance(token_count, int)
        assert token_count > 0
        assert 150 < token_count < 400  # Reasonable range for this file
    
    def test_count_tokens_markdown(self):
        """Test token counting for Markdown file."""
        file_path = str(self.test_dir / "test.md")
        token_count = self.counter.count_tokens_in_file(file_path)
        
        assert isinstance(token_count, int)
        assert token_count > 0
        assert 100 < token_count < 300  # Reasonable range for this file
    
    def test_count_tokens_plain_text(self):
        """Test token counting for plain text file."""
        file_path = str(self.test_dir / "test.txt")
        token_count = self.counter.count_tokens_in_file(file_path)
        
        assert isinstance(token_count, int)
        assert token_count > 0
        assert 50 < token_count < 150  # Reasonable range for this file
    
    def test_count_tokens_empty_file(self):
        """Test token counting for empty file."""
        file_path = str(self.test_dir / "empty.py")
        token_count = self.counter.count_tokens_in_file(file_path)
        
        assert isinstance(token_count, int)
        assert token_count == 0
    
    def test_count_tokens_string(self):
        """Test token counting for string content."""
        test_string = "This is a test string for token counting."
        token_count = self.counter.count_tokens(test_string)
        
        assert isinstance(token_count, int)
        assert token_count > 0
        assert token_count == 9  # Expected for this string
    
    def test_count_tokens_empty_string(self):
        """Test token counting for empty string."""
        token_count = self.counter.count_tokens("")
        assert token_count == 0
    
    def test_count_tokens_unicode(self):
        """Test token counting with Unicode characters."""
        unicode_string = "Hello 世界 🌍 Café résumé"
        token_count = self.counter.count_tokens(unicode_string)
        
        assert isinstance(token_count, int)
        assert token_count > 0
    
    def test_count_tokens_special_characters(self):
        """Test token counting with special characters."""
        special_string = '''
        Special chars: !@#$%^&*()_+-=[]{}|;':",./<>?
        Code: `print("Hello")`
        Math: ∑∏∫∂
        '''
        token_count = self.counter.count_tokens(special_string)
        
        assert isinstance(token_count, int)
        assert token_count > 0
    
    def test_count_tokens_multiple_files(self):
        """Test counting tokens across multiple files."""
        files = [
            str(self.test_dir / "test.py"),
            str(self.test_dir / "test.js"),
            str(self.test_dir / "test.md"),
            str(self.test_dir / "test.txt")
        ]
        
        total_tokens = self.counter.count_tokens_in_files(files)
        
        assert isinstance(total_tokens, int)
        assert total_tokens > 0
        assert total_tokens > 300  # Should be larger than any single file
    
    def test_count_tokens_nonexistent_file(self):
        """Test handling of non-existent file."""
        file_path = str(self.test_dir / "nonexistent.py")
        
        with pytest.raises(FileNotFoundError):
            self.counter.count_tokens_in_file(file_path)
    
    def test_count_tokens_binary_file(self):
        """Test handling of binary file."""
        # Create binary file
        binary_file = self.test_dir / "binary.dat"
        binary_file.write_bytes(b'\x00\x01\x02\x03\x04\x05')
        
        file_path = str(binary_file)
        
        # Should handle gracefully
        try:
            token_count = self.counter.count_tokens_in_file(file_path)
            # Either return 0 or raise appropriate exception
            assert isinstance(token_count, int)
        except Exception as e:
            # Should raise meaningful exception
            assert "binary" in str(e).lower() or "decode" in str(e).lower()
    
    def test_count_tokens_large_file(self):
        """Test token counting for large file."""
        # Create large file
        large_file = self.test_dir / "large.py"
        large_content = 'print("Hello World")\n' * 1000
        large_file.write_text(large_content)
        
        file_path = str(large_file)
        token_count = self.counter.count_tokens_in_file(file_path)
        
        assert isinstance(token_count, int)
        assert token_count > 1000
    
    def test_count_tokens_different_encodings(self):
        """Test token counting with different text encodings."""
        # Create file with UTF-8 encoding
        utf8_file = self.test_dir / "utf8.txt"
        utf8_file.write_text("UTF-8 content: 世界 🌍", encoding='utf-8')
        
        token_count = self.counter.count_tokens_in_file(str(utf8_file))
        assert isinstance(token_count, int)
        assert token_count > 0
    
    def test_count_tokens_whitespace_variations(self):
        """Test token counting with different whitespace patterns."""
        test_cases = [
            "No extra spaces",
            "  Leading spaces",
            "Trailing spaces  ",
            "Multiple   spaces   between   words",
            "\tTab\tseparated\tcontent",
            "\nNewline\nseparated\ncontent\n",
            "Mixed\t \nwhitespace\t \ncontent"
        ]
        
        for test_string in test_cases:
            token_count = self.counter.count_tokens(test_string)
            assert isinstance(token_count, int)
            assert token_count >= 1
    
    def test_count_tokens_code_blocks(self):
        """Test token counting for code blocks."""
        code_block = '''
        ```python
        def example():
            """Example function."""
            return "Hello, World!"
        ```
        
        ```javascript
        function example() {
            return "Hello, World!";
        }
        ```
        '''
        
        token_count = self.counter.count_tokens(code_block)
        assert isinstance(token_count, int)
        assert token_count > 10
    
    def test_count_tokens_html_content(self):
        """Test token counting for HTML content."""
        html_content = '''
        <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <h1>Hello World</h1>
            <p>This is a test paragraph.</p>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
        </body>
        </html>
        '''
        
        token_count = self.counter.count_tokens(html_content)
        assert isinstance(token_count, int)
        assert token_count > 10
    
    def test_count_tokens_json_content(self):
        """Test token counting for JSON content."""
        json_content = '''
        {
            "name": "test",
            "version": "1.0.0",
            "dependencies": {
                "python": ">=3.8",
                "packages": ["numpy", "pandas"]
            },
            "config": {
                "debug": true,
                "max_items": 100
            }
        }
        '''
        
        token_count = self.counter.count_tokens(json_content)
        assert isinstance(token_count, int)
        assert token_count > 10
    
    def test_count_tokens_sql_content(self):
        """Test token counting for SQL content."""
        sql_content = '''
        SELECT 
            users.id,
            users.name,
            users.email,
            COUNT(orders.id) as order_count
        FROM users
        LEFT JOIN orders ON users.id = orders.user_id
        WHERE users.active = true
        GROUP BY users.id, users.name, users.email
        ORDER BY order_count DESC
        LIMIT 10;
        '''
        
        token_count = self.counter.count_tokens(sql_content)
        assert isinstance(token_count, int)
        assert token_count > 10
    
    def test_count_tokens_yaml_content(self):
        """Test token counting for YAML content."""
        yaml_content = '''
        name: test-project
        version: 1.0.0
        description: A test project
        dependencies:
          - python>=3.8
          - numpy>=1.20.0
          - pandas>=1.3.0
        config:
          debug: true
          max_items: 100
          nested:
            key1: value1
            key2: value2
        '''
        
        token_count = self.counter.count_tokens(yaml_content)
        assert isinstance(token_count, int)
        assert token_count > 10
    
    def test_count_tokens_repeated_content(self):
        """Test token counting with repeated content."""
        repeated_content = "This is repeated. " * 100
        
        token_count = self.counter.count_tokens(repeated_content)
        assert isinstance(token_count, int)
        assert token_count > 0
    
    def test_count_tokens_very_long_words(self):
        """Test token counting with very long words."""
        long_word = "a" * 1000
        token_count = self.counter.count_tokens(long_word)
        assert isinstance(token_count, int)
        assert token_count > 0
    
    def test_count_tokens_mixed_case(self):
        """Test token counting with mixed case text."""
        mixed_case = '''
        This Is A Test With Mixed Case Words.
        SOME WORDS ARE ALL CAPS.
        some words are all lowercase.
        Some Words Are Title Case.
        '''
        
        token_count = self.counter.count_tokens(mixed_case)
        assert isinstance(token_count, int)
        assert token_count > 10
    
    def test_count_tokens_numbers_and_dates(self):
        """Test token counting with numbers and dates."""
        numeric_content = '''
        Numbers: 123, 456.78, -90, 1.23e4
        Dates: 2023-12-25, 12/25/2023, 25-12-2023
        Times: 14:30:00, 2:30 PM
        Currency: $1,234.56, €500.00, £100.00
        '''
        
        token_count = self.counter.count_tokens(numeric_content)
        assert isinstance(token_count, int)
        assert token_count > 10
    
    def test_count_tokens_email_and_urls(self):
        """Test token counting with emails and URLs."""
        contact_content = '''
        Contact us at:
        Email: support@example.com
        Website: https://www.example.com
        Documentation: https://docs.example.com/api/v1
        Repository: https://github.com/user/repo
        '''
        
        token_count = self.counter.count_tokens(contact_content)
        assert isinstance(token_count, int)
        assert token_count > 10
    
    def test_count_tokens_performance(self):
        """Test token counting performance with moderately large content."""
        # Create moderately large content
        large_content = "This is a test sentence. " * 1000
        
        import time
        start_time = time.time()
        
        token_count = self.counter.count_tokens(large_content)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert isinstance(token_count, int)
        assert token_count > 0
        assert duration < 1.0  # Should complete quickly
    
    def test_count_tokens_consistency(self):
        """Test that token counting is consistent across multiple calls."""
        test_string = "This is a consistent test string."
        
        count1 = self.counter.count_tokens(test_string)
        count2 = self.counter.count_tokens(test_string)
        count3 = self.counter.count_tokens(test_string)
        
        assert count1 == count2 == count3
    
    def test_count_tokens_edge_cases(self):
        """Test token counting edge cases."""
        edge_cases = [
            "",  # Empty string
            " ",  # Single space
            "\n",  # Single newline
            "\t",  # Single tab
            "a",  # Single character
            ".",  # Single punctuation
            "123",  # Numbers only
            "   ",  # Multiple spaces
            "\n\n\n",  # Multiple newlines
            "a\nb\tc d",  # Mixed whitespace
        ]
        
        for test_case in edge_cases:
            token_count = self.counter.count_tokens(test_case)
            assert isinstance(token_count, int)
            assert token_count >= 0
    
    def test_count_tokens_encoding_error_handling(self):
        """Test handling of encoding errors."""
        # Create file with invalid UTF-8 sequence
        invalid_file = self.test_dir / "invalid.txt"
        invalid_file.write_bytes(b'\xff\xfe\x00\x00invalid utf-8')
        
        try:
            token_count = self.counter.count_tokens_in_file(str(invalid_file))
            # Should handle gracefully
            assert isinstance(token_count, int)
        except Exception as e:
            # Should raise meaningful exception
            assert "encoding" in str(e).lower() or "decode" in str(e).lower()
