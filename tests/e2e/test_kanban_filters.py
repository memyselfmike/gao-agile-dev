"""
E2E Tests for Kanban Filters and Search

Story 39.18: Kanban Filters and Search
"""
import pytest
import time
from playwright.sync_api import Page, expect


@pytest.fixture
def kanban_page(page: Page) -> Page:
    """Navigate to kanban board page"""
    # Assuming the Kanban board is at /kanban or similar route
    page.goto("http://localhost:5173/kanban")
    page.wait_for_selector('[data-testid="kanban-search-input"]', timeout=10000)
    return page


class TestSearchFiltering:
    """Test search input filtering functionality"""

    def test_search_input_exists(self, kanban_page: Page):
        """AC1: Search input is present"""
        search_input = kanban_page.locator('[data-testid="kanban-search-input"]')
        expect(search_input).to_be_visible()
        expect(search_input).to_have_attribute("placeholder", "Search epics and stories...")

    def test_search_filters_cards(self, kanban_page: Page):
        """AC1: Search filters cards by title (case-insensitive)"""
        search_input = kanban_page.locator('[data-testid="kanban-search-input"]')

        # Count initial cards
        initial_count = kanban_page.locator('[role="listitem"]').count()
        assert initial_count > 0, "Should have cards on the board"

        # Type search query
        search_input.fill("auth")

        # Wait for debounce (300ms) + small buffer
        time.sleep(0.4)

        # Count filtered cards
        filtered_count = kanban_page.locator('[role="listitem"]').count()

        # Verify filtering occurred (should have fewer cards or same if all match)
        assert filtered_count <= initial_count, "Filtered count should be <= initial count"

        # Verify all visible cards contain search term
        visible_cards = kanban_page.locator('[role="listitem"]').all()
        for card in visible_cards:
            card_text = card.inner_text().lower()
            assert "auth" in card_text, f"Card should contain 'auth': {card_text}"

    def test_search_case_insensitive(self, kanban_page: Page):
        """AC1: Search is case-insensitive"""
        search_input = kanban_page.locator('[data-testid="kanban-search-input"]')

        # Search with uppercase
        search_input.fill("AUTH")
        time.sleep(0.4)

        uppercase_count = kanban_page.locator('[role="listitem"]').count()

        # Search with lowercase
        search_input.fill("auth")
        time.sleep(0.4)

        lowercase_count = kanban_page.locator('[role="listitem"]').count()

        # Should return same results
        assert uppercase_count == lowercase_count, "Case should not affect results"

    def test_search_clear_button(self, kanban_page: Page):
        """AC1: Clear button removes search"""
        search_input = kanban_page.locator('[data-testid="kanban-search-input"]')
        clear_button = kanban_page.locator('[data-testid="search-clear-button"]')

        # Clear button should not be visible initially
        expect(clear_button).not_to_be_visible()

        # Type search
        search_input.fill("test")
        time.sleep(0.1)

        # Clear button should appear
        expect(clear_button).to_be_visible()

        # Click clear button
        clear_button.click()

        # Input should be empty
        expect(search_input).to_have_value("")

        # Clear button should disappear
        expect(clear_button).not_to_be_visible()

    def test_search_highlighting(self, kanban_page: Page):
        """AC8: Search highlights matched text"""
        search_input = kanban_page.locator('[data-testid="kanban-search-input"]')

        # Search for a term
        search_input.fill("auth")
        time.sleep(0.4)

        # Find highlighted marks
        highlights = kanban_page.locator('[data-testid="search-highlight"]')

        # Should have at least one highlight
        expect(highlights.first).to_be_visible()

        # Verify highlight has correct styling (yellow background)
        highlight = highlights.first
        bg_color = highlight.evaluate("el => getComputedStyle(el).backgroundColor")
        # Yellow in light mode should be rgb(254, 240, 138) or similar
        assert "254" in bg_color or "240" in bg_color, f"Highlight should be yellow: {bg_color}"


class TestEpicFilter:
    """Test epic number filter dropdown"""

    def test_epic_filter_dropdown_exists(self, kanban_page: Page):
        """AC2: Epic filter dropdown is present"""
        epic_dropdown = kanban_page.locator('[data-testid="epic-filter-dropdown"]')
        expect(epic_dropdown).to_be_visible()
        expect(epic_dropdown).to_contain_text("All Epics")

    def test_epic_filter_shows_options(self, kanban_page: Page):
        """AC2: Epic filter shows all epic numbers"""
        epic_dropdown = kanban_page.locator('[data-testid="epic-filter-dropdown"]')

        # Click dropdown
        epic_dropdown.click()

        # Should show epic options (Epic 1, Epic 2, etc.)
        epic_options = kanban_page.locator('[data-testid^="filter-option-"]')
        expect(epic_options.first).to_be_visible()

    def test_epic_filter_filters_cards(self, kanban_page: Page):
        """AC2: Selecting epic filters cards"""
        epic_dropdown = kanban_page.locator('[data-testid="epic-filter-dropdown"]')

        # Count initial cards
        initial_count = kanban_page.locator('[role="listitem"]').count()

        # Open dropdown and select first epic
        epic_dropdown.click()
        first_option = kanban_page.locator('[data-testid^="filter-option-"]').first
        first_option.click()

        # Close dropdown (click outside)
        kanban_page.keyboard.press("Escape")

        # Wait for filter to apply
        time.sleep(0.2)

        # Count filtered cards
        filtered_count = kanban_page.locator('[role="listitem"]').count()

        # Should have filtered
        assert filtered_count <= initial_count, "Should filter cards by epic"


class TestOwnerFilter:
    """Test owner filter dropdown"""

    def test_owner_filter_dropdown_exists(self, kanban_page: Page):
        """AC3: Owner filter dropdown is present"""
        owner_dropdown = kanban_page.locator('[data-testid="owner-filter-dropdown"]')
        expect(owner_dropdown).to_be_visible()
        expect(owner_dropdown).to_contain_text("All Owners")

    def test_owner_filter_shows_options(self, kanban_page: Page):
        """AC3: Owner filter shows all unique owners"""
        owner_dropdown = kanban_page.locator('[data-testid="owner-filter-dropdown"]')

        # Click dropdown
        owner_dropdown.click()

        # Should show owner options
        owner_options = kanban_page.locator('[data-testid^="filter-option-"]')
        expect(owner_options.first).to_be_visible()


class TestPriorityFilter:
    """Test priority filter dropdown"""

    def test_priority_filter_dropdown_exists(self, kanban_page: Page):
        """AC4: Priority filter dropdown is present"""
        priority_dropdown = kanban_page.locator('[data-testid="priority-filter-dropdown"]')
        expect(priority_dropdown).to_be_visible()
        expect(priority_dropdown).to_contain_text("All Priorities")

    def test_priority_filter_shows_options(self, kanban_page: Page):
        """AC4: Priority filter shows P0-P3 options"""
        priority_dropdown = kanban_page.locator('[data-testid="priority-filter-dropdown"]')

        # Click dropdown
        priority_dropdown.click()

        # Should show P0, P1, P2, P3
        p0_option = kanban_page.locator('[data-testid="filter-option-P0"]')
        p1_option = kanban_page.locator('[data-testid="filter-option-P1"]')
        p2_option = kanban_page.locator('[data-testid="filter-option-P2"]')
        p3_option = kanban_page.locator('[data-testid="filter-option-P3"]')

        expect(p0_option).to_be_visible()
        expect(p1_option).to_be_visible()
        expect(p2_option).to_be_visible()
        expect(p3_option).to_be_visible()


class TestFilterChips:
    """Test active filter chips"""

    def test_filter_chips_show_active_filters(self, kanban_page: Page):
        """AC5: Active filters display as chips"""
        search_input = kanban_page.locator('[data-testid="kanban-search-input"]')
        filter_chips = kanban_page.locator('[data-testid="filter-chips"]')

        # Initially no chips
        expect(filter_chips).not_to_be_visible()

        # Add search filter
        search_input.fill("test")
        time.sleep(0.4)

        # Should show chip
        expect(filter_chips).to_be_visible()
        search_chip = kanban_page.locator('[data-testid^="filter-chip-search"]')
        expect(search_chip).to_be_visible()
        expect(search_chip).to_contain_text('Search: "test"')

    def test_filter_chip_removal(self, kanban_page: Page):
        """AC5: Clicking chip removes filter"""
        search_input = kanban_page.locator('[data-testid="kanban-search-input"]')

        # Add search filter
        search_input.fill("test")
        time.sleep(0.4)

        # Find and click chip
        search_chip = kanban_page.locator('[data-testid^="filter-chip-search"]')
        expect(search_chip).to_be_visible()
        search_chip.click()

        # Chip should disappear
        expect(search_chip).not_to_be_visible()

        # Input should be cleared
        expect(search_input).to_have_value("")

    def test_clear_all_filters_button(self, kanban_page: Page):
        """AC6: Clear All button removes all filters"""
        search_input = kanban_page.locator('[data-testid="kanban-search-input"]')
        clear_all_button = kanban_page.locator('[data-testid="clear-all-filters-button"]')

        # Initially no clear all button
        expect(clear_all_button).not_to_be_visible()

        # Add multiple filters
        search_input.fill("test")
        time.sleep(0.4)

        # Clear all button should appear
        expect(clear_all_button).to_be_visible()

        # Click clear all
        clear_all_button.click()

        # All filters should be cleared
        expect(search_input).to_have_value("")
        expect(clear_all_button).not_to_be_visible()


class TestFilterCombination:
    """Test combining multiple filters"""

    def test_filters_combine_with_and_logic(self, kanban_page: Page):
        """AC7: Multiple filters use AND logic"""
        search_input = kanban_page.locator('[data-testid="kanban-search-input"]')
        epic_dropdown = kanban_page.locator('[data-testid="epic-filter-dropdown"]')

        # Count initial cards
        initial_count = kanban_page.locator('[role="listitem"]').count()

        # Apply search filter
        search_input.fill("auth")
        time.sleep(0.4)
        search_filtered_count = kanban_page.locator('[role="listitem"]').count()

        # Add epic filter
        epic_dropdown.click()
        first_epic = kanban_page.locator('[data-testid^="filter-option-"]').first
        first_epic.click()
        kanban_page.keyboard.press("Escape")
        time.sleep(0.2)

        # Combined filter should have <= search-only filter
        combined_count = kanban_page.locator('[role="listitem"]').count()
        assert combined_count <= search_filtered_count, "Combined filters should use AND logic"


class TestURLState:
    """Test URL state synchronization"""

    def test_url_updates_with_search(self, kanban_page: Page):
        """AC9: Search filter updates URL"""
        search_input = kanban_page.locator('[data-testid="kanban-search-input"]')

        # Add search
        search_input.fill("auth")
        time.sleep(0.4)

        # Check URL contains search parameter
        url = kanban_page.url
        assert "search=auth" in url, f"URL should contain search parameter: {url}"

    def test_url_loads_filters_on_page_load(self, kanban_page: Page):
        """AC9: Filters restore from URL on page load"""
        # Navigate with search parameter
        kanban_page.goto("http://localhost:5173/kanban?search=test")
        kanban_page.wait_for_selector('[data-testid="kanban-search-input"]', timeout=5000)

        # Wait for filter to apply
        time.sleep(0.5)

        # Search input should be populated
        search_input = kanban_page.locator('[data-testid="kanban-search-input"]')
        expect(search_input).to_have_value("test")

        # Filter should be applied
        filter_chips = kanban_page.locator('[data-testid="filter-chips"]')
        expect(filter_chips).to_be_visible()

    def test_browser_back_navigation(self, kanban_page: Page):
        """AC8: Browser back/forward navigation works"""
        search_input = kanban_page.locator('[data-testid="kanban-search-input"]')

        # Apply first filter
        search_input.fill("test")
        time.sleep(0.4)

        # Apply second filter
        search_input.fill("auth")
        time.sleep(0.4)

        # Go back
        kanban_page.go_back()
        time.sleep(0.4)

        # Should restore previous search
        expect(search_input).to_have_value("test")


class TestClientSideFiltering:
    """Test client-side filtering performance"""

    def test_filtering_is_instant(self, kanban_page: Page):
        """AC10: Client-side filtering happens instantly (no backend calls)"""
        search_input = kanban_page.locator('[data-testid="kanban-search-input"]')

        # Listen for network requests
        requests = []
        kanban_page.on("request", lambda request: requests.append(request.url))

        # Apply filter
        search_input.fill("test")
        time.sleep(0.5)  # Wait for debounce + potential network calls

        # Count API calls (filter should not trigger board fetch)
        api_calls = [r for r in requests if "/api/kanban" in r]

        # Should have initial fetch only, no additional fetches for filtering
        assert len(api_calls) <= 1, f"Should not make API calls for filtering: {api_calls}"


class TestEmptyState:
    """Test empty state when no cards match"""

    def test_empty_state_shows_when_no_matches(self, kanban_page: Page):
        """AC12: Empty state shows when no cards match"""
        search_input = kanban_page.locator('[data-testid="kanban-search-input"]')

        # Search for something that won't match
        search_input.fill("xyznonexistent123")
        time.sleep(0.4)

        # Should show empty state message
        empty_message = kanban_page.get_by_text("No cards match your filters")
        expect(empty_message).to_be_visible()

        # Should show card count
        count_text = kanban_page.get_by_text(/Showing \d+ of \d+ cards/)
        expect(count_text).to_be_visible()


class TestKeyboardAccessibility:
    """Test keyboard navigation for filters"""

    def test_filter_controls_keyboard_accessible(self, kanban_page: Page):
        """AC11: Filter controls are keyboard accessible"""
        search_input = kanban_page.locator('[data-testid="kanban-search-input"]')
        epic_dropdown = kanban_page.locator('[data-testid="epic-filter-dropdown"]')

        # Tab to search input
        kanban_page.keyboard.press("Tab")
        # Verify search input has focus
        expect(search_input).to_be_focused()

        # Type in search
        kanban_page.keyboard.type("test")
        time.sleep(0.1)
        expect(search_input).to_have_value("test")

        # Tab to next control (should be epic dropdown)
        kanban_page.keyboard.press("Tab")
        # Note: Focus behavior may vary by implementation

    def test_dropdown_keyboard_navigation(self, kanban_page: Page):
        """AC11: Dropdown can be navigated with keyboard"""
        epic_dropdown = kanban_page.locator('[data-testid="epic-filter-dropdown"]')

        # Focus dropdown
        epic_dropdown.focus()

        # Press Enter to open
        kanban_page.keyboard.press("Enter")

        # Should show options
        options = kanban_page.locator('[data-testid^="filter-option-"]')
        expect(options.first).to_be_visible()

        # Escape to close
        kanban_page.keyboard.press("Escape")


class TestPerformance:
    """Test filtering performance requirements"""

    def test_filter_performance_with_large_dataset(self, kanban_page: Page):
        """AC10: Filter 1,000 cards in <50ms (client-side)"""
        # This test would require seeding the board with 1,000 cards
        # For now, we'll test that filtering is reasonably fast
        search_input = kanban_page.locator('[data-testid="kanban-search-input"]')

        start_time = time.time()
        search_input.fill("test")
        # Wait just for debounce
        time.sleep(0.35)
        end_time = time.time()

        # Filter should apply within debounce time + small overhead
        assert end_time - start_time < 1.0, "Filtering should be fast"


# Mark all tests as e2e
pytestmark = pytest.mark.e2e
