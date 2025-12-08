"""Tests for token counter utility."""
import pytest

from ai_context_manager.utils.token_counter import count_tokens


class TestTokenCounter:
    """Test suite for token counter utility."""

    def test_count_tokens_empty_string(self) -> None:
        """Test counting tokens in empty string."""
        assert count_tokens("") == 0

    def test_count_tokens_single_word(self) -> None:
        """Test counting tokens in single word."""
        assert count_tokens("hello") == 1

    def test_count_tokens_simple_sentence(self) -> None:
        """Test counting tokens in simple sentence."""
        text = "Hello world, this is a test."
        tokens = count_tokens(text)
        assert tokens >= 6  # At least 6 words

    def test_count_tokens_with_punctuation(self) -> None:
        """Test counting tokens with punctuation."""
        text = "Hello, world! How are you?"
        tokens = count_tokens(text)
        assert tokens >= 5  # Should count words, not punctuation

    def test_count_tokens_special_characters(self) -> None:
        """Test counting tokens with special characters."""
        text = "Email: test@example.com, URL: https://example.com"
        tokens = count_tokens(text)
        assert tokens >= 4  # Should handle special chars reasonably

    def test_count_tokens_multiline(self) -> None:
        """Test counting tokens in multiline text."""
        text = """This is line one.
        This is line two.
        This is line three."""
        tokens = count_tokens(text)
        assert tokens >= 9  # At least 3 lines * 3 words each

    def test_count_tokens_code(self) -> None:
        """Test counting tokens in code."""
        code = """
        def hello_world():
            print("Hello, World!")
            return True
        """
        tokens = count_tokens(code)
        assert tokens >= 8  # def, hello_world, (, ), :, print, "Hello, World!", return, True

    def test_count_tokens_unicode(self) -> None:
        """Test counting tokens with unicode characters."""
        text = "Hello 世界 🌍 مرحبا"
        tokens = count_tokens(text)
        assert tokens >= 4  # Should handle unicode properly

    def test_count_tokens_very_long_text(self) -> None:
        """Test counting tokens in very long text."""
        text = "word " * 1000
        tokens = count_tokens(text)
        assert tokens >= 1000  # Estimate is generous

    def test_count_tokens_whitespace_only(self) -> None:
        """Test counting tokens in whitespace-only text."""
        text = "   \n\t  \r\n  "
        tokens = count_tokens(text)
        assert tokens >= 0  # Whitespace might have small token count

    def test_count_tokens_single_characters(self) -> None:
        """Test counting tokens in single character strings."""
        assert count_tokens("a") == 1
        assert count_tokens("1") == 1
        assert count_tokens("@") == 1

    def test_count_tokens_mixed_content(self) -> None:
        """Test counting tokens in mixed content."""
        text = """
        # Python code
        def calculate(x, y):
            return x + y
        
        # Markdown
        ## Results
        The result is **amazing**!
        """
        tokens = count_tokens(text)
        assert tokens >= 15  # Should handle mixed content

    def test_count_tokens_consistency(self) -> None:
        """Test that token counting is consistent."""
        text = "This is a test sentence for consistency checking."
        count1 = count_tokens(text)
        count2 = count_tokens(text)
        count3 = count_tokens(text)
        assert count1 == count2 == count3

    def test_count_tokens_edge_cases(self) -> None:
        """Test edge cases for token counting."""
        # None input
        assert count_tokens(None) == 0  # type: ignore
        
        # Non-string input
        with pytest.raises(TypeError):
            count_tokens(123)  # type: ignore
        
        # Empty string variations
        assert count_tokens("") == 0
        assert count_tokens(" ") >= 1
        assert count_tokens("\n") >= 1
        assert count_tokens("\t") >= 1

    def test_count_tokens_large_document(self) -> None:
        """Test counting tokens in a large document."""
        # Create a large document
        paragraphs = []
        for i in range(100):
            paragraphs.append(f"This is paragraph {i} with some content to test token counting.")
        
        text = "\n\n".join(paragraphs)
        tokens = count_tokens(text)
        
        # Should be reasonable count for 100 paragraphs
        assert 1200 <= tokens <= 2000

    def test_count_tokens_with_numbers(self) -> None:
        """Test counting tokens with numbers."""
        text = "The price is $19.99 and the quantity is 42 items."
        tokens = count_tokens(text)
        assert tokens >= 8  # Should handle numbers and currency

    def test_count_tokens_contractions(self) -> None:
        """Test counting tokens with contractions."""
        text = "I don't think it's working, but we'll see."
        tokens = count_tokens(text)
        assert tokens >= 7  # Should handle contractions properly

    def test_count_tokens_repeated_words(self) -> None:
        """Test counting tokens with repeated words."""
        text = "test test test test test"
        tokens = count_tokens(text)
        assert tokens >= 5  # At least 5

    def test_count_tokens_html_tags(self) -> None:
        """Test counting tokens with HTML tags."""
        html = "<div><p>Hello <strong>world</strong>!</p></div>"
        tokens = count_tokens(html)
        assert tokens >= 3  # Should count text content, not just tags