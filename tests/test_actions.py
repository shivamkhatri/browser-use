import asyncio
import pytest
from browser_use.actions import DatePickerAction
from datetime import datetime
from dateutil.parser import ParserError
from playwright.async_api import TimeoutError, ElementHandle, Locator
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_invalid_date_input(monkeypatch):
    """
    Test that DatePickerAction.execute returns False and sets last_error correctly
    when an invalid date string is provided.
    """
    # Create a fake Page and Context.
    class FakePage:
        async def wait_for_selector(self, selector):
            return MagicMock()
    class FakeContext:
        async def get_current_page(self):
            return FakePage()
    # Dummy element: using a MagicMock so that it is not a string;
    # thus, page.wait_for_selector won't be invoked.
    fake_element = MagicMock()
    # Monkeypatch the module-level parse (imported in browser_use.actions) to raise ParserError.
    def fake_parse(value):
        raise ParserError("Invalid date string")
    monkeypatch.setattr("browser_use.actions.parse", fake_parse)
    # Instantiate the action with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Try to execute with an invalid date string.
    result = await action.execute(fake_element, "not-a-date")
    # The expected behavior is to return False and set last_error with a ValueError.
    assert result is False, "Expected execute to return False on invalid date"
    assert isinstance(action.last_error, ValueError)
    assert "Invalid date: not-a-date" in str(action.last_error)
@pytest.mark.asyncio
async def test_valid_date_input_with_selector():
    """
    Test that DatePickerAction.execute returns True with no error when a valid date string
    is provided and the element is specified as a selector string. This covers the branch
    where page.wait_for_selector is used to locate the element.
    """
    # Define a fake element that simulates a date picker input.
    class FakeElement:
        def __init__(self):
            self.value = ""
        async def fill(self, val):
            self.value = val
        async def input_value(self):
            return self.value
    # Define a fake page that returns the FakeElement when wait_for_selector is called.
    class FakePage:
        async def wait_for_selector(self, selector):
            # Simulate a successful selector lookup.
            return FakeElement()
    # Define a fake context that returns our FakePage as the current page.
    class FakeContext:
        async def get_current_page(self):
            return FakePage()
    # Instantiate the DatePickerAction with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Valid date string and a custom format.
    valid_date_str = "2023-10-01"
    custom_format = "%d-%m-%Y"  # Expected formatted date: "01-10-2023"
    # Execute the action while passing a selector (string) for the element.
    result = await action.execute("dummy-selector", valid_date_str, custom_format)
    # Verify that execution was successful and no error is set.
    assert result is True, "Expected execute to return True on valid date input with selector"
    assert action.last_error is None, "Expected last_error to be None on successful date input"
@pytest.mark.asyncio
async def test_context_exception_handling():
    """
    Test that DatePickerAction.execute returns False and sets last_error correctly
    when context.get_current_page raises an exception.
    """
    # Define a fake context that raises an exception when get_current_page is called.
    class FakeContext:
        async def get_current_page(self):
            raise Exception("Simulated error in get_current_page")
    # Dummy element: using a MagicMock; it will not be used since get_current_page fails.
    fake_element = MagicMock()
    # Instantiate the action with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Attempt to execute; it should catch the exception and return False.
    result = await action.execute(fake_element, "2023-10-10")
    # Validate that the method returned False and last_error contains the simulated exception.
    assert result is False, "Expected execute to return False when get_current_page raises an exception"
    assert isinstance(action.last_error, Exception), "Expected last_error to be an Exception"
    assert "Simulated error in get_current_page" in str(action.last_error)
@pytest.mark.asyncio
async def test_selector_timeout():
    """
    Test that DatePickerAction.execute returns False and sets last_error correctly
    when wait_for_selector times out (i.e., the selector cannot be located).
    """
    # Define a fake page where wait_for_selector always raises TimeoutError.
    class FakePage:
        async def wait_for_selector(self, selector):
            raise TimeoutError("Simulated timeout error")
    # Define a fake context that returns our FakePage as the current page.
    class FakeContext:
        async def get_current_page(self):
            return FakePage()
    # Instantiate DatePickerAction with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Execute the action with a selector string; the lookup will fail due to timeout.
    result = await action.execute("nonexistent-selector", "2023-12-31")
    # Validate that the method returns False and last_error is set to a ValueError with the expected message.
    assert result is False, "Expected execute to return False when wait_for_selector times out"
    assert isinstance(action.last_error, ValueError), "Expected last_error to be a ValueError"
    assert "Element not found: nonexistent-selector" in str(action.last_error)
@pytest.mark.asyncio
async def test_valid_date_input_with_datetime():
    """
    Test that DatePickerAction.execute returns True and correctly formats
    a datetime object input using the default format when the element is provided
    directly (i.e., not as a selector string).
    """
    # Define a fake element simulating a date picker input.
    class FakeElement:
        def __init__(self):
            self.value = ""
        async def fill(self, val):
            self.value = val
        async def input_value(self):
            return self.value
    # Define a fake context that is not used because the element is provided directly,
    # but still returned by get_current_page if needed.
    class FakePage:
        async def wait_for_selector(self, selector):
            return FakeElement()
    class FakeContext:
        async def get_current_page(self):
            return FakePage()
    # Instantiate DatePickerAction with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Create a datetime object for testing.
    date_obj = datetime(2023, 9, 15)  # Expected formatted date: "2023-09-15"
    # Create a fake element; bypassing the selector branch.
    fake_element = FakeElement()
    # Execute the action with the datetime object.
    result = await action.execute(fake_element, date_obj)
    # Validate that the action returns True and the fake element's value is correctly updated.
    assert result is True, "Expected execute to return True for valid datetime input"
    assert await fake_element.input_value() == "2023-09-15"
@pytest.mark.asyncio
async def test_element_fill_exception():
    """
    Test that DatePickerAction.execute returns False and sets last_error correctly
    when element.fill() raises an exception.
    """
    # Define a fake element that simulates an error when trying to clear or fill the value.
    class FakeElement:
        async def fill(self, val):
            raise Exception("Simulated fill error")
        async def input_value(self):
            return ""
    # Define a fake context that returns a fake page (though it won't be used because the element is provided directly).
    class FakeContext:
        async def get_current_page(self):
            class FakePage:
                async def wait_for_selector(self, selector):
                    return FakeElement()
            return FakePage()
    # Instantiate DatePickerAction with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Execute the date picker action with a valid date string.
    result = await action.execute(FakeElement(), "2023-11-11")
    # Verify that execution failed and last_error contains the simulated exception message.
    assert result is False, "Expected execute to return False when element.fill raises an exception"
    assert isinstance(action.last_error, Exception), "Expected last_error to be an Exception"
    assert "Simulated fill error" in str(action.last_error)
@pytest.mark.asyncio
async def test_wait_for_selector_returns_none():
    """
    Test that DatePickerAction.execute returns False and sets last_error correctly
    when wait_for_selector returns None (simulating that the element is not found).
    """
    # Define a fake page where wait_for_selector always returns None.
    class FakePage:
        async def wait_for_selector(self, selector):
            return None
    # Define a fake context using the FakePage.
    class FakeContext:
        async def get_current_page(self):
            return FakePage()
    # Instantiate DatePickerAction with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Execute the action using a selector. It should fail because wait_for_selector returns None.
    result = await action.execute("dummy-selector", "2023-10-06")
    # Validate that the result is False and the last_error indicates the element was not found.
    assert result is False, "Expected execute to return False when wait_for_selector returns None"
    assert isinstance(action.last_error, ValueError), "Expected last_error to be a ValueError"
    assert "Element not found:" in str(action.last_error)
@pytest.mark.asyncio
async def test_valid_date_input_with_locator():
    """
    Test that DatePickerAction.execute returns True when a valid date string is provided
    and the element is provided as a locator-like object (simulated by FakeLocator), ensuring
    that the action uses the default date format ("%Y-%m-%d").
    """
    # Define a fake locator that simulates a date picker input.
    class FakeLocator:
        def __init__(self):
            self.value = ""
        async def fill(self, val):
            self.value = val
        async def input_value(self):
            return self.value
    # Define a fake context that returns a dummy page (not used in this test)
    class FakeContext:
        async def get_current_page(self):
            class DummyPage:
                async def wait_for_selector(self, selector):
                    return None
            return DummyPage()
    # Instantiate DatePickerAction with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Valid date string using the default format.
    valid_date_str = "2023-10-20"
    # Create a FakeLocator instance
    fake_locator = FakeLocator()
    # Execute the action passing the fake locator.
    result = await action.execute(fake_locator, valid_date_str)
    # Verify that the execution was successful and the fake_locator's value is correctly updated.
    assert result is True, "Expected execute to return True for valid date input with locator"
    assert await fake_locator.input_value() == "2023-10-20"
@pytest.mark.asyncio
async def test_date_picker_verification_failure():
    """
    Test that DatePickerAction.execute returns False when the element's input_value remains empty 
    even after filling with a valid date. This simulates a scenario where the date update is not reflected.
    """
    # Define a fake element that simulates a date picker input, but never updates its value.
    class FakeElement:
        async def fill(self, val):
            # Simulate a successful fill that, for some reason, doesn't change the element's value.
            pass
        async def input_value(self):
            # Always returns an empty string (simulating verification failure)
            return ""
    # Create a fake context that is not used because the element is provided directly,
    # but still returned by get_current_page if needed.
    class FakeContext:
        async def get_current_page(self):
            class FakePage:
                async def wait_for_selector(self, selector):
                    return FakeElement()
            return FakePage()
    # Instantiate DatePickerAction with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Execute the action with a valid date string; using a fake element that never updates.
    fake_element = FakeElement()
    result = await action.execute(fake_element, "2023-10-31")
    # Validate that the action returns False due to the input value verification failure,
    # and that no new error was recorded in last_error.
    assert result is False, "Expected execute to return False when input_value remains empty"
    assert action.last_error is None, "Did not expect any error to be set when fill succeeds but verification fails"
@pytest.mark.asyncio
async def test_second_fill_exception():
    """
    Test that DatePickerAction.execute returns False and sets last_error correctly
    when the second call to element.fill (filling the formatted date) raises an exception.
    """
    class FakeElement:
        def __init__(self):
            self.call_count = 0
        async def fill(self, val):
            if self.call_count == 0:
                # First call: clear the element successfully.
                self.call_count += 1
                self.value = ""
            else:
                # Second call: simulate failure when inputting the date.
                raise Exception("Simulated fill error on input")
        async def input_value(self):
            # This would normally return the current value, but here it's not updated due to the exception.
            return ""
    class FakeContext:
        async def get_current_page(self):
            # Although the element is provided directly, a FakePage is created to satisfy the context interface.
            class FakePage:
                async def wait_for_selector(self, selector):
                    return FakeElement()
            return FakePage()
    # Instantiate the action with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Use a valid date string so that formatting succeeds, expecting the second fill to raise an exception.
    result = await action.execute(FakeElement(), "2023-10-10")
    # The test verifies that the function returns False and that last_error captures the simulated exception.
    assert result is False, "Expected execute to return False when second fill call fails"
    assert isinstance(action.last_error, Exception)
    assert "Simulated fill error on input" in str(action.last_error)
@pytest.mark.asyncio
async def test_valid_date_input_with_locator_and_custom_format():
    """
    Test that DatePickerAction.execute processes a datetime object correctly when provided as 
    a locator with a custom format. This verifies that the element is filled with the date string
    matching the provided custom format.
    """
    # Define a fake locator that simulates a date picker input.
    class FakeLocator:
        def __init__(self):
            self.value = ""
        async def fill(self, val):
            self.value = val
        async def input_value(self):
            return self.value
    # Define a fake context that returns a dummy page (not used in this test since we pass a locator directly).
    class FakeContext:
        async def get_current_page(self):
            class DummyPage:
                async def wait_for_selector(self, selector):
                    return FakeLocator()
            return DummyPage()
    # Instantiate DatePickerAction with our fake context.
    action = DatePickerAction(context=FakeContext())
    # Create a datetime object and specify a custom format.
    date_obj = datetime(2023, 11, 25)
    custom_format = "%m/%d/%Y"  # Expected formatted date: "11/25/2023"
    # Create an instance of FakeLocator.
    fake_locator = FakeLocator()
    # Execute the action with the locator, datetime input, and custom format.
    result = await action.execute(fake_locator, date_obj, custom_format)
    # Verify that the action was successful.
    assert result is True, "Expected execute to return True when processing datetime with locator and custom format"
    # Verify that the filled value matches the expected custom format.
    filled_value = await fake_locator.input_value()
    expected_value = date_obj.strftime(custom_format)
    assert filled_value == expected_value, f"Expected filled value to be {expected_value} but got {filled_value}"
@pytest.mark.asyncio
async def test_invalid_element_type():
    """
    Test that DatePickerAction.execute returns False and sets last_error when an unsupported element type
    (like an integer) is provided. This simulates a scenario where the element does not have the 'fill' method.
    """
    class FakeContext:
        async def get_current_page(self):
            class DummyPage:
                async def wait_for_selector(self, selector):
                    return None
            return DummyPage()
    # Instantiate the action with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Pass an integer as the element which doesn't have a 'fill' method.
    result = await action.execute(123, "2023-10-10")
    # Verify that the execute returns False and last_error captures the attribute error.
    assert result is False, "Expected execute to return False when element type is invalid"
    assert action.last_error is not None, "Expected an error to be recorded for invalid element type"
    # Check that the error message indicates that the provided element lacks the 'fill' method.
    assert "has no attribute 'fill'" in str(action.last_error), "Error message should indicate missing 'fill' attribute"
@pytest.mark.asyncio
async def test_invalid_date_value_type():
    """
    Test that DatePickerAction.execute returns False and sets last_error correctly
    when an unsupported type (e.g. integer) is provided for date_value.
    This verifies that the AttributeError (due to missing strftime) is caught.
    """
    # Create a fake element that supports fill and input_value.
    class FakeElement:
        async def fill(self, val):
            self.value = val
        async def input_value(self):
            return getattr(self, 'value', '')
    # Create a fake context that returns a fake page (though not used since element is provided directly).
    class FakeContext:
        async def get_current_page(self):
            class FakePage:
                async def wait_for_selector(self, selector):
                    return FakeElement()
            return FakePage()
    # Instantiate the DatePickerAction with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Pass an integer for date_value, which does not have a 'strftime' method.
    result = await action.execute(FakeElement(), 123)
    # Verify that the execute method returns False and last_error reflects the AttributeError.
    assert result is False, "Expected execute to return False when date_value is an unsupported type"
    assert action.last_error is not None, "Expected last_error to be set due to the unsupported date_value type"
    assert "strftime" in str(action.last_error), "Error message should indicate missing 'strftime' method"
@pytest.mark.asyncio
async def test_input_value_exception():
    """
    Test that DatePickerAction.execute returns False and sets last_error correctly when 
    the element's input_value method raises an exception during verification.
    """
    # Define a fake element that successfully fills the date value but raises an exception on input_value.
    class FakeElement:
        async def fill(self, val):
            self.value = val
        async def input_value(self):
            raise Exception("Simulated input_value error")
    # Define a fake context. Although the element is provided directly, get_current_page must be callable.
    class FakeContext:
        async def get_current_page(self):
            class DummyPage:
                async def wait_for_selector(self, selector):
                    return FakeElement()
            return DummyPage()
    # Instantiate the DatePickerAction with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Invoke the execute method with the FakeElement and a valid date string.
    result = await action.execute(FakeElement(), "2023-12-25")
    # Assert that the action returns False due to failure in input_value verification,
    # and that last_error captures the exception message.
    assert result is False, "Expected execute to return False when input_value raises an exception"
    assert isinstance(action.last_error, Exception), "Expected last_error to be set as an Exception"
    assert "Simulated input_value error" in str(action.last_error)
@pytest.mark.asyncio
async def test_non_leap_year_invalid_date():
    """
    Test that DatePickerAction.execute returns False and sets last_error
    when a non-leap year invalid date string ("2023-02-29") is provided using a selector.
    This test does not monkeypatch the parse function, relying on dateutil's actual behavior.
    """
    # Fake element to simulate the date picker input.
    class FakeElement:
        def __init__(self):
            self.value = ""
        async def fill(self, val):
            self.value = val
        async def input_value(self):
            return self.value
    # Fake page that returns a FakeElement when asked for a selector.
    class FakePage:
        async def wait_for_selector(self, selector):
            return FakeElement()
    # Fake context returning our FakePage.
    class FakeContext:
        async def get_current_page(self):
            return FakePage()
    # Instantiate the DatePickerAction using the fake context.
    action = DatePickerAction(context=FakeContext())
    # Pass an invalid non-leap year date string.
    invalid_date_str = "2023-02-29"
    result = await action.execute("dummy-selector", invalid_date_str)
    # Verify that the execution returns False and last_error is set appropriately.
    assert result is False, "Expected execute to return False for non-leap year invalid date"
    assert isinstance(action.last_error, ValueError), "Expected last_error to be a ValueError"
    assert f"Invalid date: {invalid_date_str}" in str(action.last_error)
@pytest.mark.asyncio
async def test_invalid_format_type():
    """
    Test that DatePickerAction.execute returns False and sets last_error correctly
    when an invalid type (non-string) is provided for the 'format' parameter.
    This ensures that a TypeError (or similar) raised during date formatting is handled.
    """
    # Define a fake element supporting fill and input_value.
    class FakeElement:
        async def fill(self, val):
            self.value = val
        async def input_value(self):
            return getattr(self, "value", "")
    # Define a fake context (not used because element is provided directly).
    class FakeContext:
        async def get_current_page(self):
            class DummyPage:
                async def wait_for_selector(self, selector):
                    return FakeElement()
            return DummyPage()
    # Instantiate the DatePickerAction with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Use a valid date string but pass an integer as the custom format.
    result = await action.execute(FakeElement(), "2023-10-10", 123)
    # Expect execution to return False and last_error to be set due to the invalid format type.
    assert result is False, "Expected execute to return False when format type is invalid"
    assert action.last_error is not None, "Expected last_error to be set when an invalid format type is provided"
    # Check that the error message indicates an issue with data types, e.g., mentioning 'str' or 'int'
    assert "str" in str(action.last_error) or "int" in str(action.last_error), (
        "Error message should indicate that format must be a string or another type issue."
    )
@pytest.mark.asyncio
async def test_empty_date_string():
    """
    Test that DatePickerAction.execute returns False and sets last_error correctly
    when an empty date string is provided. An empty string should trigger a ParserError
    that is caught and converted to a ValueError.
    """
    # Fake element that simulates a date picker input.
    class FakeElement:
        def __init__(self):
            self.value = ""
        async def fill(self, val):
            self.value = val
        async def input_value(self):
            return self.value
    # Fake context that returns a FakePage.
    class FakeContext:
        async def get_current_page(self):
            class FakePage:
                async def wait_for_selector(self, selector):
                    return FakeElement()
            return FakePage()
    # Instantiate the DatePickerAction with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Provide a fake element (bypassing the selector branch) and an empty date string.
    fake_element = FakeElement()
    result = await action.execute(fake_element, "")
    # Validate that the action returns False and last_error is set to a ValueError indicating an invalid date.
    assert result is False, "Expected execute to return False for an empty date string"
    assert isinstance(action.last_error, ValueError), "Expected a ValueError in last_error for empty date string"
    assert "Invalid date:" in str(action.last_error)
@pytest.mark.asyncio
async def test_valid_date_input_selector_with_datetime():
    """
    Test that DatePickerAction.execute returns True and correctly formats a datetime input
    when the element is provided as a selector string. This verifies that the branch for
    selector string input and datetime date_value is executed using the default format ("%Y-%m-%d").
    """
    class FakeElement:
        def __init__(self):
            self.value = ""
        async def fill(self, val):
            self.value = val
        async def input_value(self):
            return self.value
    class FakePage:
        def __init__(self):
            self.fake_element = FakeElement()  # persistent instance to verify later
        async def wait_for_selector(self, selector):
            return self.fake_element
    class FakeContext:
        def __init__(self):
            self.page = FakePage()
        async def get_current_page(self):
            return self.page
    # Instantiate the DatePickerAction with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Define a datetime value.
    test_date = datetime(2021, 12, 31)  # Expected formatted date: "2021-12-31"
    # Use a selector string for the element.
    selector = "date-picker-selector"
    # Execute the action.
    result = await action.execute(selector, test_date)
    # Verify that it returns True.
    assert result is True, "Expected execute to return True with a valid datetime input and selector string"
    # Verify that the fake element's value is the formatted date string.
    page = await action.context.get_current_page()
    fake_element = page.fake_element
    assert await fake_element.input_value() == "2021-12-31", (
        "Expected the fake element's value to be formatted as '2021-12-31'"
    )
    assert action.last_error is None, "Expected last_error to remain None on successful execution"
@pytest.mark.asyncio
async def test_date_string_with_time_info():
    """
    Test that DatePickerAction.execute correctly strips off the time portion from an ISO 8601 date string.
    The default behavior should format the date to "%Y-%m-%d" (e.g., "2023-10-05T15:23:00" becomes "2023-10-05").
    """
    class FakeElement:
        def __init__(self):
            self.value = ""
        async def fill(self, val):
            self.value = val
        async def input_value(self):
            return self.value
    # Fake context with a dummy get_current_page. This isn't used when the element is provided directly.
    class FakeContext:
        async def get_current_page(self):
            class DummyPage:
                async def wait_for_selector(self, selector):
                    return FakeElement()
            return DummyPage()
    # Instantiate the DatePickerAction with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Date string that includes a time portion.
    date_input = "2023-10-05T15:23:00"
    fake_element = FakeElement()
    # Execute should parse the input and fill the date portion only.
    result = await action.execute(fake_element, date_input)
    # Validate that the method returns True.
    assert result is True, "Expected execute to return True for date string containing time info"
    # Validate that the fake element's value is the date only part using default "%Y-%m-%d" format.
    value = await fake_element.input_value()
    assert value == "2023-10-05", f"Expected element value to be '2023-10-05' but got {value}"
@pytest.mark.asyncio
async def test_null_current_page():
    """
    Test that DatePickerAction.execute returns False and sets last_error correctly
    when context.get_current_page returns None (simulating no available page), which triggers
    an AttributeError when trying to call wait_for_selector on None.
    """
    class FakeContext:
        async def get_current_page(self):
            return None  # Simulate no current page available
    # Instantiate DatePickerAction with the FakeContext.
    action = DatePickerAction(context=FakeContext())
    # Pass a selector string so that the branch calling wait_for_selector is executed.
    result = await action.execute("dummy-selector", "2023-10-10")
    # The expected behavior is to return False due to the AttributeError.
    assert result is False, "Expected execute to return False when context.get_current_page returns None"
    # Check that last_error indicates the AttributeError due to calling wait_for_selector on None.
    assert action.last_error is not None, "Expected last_error to be set due to NoneType error."
    assert "NoneType" in str(action.last_error) or "has no attribute" in str(action.last_error), (
        "Error message should indicate that wait_for_selector was called on None."
    )
@pytest.mark.asyncio
async def test_input_verification_non_strict():
    """
    Test that DatePickerAction.execute returns True when element.input_value() returns a non-empty value 
    even if it does not exactly match the filled date string.
    This tests that the verification step only checks a truthy/non-empty value.
    """
    # Define a fake element that does not update its value based on fill() but always returns a non-empty string.
    class FakeElement:
        async def fill(self, val):
            # Ignoring the provided value and not storing it.
            pass
        async def input_value(self):
            return "unexpected"
    # Define a fake context; since we pass an element directly, the get_current_page branch won't be used.
    class FakeContext:
        async def get_current_page(self):
            class DummyPage:
                async def wait_for_selector(self, selector):
                    return FakeElement()
            return DummyPage()
    # Instantiate the DatePickerAction with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Provide a valid date string.
    result = await action.execute(FakeElement(), "2023-10-10")
    # Since input_value returns a non-empty string ("unexpected"), the verification should pass and return True.
    assert result is True, "Expected execute to return True when input_value returns a non-empty string."
    # No error should be recorded.
    assert action.last_error is None, "Expected last_error to be None when verification passes."
@pytest.mark.asyncio
async def test_valid_date_input_with_non_iso_string():
    """
    Test that DatePickerAction.execute correctly processes a valid non-ISO date string (MM/DD/YYYY)
    by parsing it and formatting it using the default format ("%Y-%m-%d").
    """
    # Define a fake element simulating a date picker input.
    class FakeElement:
        def __init__(self):
            self.value = ""
        async def fill(self, val):
            self.value = val
        async def input_value(self):
            return self.value
    # Define a fake context (not used in this branch because element is provided directly).
    class FakeContext:
        async def get_current_page(self):
            class DummyPage:
                async def wait_for_selector(self, selector):
                    return FakeElement()
            return DummyPage()
    # Instantiate DatePickerAction with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Provide a non-ISO date string in MM/DD/YYYY format.
    non_iso_date = "10/31/2023"
    fake_element = FakeElement()
    # Execute the action.
    result = await action.execute(fake_element, non_iso_date)
    # dateutil.parser.parse should parse "10/31/2023" as October 31, 2023
    # and the action should fill the element with the default formatted date "2023-10-31".
    expected_date_str = "2023-10-31"
    assert result is True, "Expected execute to return True for a valid non-ISO date string"
    assert await fake_element.input_value() == expected_date_str, (
        f"Expected element value to be '{expected_date_str}', got '{await fake_element.input_value()}'"
    )
@pytest.mark.asyncio
async def test_page_without_wait_for_selector():
    """
    Test that DatePickerAction.execute returns False and sets last_error correctly
    when the current page returned by context.get_current_page does not have the 'wait_for_selector'
    attribute, simulating a misconfigured context.
    """
    class FakeContext:
        async def get_current_page(self):
            # Return an object that does not implement wait_for_selector.
            return object()
    action = DatePickerAction(context=FakeContext())
    result = await action.execute("dummy-selector", "2023-10-10")
    assert result is False, "Expected execute to return False when current page is misconfigured."
    assert action.last_error is not None, "Expected last_error to be set due to missing wait_for_selector attribute."
    error_str = str(action.last_error)
    assert "has no attribute" in error_str or "object" in error_str, (
        "Expected error message to mention missing 'wait_for_selector' attribute."
    )
@pytest.mark.asyncio
async def test_selector_returns_invalid_element():
    """
    Test that DatePickerAction.execute returns False and sets last_error correctly
    when a selector string is provided and the page.wait_for_selector returns an object
    that does not implement the required fill and input_value methods.
    """
    # Define a fake element that does not have the required fill and input_value methods.
    class FakeElementWithoutFill:
        pass
    # Define a fake page whose wait_for_selector returns an invalid element.
    class FakePage:
        async def wait_for_selector(self, selector):
            return FakeElementWithoutFill()
    # Define a fake context that returns the fake page.
    class FakeContext:
        async def get_current_page(self):
            return FakePage()
    # Instantiate the DatePickerAction with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Execute the action using a selector string.
    result = await action.execute("invalid-selector", "2023-08-08")
    # Verify that the action returns False and last_error indicates a missing 'fill' attribute.
    assert result is False, "Expected execute to return False when the returned element lacks 'fill'"
    assert action.last_error is not None, "Expected last_error to be set for invalid element type"
    assert "has no attribute 'fill'" in str(action.last_error), (
        "Error message should indicate that the provided element lacks the 'fill' attribute."
    )
@pytest.mark.asyncio
async def test_date_string_with_timezone():
    """
    Test that DatePickerAction.execute correctly handles a date string that includes timezone info.
    The timezone and time portion should be ignored and the element filled with the default formatted date ("%Y-%m-%d").
    """
    # Define a fake element simulating a date picker input.
    class FakeElement:
        def __init__(self):
            self.value = ""
        async def fill(self, val):
            self.value = val
        async def input_value(self):
            return self.value
    # Define a fake context that returns a dummy page with a wait_for_selector method.
    class FakeContext:
        async def get_current_page(self):
            class DummyPage:
                async def wait_for_selector(self, selector):
                    return FakeElement()
            return DummyPage()
    # Instantiate DatePickerAction with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Provide a date string with timezone information.
    date_with_timezone = "2023-10-05T12:00:00+02:00"
    fake_element = FakeElement()
    # Execute the action.
    result = await action.execute(fake_element, date_with_timezone)
    # Verify that execution returns True and the element's value is the date portion formatted as "2023-10-05".
    assert result is True, "Expected execute to return True when handling a date string with timezone information"
    assert await fake_element.input_value() == "2023-10-05", (
        f"Expected element value to be '2023-10-05', got '{await fake_element.input_value()}'"
    )
@pytest.mark.asyncio
async def test_unexpected_exception_in_date_parsing(monkeypatch):
    """
    Test that DatePickerAction.execute returns False and sets last_error correctly
    when an unexpected exception (not ParserError) is raised during date parsing.
    """
    # Define a fake element that supports fill and input_value.
    class FakeElement:
        async def fill(self, val):
            self.value = val
        async def input_value(self):
            return getattr(self, "value", "")
    # Define a fake context (not really used because element is provided directly).
    class FakeContext:
        async def get_current_page(self):
            class DummyPage:
                async def wait_for_selector(self, selector):
                    return FakeElement()
            return DummyPage()
    # Monkeypatch the parse function (imported in browser_use.actions) to raise an unexpected exception.
    def fake_parse(value):
        raise TypeError("Unexpected error")
    monkeypatch.setattr("browser_use.actions.parse", fake_parse)
    # Instantiate DatePickerAction with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Execute the action with a valid date string.
    result = await action.execute(FakeElement(), "2023-01-01")
    # Assert that the result is False and last_error contains the unexpected error.
    assert result is False, "Expected execute to return False when an unexpected error occurs during date parsing"
    assert isinstance(action.last_error, TypeError), "Expected last_error to be a TypeError"
    assert "Unexpected error" in str(action.last_error), "Expected the error message to contain 'Unexpected error'"
@pytest.mark.asyncio
async def test_invalid_date_value_none():
    """
    Test that DatePickerAction.execute returns False and sets last_error
    when None is provided as the date_value. Since None does not have the 'strftime'
    method, an AttributeError (or similar error) is expected, and execute should catch it.
    """
    class FakeElement:
        async def fill(self, val):
            self.value = val
        async def input_value(self):
            return getattr(self, 'value', '')
    class FakeContext:
        async def get_current_page(self):
            class FakePage:
                async def wait_for_selector(self, selector):
                    return FakeElement()
            return FakePage()
    # Instantiate the action with the fake context.
    action = DatePickerAction(context=FakeContext())
    # Call execute with a valid FakeElement but an unsupported None for date_value.
    result = await action.execute(FakeElement(), None)
    assert result is False, "Expected execute to return False when date_value is None"
    assert action.last_error is not None, "Expected last_error to be set when date_value is None"
    # The error should mention that NoneType has no attribute 'strftime'
    assert "NoneType" in str(action.last_error), "Expected error message to mention NoneType issues"
@pytest.mark.asyncio
async def test_direct_element_with_context_none():
    """
    Test that DatePickerAction.execute works correctly even if 
    context.get_current_page returns None, when the element is provided directly.
    This confirms that the page obtained from the context is ignored if the element is not a selector,
    ensuring that the action proceeds to process the date input normally.
    """
    # Define a FakeContext that returns None for get_current_page.
    class FakeContext:
        async def get_current_page(self):
            return None
    # Define a FakeElement that supports fill and input_value.
    class FakeElement:
        def __init__(self):
            self.value = ""
        async def fill(self, val):
            self.value = val
        async def input_value(self):
            return self.value
    # Instantiate DatePickerAction with the FakeContext.
    action = DatePickerAction(context=FakeContext())
    # Define a valid date string using the default format.
    valid_date = "2023-12-01"
    fake_element = FakeElement()
    # Execute the action.
    result = await action.execute(fake_element, valid_date)
    # Validate that the action returns True, and that the element's value is correctly set.
    assert result is True, "Expected execute to return True when element is provided directly even if get_current_page returns None"
    assert await fake_element.input_value() == "2023-12-01", "Expected the element's value to be formatted correctly with the default date format"