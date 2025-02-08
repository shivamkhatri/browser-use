import pytest
from types import SimpleNamespace
from browser_use.agent.prompts import AgentMessagePrompt, SystemPrompt, PlannerPrompt
from langchain_core.messages import HumanMessage, SystemMessage
import datetime
import re

def test_agent_message_prompt_get_user_message_with_and_without_vision():
    """
    Test AgentMessagePrompt.get_user_message returns the correct message structure
    when use_vision is True (i.e., returns a list with image data) and when False (i.e., returns a plain string).
    """
    class DummyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return "dummy interactive element"
    dummy_state = SimpleNamespace(
        url="http://example.com",
        tabs=["http://example.com", "http://test.com"],
        element_tree=DummyElementTree(),
        pixels_above=10,
        pixels_below=20,
        screenshot="dummy_base64_image_string"
    )
    prompt = AgentMessagePrompt(state=dummy_state)
    message_with_vision = prompt.get_user_message(use_vision=True)
    assert isinstance(message_with_vision, HumanMessage), "The returned message should be of type HumanMessage."
    assert isinstance(message_with_vision.content, list), (
        "When use_vision is True and screenshot exists, content should be a list."
    )
    types_in_content = {item.get('type') for item in message_with_vision.content if isinstance(item, dict)}
    assert "text" in types_in_content, "The message content should include a 'text' item."
    assert "image_url" in types_in_content, "The message content should include an 'image_url' item."
    message_without_vision = prompt.get_user_message(use_vision=False)
    assert isinstance(message_without_vision, HumanMessage), "The returned message should be of type HumanMessage."
    assert isinstance(message_without_vision.content, str), (
        "When use_vision is False, content should be a string."
    )

def test_planner_prompt_get_system_message():
    """
    Test that PlannerPrompt.get_system_message returns a SystemMessage containing the expected JSON fields.
    """
    planner_prompt = PlannerPrompt(action_description="noop_action_function")
    system_message = planner_prompt.get_system_message()
    assert isinstance(system_message, SystemMessage), "Expected a SystemMessage instance."
    content = system_message.content
    expected_keys = ["state_analysis", "progress_evaluation", "challenges", "next_steps", "reasoning"]
    for key in expected_keys:
        assert key in content, f"Expected key '{key}' not found in the system message content."

def test_system_prompt_get_system_message_content():
    """
    Test that SystemPrompt.get_system_message returns a SystemMessage with content that includes
    the input format, important rules, and the given action description.
    """
    action_description = "test_action_function"
    max_actions = 5
    sp = SystemPrompt(action_description=action_description, max_actions_per_step=max_actions)
    input_fmt = sp.input_format()
    important_rules = sp.important_rules()
    system_message = sp.get_system_message()
    assert isinstance(system_message, SystemMessage), "Expected a SystemMessage instance."
    content = system_message.content
    assert isinstance(content, str), "SystemMessage content should be a string."
    assert "INPUT STRUCTURE:" in content, "Input structure instructions not found in the system message."
    assert "RESPONSE FORMAT:" in content, "Important rules with the response format are missing in the system message."
    assert f"Functions:\n{action_description}" in content, "The action description is not correctly included in the system message."

def test_agent_message_prompt_empty_elements_and_results():
    """
    Test AgentMessagePrompt.get_user_message when the page has no clickable elements and a result includes
    extracted content and an error exceeding the max_error_length. This test verifies that:
    - The message indicates an empty page.
    - The extracted content and error (trimmed to max_error_length) are appended.
    - Step information and the current date/time are included in the message.
    """
    class DummyEmptyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return ""
    dummy_state = SimpleNamespace(
        url="http://empty.com",
        tabs=["http://empty.com"],
        element_tree=DummyEmptyElementTree(),
        pixels_above=0,
        pixels_below=0,
        screenshot=""
    )
    long_error = "E" * 500
    dummy_result = [SimpleNamespace(extracted_content="Dummy extracted result", error=long_error)]
    dummy_step_info = SimpleNamespace(step_number=0, max_steps=5)
    prompt = AgentMessagePrompt(
        state=dummy_state,
        result=dummy_result,
        max_error_length=400,
        step_info=dummy_step_info
    )
    message = prompt.get_user_message(use_vision=False)
    assert isinstance(message, HumanMessage), "Expected a HumanMessage instance."
    assert isinstance(message.content, str), "Expected the message content to be a string when use_vision is False."
    content = message.content
    assert "empty page" in content, "The output should indicate an empty page when no clickable elements are found."
    assert "Action result 1/1: Dummy extracted result" in content, "Extracted content not found in message output."
    expected_trimmed_error = long_error[-400:]
    assert f"...{expected_trimmed_error}" in content, "The error message was not correctly trimmed to max_error_length."
    assert "Current step: 1/5" in content, "Step information is not correctly included in the message."
    assert "Current date and time:" in content, "Current date and time information is missing in the output."

def test_system_prompt_important_rules_includes_max_actions():
    """
    Test that SystemPrompt.important_rules() returns a string that includes the max_actions_per_step value.
    This verifies that the maximum actions information is correctly embedded in the important rules description.
    """
    max_actions = 7
    action_description = "dummy_action_function"
    sp = SystemPrompt(action_description=action_description, max_actions_per_step=max_actions)
    important_rules_text = sp.important_rules()
    expected_text = f"   - use maximum {max_actions} actions per sequence"
    assert expected_text in important_rules_text, (
        f"Expected important rules to include '{expected_text}', but got: {important_rules_text}"
    )

def test_agent_message_prompt_multiple_results():
    """
    Test that AgentMessagePrompt.get_user_message correctly concatenates multiple results.
    This verifies that extracted content and error messages from multiple results are appended 
    with proper numbering and that errors are trimmed to the max_error_length.
    """
    class DummyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return "Element A, Element B"
    dummy_state = SimpleNamespace(
        url="http://multiresult.com",
        tabs=["http://multiresult.com", "http://other.com"],
        element_tree=DummyElementTree(),
        pixels_above=5,
        pixels_below=5,
        screenshot=""
    )
    result1 = SimpleNamespace(extracted_content="Extracted1", error="")
    long_error = "E" * 450
    result2 = SimpleNamespace(extracted_content="", error=long_error)
    prompt = AgentMessagePrompt(
        state=dummy_state,
        result=[result1, result2],
        max_error_length=400,
        step_info=SimpleNamespace(step_number=2, max_steps=10)
    )
    message = prompt.get_user_message(use_vision=False)
    content = message.content
    assert "Action result 1/2: Extracted1" in content, "Extracted content from first result not found."
    expected_trimmed_error = long_error[-400:]
    assert f"Action error 2/2: ...{expected_trimmed_error}" in content, "Trimmed error message for second result incorrect."
    assert "Element A, Element B" in content, "Clickable element text not included in the message content."

def test_agent_message_prompt_include_attributes():
    """
    Test that AgentMessagePrompt.get_user_message correctly passes the include_attributes list to the
    element_tree.clickable_elements_to_string method and uses its result in the output.
    """
    class DummySpyElementTree:
        def __init__(self):
            self.called_with = None
        def clickable_elements_to_string(self, include_attributes):
            self.called_with = include_attributes
            return "Attributes: " + ", ".join(include_attributes) if include_attributes else "no attributes"
    spy_tree = DummySpyElementTree()
    dummy_state = SimpleNamespace(
        url="http://attributes-test.com",
        tabs=["http://attributes-test.com"],
        element_tree=spy_tree,
        pixels_above=0,
        pixels_below=0,
        screenshot=""
    )
    include_attrs = ["attr1", "attr2", "attr3"]
    prompt = AgentMessagePrompt(state=dummy_state, include_attributes=include_attrs)
    message = prompt.get_user_message(use_vision=False)
    assert spy_tree.called_with == include_attrs, (
        f"Expected clickable_elements_to_string to be called with {include_attrs}, but got {spy_tree.called_with}"
    )
    content = message.content
    assert "Attributes: attr1, attr2, attr3" in content, (
        "The output should include the element tree string with the provided attributes."
    )

def test_agent_message_prompt_without_step_info():
    """
    Test that AgentMessagePrompt.get_user_message functions correctly when no step_info (and no result)
    is provided. The test verifies that the message includes the current date and time,
    but does not include step number information.
    """
    class DummyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return "Dummy interactive element text"
    dummy_state = SimpleNamespace(
        url="http://nostepinfo.com",
        tabs=["http://nostepinfo.com"],
        element_tree=DummyElementTree(),
        pixels_above=0,
        pixels_below=0,
        screenshot=""
    )
    prompt = AgentMessagePrompt(
        state=dummy_state,
        result=None,
        step_info=None
    )
    message = prompt.get_user_message(use_vision=False)
    assert isinstance(message, HumanMessage), "Expected a HumanMessage instance."
    content = message.content
    assert "Current date and time:" in content, "Current date and time should be included in the message."
    assert "Current step:" not in content, "Step information should be omitted when step_info is None."
    assert "Dummy interactive element text" in content, "Element tree text not found in the message content."

def test_agent_message_prompt_empty_tabs_in_state():
    """
    Test that AgentMessagePrompt.get_user_message correctly handles an empty tabs list in the browser state.
    The test verifies that the output message contains "Available tabs:" followed by an empty list,
    and that the rest of the message is formatted as expected.
    """
    class DummyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return "dummy interactive element"
    dummy_state = SimpleNamespace(
        url="http://emptytabs.com",
        tabs=[],
        element_tree=DummyElementTree(),
        pixels_above=0,
        pixels_below=0,
        screenshot=""
    )
    prompt = AgentMessagePrompt(state=dummy_state)
    message = prompt.get_user_message(use_vision=False)
    assert isinstance(message, HumanMessage), "Expected a HumanMessage instance."
    content = message.content
    assert "Available tabs:" in content, "Expected 'Available tabs:' to be in the message."
    assert "[]" in content, "Expected an empty list representation for tabs in the message."
    assert "dummy interactive element" in content, "Expected clickable elements to be in the message content."
    assert "http://emptytabs.com" in content, "Expected the state's URL to be present in the message content."

def test_agent_message_prompt_formatting_page_markers():
    """
    Test that AgentMessagePrompt.get_user_message correctly adds "[Start of page]" and "[End of page]"
    markers when there is non-empty clickable element text and both pixels_above and pixels_below are zero.
    """
    class DummyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return "Test element for formatting"
    dummy_state = SimpleNamespace(
        url="http://formattingtest.com",
        tabs=["http://formattingtest.com"],
        element_tree=DummyElementTree(),
        pixels_above=0,
        pixels_below=0,
        screenshot=""
    )
    prompt = AgentMessagePrompt(state=dummy_state)
    message = prompt.get_user_message(use_vision=False)
    assert isinstance(message, HumanMessage), "Expected a HumanMessage instance."
    content = message.content
    assert isinstance(content, str), "Expected the message content to be a string when use_vision is False."
    assert "[Start of page]" in content, "Content should include '[Start of page]' when no pixels above are provided."
    assert "[End of page]" in content, "Content should include '[End of page]' when no pixels below are provided."
    assert "Test element for formatting" in content, "Clickable element text from the DummyElementTree is missing."
    assert "Current url: http://formattingtest.com" in content, "State URL is not correctly included in the message content."
    assert "Available tabs:" in content, "The message should include an 'Available tabs:' line."

def test_agent_message_prompt_short_error():
    """
    Test that AgentMessagePrompt.get_user_message correctly appends a short error message
    (i.e., when the error's length is lower than max_error_length) without trimming any characters.
    The test verifies that the full error string is included in the output with the required "..." prefix.
    """
    class DummyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return "dummy clickable element"
    dummy_state = SimpleNamespace(
        url="http://shorterror.com",
        tabs=["http://shorterror.com"],
        element_tree=DummyElementTree(),
        pixels_above=0,
        pixels_below=0,
        screenshot=""
    )
    short_error = "short err"
    dummy_result = [SimpleNamespace(extracted_content="Extraction OK", error=short_error)]
    prompt = AgentMessagePrompt(
        state=dummy_state,
        result=dummy_result,
        max_error_length=400,
        step_info=SimpleNamespace(step_number=0, max_steps=3)
    )
    message = prompt.get_user_message(use_vision=False)
    assert isinstance(message, HumanMessage), "Expected a HumanMessage instance."
    content = message.content
    assert "Action result 1/1: Extraction OK" in content, "Extracted content is not correctly included."
    expected_error_text = f"Action error 1/1: ...{short_error}"
    assert expected_error_text in content, "Short error message handling is incorrect."
    assert "http://shorterror.com" in content, "The state's URL is missing from the message content."

def test_agent_message_prompt_use_vision_true_with_empty_screenshot():
    """
    Test that AgentMessagePrompt.get_user_message returns a plain text HumanMessage even when
    use_vision is True if the state.screenshot is empty. This ensures that the absence of screenshot
    correctly leads to string content instead of a list with image data.
    """
    class DummyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return "Test element with no screenshot"
    dummy_state = SimpleNamespace(
        url="http://noscreenshot.com",
        tabs=["http://noscreenshot.com"],
        element_tree=DummyElementTree(),
        pixels_above=0,
        pixels_below=0,
        screenshot=""
    )
    prompt = AgentMessagePrompt(state=dummy_state)
    message = prompt.get_user_message(use_vision=True)
    assert isinstance(message, HumanMessage), "The returned message should be of type HumanMessage."
    assert isinstance(message.content, str), (
        "When screenshot is empty, even if use_vision is True, content should be a string."
    )
    content = message.content
    assert "Test element with no screenshot" in content, "Expected element tree text not found in message content."
    assert "http://noscreenshot.com" in content, "State URL should be included in the message content."
    assert "image_url" not in content, "There should be no image_url in the content when screenshot is empty."

def test_agent_message_prompt_with_none_result_values():
    """
    Test that AgentMessagePrompt.get_user_message handles a result with None extracted_content and None error.
    The test verifies that no "Action result" or "Action error" message is appended when both values are None.
    """
    class DummyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return "Interactive content here"
    dummy_state = SimpleNamespace(
        url="http://testnone.com",
        tabs=["http://testnone.com"],
        element_tree=DummyElementTree(),
        pixels_above=0,
        pixels_below=0,
        screenshot=""
    )
    none_result = SimpleNamespace(extracted_content=None, error=None)
    prompt = AgentMessagePrompt(
        state=dummy_state,
        result=[none_result],
        max_error_length=400,
        step_info=SimpleNamespace(step_number=1, max_steps=3)
    )
    message = prompt.get_user_message(use_vision=False)
    content = message.content
    assert isinstance(message, HumanMessage), "The returned message should be a HumanMessage instance."
    assert isinstance(content, str), "Message content should be a string when use_vision is False."
    assert "Interactive content here" in content, "Interactive content from the dummy element tree is missing."
    assert "Action result" not in content, "No action result should be appended when extracted_content is None."
    assert "Action error" not in content, "No action error should be appended when error is None."

def test_agent_message_prompt_with_empty_result_values():
    """
    Test that AgentMessagePrompt.get_user_message does not append any "Action result" or "Action error"
    lines when the provided result has empty strings for extracted_content and error.
    """
    class DummyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return "Test clickable content"
    dummy_state = SimpleNamespace(
        url="http://emptyresult.com",
        tabs=["http://emptyresult.com"],
        element_tree=DummyElementTree(),
        pixels_above=0,
        pixels_below=0,
        screenshot=""
    )
    dummy_result = [SimpleNamespace(extracted_content="", error="")]
    dummy_step_info = SimpleNamespace(step_number=0, max_steps=3)
    prompt = AgentMessagePrompt(state=dummy_state, result=dummy_result, max_error_length=400, step_info=dummy_step_info)
    message = prompt.get_user_message(use_vision=False)
    content = message.content
    assert "Action result" not in content, "No action result should be appended when extracted_content is empty."
    assert "Action error" not in content, "No action error should be appended when error is empty."
    assert "Test clickable content" in content, "Clickable element text should be present in the message."

def test_agent_message_prompt_with_none_screenshot():
    """
    Test that AgentMessagePrompt.get_user_message returns a plain text HumanMessage even when
    use_vision is True and the state's screenshot is None. This ensures that a None screenshot is
    treated as an empty string and does not trigger the vision/image format.
    """
    class DummyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return "Element without screenshot"
    dummy_state = SimpleNamespace(
        url="http://nonescreenshot.com",
        tabs=["http://nonescreenshot.com"],
        element_tree=DummyElementTree(),
        pixels_above=15,
        pixels_below=15,
        screenshot=None
    )
    prompt = AgentMessagePrompt(state=dummy_state)
    message = prompt.get_user_message(use_vision=True)
    assert isinstance(message, HumanMessage), "Expected message to be an instance of HumanMessage."
    assert isinstance(message.content, str), "Expected message content to be a string when screenshot is None."
    assert "http://nonescreenshot.com" in message.content, "State URL must be present in the message content."
    assert "Element without screenshot" in message.content, "Expected clickable element text not found in the message content."

def test_agent_message_prompt_formatting_with_pixels():
    """
    Test that AgentMessagePrompt.get_user_message correctly adds the markers for both pixels_above and 
    pixels_below when clickable elements are present. This verifies that the formatted element string 
    includes the appropriate scroll indicators and does not include the "[Start of page]" marker when pixels_above is nonzero.
    """
    class DummyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return "Formatted Element"
    dummy_state = SimpleNamespace(
        url="http://formatwithpixels.com",
        tabs=["http://formatwithpixels.com"],
        element_tree=DummyElementTree(),
        pixels_above=50,
        pixels_below=100,
        screenshot=""
    )
    prompt = AgentMessagePrompt(state=dummy_state)
    message = prompt.get_user_message(use_vision=False)
    content = message.content
    expected_above_marker = f"... {dummy_state.pixels_above} pixels above - scroll or extract content to see more ..."
    assert expected_above_marker in content, f"Expected above marker '{expected_above_marker}' not found in message content."
    expected_below_marker = f"... {dummy_state.pixels_below} pixels below - scroll or extract content to see more ..."
    assert expected_below_marker in content, f"Expected below marker '{expected_below_marker}' not found in message content."
    assert "[Start of page]" not in content, "Unexpected '[Start of page]' marker found despite pixels_above being nonzero."
    assert "Formatted Element" in content, "Expected clickable element text 'Formatted Element' not found in message content."

def test_agent_message_prompt_invalid_step_info():
    """
    Test that AgentMessagePrompt.get_user_message raises an AttributeError when the provided
    step_info is missing required attributes.
    """
    class DummyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return "dummy element"
    dummy_state = SimpleNamespace(
        url="http://error-step.com",
        tabs=["http://error-step.com"],
        element_tree=DummyElementTree(),
        pixels_above=0,
        pixels_below=0,
        screenshot=""
    )
    incomplete_step_info = SimpleNamespace(max_steps=5)
    agent_prompt = AgentMessagePrompt(state=dummy_state, step_info=incomplete_step_info)
    with pytest.raises(AttributeError):
        agent_prompt.get_user_message(use_vision=False)

def test_agent_message_prompt_timestamp_format():
    """
    Test that AgentMessagePrompt.get_user_message includes the current date and time in the expected format.
    This verifies that the time string appended to the state description matches the "YYYY-MM-DD HH:MM" pattern.
    """
    class DummyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return "Test element for timestamp"
    dummy_state = SimpleNamespace(
        url="http://timestamp-test.com",
        tabs=["http://timestamp-test.com"],
        element_tree=DummyElementTree(),
        pixels_above=0,
        pixels_below=0,
        screenshot=""
    )
    dummy_step_info = SimpleNamespace(step_number=1, max_steps=5)
    prompt = AgentMessagePrompt(state=dummy_state, step_info=dummy_step_info)
    message = prompt.get_user_message(use_vision=False)
    assert isinstance(message, HumanMessage), "Expected the message to be an instance of HumanMessage."
    content = message.content
    timestamp_match = re.search(r"Current date and time: (\d{4}-\d{2}-\d{2} \d{2}:\d{2})", content)
    assert timestamp_match, "Timestamp not found or not in expected format in the message content."
    timestamp_str = timestamp_match.group(1)
    pattern = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$"
    assert re.match(pattern, timestamp_str), f"Timestamp '{timestamp_str}' does not match expected format YYYY-MM-DD HH:MM."

def test_agent_message_prompt_with_whitespace_results():
    """
    Test that when AgentMessagePrompt receives a result with whitespace only for extracted_content
    and error, both are appended in the output as they are truthy and not skipped.
    """
    class DummyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return "Element for whitespace test"
    dummy_state = SimpleNamespace(
        url="http://whitespace.com",
        tabs=["http://whitespace.com"],
        element_tree=DummyElementTree(),
        pixels_above=0,
        pixels_below=0,
        screenshot=""
    )
    whitespace_result = SimpleNamespace(extracted_content=" ", error=" ")
    dummy_step_info = SimpleNamespace(step_number=0, max_steps=2)
    prompt = AgentMessagePrompt(
        state=dummy_state,
        result=[whitespace_result],
        max_error_length=400,
        step_info=dummy_step_info
    )
    message = prompt.get_user_message(use_vision=False)
    content = message.content
    assert "Action result 1/1:  " in content, "Expected whitespace in action result line not found."
    assert "Action error 1/1: ... " in content, "Expected whitespace in action error line not found."
    assert "Element for whitespace test" in content, "Expected clickable element text not found in the message."

def test_agent_message_prompt_with_none_pixels():
    """
    Test that AgentMessagePrompt.get_user_message correctly handles browser state when 
    pixels_above and pixels_below are None. In this case, they should be treated as zero,
    and the output should include both "[Start of page]" and "[End of page]" markers.
    """
    class DummyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return "Test element with None pixels"
    dummy_state = SimpleNamespace(
        url="http://nonepixels.com",
        tabs=["http://nonepixels.com"],
        element_tree=DummyElementTree(),
        pixels_above=None,
        pixels_below=None,
        screenshot=""
    )
    prompt = AgentMessagePrompt(state=dummy_state)
    message = prompt.get_user_message(use_vision=False)
    content = message.content
    assert "[Start of page]" in content, "Expected '[Start of page]' marker when pixels_above is None."
    assert "[End of page]" in content, "Expected '[End of page]' marker when pixels_below is None."
    assert "Test element with None pixels" in content, "Expected clickable element text not found in the message content."

def test_agent_message_prompt_empty_result_list():
    """
    Test that when AgentMessagePrompt is provided with an empty result list,
    get_user_message returns a valid HumanMessage that does not include any "Action result" 
    or "Action error" lines, but still includes the browser state's information and step info.
    """
    class DummyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return "Test clickable element"
    dummy_state = SimpleNamespace(
        url="http://emptyresultlist.com",
        tabs=["http://emptyresultlist.com"],
        element_tree=DummyElementTree(),
        pixels_above=0,
        pixels_below=0,
        screenshot=""
    )
    dummy_step_info = SimpleNamespace(step_number=1, max_steps=3)
    prompt = AgentMessagePrompt(
        state=dummy_state,
        result=[],
        step_info=dummy_step_info,
        max_error_length=400
    )
    message = prompt.get_user_message(use_vision=False)
    assert isinstance(message, HumanMessage), "Expected a HumanMessage instance."
    content = message.content
    assert "Action result" not in content, "No action result should be included for an empty result list."
    assert "Action error" not in content, "No action error should be included for an empty result list."
    assert "http://emptyresultlist.com" in content, "State URL must be present."
    assert "Available tabs:" in content, "Tabs information must be present."
    assert "Test clickable element" in content, "Clickable element text must be present."

def test_agent_message_prompt_with_none_tabs():
    """
    Test that AgentMessagePrompt.get_user_message correctly handles a scenario where the state's 'tabs'
    attribute is None. The test verifies that the output message contains "Available tabs:" followed
    by 'None' and that the rest of the state information is properly included.
    """
    class DummyElementTree:
        def clickable_elements_to_string(self, include_attributes):
            return "Test element for none tabs"
    dummy_state = SimpleNamespace(
        url="http://nonetabs.com",
        tabs=None,
        element_tree=DummyElementTree(),
        pixels_above=0,
        pixels_below=0,
        screenshot=""
    )
    prompt = AgentMessagePrompt(state=dummy_state)
    message = prompt.get_user_message(use_vision=False)
    assert isinstance(message, HumanMessage), "Expected message to be a HumanMessage instance."
    content = message.content
    assert "Available tabs:" in content, "Expected 'Available tabs:' to be in the message."
    assert "None" in content, "Expected 'None' to be displayed for tabs when state.tabs is None."
    assert "Test element for none tabs" in content, "Expected clickable element text to be present in the message."
    assert "http://nonetabs.com" in content, "Expected the state's URL to be present in the message."
