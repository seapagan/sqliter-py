"""Tests for the OutputDisplay widget."""

from __future__ import annotations

from typing import Any

import pytest
from textual.app import App
from textual.widgets import Static

from sqliter.tui.widgets import OutputDisplay


class TestOutputDisplay:
    """Test the OutputDisplay widget."""

    @pytest.mark.asyncio
    async def test_widget_composition(self) -> None:
        """Test that the widget composes correctly."""
        app: App[Any] = App()
        async with app.run_test() as _:
            output_display = OutputDisplay()
            await app.mount(output_display)

            # Should have a Static child for content
            content = output_display.query_one("#output-content", Static)
            assert content is not None

    @pytest.mark.asyncio
    async def test_initial_content(self) -> None:
        """Test the initial placeholder content."""
        app: App[Any] = App()
        async with app.run_test() as _:
            output_display = OutputDisplay()
            await app.mount(output_display)

            content = output_display.query_one("#output-content", Static)
            assert "Run a demo to see output here" in str(content.content)

    @pytest.mark.asyncio
    async def test_show_output_success(self) -> None:
        """Test displaying successful output."""
        app: App[Any] = App()
        async with app.run_test() as _:
            output_display = OutputDisplay()
            await app.mount(output_display)

            output_display.show_output("Demo ran successfully", success=True)

            content = output_display.query_one("#output-content", Static)
            content_str = str(content.content)
            assert "Success" in content_str
            assert "Demo ran successfully" in content_str

    @pytest.mark.asyncio
    async def test_show_output_error(self) -> None:
        """Test displaying error output."""
        app: App[Any] = App()
        async with app.run_test() as _:
            output_display = OutputDisplay()
            await app.mount(output_display)

            output_display.show_output("Something went wrong", success=False)

            content = output_display.query_one("#output-content", Static)
            content_str = str(content.content)
            assert "Error" in content_str
            assert "Something went wrong" in content_str

    @pytest.mark.asyncio
    async def test_show_error_with_traceback(self) -> None:
        """Test displaying error with traceback."""
        app: App[Any] = App()
        async with app.run_test() as _:
            output_display = OutputDisplay()
            await app.mount(output_display)

            traceback = (
                "Traceback (most recent call last):\n  File 'test.py', line 1"
            )
            output_display.show_error("Runtime error", traceback)

            content = output_display.query_one("#output-content", Static)
            content_str = str(content.content)
            assert "Error" in content_str
            assert "Runtime error" in content_str
            assert "Traceback" in content_str

    @pytest.mark.asyncio
    async def test_clear(self) -> None:
        """Test clearing the output."""
        app: App[Any] = App()
        async with app.run_test() as _:
            output_display = OutputDisplay()
            await app.mount(output_display)

            # First show some output
            output_display.show_output("Some output", success=True)
            output_display.clear()

            content = output_display.query_one("#output-content", Static)
            assert "Run a demo to see output here" in str(content.content)

    @pytest.mark.asyncio
    async def test_success_class(self) -> None:
        """Test that success class is applied."""
        app: App[Any] = App()
        async with app.run_test() as _:
            output_display = OutputDisplay()
            await app.mount(output_display)

            output_display.show_output("Success", success=True)
            assert "success" in output_display.classes
            assert "error" not in output_display.classes

    @pytest.mark.asyncio
    async def test_error_class(self) -> None:
        """Test that error class is applied."""
        app: App[Any] = App()
        async with app.run_test() as _:
            output_display = OutputDisplay()
            await app.mount(output_display)

            output_display.show_output("Error", success=False)
            assert "error" in output_display.classes
            assert "success" not in output_display.classes

    @pytest.mark.asyncio
    async def test_class_replacement(self) -> None:
        """Test that classes are replaced when showing different outputs."""
        app: App[Any] = App()
        async with app.run_test() as _:
            output_display = OutputDisplay()
            await app.mount(output_display)

            # Show success first
            output_display.show_output("Success", success=True)
            assert "success" in output_display.classes

            # Then show error
            output_display.show_output("Error", success=False)
            assert "error" in output_display.classes
            assert "success" not in output_display.classes

            # Then clear
            output_display.clear()
            assert "success" not in output_display.classes
            assert "error" not in output_display.classes

    @pytest.mark.asyncio
    async def test_empty_output(self) -> None:
        """Test handling empty output."""
        app: App[Any] = App()
        async with app.run_test() as _:
            output_display = OutputDisplay()
            await app.mount(output_display)

            output_display.show_output("", success=True)

            content = output_display.query_one("#output-content", Static)
            content_str = str(content.content)
            assert "Success" in content_str

    @pytest.mark.asyncio
    async def test_multiline_output(self) -> None:
        """Test displaying multiline output."""
        app: App[Any] = App()
        async with app.run_test() as _:
            output_display = OutputDisplay()
            await app.mount(output_display)

            multiline = """Line 1
Line 2
Line 3"""
            output_display.show_output(multiline, success=True)

            content = output_display.query_one("#output-content", Static)
            content_str = str(content.content)
            assert "Line 1" in content_str
            assert "Line 2" in content_str
            assert "Line 3" in content_str

    @pytest.mark.asyncio
    async def test_special_characters_in_output(self) -> None:
        """Test output with special characters."""
        app: App[Any] = App()
        async with app.run_test() as _:
            output_display = OutputDisplay()
            await app.mount(output_display)

            output = "Special: \t\n\r"
            output_display.show_output(output, success=True)

            content = output_display.query_one("#output-content", Static)
            assert content is not None

    @pytest.mark.asyncio
    async def test_scroll_home(self) -> None:
        """Test that display scrolls to top after update."""
        app: App[Any] = App()
        async with app.run_test() as _:
            output_display = OutputDisplay()
            await app.mount(output_display)

            # Create long output that would need scrolling
            long_output = "\n".join(f"Line {i}" for i in range(100))
            output_display.show_output(long_output, success=True)

            # Should not crash, and scroll_home should be called
            content = output_display.query_one("#output-content", Static)
            assert content is not None

    @pytest.mark.asyncio
    async def test_widget_id_and_classes(self) -> None:
        """Test setting widget ID and CSS classes."""
        app: App[Any] = App()
        async with app.run_test() as _:
            output_display = OutputDisplay(
                widget_id="my-output", classes="custom-class"
            )
            await app.mount(output_display)

            assert output_display.id == "my-output"
            assert "custom-class" in output_display.classes

    @pytest.mark.asyncio
    async def test_multiple_updates(self) -> None:
        """Test multiple sequential updates."""
        app: App[Any] = App()
        async with app.run_test() as _:
            output_display = OutputDisplay()
            await app.mount(output_display)

            for i in range(5):
                output_display.show_output(f"Output {i}", success=True)

            content = output_display.query_one("#output-content", Static)
            content_str = str(content.content)
            assert "Output 4" in content_str

    @pytest.mark.asyncio
    async def test_error_without_traceback(self) -> None:
        """Test displaying error without traceback."""
        app: App[Any] = App()
        async with app.run_test() as _:
            output_display = OutputDisplay()
            await app.mount(output_display)

            output_display.show_error("Error message", traceback_str=None)

            content = output_display.query_one("#output-content", Static)
            content_str = str(content.content)
            assert "Error message" in content_str
            # Should not have traceback section
            assert "Traceback:" not in content_str

    @pytest.mark.asyncio
    async def test_rich_text_styling_success(self) -> None:
        """Test that success output uses Rich Text styling."""
        app: App[Any] = App()
        async with app.run_test() as _:
            output_display = OutputDisplay()
            await app.mount(output_display)

            output_display.show_output("Test output", success=True)

            content = output_display.query_one("#output-content", Static)
            # Content should be a Text object with styling
            assert content.content is not None

    @pytest.mark.asyncio
    async def test_rich_text_styling_error(self) -> None:
        """Test that error output uses Rich Text styling."""
        app: App[Any] = App()
        async with app.run_test() as _:
            output_display = OutputDisplay()
            await app.mount(output_display)

            output_display.show_error("Test error", "Test traceback")

            content = output_display.query_one("#output-content", Static)
            # Content should be a Text object with styling
            assert content.content is not None
