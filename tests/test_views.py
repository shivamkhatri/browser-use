import pytest
from browser_use.browser.views import BrowserStateHistory, TabInfo
from browser_use.browser.views import BrowserStateHistory, BrowserError, URLNotAllowedError
from browser_use.browser.views import GroupTabsAction, UngroupTabsAction
from pydantic import ValidationError
from browser_use.browser.views import TabInfo, BrowserStateHistory, BrowserError, URLNotAllowedError, GroupTabsAction, UngroupTabsAction

def test_browser_state_history_to_dict():
    """
    Test the conversion of BrowserStateHistory to a dictionary representation.
    This verifies that the 'tabs', 'screenshot', 'interacted_element', 'url', and 'title'
    fields are correctly processed into the expected dictionary format.
    """
    # Create a dummy DOMHistoryElement with a simple to_dict method.
    class DummyDOMHistoryElement:
        def to_dict(self):
            return {"dummy": "element"}
    # Setup TabInfo instances.
    tab1 = TabInfo(page_id=1, url="http://example.com", title="Example")
    tab2 = TabInfo(page_id=2, url="http://test.com", title="Test")
    
    # Create a BrowserStateHistory instance with dummy data,
    # including a list of interacted elements (one valid element and one None).
    state_history = BrowserStateHistory(
        url="http://history.com",
        title="History",
        tabs=[tab1, tab2],
        interacted_element=[DummyDOMHistoryElement(), None],
        screenshot="dummy-screenshot"
    )
    
    # Convert state_history to a dictionary.
    result = state_history.to_dict()
    
    # Expected dictionary representation.
    expected_tabs = [tab1.model_dump(), tab2.model_dump()]
    expected_interacted = [{"dummy": "element"}, None]
    # Assert that all parts of the dictionary are as expected.
    assert result["url"] == "http://history.com"
    assert result["title"] == "History"
    assert result["tabs"] == expected_tabs
    assert result["screenshot"] == "dummy-screenshot"
    assert result["interacted_element"] == expected_interacted
def test_browser_state_history_empty_fields_and_error_exceptions():
    """
    Test conversion of BrowserStateHistory to dictionary when provided with empty fields,
    and verify that BrowserError and URLNotAllowedError behave as expected exception classes.
    """
    # Create a BrowserStateHistory instance with empty tabs and interacted_element lists, and no screenshot.
    state_history = BrowserStateHistory(
        url="http://empty.com",
        title="Empty State",
        tabs=[],
        interacted_element=[],
        screenshot=None
    )
    # Convert to dict and verify empty lists and None screenshot.
    result = state_history.to_dict()
    assert result["url"] == "http://empty.com"
    assert result["title"] == "Empty State"
    assert result["tabs"] == []
    assert result["interacted_element"] == []
    assert result["screenshot"] is None
    # Also verify the exception hierarchy: URLNotAllowedError is a type of BrowserError.
    with pytest.raises(BrowserError, match="URL is not allowed"):
        raise URLNotAllowedError("URL is not allowed")
def test_group_and_ungroup_tabs_default_values():
    """
    Test that:
    - GroupTabsAction assigns the default color ("blue") when no color is provided,
      and that it accepts a custom color.
    - UngroupTabsAction correctly initializes with the provided tab_ids.
    ... existing code
    """
    # Test GroupTabsAction default color.
    group_action = GroupTabsAction(tab_ids=[1, 2, 3], title="Group Tabs")
    assert group_action.color == "blue", "Expected default color to be 'blue'"
    
    # Test GroupTabsAction with a custom color.
    group_action_custom = GroupTabsAction(tab_ids=[4, 5], title="Custom Group", color="red")
    assert group_action_custom.color == "red", "Expected custom color to be 'red'"
    
    # Test UngroupTabsAction field initialization.
    ungroup_action = UngroupTabsAction(tab_ids=[1, 2])
    assert ungroup_action.tab_ids == [1, 2], "Expected tab_ids to equal [1, 2]"
def test_invalid_group_tabs_action_raises_validation_error():
    """
    Test that invalid input data for GroupTabsAction and UngroupTabsAction
    (e.g., missing required fields or wrong types) raises a pydantic.ValidationError.
    """
    from pydantic import ValidationError
    from browser_use.browser.views import GroupTabsAction, UngroupTabsAction
    # Test missing required field "title" for GroupTabsAction.
    with pytest.raises(ValidationError, match="Field required"):
        # Omitting the 'title' field should trigger a validation error.
        GroupTabsAction(tab_ids=[1, 2, 3])
    # Test invalid type for tab_ids (e.g., a string instead of a list of integers).
    with pytest.raises(ValidationError, match="Input should be a valid list"):
        GroupTabsAction(tab_ids="not-a-list", title="Invalid")
    # Test similarly for UngroupTabsAction with wrong type for tab_ids.
    with pytest.raises(ValidationError, match="Input should be a valid list"):
        UngroupTabsAction(tab_ids="not-a-list")
def test_invalid_group_tabs_action_raises_validation_error():
    """
    Test that invalid input data for GroupTabsAction and UngroupTabsAction
    raises a pydantic.ValidationError when provided with missing required fields or wrong types.
    """
    # Test missing required field "title" for GroupTabsAction.
    with pytest.raises(ValidationError, match="Field required"):
        GroupTabsAction(tab_ids=[1, 2, 3])
    # Test invalid type for tab_ids (e.g., a string instead of a list of integers).
    with pytest.raises(ValidationError, match="Input should be a valid list"):
        GroupTabsAction(tab_ids="not-a-list", title="Invalid")
    # Test similarly for UngroupTabsAction with wrong type for tab_ids.
    with pytest.raises(ValidationError, match="Input should be a valid list"):
        UngroupTabsAction(tab_ids="not-a-list")
def test_invalid_group_tabs_action_raises_validation_error():
    """
    Test that invalid input data for GroupTabsAction and UngroupTabsAction
    raises a pydantic.ValidationError when provided with missing required fields or wrong types.
    This confirms that:
      - Missing the required 'title' field of GroupTabsAction raises a validation error with "Field required".
      - Passing an incorrect type for 'tab_ids' (e.g. a string) raises a validation error with the message "Input should be a valid list".
    """
    # Test missing required field "title" for GroupTabsAction.
    with pytest.raises(ValidationError, match="Field required"):
        GroupTabsAction(tab_ids=[1, 2, 3])
    # Test invalid type for tab_ids (e.g., a string instead of a list of integers).
    with pytest.raises(ValidationError, match="Input should be a valid list"):
        GroupTabsAction(tab_ids="not-a-list", title="Invalid")
    # Test similarly for UngroupTabsAction with wrong type for tab_ids.
    with pytest.raises(ValidationError, match="Input should be a valid list"):
        UngroupTabsAction(tab_ids="not-a-list")