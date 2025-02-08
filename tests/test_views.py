import pytest
from pydantic import ValidationError
from browser_use.controller.views import (
    NoParamsAction,
    ClickElementAction,
    ScrollAction,
    SendKeysAction,
    InputTextAction,
    ExtractPageContentAction,
    SwitchTabAction,
    SearchGoogleAction,
    GoToUrlAction,
    DoneAction,
    OpenTabAction,
)

def test_no_params_action_ignores_inputs():
    """
    Test that NoParamsAction ignores all incoming data and always produces an empty dictionary.
    """
    instance = NoParamsAction(dummy="ignored", random=123, key="value")
    assert instance.dict() == {}

def test_click_element_action_without_xpath():
    """
    Test that ClickElementAction correctly handles the optional 'xpath' field:
    - When not provided, it defaults to None.
    - When provided, it is properly set.
    """
    # Case 1: Without providing xpath; should default to None.
    instance_without_xpath = ClickElementAction(index=1)
    assert instance_without_xpath.index == 1
    assert instance_without_xpath.xpath is None

    # Case 2: Providing xpath explicitly.
    test_xpath = "//div[@class='button']"
    instance_with_xpath = ClickElementAction(index=2, xpath=test_xpath)
    assert instance_with_xpath.index == 2
    assert instance_with_xpath.xpath == test_xpath

def test_scroll_action_default_and_explicit():
    """
    Test that ScrollAction correctly handles the optional 'amount' field.
    It should be None by default when not provided and correctly set when given.
    """
    # Case 1: Without providing amount; should default to None.
    default_instance = ScrollAction()
    assert default_instance.amount is None

    # Case 2: Explicitly providing the amount.
    explicit_value = 150
    explicit_instance = ScrollAction(amount=explicit_value)
    assert explicit_instance.amount == explicit_value

def test_send_keys_action_assigns_keys():
    """
    Test that SendKeysAction correctly assigns the 'keys' attribute from the provided input.
    """
    test_keys = "Ctrl+C"
    instance = SendKeysAction(keys=test_keys)
    assert instance.keys == test_keys

def test_input_text_action_optional_xpath():
    """
    Test that InputTextAction correctly handles the optional 'xpath' field:
    - When not provided, it is None.
    - When provided, it is properly set.
    """
    # Case 1: Without providing xpath, it should default to None.
    instance_without_xpath = InputTextAction(index=0, text="hello")
    assert instance_without_xpath.index == 0
    assert instance_without_xpath.text == "hello"
    assert instance_without_xpath.xpath is None

    # Case 2: Providing xpath explicitly.
    test_xpath = "//input[@id='username']"
    instance_with_xpath = InputTextAction(index=1, text="world", xpath=test_xpath)
    assert instance_with_xpath.index == 1
    assert instance_with_xpath.text == "world"
    assert instance_with_xpath.xpath == test_xpath

def test_extract_page_content_action_assigns_value():
    """
    Test that ExtractPageContentAction correctly assigns the 'value' attribute from the provided input.
    """
    test_value = "Sample page content for extraction."
    instance = ExtractPageContentAction(value=test_value)
    assert instance.value == test_value

def test_switch_tab_action_assigns_page_id():
    """
    Test that SwitchTabAction correctly assigns the 'page_id' attribute from the provided input.
    """
    instance = SwitchTabAction(page_id=3)
    assert instance.page_id == 3

def test_search_google_action_validation():
    """
    Test that SearchGoogleAction:
    - Successfully creates an instance when the required 'query' is provided.
    - Raises a ValidationError when 'query' is omitted.
    """
    # Verify that providing a query creates a valid instance.
    valid_query = "OpenAI"
    instance = SearchGoogleAction(query=valid_query)
    assert instance.query == valid_query

    # Verify that omitting the 'query' field raises a ValidationError.
    with pytest.raises(ValidationError):
        SearchGoogleAction()

def test_goto_url_and_done_action_validation():
    """
    Test that GoToUrlAction and DoneAction:
    - Properly assign the provided 'url' and 'text' fields.
    - Raise a ValidationError when required fields are missing.
    """
    valid_url = "https://example.com"
    valid_text = "Operation completed successfully."

    # Test GoToUrlAction with valid input.
    instance_goto = GoToUrlAction(url=valid_url)
    assert instance_goto.url == valid_url

    # Test that missing 'url' in GoToUrlAction raises a ValidationError.
    with pytest.raises(ValidationError):
        GoToUrlAction()

    # Test DoneAction with valid input.
    instance_done = DoneAction(text=valid_text)
    assert instance_done.text == valid_text

    # Test that missing 'text' in DoneAction raises a ValidationError.
    with pytest.raises(ValidationError):
        DoneAction()

def test_open_tab_action_validation():
    """
    Test that OpenTabAction correctly assigns the provided 'url' field and
    raises a ValidationError when the URL is omitted.
    """
    # Case 1: Providing a valid URL, the instance should have the same URL.
    valid_url = "https://example.com/newpage"
    instance = OpenTabAction(url=valid_url)
    assert instance.url == valid_url

    # Case 2: Omitting the required 'url' field should raise a ValidationError.
    with pytest.raises(ValidationError):
        OpenTabAction()
