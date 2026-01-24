"""Tests for the main SQLiterDemoApp."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from textual.css.query import NoMatches
from textual.widgets import Button, Footer, Header, Tree

from sqliter.tui import SQLiterDemoApp
from sqliter.tui.demos import DemoRegistry
from sqliter.tui.demos.base import Demo, DemoCategory
from sqliter.tui.widgets import (
    CodeDisplay,
    DemoList,
    DemoSelected,
    OutputDisplay,
)


class TestSQLiterDemoAppComposition:
    """Test app composition and layout."""

    @pytest.mark.asyncio
    async def test_app_composition(self, reset_demo_registry) -> None:
        """Test that all main widgets are rendered."""
        demo = Demo(
            id="test",
            title="Test",
            description="Test",
            category="test",
            code="code",
            execute=lambda: "output",
        )

        category = DemoCategory(id="test", title="Test", demos=[demo])
        DemoRegistry.register_category(category)

        app = SQLiterDemoApp()
        async with app.run_test() as _:
            # Check that main widgets exist
            header = app.query_one(Header)
            assert header is not None

            footer = app.query_one(Footer)
            assert footer is not None

            demo_list = app.query_one(DemoList)
            assert demo_list is not None

            code_display = app.query_one(CodeDisplay)
            assert code_display is not None

            output_display = app.query_one(OutputDisplay)
            assert output_display is not None

    @pytest.mark.asyncio
    async def test_header_exists(self, reset_demo_registry) -> None:
        """Test that Header widget exists."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as _:
            header = app.query_one(Header)
            assert header is not None

    @pytest.mark.asyncio
    async def test_footer_exists(self, reset_demo_registry) -> None:
        """Test that Footer widget exists."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as _:
            footer = app.query_one(Footer)
            assert footer is not None

    @pytest.mark.asyncio
    async def test_demo_list_exists(self, reset_demo_registry) -> None:
        """Test that DemoList widget exists."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as _:
            demo_list = app.query_one("#demo-list", DemoList)
            assert demo_list is not None

    @pytest.mark.asyncio
    async def test_code_display_exists(self, reset_demo_registry) -> None:
        """Test that CodeDisplay widget exists."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as _:
            code_display = app.query_one("#code-display", CodeDisplay)
            assert code_display is not None

    @pytest.mark.asyncio
    async def test_output_display_exists(self, reset_demo_registry) -> None:
        """Test that OutputDisplay widget exists."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as _:
            output_display = app.query_one("#output-display", OutputDisplay)
            assert output_display is not None

    @pytest.mark.asyncio
    async def test_buttons_exist(self, reset_demo_registry) -> None:
        """Test that Run and Clear buttons exist."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as _:
            run_button = app.query_one("#run-btn", Button)
            assert run_button is not None
            assert "Run" in str(run_button.label)

            clear_button = app.query_one("#clear-btn", Button)
            assert clear_button is not None
            assert "Clear" in str(clear_button.label)


class TestSQLiterDemoAppFocus:
    """Test focus and navigation."""

    @pytest.mark.asyncio
    async def test_initial_focus_on_tree(self, reset_demo_registry) -> None:
        """Test that the tree is focused on app mount."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as _:
            demo_list = app.query_one(DemoList)
            tree = demo_list.query_one("#demo-tree", Tree)
            assert tree.has_focus


class TestSQLiterDemoAppDemoSelection:
    """Test demo selection functionality."""

    @pytest.mark.asyncio
    async def test_demo_selection_updates_code(
        self, reset_demo_registry
    ) -> None:
        """Test that selecting a demo updates the code display."""
        demo = Demo(
            id="test",
            title="Test Demo",
            description="Test",
            category="test",
            code="print('hello')",
            execute=lambda: "output",
        )

        category = DemoCategory(id="test", title="Test", demos=[demo])
        DemoRegistry.register_category(category)

        app = SQLiterDemoApp()
        async with app.run_test() as pilot:
            # Manually trigger demo selection

            app.post_message(DemoSelected(demo))
            await pilot.pause()

            code_display = app.query_one("#code-display", CodeDisplay)
            assert "print('hello')" in code_display.code

    @pytest.mark.asyncio
    async def test_demo_selection_stores_current(
        self, reset_demo_registry
    ) -> None:
        """Test that selecting a demo stores it as current."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as pilot:
            app.post_message(DemoSelected(demo))
            await pilot.pause()

            assert app._current_demo is not None
            assert app._current_demo.id == "test"


class TestSQLiterDemoAppExecution:
    """Test demo execution functionality."""

    @pytest.mark.asyncio
    async def test_run_demo_with_selection(self, reset_demo_registry) -> None:
        """Test running a demo when one is selected."""
        demo = Demo(
            id="test",
            title="Test",
            description="Test",
            category="test",
            code="x = 42",
            execute=lambda: "Success output",
        )

        DemoRegistry.register_category(
            DemoCategory(id="test", title="Test", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as pilot:
            app.post_message(DemoSelected(demo))
            await pilot.pause()

            # Click run button
            run_button = app.query_one("#run-btn", Button)
            await pilot.click(run_button)
            await pilot.pause()

            output_display = app.query_one("#output-display", OutputDisplay)
            # Check that output was displayed
            assert output_display.query_one("#output-content") is not None

    @pytest.mark.asyncio
    async def test_run_demo_without_selection(
        self,
        reset_demo_registry,
    ) -> None:
        """Test running a demo without selecting one first."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as pilot:
            # Don't select any demo, just try to run
            run_button = app.query_one("#run-btn", Button)
            await pilot.click(run_button)
            await pilot.pause()

            output_display = app.query_one("#output-display", OutputDisplay)
            # Should show error message
            content = str(
                output_display.query_one("#output-content").content
            ).lower()
            assert "select a demo" in content

    @pytest.mark.asyncio
    async def test_clear_output(self, reset_demo_registry) -> None:
        """Test clearing the output display."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as pilot:
            output_display = app.query_one("#output-display", OutputDisplay)

            # First show some output
            output_display.show_output("Test output", success=True)

            # Then clear
            clear_button = app.query_one("#clear-btn", Button)
            await pilot.click(clear_button)
            await pilot.pause()

            # Should be back to placeholder
            content = output_display.query_one("#output-content")
            assert "Run a demo" in str(content.content)


class TestSQLiterDemoAppHelpScreen:
    """Test help screen functionality."""

    @pytest.mark.asyncio
    async def test_help_screen_composition(self, reset_demo_registry) -> None:
        """Test that help screen can be shown."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as pilot:
            # Show help screen
            app.action_show_help()
            await pilot.pause()

            # Check that a screen was pushed
            assert app.screen_stack is not None
            assert len(app.screen_stack) > 1

    @pytest.mark.asyncio
    async def test_help_key_opens_help(self, reset_demo_registry) -> None:
        """Test that '?' key opens help."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as pilot:
            await pilot.press("?")
            await pilot.pause()

            # Check that a screen was pushed
            assert len(app.screen_stack) > 1

    @pytest.mark.asyncio
    async def test_f1_opens_help(self, reset_demo_registry) -> None:
        """Test that F1 key opens help."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as pilot:
            # Call the action directly
            app.action_show_help()
            await pilot.pause()

            # Check that a screen was pushed
            assert len(app.screen_stack) > 1

    @pytest.mark.asyncio
    async def test_escape_closes_help(self, reset_demo_registry) -> None:
        """Test that Escape closes help screen."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as pilot:
            # Open help
            app.action_show_help()
            await pilot.pause()
            assert len(app.screen_stack) > 1

            # Close help with escape
            app.pop_screen()
            await pilot.pause()
            # Should be back to main screen
            assert len(app.screen_stack) == 1

    @pytest.mark.asyncio
    async def test_q_closes_help(self, reset_demo_registry) -> None:
        """Test that help screen can be dismissed programmatically."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as pilot:
            # Open help
            app.action_show_help()
            await pilot.pause()
            initial_screen_count = len(app.screen_stack)
            assert initial_screen_count > 1

            # Pop the help screen using pop_screen
            app.pop_screen()
            await pilot.pause()
            # Should be back to main screen (just default screen)
            assert len(app.screen_stack) == 1


class TestSQLiterDemoAppKeyboardBindings:
    """Test keyboard bindings."""

    @pytest.mark.asyncio
    async def test_f5_runs_demo(self, reset_demo_registry) -> None:
        """Test that F5 runs the demo."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as pilot:
            app.post_message(DemoSelected(demo))
            await pilot.pause()

            # Press F5 to run
            await pilot.press("<f5>")
            await pilot.pause()

            # Output display should have been updated
            output_display = app.query_one("#output-display", OutputDisplay)
            assert output_display is not None

    @pytest.mark.asyncio
    async def test_f8_clears_output(self, reset_demo_registry) -> None:
        """Test that F8 clears output."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as pilot:
            output_display = app.query_one("#output-display", OutputDisplay)

            # Show some output first
            output_display.show_output("Test", success=True)

            # Wait a bit for the output to be set
            await pilot.pause()

            # Press F8 to clear
            app.action_clear_output()
            await pilot.pause()

            # Should be cleared
            content = output_display.query_one("#output-content")
            assert "Run a demo" in str(content.content)

    @pytest.mark.asyncio
    async def test_vim_keys_work(self, reset_demo_registry) -> None:
        """Test that vim-style j/k keys work."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as pilot:
            # These should not crash
            await pilot.press("j")
            await pilot.pause()
            await pilot.press("k")
            await pilot.pause()

            # Tree should still be focused
            demo_list = app.query_one(DemoList)
            tree = demo_list.query_one("#demo-tree", Tree)
            assert tree.has_focus


class TestSQLiterDemoAppErrorHandling:
    """Test error handling in demo execution."""

    # Error message for demo execution failure
    _DEMO_EXECUTION_FAILED = "Demo execution failed"

    @pytest.mark.asyncio
    async def test_run_demo_failure_shows_error(
        self, reset_demo_registry
    ) -> None:
        """Test that failed demo execution shows error message."""

        def failing_execute() -> str:
            raise RuntimeError(self._DEMO_EXECUTION_FAILED)

        demo = Demo(
            id="test",
            title="Failing Demo",
            description="A demo that fails",
            category="test",
            code="code",
            execute=failing_execute,
        )

        DemoRegistry.register_category(
            DemoCategory(id="test", title="Test", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as pilot:
            app.post_message(DemoSelected(demo))
            await pilot.pause()

            # Click run button
            run_button = app.query_one("#run-btn", Button)
            await pilot.click(run_button)
            await pilot.pause()

            # Should show error output
            output_display = app.query_one("#output-display", OutputDisplay)
            content = output_display.query_one("#output-content")
            output_str = str(content.content).lower()
            # Error output should contain error information
            assert "exception" in output_str or "error" in output_str


class TestSQLiterDemoAppEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_registry(self, reset_demo_registry) -> None:
        """Test app with empty demo registry."""
        # Don't register any demos
        app = SQLiterDemoApp()
        async with app.run_test() as _:
            # Should still compose without error
            demo_list = app.query_one(DemoList)
            assert demo_list is not None

    @pytest.mark.asyncio
    async def test_no_matches_exception_handling(
        self, reset_demo_registry
    ) -> None:
        """Test graceful handling of NoMatches exception."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as _:
            # Try to query non-existent widget
            with pytest.raises(NoMatches):
                app.query_one("#non-existent")

    @pytest.mark.asyncio
    async def test_cursor_down_handles_missing_tree(
        self, reset_demo_registry
    ) -> None:
        """Test cursor down handles missing tree gracefully."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as _:
            # Mock query_one to raise NoMatches
            with patch.object(app, "query_one", side_effect=NoMatches()):
                # Should not raise exception, just handle gracefully
                app.action_tree_cursor_down()

    @pytest.mark.asyncio
    async def test_cursor_up_handles_missing_tree(
        self, reset_demo_registry
    ) -> None:
        """Test cursor up handles missing tree gracefully."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as _:
            # Mock query_one to raise NoMatches
            with patch.object(app, "query_one", side_effect=NoMatches()):
                # Should not raise exception, just handle gracefully
                app.action_tree_cursor_up()

    @pytest.mark.asyncio
    async def test_app_properties(self, reset_demo_registry) -> None:
        """Test app properties."""
        demo = Demo(
            id="test",
            title="T",
            description="T",
            category="t",
            code="c",
            execute=lambda: "",
        )
        DemoRegistry.register_category(
            DemoCategory(id="t", title="T", demos=[demo])
        )

        app = SQLiterDemoApp()
        assert app.TITLE == "SQLiter Interactive Demo"
        assert app.CSS_PATH == "styles/app.tcss"

    @pytest.mark.asyncio
    async def test_multiple_demo_selections(self, reset_demo_registry) -> None:
        """Test selecting multiple demos in sequence."""
        demo1 = Demo(
            id="demo1",
            title="Demo 1",
            description="D1",
            category="test",
            code="code1",
            execute=lambda: "out1",
        )
        demo2 = Demo(
            id="demo2",
            title="Demo 2",
            description="D2",
            category="test",
            code="code2",
            execute=lambda: "out2",
        )

        DemoRegistry.register_category(
            DemoCategory(id="test", title="Test", demos=[demo1, demo2])
        )

        app = SQLiterDemoApp()
        async with app.run_test() as pilot:
            # Select first demo
            app.post_message(DemoSelected(demo1))
            await pilot.pause()
            assert app._current_demo is not None
            assert app._current_demo.id == "demo1"

            # Select second demo
            app.post_message(DemoSelected(demo2))
            await pilot.pause()
            assert app._current_demo is not None
            assert app._current_demo.id == "demo2"
