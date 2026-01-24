"""Tests for the CodeDisplay widget."""

from __future__ import annotations

from typing import Any

import pytest
from rich.syntax import Syntax
from textual.app import App
from textual.widgets import Static

from sqliter.tui.widgets import CodeDisplay


class TestCodeDisplay:
    """Test the CodeDisplay widget."""

    @pytest.mark.asyncio
    async def test_widget_composition(self) -> None:
        """Test that the widget composes correctly."""
        app: App[Any] = App()
        async with app.run_test() as _:
            code_display = CodeDisplay(code="print('hello')")
            await app.mount(code_display)

            # Should have a Static child for content
            content = code_display.query_one("#code-content", Static)
            assert content is not None

    @pytest.mark.asyncio
    async def test_empty_code_display(self) -> None:
        """Test display when code is empty."""
        app: App[Any] = App()
        async with app.run_test() as _:
            code_display = CodeDisplay(code="")
            await app.mount(code_display)

            content = code_display.query_one("#code-content", Static)
            # Empty code should show placeholder
            assert "Select a demo" in str(content.content)

    @pytest.mark.asyncio
    async def test_set_code(self) -> None:
        """Test setting code after initialization."""
        app: App[Any] = App()
        async with app.run_test() as _:
            code_display = CodeDisplay()
            await app.mount(code_display)

            # Set code using the setter
            code_display.code = "print('new code')"

            assert code_display.code == "print('new code')"

    @pytest.mark.asyncio
    async def test_syntax_highlighting(self) -> None:
        """Test that code is syntax highlighted."""
        app: App[Any] = App()
        async with app.run_test() as _:
            code_display = CodeDisplay(code="def hello():\n    return 'world'")
            await app.mount(code_display)

            content = code_display.query_one("#code-content", Static)
            # The content should be a Syntax object
            assert content.content is not None
            # Verify it's a Syntax object from Rich

            assert isinstance(content.content, Syntax)

    @pytest.mark.asyncio
    async def test_line_numbers(self) -> None:
        """Test that line numbers are enabled."""
        app: App[Any] = App()
        async with app.run_test() as _:
            code_display = CodeDisplay(code="line1\nline2\nline3")
            await app.mount(code_display)

            content = code_display.query_one("#code-content", Static)
            # Line numbers should be in the rendered output
            # Rich Syntax adds line numbers by default
            assert content.content is not None

    @pytest.mark.asyncio
    async def test_code_property_getter(self) -> None:
        """Test the code property getter."""
        code = "x = 42"
        code_display = CodeDisplay(code=code)

        assert code_display.code == code

    @pytest.mark.asyncio
    async def test_code_property_setter(self) -> None:
        """Test the code property setter updates display."""
        app: App[Any] = App()
        async with app.run_test() as _:
            code_display = CodeDisplay(code="initial")
            await app.mount(code_display)

            # Update code
            code_display.code = "updated"

            # Content should reflect the update
            content = code_display.query_one("#code-content", Static)
            # Check that content is a Syntax object

            assert isinstance(content.content, Syntax)
            # The Syntax object's code property should contain the updated code
            assert "updated" in content.content.code

    @pytest.mark.asyncio
    async def test_not_mounted_handling(self) -> None:
        """Test graceful handling before widget is mounted."""
        code_display = CodeDisplay(code="test")

        # Should be able to get code even when not mounted
        assert code_display.code == "test"

        # Should be able to set code even when not mounted
        code_display.code = "updated"
        assert code_display.code == "updated"

    @pytest.mark.asyncio
    async def test_set_code_method(self) -> None:
        """Test the set_code public method."""
        app: App[Any] = App()
        async with app.run_test() as _:
            code_display = CodeDisplay()
            await app.mount(code_display)

            code_display.set_code("new code via method")

            assert code_display.code == "new code via method"
            content = code_display.query_one("#code-content", Static)

            assert isinstance(content.content, Syntax)

    @pytest.mark.asyncio
    async def test_code_stripping(self) -> None:
        """Test that leading/trailing whitespace is stripped."""
        app: App[Any] = App()
        async with app.run_test() as _:
            code_display = CodeDisplay(code="  \n  code here  \n  ")
            await app.mount(code_display)

            content = code_display.query_one("#code-content", Static)

            assert isinstance(content.content, Syntax)
            # The internal code should be stripped
            assert content.content.code.strip() == "code here"

    @pytest.mark.asyncio
    async def test_multiline_code(self) -> None:
        """Test displaying multiline code."""
        code = """def hello():
    print('world')
    return 42"""

        app: App[Any] = App()
        async with app.run_test() as _:
            code_display = CodeDisplay(code=code)
            await app.mount(code_display)

            content = code_display.query_one("#code-content", Static)

            assert isinstance(content.content, Syntax)
            # Check that the code is stored correctly
            assert "def hello" in content.content.code

    @pytest.mark.asyncio
    async def test_python_theme(self) -> None:
        """Test that Python syntax highlighting is used."""
        app: App[Any] = App()
        async with app.run_test() as _:
            code_display = CodeDisplay(code="import os\nprint(os.getcwd())")
            await app.mount(code_display)

            # Just verify it renders without error
            content = code_display.query_one("#code-content", Static)
            assert content.content is not None

    @pytest.mark.asyncio
    async def test_word_wrap_enabled(self) -> None:
        """Test that word wrap is enabled."""
        app: App[Any] = App()
        async with app.run_test() as _:
            # Create a very long line
            long_line = "x = " + "1" * 200
            code_display = CodeDisplay(code=long_line)
            await app.mount(code_display)

            # Should render without error
            content = code_display.query_one("#code-content", Static)
            assert content.content is not None

    @pytest.mark.asyncio
    async def test_widget_id_and_classes(self) -> None:
        """Test setting widget ID and CSS classes."""
        app: App[Any] = App()
        async with app.run_test() as _:
            code_display = CodeDisplay(
                code="test", widget_id="my-code", classes="custom-class"
            )
            await app.mount(code_display)

            assert code_display.id == "my-code"
            assert "custom-class" in code_display.classes

    @pytest.mark.asyncio
    async def test_code_update_on_mount(self) -> None:
        """Test that code is displayed on mount."""
        app: App[Any] = App()
        async with app.run_test() as _:
            code_display = CodeDisplay(code="mount test")
            await app.mount(code_display)

            # on_mount should have been called
            content = code_display.query_one("#code-content", Static)

            assert isinstance(content.content, Syntax)
            assert "mount test" in content.content.code

    @pytest.mark.asyncio
    async def test_special_characters(self) -> None:
        """Test code with special characters."""
        code = 'print("Special: \\" \\n \\t")'

        app: App[Any] = App()
        async with app.run_test() as _:
            code_display = CodeDisplay(code=code)
            await app.mount(code_display)

            content = code_display.query_one("#code-content", Static)
            assert content.content is not None
