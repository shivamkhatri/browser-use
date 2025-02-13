import datetime
import pytest
from browser_use.agent.prompts import AgentMessagePrompt
from browser_use.agent.prompts import AgentMessagePrompt, PlannerPrompt, SystemPrompt
from browser_use.agent.views import ActionResult, AgentStepInfo
from datetime import datetime
from langchain_core.messages import SystemMessage
from types import SimpleNamespace

def test_agent_message_prompt_get_user_message_with_and_without_screenshot():
    """
    Test AgentMessagePrompt.get_user_message behavior with and without a screenshot.
    Verifies that when a screenshot is provided with use_vision True, the HumanMessage content is a list
    containing an 'image_url' item, and when no screenshot is available, the HumanMessage content is a string
    containing the URL.
    """
    class FakeElementTree:
        def __init__(self, text):
            self.text = text
        def clickable_elements_to_string(self, include_attributes):
            return self.text
    # Create a fake state with a screenshot (simulate the vision branch)
    state_with_screenshot = SimpleNamespace(
        url="http://example.com",
        tabs="Tab1, Tab2",
        pixels_above=100,
        pixels_below=50,
        screenshot="dummy_base64_screenshot",
        element_tree=FakeElementTree("Button: Submit")
    )
    prompt_with_screenshot = AgentMessagePrompt(
        state_with_screenshot,
        result=[],
        include_attributes=[],
        step_info=None
    )
    human_message_with = prompt_with_screenshot.get_user_message(use_vision=True)
    # When a screenshot exists and vision is used, expect a list with an image message.
    assert isinstance(human_message_with.content, list)
    image_items = [item for item in human_message_with.content if item.get('type') == 'image_url']
    assert len(image_items) > 0, "Expected an image_url item in the message content"
    # Create a fake state without a screenshot (simulate missing visual context)
    state_without_screenshot = SimpleNamespace(
        url="http://example.com",
        tabs="Tab1, Tab2",
        pixels_above=0,
        pixels_below=0,
        screenshot=None,
        element_tree=FakeElementTree("Input: Username")
    )
    prompt_without_screenshot = AgentMessagePrompt(
        state_without_screenshot,
        result=[],
        include_attributes=[],
        step_info=None
    )
    human_message_without = prompt_without_screenshot.get_user_message(use_vision=True)
    # When there is no screenshot, expect the content to be a string.
    assert isinstance(human_message_without.content, str)
    assert "http://example.com" in human_message_without.content
def test_agent_message_prompt_with_step_info_and_results():
    """
    Test AgentMessagePrompt.get_user_message when step_info and result objects are provided.
    Verifies that the message string includes step info details and action result information
    (both extracted content and error messages), ensuring proper formatting of the output state description.
    """
    class FakeElementTree:
        def __init__(self, text):
            self.text = text
        def clickable_elements_to_string(self, include_attributes):
            return self.text
    fake_state = SimpleNamespace(
        url="http://test.com",
        tabs="Home, About, Contact",
        pixels_above=20,
        pixels_below=20,
        screenshot=None,
        element_tree=FakeElementTree("Link: Home Page")
    )
    fake_step_info = SimpleNamespace(step_number=1, max_steps=5)
    action_result1 = ActionResult()
    action_result1.extracted_content = "Step1 completed successfully."
    action_result1.error = None
    long_error = "X" * 500  # error string longer than typical max_error_length.
    action_result2 = ActionResult()
    action_result2.extracted_content = ""
    action_result2.error = long_error
    prompt = AgentMessagePrompt(
        state=fake_state,
        result=[action_result1, action_result2],
        include_attributes=[],
        step_info=fake_step_info,
        max_error_length=300  # for testing truncation.
    )
    human_message = prompt.get_user_message(use_vision=True)
    assert isinstance(human_message.content, str)
    message_content = human_message.content
    assert "http://test.com" in message_content
    # Check step info is included (displaying step_number+1 out of max_steps)
    assert "Current step: 2/5" in message_content
    # Check the extracted content and the truncated error
    assert "Step1 completed successfully." in message_content
    truncated_error = long_error[-300:]
    assert truncated_error in message_content
def test_planner_prompt_get_system_message():
    """
    Test PlannerPrompt.get_system_message returns a SystemMessage containing the planning agent prompt,
    ensuring that all expected JSON fields and instructions are present.
    """
    planner_prompt = PlannerPrompt(action_description="Dummy action function descriptions")
    system_message = planner_prompt.get_system_message()
    # Verify the returned message is an instance of SystemMessage
    assert isinstance(system_message, SystemMessage)
    content = system_message.content
    assert "You are a planning agent" in content, "Expected planning agent instructions missing"
    assert "state_analysis" in content, "Expected 'state_analysis' field not found"
    assert "progress_evaluation" in content, "Expected 'progress_evaluation' field not found"
    assert "challenges" in content, "Expected 'challenges' field not found"
    assert "next_steps" in content, "Expected 'next_steps' field not found"
    assert "reasoning" in content, "Expected 'reasoning' field not found"
def test_system_prompt_get_system_message_includes_all_sections():
    """
    Test that SystemPrompt.get_system_message returns a SystemMessage containing the full prompt.
    This ensures that the output includes input instructions, important rules, the function descriptions
    we pass in, and the maximum actions limit.
    """
    dummy_action_description = "Dummy action function: perform_action(param)"
    max_actions = 5
    system_prompt = SystemPrompt(action_description=dummy_action_description, max_actions_per_step=max_actions)
    system_message = system_prompt.get_system_message()
    assert isinstance(system_message, SystemMessage)
    content = system_message.content
    assert "INPUT STRUCTURE:" in content, "Input instructions not found in system message content"
    assert "1. RESPONSE FORMAT:" in content, "Important rules not found in system message content"
    assert dummy_action_description in content, "Dummy action description not included in system message content"
    assert f"- use maximum {max_actions} actions per sequence" in content, "Max actions limit not properly included in system message content"
def test_agent_message_prompt_with_screenshot_but_use_vision_false():
    """
    Test that AgentMessagePrompt.get_user_message returns a string (ignoring the screenshot)
    when use_vision is False, even if a screenshot exists in the state.
    This ensures that the vision branch is bypassed when not requested.
    """
    class FakeElementTree:
        def __init__(self, text):
            self.text = text
        def clickable_elements_to_string(self, include_attributes):
            return self.text
    state_with_screenshot = SimpleNamespace(
        url="http://vision-false.com",
        tabs="Main, Extra",
        pixels_above=10,
        pixels_below=10,
        screenshot="dummy_base64_string",
        element_tree=FakeElementTree("Button: OK")
    )
    prompt = AgentMessagePrompt(
        state_with_screenshot,
        result=[],
        include_attributes=[],
        step_info=None
    )
    human_message = prompt.get_user_message(use_vision=False)
    assert isinstance(human_message.content, str)
    assert "http://vision-false.com" in human_message.content
def test_system_prompt_important_rules_content():
    """
    Test that SystemPrompt.important_rules returns a string that includes
    the expected key sections and correctly includes the maximum actions limit.
    """
    dummy_action_description = "perform_action(param)"
    max_actions = 3
    sp = SystemPrompt(action_description=dummy_action_description, max_actions_per_step=max_actions)
    rules_output = sp.important_rules()
    assert "1. RESPONSE FORMAT:" in rules_output
    assert "2. ACTIONS:" in rules_output
    assert f"use maximum {max_actions} actions per sequence" in rules_output
def test_agent_message_prompt_error_no_truncation_if_short():
    """
    Test that AgentMessagePrompt.get_user_message includes the full error message
    without truncation when the error message is shorter than max_error_length.
    """
    class FakeElementTree:
        def __init__(self, text):
            self.text = text
        def clickable_elements_to_string(self, include_attributes):
            return self.text
    fake_state = SimpleNamespace(
        url="http://short-error.com",
        tabs="TabA, TabB",
        pixels_above=0,
        pixels_below=0,
        screenshot=None,
        element_tree=FakeElementTree("Text: Sample")
    )
    short_error = "This is a short error."
    action_result = ActionResult()
    action_result.extracted_content = ""
    action_result.error = short_error
    prompt = AgentMessagePrompt(
        state=fake_state,
        result=[action_result],
        include_attributes=[],
        step_info=None,
        max_error_length=300
    )
    human_message = prompt.get_user_message(use_vision=True)
    assert isinstance(human_message.content, str)
    assert short_error in human_message.content
def test_agent_message_prompt_empty_elements():
    """
    Test that AgentMessagePrompt.get_user_message produces the expected output when 
    the clickable_elements_to_string returns an empty string, simulating an empty page.
    Verifies that the generated state description contains 'empty page' and includes the correct URL.
    """
    class FakeEmptyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return ""
    fake_state = SimpleNamespace(
        url="http://empty.com",
        tabs="Tab1, Tab2",
        pixels_above=0,
        pixels_below=0,
        screenshot=None,
        element_tree=FakeEmptyElementTree()
    )
    prompt = AgentMessagePrompt(
        state=fake_state,
        result=[],
        include_attributes=[],
        step_info=None
    )
    human_message = prompt.get_user_message(use_vision=True)
    assert isinstance(human_message.content, str)
    content = human_message.content
    assert "empty page" in content, "Expected 'empty page' in state description when no elements are present"
    assert "http://empty.com" in content
def test_agent_message_prompt_formatting_elements_with_pixels_below():
    """
    Test that AgentMessagePrompt.get_user_message correctly formats the state description when
    there are no pixels above but some pixels below.
    This test verifies that the interactive elements section includes a "[Start of page]" header,
    a scroll indicator for the pixels below, the interactive elements text, and the correct URL.
    """
    class FakeElementTree:
        def __init__(self, text):
            self.text = text
        def clickable_elements_to_string(self, include_attributes):
            return self.text
    fake_state = SimpleNamespace(
        url="http://formatting.com",
        tabs="Main",
        pixels_above=0,
        pixels_below=100,
        screenshot=None,
        element_tree=FakeElementTree("Radio: Option1")
    )
    prompt = AgentMessagePrompt(
        state=fake_state,
        result=[],
        include_attributes=[],
        step_info=None
    )
    human_message = prompt.get_user_message(use_vision=True)
    content = human_message.content
    assert isinstance(content, str)
    # Verify that "[Start of page]" is included within the interactive elements section.
    assert "[Start of page]" in content, "Content should include '[Start of page]' in the interactive elements section"
    assert f"... {fake_state.pixels_below} pixels below - scroll or extract content to see more ..." in content
    assert "Radio: Option1" in content
    assert "http://formatting.com" in content
def test_agent_message_prompt_with_both_extracted_and_error():
    """
    Test that AgentMessagePrompt.get_user_message correctly includes both extracted_content 
    and error when both are present in an action result.
    """
    class FakeElementTree:
        def __init__(self, text):
            self.text = text
        def clickable_elements_to_string(self, include_attributes):
            return self.text
    fake_state = SimpleNamespace(
        url="http://both-fields.com",
        tabs="Home, Services",
        pixels_above=30,
        pixels_below=30,
        screenshot=None,
        element_tree=FakeElementTree("Button: Next")
    )
    action_result = ActionResult()
    action_result.extracted_content = "Data extracted successfully."
    action_result.error = "Error occurred during execution."
    prompt = AgentMessagePrompt(
        state=fake_state,
        result=[action_result],
        include_attributes=[],
        step_info=None,
        max_error_length=100
    )
    human_message = prompt.get_user_message(use_vision=True)
    assert isinstance(human_message.content, str)
    content = human_message.content
    assert "Action result 1/1: Data extracted successfully." in content, "Extracted content missing in output"
    assert "Action error 1/1: ...Error occurred during execution." in content, "Error message missing or not formatted as expected"
    assert "http://both-fields.com" in content
def test_agent_message_prompt_with_no_result():
    """
    Test that AgentMessagePrompt.get_user_message properly handles when result is None.
    Verifies that no action result or error messages are appended to the state description.
    """
    class FakeElementTree:
        def __init__(self, text):
            self.text = text
        def clickable_elements_to_string(self, include_attributes):
            return self.text
    fake_state = SimpleNamespace(
        url="http://noresult.com",
        tabs="TabA, TabB",
        pixels_above=15,
        pixels_below=15,
        screenshot=None,
        element_tree=FakeElementTree("Link: Dashboard")
    )
    # Pass result as None.
    prompt = AgentMessagePrompt(
        state=fake_state,
        result=None,
        include_attributes=[],
        step_info=None
    )
    human_message = prompt.get_user_message(use_vision=False)
    assert isinstance(human_message.content, str)
    content = human_message.content
    # Verify that the state description contains the page URL and interactive elements.
    assert "http://noresult.com" in content
    assert "Link: Dashboard" in content
    # Verify that no action result or action error details are present.
    assert "Action result" not in content
    assert "Action error" not in content
def test_agent_message_prompt_without_step_info_includes_date_only():
    """
    Test that when no step_info is provided, the output of get_user_message
    includes the current date and time, but does not include any step count details.
    """
    class FakeElementTree:
        def __init__(self, text):
            self.text = text
        def clickable_elements_to_string(self, include_attributes):
            return self.text
    fake_state = SimpleNamespace(
        url="http://nostep.com",
        tabs="Main",
        pixels_above=0,
        pixels_below=0,
        screenshot=None,
        element_tree=FakeElementTree("Paragraph: Welcome")
    )
    prompt = AgentMessagePrompt(
        state=fake_state,
        result=[],
        include_attributes=[],
        step_info=None
    )
    human_message = prompt.get_user_message(use_vision=False)
    content = human_message.content
    # Check that the output includes the current date and time.
    assert "Current date and time:" in content, "Output should include current date and time."
    # And that it does NOT include any step count information.
    assert "Current step:" not in content, "Output should not include step details when step_info is None."
def test_agent_message_prompt_with_empty_action_result_fields():
    """
    Test that AgentMessagePrompt.get_user_message does not include any action result or error details
    when an ActionResult item has both extracted_content and error as None.
    This ensures that no additional output is appended to the state description in such cases.
    """
    class FakeElementTree:
        def __init__(self, text):
            self.text = text
        def clickable_elements_to_string(self, include_attributes):
            return self.text
    fake_state = SimpleNamespace(
        url="http://empty-result.com",
        tabs="Main, Secondary",
        pixels_above=0,
        pixels_below=0,
        screenshot=None,
        element_tree=FakeElementTree("Button: Continue")
    )
    # Create an ActionResult where both extracted_content and error are None.
    empty_action_result = ActionResult()
    empty_action_result.extracted_content = None
    empty_action_result.error = None
    prompt = AgentMessagePrompt(
        state=fake_state,
        result=[empty_action_result],
        include_attributes=[],
        step_info=None,
        max_error_length=300
    )
    human_message = prompt.get_user_message(use_vision=False)
    assert isinstance(human_message.content, str)
    content = human_message.content
    # Verify that with both fields None, no 'Action result' or 'Action error' strings are added.
    assert "Action result" not in content, "Unexpected 'Action result' found in output when fields are None."
    assert "Action error" not in content, "Unexpected 'Action error' found in output when fields are None."
    # Also verify the primary content like URL and interactive element are present.
    assert "http://empty-result.com" in content, "Expected URL not found in content."
    assert "Button: Continue" in content
def test_agent_message_prompt_formatting_elements_with_pixels_above_only():
    """
    Test that AgentMessagePrompt.get_user_message correctly formats the state description when
    only 'pixels_above' is provided (and 'pixels_below' is 0). Verifies that the output includes the
    above content hint and ends with "[End of page]" indicating no content below.
    """
    class FakeElementTree:
        def __init__(self, text):
            self.text = text
        def clickable_elements_to_string(self, include_attributes):
            return self.text
    fake_state = SimpleNamespace(
        url="http://aboveonly.com",
        tabs="Tab1",
        pixels_above=50,
        pixels_below=0,
        screenshot=None,
        element_tree=FakeElementTree("Paragraph: Header content")
    )
    prompt = AgentMessagePrompt(
        state=fake_state,
        result=[],
        include_attributes=[],
        step_info=None
    )
    human_message = prompt.get_user_message(use_vision=False)
    content = human_message.content
    # Check that the state URL is included
    assert "http://aboveonly.com" in content, "State URL missing in output"
    # Check that the above content hint is included
    expected_above_hint = f"... {fake_state.pixels_above} pixels above - scroll or extract content to see more ..."
    assert expected_above_hint in content, "Pixels above hint missing in output"
    # Check that since pixels_below is 0 the output ends with '[End of page]'
    assert content.strip().endswith("[End of page]"), "Expected '[End of page]' at the end of content when pixels_below is 0"
    # Verify that the interactive element text is present
    assert "Paragraph: Header content" in content, "Interactive element text missing in output"
def test_agent_message_prompt_formatting_elements_with_pixels_above_only():
    """
    Test that AgentMessagePrompt.get_user_message correctly formats the interactive elements part
    when only 'pixels_above' is provided (and 'pixels_below' is 0). This verifies that the output includes
    the above content hint and that within the interactive elements block, it ends with "[End of page]".
    """
    class FakeElementTree:
        def __init__(self, text):
            self.text = text
        def clickable_elements_to_string(self, include_attributes):
            return self.text
    fake_state = SimpleNamespace(
        url="http://aboveonly.com",
        tabs="Tab1",
        pixels_above=50,
        pixels_below=0,
        screenshot=None,
        element_tree=FakeElementTree("Paragraph: Header content")
    )
    prompt = AgentMessagePrompt(
        state=fake_state,
        result=[],
        include_attributes=[],
        step_info=None
    )
    human_message = prompt.get_user_message(use_vision=False)
    content = human_message.content
    # Verify state URL inclusion
    assert "http://aboveonly.com" in content, "State URL missing in output"
    # Check that the above content hint is included in the interactive element part.
    expected_above_hint = f"... {fake_state.pixels_above} pixels above - scroll or extract content to see more ..."
    assert expected_above_hint in content, "Pixels above hint missing in output"
    # Extract interactive elements block:
    # The interactive elements block is between "Interactive elements from current page:" and "Current date and time:"
    start_marker = "Interactive elements from current page:"
    end_marker = "Current date and time:"
    assert start_marker in content, "Start marker for interactive elements not found"
    assert end_marker in content, "End marker for interactive elements not found"
    interactive_block = content.split(start_marker)[1].split(end_marker)[0]
    # Remove any extra whitespace/newlines from the block.
    interactive_block = interactive_block.strip()
    # Check that the block ends with "[End of page]"
    assert interactive_block.endswith("[End of page]"), "Expected '[End of page]' at the end of the interactive elements block when pixels_below is 0"
    # Verify that the interactive element text is present.
    assert "Paragraph: Header content" in interactive_block, "Interactive element text missing in output"import pytest
import datetime
from datetime import datetime
from types import SimpleNamespace

from browser_use.agent.prompts import AgentMessagePrompt, PlannerPrompt, SystemPrompt
from browser_use.agent.views import ActionResult, AgentStepInfo
from langchain_core.messages import HumanMessage, SystemMessage


def test_agent_message_prompt_with_none_pixels():
    """
    Test that AgentMessagePrompt.get_user_message correctly handles a state where
    pixels_above and pixels_below are None. It verifies that the interactive elements block
    uses default formatting (adding [Start of page] and [End of page]) without any scroll hints.
    """
    # Define a fake element tree that returns a non-empty string.
    class FakeElementTree:
        def __init__(self, text):
            self.text = text
        def clickable_elements_to_string(self, include_attributes):
            return self.text

    # Create a fake state with pixels_above and pixels_below set to None, and no screenshot.
    fake_state = SimpleNamespace(
        url="http://nonepixels.com",
        tabs="Main, Secondary",
        pixels_above=None,
        pixels_below=None,
        screenshot=None,
        element_tree=FakeElementTree("Div: Content block")
    )
    # No results and no step_info provided.
    prompt = AgentMessagePrompt(
        state=fake_state,
        result=[],
        include_attributes=[],
        step_info=None
    )
    human_message = prompt.get_user_message(use_vision=True)
    
    # Assert that the content is a string (since no screenshot and vision branch is not triggered)
    assert isinstance(human_message.content, str)
    content = human_message.content
    
    # Check that the URL is included
    assert "http://nonepixels.com" in content, "The URL should be present in the state description."
    
    # Verify that the interactive elements block starts with "[Start of page]"
    assert "[Start of page]" in content, "The interactive elements block should include '[Start of page]'."
    
    # Verify that the interactive elements block ends with "[End of page]" since no pixels_below exist.
    assert content.rstrip().endswith("[End of page]"), "The interactive elements block should end with '[End of page]' when pixels_below is None or 0."
    
    # Ensure that no scroll/hint text related to pixels is present since both pixels_above and pixels_below are None.
    assert "pixels above" not in content, "No pixels above notice should be present when pixels_above is None."
    assert "pixels below" not in content, "No pixels below notice should be present when pixels_below is None."
import pytest
import datetime
from datetime import datetime
from types import SimpleNamespace

from browser_use.agent.prompts import AgentMessagePrompt, PlannerPrompt, SystemPrompt
from browser_use.agent.views import ActionResult, AgentStepInfo
from langchain_core.messages import HumanMessage, SystemMessage


def test_agent_message_prompt_with_none_pixels():
    """
    Test that AgentMessagePrompt.get_user_message correctly handles a state where
    pixels_above and pixels_below are None. It verifies that the interactive elements block
    uses default formatting with [Start of page] at the beginning and [End of page] at the end,
    even though additional state information (like current date/time) is appended after the block.
    """
    # Define a fake element tree that returns a non-empty string.
    class FakeElementTree:
        def __init__(self, text):
            self.text = text
        def clickable_elements_to_string(self, include_attributes):
            return self.text

    # Create a fake state with pixels_above and pixels_below set to None, and no screenshot.
    fake_state = SimpleNamespace(
        url="http://nonepixels.com",
        tabs="Main, Secondary",
        pixels_above=None,
        pixels_below=None,
        screenshot=None,
        element_tree=FakeElementTree("Div: Content block")
    )
    # No results and no step_info provided.
    prompt = AgentMessagePrompt(
        state=fake_state,
        result=[],
        include_attributes=[],
        step_info=None
    )
    human_message = prompt.get_user_message(use_vision=True)
    
    # Assert that the content is a string (since no screenshot and vision branch is not triggered)
    assert isinstance(human_message.content, str)
    content = human_message.content
    
    # Check that the URL is included
    assert "http://nonepixels.com" in content, "The URL should be present in the state description."
    
    # Extract the interactive elements block: it is located between the marker and the date info.
    start_marker = "Interactive elements from current page:"
    end_marker = "Current date and time:"
    assert start_marker in content, "Missing the interactive elements start marker."
    # If the end_marker exists, extract only the interactive block.
    if end_marker in content:
        interactive_block = content.split(start_marker)[1].split(end_marker)[0]
    else:
        interactive_block = content.split(start_marker)[1]
    interactive_block = interactive_block.strip()
    
    # Verify that the interactive elements block starts with "[Start of page]"
    assert interactive_block.startswith("[Start of page]"), "The interactive elements block should include '[Start of page]'."
    
    # Verify that the interactive elements block ends with "[End of page]" since no pixels_below exist.
    assert interactive_block.endswith("[End of page]"), "The interactive elements block should end with '[End of page]' when pixels_below is None or 0."
    
    # Ensure that no scroll/hint text related to pixels is present since both pixels_above and pixels_below are None.
    assert "pixels above" not in interactive_block, "No pixels above notice should be present when pixels_above is None."
    assert "pixels below" not in interactive_block, "No pixels below notice should be present when pixels_below is None."

# ... existing tests
import pytest
import datetime
from datetime import datetime
from types import SimpleNamespace

from browser_use.agent.prompts import AgentMessagePrompt, PlannerPrompt, SystemPrompt
from browser_use.agent.views import ActionResult, AgentStepInfo
from langchain_core.messages import HumanMessage, SystemMessage


def test_agent_message_prompt_with_none_pixels():
    """
    Test that AgentMessagePrompt.get_user_message correctly handles a state where
    pixels_above and pixels_below are None. It verifies that the interactive elements block
    uses default formatting with [Start of page] at the beginning and [End of page] at the end,
    by extracting the interactive elements block from the overall output.
    """
    # Define a fake element tree that returns a non-empty string.
    class FakeElementTree:
        def __init__(self, text):
            self.text = text
        def clickable_elements_to_string(self, include_attributes):
            return self.text

    # Create a fake state with pixels_above and pixels_below set to None, and no screenshot.
    fake_state = SimpleNamespace(
        url="http://nonepixels.com",
        tabs="Main, Secondary",
        pixels_above=None,
        pixels_below=None,
        screenshot=None,
        element_tree=FakeElementTree("Div: Content block")
    )
    # No results and no step_info provided.
    prompt = AgentMessagePrompt(
        state=fake_state,
        result=[],
        include_attributes=[],
        step_info=None
    )
    human_message = prompt.get_user_message(use_vision=True)
    
    # Assert that the content is a string (since no screenshot and vision branch is not triggered)
    assert isinstance(human_message.content, str)
    content = human_message.content
    
    # Check that the URL is included
    assert "http://nonepixels.com" in content, "The URL should be present in the state description."
    
    # Extract the interactive elements block using the defined markers.
    start_marker = "Interactive elements from current page:"
    end_marker = "Current date and time:"
    assert start_marker in content, "Missing the interactive elements start marker."
    assert end_marker in content, "Missing the current date and time marker."
    # Extract only the interactive block.
    interactive_block = content.split(start_marker)[1].split(end_marker)[0]
    interactive_block = interactive_block.strip()
    
    # Verify that the interactive elements block starts with "[Start of page]"
    assert interactive_block.startswith("[Start of page]"), "The interactive elements block should include '[Start of page]'."
    
    # Verify that the interactive elements block ends with "[End of page]" since no pixels_below exist.
    assert interactive_block.endswith("[End of page]"), "The interactive elements block should end with '[End of page]' when pixels_below is None or 0."
    
    # Ensure that no scroll/hint text related to pixels is present in the interactive block since both pixels_above and pixels_below are None.
    assert "pixels above" not in interactive_block, "No pixels above notice should be present when pixels_above is None."
    assert "pixels below" not in interactive_block, "No pixels below notice should be present when pixels_below is None."
    
# ... existing tests
