import pytest
from browser_use.dom.views import DOMElementNode
from browser_use.dom.views import DOMElementNode, DOMTextNode
from browser_use.dom.views import DOMTextNode
from browser_use.dom.views import DOMTextNode, DOMElementNode

def test_uncovered_scenarios(monkeypatch):
    """
    Test various DOMElementNode methods to increase coverage:
      - Verify that get_all_text_till_next_clickable_element skips text under a highlighted child.
      - Check that clickable_elements_to_string properly includes highlighted elements and shows text nodes without a highlighted parent.
      - Ensure that the __repr__ method produces a string that contains tag and highlight info.
      - Validate that get_file_upload_element correctly finds an input of type "file" either in children or siblings.
      - Mock the hash property (which uses HistoryTreeProcessor._hash_dom_element) to return a dummy hash.
    """
    from browser_use.dom.views import DOMElementNode, DOMTextNode
    # Build a simple DOM tree for text collection
    # Root div with three children:
    #   1. A text node "Hello"
    #   2. A span element with highlight_index=1 containing text "World"
    #   3. A text node "Bye"
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    text1 = DOMTextNode(
        is_visible=True,
        parent=root,
        text="Hello",
        type='TEXT_NODE'
    )
    span = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name='span',
        xpath='/div/span',
        attributes={'class': 'highlight'},
        children=[],
        highlight_index=1
    )
    span_text = DOMTextNode(
        is_visible=True,
        parent=span,
        text="World",
        type='TEXT_NODE'
    )
    span.children.append(span_text)
    text2 = DOMTextNode(
        is_visible=True,
        parent=root,
        text="Bye",
        type='TEXT_NODE'
    )
    root.children.extend([text1, span, text2])
    
    # Test get_all_text_till_next_clickable_element:
    # The text inside the highlighted span ("World") should be skipped.
    collected_text = root.get_all_text_till_next_clickable_element()
    assert collected_text == "Hello\nBye"
    # Test clickable_elements_to_string:
    # The formatted output should include the highlighted node with its attribute and also include text nodes.
    clickable_str = root.clickable_elements_to_string(include_attributes=['class'])
    assert '[1]<span class="highlight">' in clickable_str
    assert "[]Hello" in clickable_str
    assert "[]Bye" in clickable_str
    # Check __repr__ of the span node contains the tag and the highlight information.
    span_repr = repr(span)
    assert "<span" in span_repr
    assert "highlight:1" in span_repr
    # Build a tree for testing get_file_upload_element:
    # Create a container form with two child inputs: one of type 'text' and one of type 'file'.
    input_text = DOMElementNode(
        is_visible=True,
        parent=None,  # to be set later
        tag_name='input',
        xpath='/input1',
        attributes={'type': 'text'},
        children=[]
    )
    input_file = DOMElementNode(
        is_visible=True,
        parent=None,  # to be set later
        tag_name='input',
        xpath='/input2',
        attributes={'type': 'file'},
        children=[]
    )
    container = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='form',
        xpath='/form',
        attributes={},
        children=[input_text, input_file]
    )
    # Set the parent for the input nodes so that siblings are connected.
    input_text.parent = container
    input_file.parent = container
    # Calling get_file_upload_element on the non-file input should return the file input.
    found_file_upload = input_text.get_file_upload_element()
    assert found_file_upload == input_file
    # Calling get_file_upload_element on the container should also find the file input.
    found_file_upload_container = container.get_file_upload_element()
    assert found_file_upload_container == input_file
    # Test the 'hash' cached_property by mocking HistoryTreeProcessor._hash_dom_element.
    # Monkey-patch the method to return a dummy hash value.
    monkeypatch.setattr(
        "browser_use.dom.history_tree_processor.service.HistoryTreeProcessor._hash_dom_element",
        lambda elem: "dummy_hash"
    )
    dummy_hash = span.hash
    assert dummy_hash == "dummy_hash"
def test_advanced_css_selector(monkeypatch):
    """
    Test that get_advanced_css_selector returns the enhanced CSS selector as provided
    by the mocked BrowserContext._enhanced_css_selector_for_element method.
    """
    # Create a simple DOM element node.
    node = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={'id': 'test'},
        children=[]
    )
    # Monkey-patch the BrowserContext._enhanced_css_selector_for_element method
    monkeypatch.setattr(
        "browser_use.browser.context.BrowserContext._enhanced_css_selector_for_element",
        lambda elem: "dummy_selector"
    )
    # Call the method and verify it returns the dummy selector.
    selector = node.get_advanced_css_selector()
    assert selector == "dummy_selector"
def test_max_depth_and_parent_highlight():
    """
    Test the get_all_text_till_next_clickable_element method with the max_depth parameter and
    verify the DOMTextNode.has_parent_with_highlight_index method:
      - Build a tree with a direct text node under the root (depth 1) and a nested text node (depth 2).
      - Verify that with max_depth=1 only the direct text node is collected.
      - Verify that with max_depth=-1 (unlimited depth) both text nodes are collected.
      - Separately, create a highlighted parent and verify that a text node under it correctly
        reports having an ancestor with a highlight index. Then, after removing the highlight,
        the check should return False.
    """
    # Build a tree for testing max_depth in get_all_text_till_next_clickable_element.
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    # Direct text node at depth 1.
    text_a = DOMTextNode(
        is_visible=True,
        parent=root,
        text="Level 1 text",
        type='TEXT_NODE'
    )
    # Nested element with a text node at depth 2.
    section = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name='section',
        xpath='/div/section',
        attributes={},
        children=[]
    )
    text_b = DOMTextNode(
        is_visible=True,
        parent=section,
        text="Level 2 text",
        type='TEXT_NODE'
    )
    section.children.append(text_b)
    root.children.extend([text_a, section])
    
    # With max_depth=1, only text_a (depth 1) is collected and text_b (depth 2) is skipped.
    collected_text_depth_1 = root.get_all_text_till_next_clickable_element(max_depth=1)
    assert collected_text_depth_1 == "Level 1 text"
    
    # With max_depth=-1 (unlimited), both texts are collected.
    collected_text_unlimited = root.get_all_text_till_next_clickable_element(max_depth=-1)
    expected_unlimited = "Level 1 text\nLevel 2 text"
    assert collected_text_unlimited == expected_unlimited
    
    # Test directly the has_parent_with_highlight_index method.
    # Create a parent with a highlight.
    highlighted_parent = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='p',
        xpath='/p',
        attributes={},
        children=[],
        highlight_index=100
    )
    child_text = DOMTextNode(
        is_visible=True,
        parent=highlighted_parent,
        text="Child with highlighted parent",
        type='TEXT_NODE'
    )
    highlighted_parent.children.append(child_text)
    
    # The child text should report that it has a parent with a highlight.
    assert child_text.has_parent_with_highlight_index() is True
    
    # Remove the highlight and test again.
    highlighted_parent.highlight_index = None
    assert child_text.has_parent_with_highlight_index() is False
def test_file_upload_element_self():
    """
    Test that get_file_upload_element returns the element itself when the element is an input of type 'file'.
    This verifies the first condition in the method.
    """
    file_input = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='input',
        xpath='/input_file',
        attributes={'type': 'file'},
        children=[]
    )
    # When the element is itself an input file, it should return itself.
    result = file_input.get_file_upload_element()
    assert result is file_input
def test_no_file_upload_element():
    """
    Test that get_file_upload_element returns None when the DOM tree does not contain an input of type 'file'.
    This verifies that the method properly checks children and siblings and returns None if no file input is found.
    """
    # Create two input elements of type 'text'
    input_text1 = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='input',
        xpath='/input1',
        attributes={'type': 'text'},
        children=[]
    )
    input_text2 = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='input',
        xpath='/input2',
        attributes={'type': 'text'},
        children=[]
    )
    # Create a container (form) element that includes these as children
    container = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='form',
        xpath='/form',
        attributes={'name': 'test_form'},
        children=[input_text1, input_text2]
    )
    # Set parents for children so that they are recognized as siblings
    input_text1.parent = container
    input_text2.parent = container
    # Test that calling get_file_upload_element on container returns None,
    # as there is no input with type 'file'.
    assert container.get_file_upload_element() is None
    # Also check that calling on one of the input_text elements returns None.
    assert input_text1.get_file_upload_element() is None
def test_repr_extras():
    """
    Test that __repr__ correctly includes all extra flags: 'interactive', 'top', 'shadow-root', and the highlight index.
    """
    # Create a DOM element with extra properties
    node = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='section',
        xpath='/section',
        attributes={'id': 'sec', 'data-test': 'example'},
        children=[],
        is_interactive=True,
        is_top_element=True,
        shadow_root=True,
        highlight_index=42
    )
    repr_str = repr(node)
    
    # Check that the __repr__ output includes the tag name and the extra flags.
    assert '<section' in repr_str
    assert 'interactive' in repr_str
    assert 'top' in repr_str
    assert 'shadow-root' in repr_str
    assert 'highlight:42' in repr_str
def test_nested_highlight_clickable_elements():
    """
    Test clickable_elements_to_string behavior when highlighted elements are nested.
    Ensures that the parent's text collection skips over nested highlighted elements,
    while the nested highlighted element is separately returned.
    """
    # Build a simple DOM tree:
    # root (non-highlighted) with two children:
    #   - a highlighted section with a normal text child "First" and a nested highlighted p with text "Nested"
    #   - a text node "Outside" directly under root.
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    # Highlighted container element with highlight_index=10.
    section = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name='section',
        xpath='/div/section',
        attributes={'class': 'container'},
        children=[],
        highlight_index=10
    )
    # Add a normal text node to section.
    text_in_section = DOMTextNode(
        is_visible=True,
        parent=section,
        text="First",
        type='TEXT_NODE'
    )
    section.children.append(text_in_section)
    # Nested highlighted element inside the section with highlight_index=20.
    nested_p = DOMElementNode(
        is_visible=True,
        parent=section,
        tag_name='p',
        xpath='/div/section/p',
        attributes={'class': 'nested'},
        children=[],
        highlight_index=20
    )
    # Add text to the nested highlighted element.
    text_in_nested = DOMTextNode(
        is_visible=True,
        parent=nested_p,
        text="Nested",
        type='TEXT_NODE'
    )
    nested_p.children.append(text_in_nested)
    # Append the nested highlighted element to the section.
    section.children.append(nested_p)
    # A text node directly under the root.
    outside_text = DOMTextNode(
        is_visible=True,
        parent=root,
        text="Outside",
        type='TEXT_NODE'
    )
    # Assemble the tree.
    root.children.extend([section, outside_text])
    # Call clickable_elements_to_string.
    formatted = root.clickable_elements_to_string(include_attributes=['class'])
    
    # The output should include:
    # - A line for the highlighted section which should only include its own text ("First") while skipping the nested highlighted content.
    # - A separate line for the nested highlighted <p> element showing its text "Nested".
    # - A line for the "Outside" text node.
    assert "[10]<section class=\"container\">" in formatted
    assert "[20]<p class=\"nested\">" in formatted
    assert "[]Outside" in formatted
    # Also, verify that the get_all_text_till_next_clickable_element method on the section node
    # returns only "First", since the nested highlighted element should be skipped.
    section_text = section.get_all_text_till_next_clickable_element()
    assert section_text == "First"
def test_highlighted_root_all_text():
    """
    Test that get_all_text_till_next_clickable_element correctly collects text when the root element is highlighted.
    Although the root element has a highlight_index, its own text nodes are still included while the text under any
    highlighted child element is skipped.
    """
    # Create a highlighted root element.
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[],
        highlight_index=3
    )
    # Add a text node directly under the root.
    text_a = DOMTextNode(
        is_visible=True,
        parent=root,
        text="A",
        type='TEXT_NODE'
    )
    # Create a child element with a highlight; its subtree should be skipped.
    child_highlight = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name='span',
        xpath='/div/span',
        attributes={},
        children=[],
        highlight_index=9
    )
    text_b = DOMTextNode(
        is_visible=True,
        parent=child_highlight,
        text="B",
        type='TEXT_NODE'
    )
    child_highlight.children.append(text_b)
    # Add another text node directly under the root.
    text_c = DOMTextNode(
        is_visible=True,
        parent=root,
        text="C",
        type='TEXT_NODE'
    )
    # Assemble the tree.
    root.children.extend([text_a, child_highlight, text_c])
    
    # Execute the method under test.
    collected_text = root.get_all_text_till_next_clickable_element()
    # Expected output skips the text under the highlighted child (i.e., "B" is omitted).
    assert collected_text == "A\nC"
def test_hash_cached_property(monkeypatch):
    """
    Test that the hash property is computed only once and then cached.
    The test monkey-patches the HistoryTreeProcessor._hash_dom_element method to increment a counter.
    It verifies that multiple accesses to the .hash property return the same value and that the dummy
    method is called only once.
    """
    call_count = {"calls": 0}
    def dummy_hash(elem):
        call_count["calls"] += 1
        return f"dummy_hash_{call_count['calls']}"
    monkeypatch.setattr(
        "browser_use.dom.history_tree_processor.service.HistoryTreeProcessor._hash_dom_element",
        dummy_hash
    )
    # Create a simple DOM element node.
    node = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    # Access the hash property twice to verify caching.
    hash_first = node.hash
    hash_second = node.hash
    # Verify that both accesses return the same value.
    assert hash_first == hash_second
    # Verify that the dummy hash function was called only once.
    assert call_count["calls"] == 1
def test_empty_dom_tree():
    """
    Test DOM methods on an empty DOM tree to ensure methods return expected results
    when no children or text nodes exist.
    """
    # Create a DOM element node with no children.
    empty_node = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    # When there are no children, get_all_text_till_next_clickable_element should return an empty string.
    assert empty_node.get_all_text_till_next_clickable_element() == ""
    
    # There are no clickable elements, so clickable_elements_to_string should likewise return an empty string.
    assert empty_node.clickable_elements_to_string() == ""
    
    # As there is no input child, get_file_upload_element should return None.
    assert empty_node.get_file_upload_element() is None
    # The __repr__ method should display the tag but no extra flags.
    repr_str = repr(empty_node)
    assert "<div" in repr_str
    assert "interactive" not in repr_str
    assert "top" not in repr_str
    assert "shadow-root" not in repr_str
    # Even if highlight_index is None, there shouldn't be any highlight info.
    assert "highlight:" not in repr_str
def test_deeply_nested_dom_text_and_clickable_elements():
    """
    Test a deeply nested DOM tree with a mix of highlighted and non-highlighted elements.
    Verifies that:
      - get_all_text_till_next_clickable_element returns the correct concatenated text,
        skipping over the text under any highlighted node (except when the highlighted node is self).
      - clickable_elements_to_string outputs clickable representations for highlighted elements and
        includes text nodes that do not have a highlighted parent.
    """
    # Build the DOM tree:
    # <div>
    #   "RootText"
    #   <section>
    #       "SecText1"
    #       <span highlight_index=5>
    #           "Ignored"  <-- This will be included in the span's own text collection
    #       </span>
    #       "After highlight"
    #   </section>
    #   "Final"
    # </div>
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    # Add a text node directly under the root.
    text_root = DOMTextNode(
        is_visible=True,
        parent=root,
        text="RootText",
        type='TEXT_NODE'
    )
    # Create the <section> element (non-highlighted).
    section = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name='section',
        xpath='/div/section',
        attributes={},
        children=[]
    )
    # Child text node under section.
    text_sec1 = DOMTextNode(
        is_visible=True,
        parent=section,
        text="SecText1",
        type='TEXT_NODE'
    )
    # Highlighted <span> element inside section.
    span = DOMElementNode(
        is_visible=True,
        parent=section,
        tag_name='span',
        xpath='/div/section/span',
        attributes={'class': 'highlighted'},
        children=[],
        highlight_index=5
    )
    text_span = DOMTextNode(
        is_visible=True,
        parent=span,
        text="Ignored",
        type='TEXT_NODE'
    )
    span.children.append(text_span)
    # Another text node under section appearing after the highlighted span.
    text_sec2 = DOMTextNode(
        is_visible=True,
        parent=section,
        text="After highlight",
        type='TEXT_NODE'
    )
    section.children.extend([text_sec1, span, text_sec2])
    # Add a final text node under the root.
    text_final = DOMTextNode(
        is_visible=True,
        parent=root,
        text="Final",
        type='TEXT_NODE'
    )
    # Assemble the tree.
    root.children.extend([text_root, section, text_final])
    
    # Test get_all_text_till_next_clickable_element on the root.
    # The expected behavior:
    #   - "RootText" is collected.
    #   - Under section, "SecText1" is collected, then the highlighted <span> is encountered so its subtree is skipped,
    #     so "Ignored" is not merged into section's text, then "After highlight" is collected.
    #   - "Final" is collected.
    expected_all_text = "RootText\nSecText1\nAfter highlight\nFinal"
    collected_text = root.get_all_text_till_next_clickable_element()
    assert collected_text == expected_all_text
    # Test clickable_elements_to_string.
    # clickable_elements_to_string should include:
    #   - A clickable representation for the highlighted <span> element (which collects its own text "Ignored").
    #   - It should also include text nodes from non-highlighted parts.
    clickable_output = root.clickable_elements_to_string(include_attributes=["class"])
    # Check that the clickable representation for the span contains the highlight index and its tag with attribute.
    assert "[5]<span class=\"highlighted\">" in clickable_output
    # Check that text nodes from the root and section are included as non-clickable elements.
    assert "[]RootText" in clickable_output
    assert "[]SecText1" in clickable_output
    assert "[]After highlight" in clickable_output
    assert "[]Final" in clickable_output
def test_max_depth_zero():
    """
    Test that providing max_depth=0 to get_all_text_till_next_clickable_element results in
    no child nodes being processed. Even if the element has text nodes as children, none
    should be collected because the recursion stops immediately.
    """
    # Create a DOM element node (root) with a text child.
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    text_child = DOMTextNode(
        is_visible=True,
        parent=root,
        text="Child Text",
        type='TEXT_NODE'
    )
    root.children.append(text_child)
    # With max_depth=0, the function should not traverse into children.
    result = root.get_all_text_till_next_clickable_element(max_depth=0)
    assert result == ""
def test_file_upload_element_without_checking_siblings():
    """
    Test that get_file_upload_element returns None when check_siblings is explicitly set to False,
    even if a sibling file input exists. Additionally, verify that the default behavior (check_siblings=True)
    returns the file input element from the container.
    """
    # Build a container (form) with two children: a text input and a file input.
    container = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='form',
        xpath='/form',
        attributes={},
        children=[]
    )
    input_text = DOMElementNode(
        is_visible=True,
        parent=container,
        tag_name='input',
        xpath='/form/input1',
        attributes={'type': 'text'},
        children=[]
    )
    input_file = DOMElementNode(
        is_visible=True,
        parent=container,
        tag_name='input',
        xpath='/form/input2',
        attributes={'type': 'file'},
        children=[]
    )
    container.children.extend([input_text, input_file])
    
    # When check_siblings is False, only search within children; since input_text has no children,
    # the file input should not be found.
    result_no_sibling = input_text.get_file_upload_element(check_siblings=False)
    assert result_no_sibling is None
    
    # With default behavior (check_siblings is True), the text input should find the sibling file input.
    result_with_sibling = input_text.get_file_upload_element()
    assert result_with_sibling == input_file
def test_clickable_elements_no_included_attributes():
    """
    Test that clickable_elements_to_string does not include any attributes when include_attributes is not provided.
    A highlighted element with attributes should only display its tag and text, without extra attribute information.
    """
    # Build a simple DOM tree with a highlighted button having attributes.
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    button = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name='button',
        xpath='/div/button',
        attributes={'class': 'btn', 'id': 'submit'},
        children=[],
        highlight_index=7
    )
    button_text = DOMTextNode(
        is_visible=True,
        parent=button,
        text="Submit",
        type='TEXT_NODE'
    )
    button.children.append(button_text)
    root.children.append(button)
    
    # Call clickable_elements_to_string without including any specific attribute keys.
    clickable_output = root.clickable_elements_to_string()
    
    # Verify that the clickable representation for the highlighted button lacks attribute formatting.
    assert "[7]<button>" in clickable_output
    assert "class=" not in clickable_output
    assert "id=" not in clickable_output
    # Also verify that the button's text ("Submit") is included in the output.
    assert "Submit" in clickable_output
def test_dataclass_repr_for_text_node():
    """
    Test that the default dataclass __repr__ for DOMTextNode (which does not override __repr__)
    returns a string containing its attributes such as 'text' and 'type'.
    This ensures that even without a custom __repr__, the dataclass representation is meaningful.
    """
    # Create a DOMTextNode instance.
    text_node = DOMTextNode(
        is_visible=True,
        parent=None,
        text="Sample",
        type="TEXT_NODE"
    )
    # Get its repr string.
    rep_str = repr(text_node)
    
    # Verify that the representation contains the 'text' value and the 'type'.
    assert "Sample" in rep_str
    assert "TEXT_NODE" in rep_str
    # Also check that the class name is present (the default dataclass repr includes this).
    assert "DOMTextNode" in rep_str
def test_uncovered_scenarios(monkeypatch):
    """
    Test various DOMElementNode methods including text extraction, clickable representation,
    __repr__ correctness, file upload element detection, and cached hash property behavior.
    """
    # Build a simple DOM tree for text collection
    # Root div with three children:
    #   1. A text node "Hello"
    #   2. A span element with highlight_index=1 containing text "World"
    #   3. A text node "Bye"
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    text1 = DOMTextNode(
        is_visible=True,
        parent=root,
        text="Hello",
        type='TEXT_NODE'
    )
    span = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name='span',
        xpath='/div/span',
        attributes={'class': 'highlight'},
        children=[],
        highlight_index=1
    )
    span_text = DOMTextNode(
        is_visible=True,
        parent=span,
        text="World",
        type='TEXT_NODE'
    )
    span.children.append(span_text)
    text2 = DOMTextNode(
        is_visible=True,
        parent=root,
        text="Bye",
        type='TEXT_NODE'
    )
    root.children.extend([text1, span, text2])
    
    # Test get_all_text_till_next_clickable_element:
    # The text inside the highlighted span ("World") should be skipped.
    collected_text = root.get_all_text_till_next_clickable_element()
    assert collected_text == "Hello\nBye"
    
    # Test clickable_elements_to_string:
    clickable_str = root.clickable_elements_to_string(include_attributes=['class'])
    assert '[1]<span class="highlight">' in clickable_str
    assert "[]Hello" in clickable_str
    assert "[]Bye" in clickable_str
    
    # Check __repr__ of the span node contains the tag and the highlight information.
    span_repr = repr(span)
    assert "<span" in span_repr
    assert "highlight:1" in span_repr
    
    # Build a tree for testing get_file_upload_element:
    input_text = DOMElementNode(
        is_visible=True,
        parent=None,  # to be set later
        tag_name='input',
        xpath='/input1',
        attributes={'type': 'text'},
        children=[]
    )
    input_file = DOMElementNode(
        is_visible=True,
        parent=None,  # to be set later
        tag_name='input',
        xpath='/input2',
        attributes={'type': 'file'},
        children=[]
    )
    container = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='form',
        xpath='/form',
        attributes={},
        children=[input_text, input_file]
    )
    input_text.parent = container
    input_file.parent = container
    
    found_file_upload = input_text.get_file_upload_element()
    assert found_file_upload == input_file
    
    found_file_upload_container = container.get_file_upload_element()
    assert found_file_upload_container == input_file
    
    # Test the 'hash' cached_property by mocking HistoryTreeProcessor._hash_dom_element.
    monkeypatch.setattr(
        "browser_use.dom.history_tree_processor.service.HistoryTreeProcessor._hash_dom_element",
        lambda elem: "dummy_hash"
    )
    dummy_hash = span.hash
    assert dummy_hash == "dummy_hash"
def test_advanced_css_selector(monkeypatch):
    """
    Test that get_advanced_css_selector returns the enhanced CSS selector as provided by the mocked BrowserContext.
    """
    node = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={'id': 'test'},
        children=[]
    )
    monkeypatch.setattr(
        "browser_use.browser.context.BrowserContext._enhanced_css_selector_for_element",
        lambda elem: "dummy_selector"
    )
    selector = node.get_advanced_css_selector()
    assert selector == "dummy_selector"
def test_max_depth_and_parent_highlight():
    """
    Test get_all_text_till_next_clickable_element with max_depth and verify has_parent_with_highlight_index functionality.
    """
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    text_a = DOMTextNode(
        is_visible=True,
        parent=root,
        text="Level 1 text",
        type='TEXT_NODE'
    )
    section = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name='section',
        xpath='/div/section',
        attributes={},
        children=[]
    )
    text_b = DOMTextNode(
        is_visible=True,
        parent=section,
        text="Level 2 text",
        type='TEXT_NODE'
    )
    section.children.append(text_b)
    root.children.extend([text_a, section])
    
    collected_text_depth_1 = root.get_all_text_till_next_clickable_element(max_depth=1)
    assert collected_text_depth_1 == "Level 1 text"
    
    collected_text_unlimited = root.get_all_text_till_next_clickable_element(max_depth=-1)
    expected_unlimited = "Level 1 text\nLevel 2 text"
    assert collected_text_unlimited == expected_unlimited
    
    highlighted_parent = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='p',
        xpath='/p',
        attributes={},
        children=[],
        highlight_index=100
    )
    child_text = DOMTextNode(
        is_visible=True,
        parent=highlighted_parent,
        text="Child with highlighted parent",
        type='TEXT_NODE'
    )
    highlighted_parent.children.append(child_text)
    
    assert child_text.has_parent_with_highlight_index() is True
    highlighted_parent.highlight_index = None
    assert child_text.has_parent_with_highlight_index() is False
def test_file_upload_element_self():
    """
    Test get_file_upload_element returns the element itself when it is an input of type 'file'.
    """
    file_input = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='input',
        xpath='/input_file',
        attributes={'type': 'file'},
        children=[]
    )
    result = file_input.get_file_upload_element()
    assert result is file_input
def test_no_file_upload_element():
    """
    Test get_file_upload_element returns None when no input of type 'file' exists in the DOM tree.
    """
    input_text1 = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='input',
        xpath='/input1',
        attributes={'type': 'text'},
        children=[]
    )
    input_text2 = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='input',
        xpath='/input2',
        attributes={'type': 'text'},
        children=[]
    )
    container = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='form',
        xpath='/form',
        attributes={'name': 'test_form'},
        children=[input_text1, input_text2]
    )
    input_text1.parent = container
    input_text2.parent = container
    assert container.get_file_upload_element() is None
    assert input_text1.get_file_upload_element() is None
def test_repr_extras():
    """
    Test __repr__ includes flags for interactive, top, shadow-root, and highlight index.
    """
    node = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='section',
        xpath='/section',
        attributes={'id': 'sec', 'data-test': 'example'},
        children=[],
        is_interactive=True,
        is_top_element=True,
        shadow_root=True,
        highlight_index=42
    )
    repr_str = repr(node)
    assert '<section' in repr_str
    assert 'interactive' in repr_str
    assert 'top' in repr_str
    assert 'shadow-root' in repr_str
    assert 'highlight:42' in repr_str
def test_nested_highlight_clickable_elements():
    """
    Test clickable_elements_to_string with nested highlighted elements.
    """
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    section = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name='section',
        xpath='/div/section',
        attributes={'class': 'container'},
        children=[],
        highlight_index=10
    )
    text_in_section = DOMTextNode(
        is_visible=True,
        parent=section,
        text="First",
        type='TEXT_NODE'
    )
    section.children.append(text_in_section)
    nested_p = DOMElementNode(
        is_visible=True,
        parent=section,
        tag_name='p',
        xpath='/div/section/p',
        attributes={'class': 'nested'},
        children=[],
        highlight_index=20
    )
    text_in_nested = DOMTextNode(
        is_visible=True,
        parent=nested_p,
        text="Nested",
        type='TEXT_NODE'
    )
    nested_p.children.append(text_in_nested)
    section.children.append(nested_p)
    outside_text = DOMTextNode(
        is_visible=True,
        parent=root,
        text="Outside",
        type='TEXT_NODE'
    )
    root.children.extend([section, outside_text])
    
    formatted = root.clickable_elements_to_string(include_attributes=['class'])
    assert "[10]<section class=\"container\">" in formatted
    assert "[20]<p class=\"nested\">" in formatted
    assert "[]Outside" in formatted
    section_text = section.get_all_text_till_next_clickable_element()
    assert section_text == "First"
def test_highlighted_root_all_text():
    """
    Test get_all_text_till_next_clickable_element with a highlighted root element.
    """
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[],
        highlight_index=3
    )
    text_a = DOMTextNode(
        is_visible=True,
        parent=root,
        text="A",
        type='TEXT_NODE'
    )
    child_highlight = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name='span',
        xpath='/div/span',
        attributes={},
        children=[],
        highlight_index=9
    )
    text_b = DOMTextNode(
        is_visible=True,
        parent=child_highlight,
        text="B",
        type='TEXT_NODE'
    )
    child_highlight.children.append(text_b)
    text_c = DOMTextNode(
        is_visible=True,
        parent=root,
        text="C",
        type='TEXT_NODE'
    )
    root.children.extend([text_a, child_highlight, text_c])
    
    collected_text = root.get_all_text_till_next_clickable_element()
    assert collected_text == "A\nC"
def test_hash_cached_property(monkeypatch):
    """
    Test that the hash property is computed once and cached thereafter.
    """
    call_count = {"calls": 0}
    def dummy_hash(elem):
        call_count["calls"] += 1
        return f"dummy_hash_{call_count['calls']}"
    monkeypatch.setattr(
        "browser_use.dom.history_tree_processor.service.HistoryTreeProcessor._hash_dom_element",
        dummy_hash
    )
    node = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    hash_first = node.hash
    hash_second = node.hash
    assert hash_first == hash_second
    assert call_count["calls"] == 1
def test_empty_dom_tree():
    """
    Test behavior of DOM methods on an empty DOM tree.
    """
    empty_node = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    assert empty_node.get_all_text_till_next_clickable_element() == ""
    assert empty_node.clickable_elements_to_string() == ""
    assert empty_node.get_file_upload_element() is None
    repr_str = repr(empty_node)
    assert "<div" in repr_str
    assert "interactive" not in repr_str
    assert "top" not in repr_str
    assert "shadow-root" not in repr_str
    assert "highlight:" not in repr_str
def test_deeply_nested_dom_text_and_clickable_elements():
    """
    Test a deeply nested DOM tree with mixed highlighted and non-highlighted elements.
    """
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    text_root = DOMTextNode(
        is_visible=True,
        parent=root,
        text="RootText",
        type='TEXT_NODE'
    )
    section = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name='section',
        xpath='/div/section',
        attributes={},
        children=[]
    )
    text_sec1 = DOMTextNode(
        is_visible=True,
        parent=section,
        text="SecText1",
        type='TEXT_NODE'
    )
    span = DOMElementNode(
        is_visible=True,
        parent=section,
        tag_name='span',
        xpath='/div/section/span',
        attributes={'class': 'highlighted'},
        children=[],
        highlight_index=5
    )
    text_span = DOMTextNode(
        is_visible=True,
        parent=span,
        text="Ignored",
        type='TEXT_NODE'
    )
    span.children.append(text_span)
    text_sec2 = DOMTextNode(
        is_visible=True,
        parent=section,
        text="After highlight",
        type='TEXT_NODE'
    )
    section.children.extend([text_sec1, span, text_sec2])
    text_final = DOMTextNode(
        is_visible=True,
        parent=root,
        text="Final",
        type='TEXT_NODE'
    )
    root.children.extend([text_root, section, text_final])
    
    expected_all_text = "RootText\nSecText1\nAfter highlight\nFinal"
    collected_text = root.get_all_text_till_next_clickable_element()
    assert collected_text == expected_all_text
    clickable_output = root.clickable_elements_to_string(include_attributes=["class"])
    assert "[5]<span class=\"highlighted\">" in clickable_output
    assert "[]RootText" in clickable_output
    assert "[]SecText1" in clickable_output
    assert "[]After highlight" in clickable_output
    assert "[]Final" in clickable_output
def test_max_depth_zero():
    """
    Test that get_all_text_till_next_clickable_element with max_depth=0 collects no child text.
    """
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    text_child = DOMTextNode(
        is_visible=True,
        parent=root,
        text="Child Text",
        type='TEXT_NODE'
    )
    root.children.append(text_child)
    result = root.get_all_text_till_next_clickable_element(max_depth=0)
    assert result == ""
def test_file_upload_element_without_checking_siblings():
    """
    Test that get_file_upload_element returns None when check_siblings is False.
    """
    container = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='form',
        xpath='/form',
        attributes={},
        children=[]
    )
    input_text = DOMElementNode(
        is_visible=True,
        parent=container,
        tag_name='input',
        xpath='/form/input1',
        attributes={'type': 'text'},
        children=[]
    )
    input_file = DOMElementNode(
        is_visible=True,
        parent=container,
        tag_name='input',
        xpath='/form/input2',
        attributes={'type': 'file'},
        children=[]
    )
    container.children.extend([input_text, input_file])
    
    result_no_sibling = input_text.get_file_upload_element(check_siblings=False)
    assert result_no_sibling is None
    
    result_with_sibling = input_text.get_file_upload_element()
    assert result_with_sibling == input_file
def test_clickable_elements_no_included_attributes():
    """
    Test that clickable_elements_to_string does not include attributes when include_attributes is empty.
    """
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    button = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name='button',
        xpath='/div/button',
        attributes={'class': 'btn', 'id': 'submit'},
        children=[],
        highlight_index=7
    )
    button_text = DOMTextNode(
        is_visible=True,
        parent=button,
        text="Submit",
        type='TEXT_NODE'
    )
    button.children.append(button_text)
    root.children.append(button)
    
    clickable_output = root.clickable_elements_to_string()
    assert "[7]<button>" in clickable_output
    assert "class=" not in clickable_output
    assert "id=" not in clickable_output
    assert "Submit" in clickable_output
def test_dataclass_repr_for_text_node():
    """
    Test the default dataclass __repr__ for DOMTextNode includes its attributes.
    """
    text_node = DOMTextNode(
        is_visible=True,
        parent=None,
        text="Sample",
        type="TEXT_NODE"
    )
    rep_str = repr(text_node)
    assert "Sample" in rep_str
    assert "TEXT_NODE" in rep_str
    assert "DOMTextNode" in rep_str
def test_first_file_upload_element_returned():
    """
    Test that get_file_upload_element returns the first encountered file input element
    from a container that contains multiple file input elements along with other elements.
    This verifies that the method correctly traverses children in order and returns the first match.
    """
    from browser_use.dom.views import DOMElementNode, DOMTextNode
    # Create a container 'form' element with three children: one text input and two file inputs.
    container = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='form',
        xpath='/form',
        attributes={},
        children=[]
    )
    # Text input element (not a file input).
    input_text = DOMElementNode(
        is_visible=True,
        parent=container,
        tag_name='input',
        xpath='/form/input_text',
        attributes={'type': 'text'},
        children=[]
    )
    # First file input element.
    file_input1 = DOMElementNode(
        is_visible=True,
        parent=container,
        tag_name='input',
        xpath='/form/input_file1',
        attributes={'type': 'file'},
        children=[]
    )
    # Second file input element.
    file_input2 = DOMElementNode(
        is_visible=True,
        parent=container,
        tag_name='input',
        xpath='/form/input_file2',
        attributes={'type': 'file'},
        children=[]
    )
    # Assemble the children in order.
    container.children.extend([input_text, file_input1, file_input2])
    # When calling get_file_upload_element on the text input, it should search siblings and return the first file input.
    result = input_text.get_file_upload_element()
    assert result == file_input1, f"Expected first file input, got {result}"
    # Likewise, calling get_file_upload_element on the container should also return the first file input.
    result_container = container.get_file_upload_element()
    assert result_container == file_input1, f"Expected first file input from container, got {result_container}"
def test_max_depth_limiting_tree():
    """
    Test that get_all_text_till_next_clickable_element correctly limits text extraction by the max_depth parameter.
    Builds a multi-level DOM tree:
      - The root contains a direct text node ("root_text").
      - A child element contains a text node ("child_text").
      - That child element contains a grandchild element with a text node ("grandchild_text").
      - The grandchild element contains a further nested element with a text node ("great_grandchild_text").
    Verifies that:
      - With max_depth set to 2, text nodes at depth 3 are not collected.
      - With unlimited depth (max_depth = -1), all text nodes are collected.
    """
    # Create the root element.
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    # Add a direct text node to root.
    root_text = DOMTextNode(
        is_visible=True,
        parent=root,
        text="root_text",
        type="TEXT_NODE"
    )
    root.children.append(root_text)
    
    # Create a child element with a text node.
    child_elem = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name='section',
        xpath='/div/section',
        attributes={},
        children=[]
    )
    child_text = DOMTextNode(
        is_visible=True,
        parent=child_elem,
        text="child_text",
        type="TEXT_NODE"
    )
    child_elem.children.append(child_text)
    
    # Create a grandchild element under the child element.
    grandchild_elem = DOMElementNode(
        is_visible=True,
        parent=child_elem,
        tag_name='div',
        xpath='/div/section/div',
        attributes={},
        children=[]
    )
    grandchild_text = DOMTextNode(
        is_visible=True,
        parent=grandchild_elem,
        text="grandchild_text",
        type="TEXT_NODE"
    )
    grandchild_elem.children.append(grandchild_text)
    
    # Create a great-grandchild element under the grandchild element.
    great_grandchild_elem = DOMElementNode(
        is_visible=True,
        parent=grandchild_elem,
        tag_name='span',
        xpath='/div/section/div/span',
        attributes={},
        children=[]
    )
    great_grandchild_text = DOMTextNode(
        is_visible=True,
        parent=great_grandchild_elem,
        text="great_grandchild_text",
        type="TEXT_NODE"
    )
    great_grandchild_elem.children.append(great_grandchild_text)
    
    # Assemble the tree.
    grandchild_elem.children.append(great_grandchild_elem)
    child_elem.children.append(grandchild_elem)
    root.children.append(child_elem)
    
    # Test with max_depth = 2. Depths: 
    #   root = 0, root_text depth 1, child_elem depth 1, child_text depth 2,
    #   grandchild_elem depth 2, grandchild_text depth 3, great-grandchild_text depth 4.
    # So only "root_text", "child_text" and nothing from grandchild_elem (since its text is at depth 3) should be collected.
    collected_text_max_depth_2 = root.get_all_text_till_next_clickable_element(max_depth=2)
    expected_text_depth_2 = "root_text\nchild_text"
    assert collected_text_max_depth_2 == expected_text_depth_2, f"Expected:\n{expected_text_depth_2}\nGot:\n{collected_text_max_depth_2}"
    
    # Test with unlimited depth (max_depth = -1). Expect all texts concatenated in the depth-first order.
    collected_text_unlimited = root.get_all_text_till_next_clickable_element(max_depth=-1)
    expected_text_unlimited = "root_text\nchild_text\ngrandchild_text\ngreat_grandchild_text"
    assert collected_text_unlimited == expected_text_unlimited, f"Expected:\n{expected_text_unlimited}\nGot:\n{collected_text_unlimited}"
def test_repr_no_extras():
    """
    Test that __repr__ returns only the tag and attributes when no extra flags
    (interactive, top, shadow-root, highlight index) are set.
    """
    # Create a DOMElementNode with attributes but no extra flags.
    node = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name="article",
        xpath="/article",
        attributes={"data-role": "main", "lang": "en"},
        children=[],
        is_interactive=False,
        is_top_element=False,
        shadow_root=False,
        highlight_index=None
    )
    # The __repr__ should output the tag with its attributes only.
    # Since Python 3.7+ dict preserves insertion order, we expect the attributes in the order provided.
    expected_repr = '<article data-role="main" lang="en">'
    assert repr(node) == expected_repr
def test_clickable_elements_attribute_filter():
    """
    Test that clickable_elements_to_string only includes attributes specified in include_attributes,
    filtering out any attributes not explicitly included.
    """
    # Create a root element.
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    # Create a clickable element (button) with multiple attributes.
    button = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name='button',
        xpath='/div/button',
        attributes={'class': 'btn', 'id': 'btn1', 'data-custom': 'value'},
        children=[],
        highlight_index=15
    )
    # Add a text node as child of the button element.
    button_text = DOMTextNode(
        is_visible=True,
        parent=button,
        text="Click Here",
        type="TEXT_NODE"
    )
    button.children.append(button_text)
    # Add the button to the root's children.
    root.children.append(button)
    
    # Call clickable_elements_to_string, asking to include only 'class' and 'id' attributes.
    clickable_output = root.clickable_elements_to_string(include_attributes=['class', 'id'])
    
    # Verify that the clickable output includes the allowed attributes but not 'data-custom'.
    assert '[15]<button class="btn" id="btn1">' in clickable_output
    assert 'data-custom' not in clickable_output
    # And verify that the button's text is included.
    assert "Click Here" in clickable_output
def test_text_node_whitespace_preservation():
    """
    Test that get_all_text_till_next_clickable_element returns a string in which overall leading
    and trailing whitespace is trimmed while internal newlines are preserved.
    """
    # Create a root element (div) with two text node children that contain extra whitespace.
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name="div",
        xpath="/div",
        attributes={},
        children=[]
    )
    text1 = DOMTextNode(
        is_visible=True,
        parent=root,
        text="   Leading and trailing   ",
        type="TEXT_NODE"
    )
    text2 = DOMTextNode(
        is_visible=True,
        parent=root,
        text="\nMiddle text\n",
        type="TEXT_NODE"
    )
    root.children.extend([text1, text2])
    
    # When get_all_text_till_next_clickable_element is called, it joins the texts with "\n" and then strips the result.
    # The joined string (before strip) is:
    #   "   Leading and trailing   \n\nMiddle text\n"
    # After .strip(), the leading whitespace and final newline are removed, resulting in:
    expected = "Leading and trailing   \n\nMiddle text"
    result = root.get_all_text_till_next_clickable_element()
    assert result == expected
def test_recursive_file_upload_element():
    """
    Test that get_file_upload_element properly finds a file input element
    in a deeply nested child even when it is not an immediate child or sibling.
    """
    # Build the DOM tree:
    # root (div)
    #   └── container (section)
    #         └── nested_container (div)
    #               └── input_file (input type="file")
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    container = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name='section',
        xpath='/div/section',
        attributes={},
        children=[]
    )
    nested_container = DOMElementNode(
        is_visible=True,
        parent=container,
        tag_name='div',
        xpath='/div/section/div',
        attributes={},
        children=[]
    )
    input_file = DOMElementNode(
        is_visible=True,
        parent=nested_container,
        tag_name='input',
        xpath='/div/section/div/input',
        attributes={'type': 'file'},
        children=[]
    )
    # Assemble the tree
    nested_container.children.append(input_file)
    container.children.append(nested_container)
    root.children.append(container)
    
    # Call get_file_upload_element on the container, expecting it to recursively find the file input
    result = container.get_file_upload_element()
    assert result == input_file, f"Expected to find the nested file input, but got {result}"
def test_repr_ignores_non_printed_fields():
    """
    Test that __repr__ of a DOMElementNode ignores properties that are not meant for display,
    such as viewport_coordinates, page_coordinates, and viewport_info, and only prints
    the tag, attributes, and extra flags (if set).
    """
    # Create dummy objects for viewport_coordinates, page_coordinates, and viewport_info.
    dummy_coord = object()
    dummy_viewport_info = object()
    
    # Build a DOMElementNode with extra non-displayed properties.
    node = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={'role': 'main'},
        children=[],
        viewport_coordinates=dummy_coord,
        page_coordinates=dummy_coord,
        viewport_info=dummy_viewport_info,
        is_interactive=True,
        is_top_element=True,
        shadow_root=False,  # Not set as shadow root so it should not appear in __repr__
        highlight_index=5
    )
    
    # Call __repr__ and verify it prints the tag, attribute, and extras but not the non-displayed properties.
    repr_str = repr(node)
    # Expected to show tag and attributes.
    assert '<div role="main">' in repr_str
    # Expected to show extra flags for interactive, top, and highlight_index, but not shadow-root.
    assert 'interactive' in repr_str
    assert 'top' in repr_str
    assert 'highlight:5' in repr_str
    assert 'shadow-root' not in repr_str
def test_unexpected_child_type():
    """
    Test that get_all_text_till_next_clickable_element safely ignores children that are not instances of DOMBaseNode.
    In this scenario, a DOMElementNode has one valid DOMTextNode and one unexpected integer.
    The method should return only the text from the valid text node.
    """
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name="div",
        xpath="/div",
        attributes={},
        children=[]
    )
    # Create a valid text node.
    valid_text = DOMTextNode(
        is_visible=True,
        parent=root,
        text="Valid text",
        type="TEXT_NODE"
    )
    # Append a valid text node and an unexpected child type (an integer).
    root.children.append(valid_text)
    root.children.append(123)  # This is not a DOM node; should be safely ignored.
    
    collected_text = root.get_all_text_till_next_clickable_element()
    assert collected_text == "Valid text"
def test_clickable_elements_depth_first_order():
    """
    Test that clickable_elements_to_string returns clickable representations and text nodes
    in the proper depth-first order for a tree with mixed highlighted (clickable) and 
    non-highlighted elements.
    """
    # Build the root element.
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    # Direct text node (non-highlighted).
    text_alpha = DOMTextNode(
        is_visible=True,
        parent=root,
        text="Alpha",
        type="TEXT_NODE"
    )
    # A highlighted element (section) with one text child.
    section = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name='section',
        xpath='/div/section',
        attributes={},
        children=[],
        highlight_index=10
    )
    # The text inside the highlighted section.
    section_text = DOMTextNode(
        is_visible=True,
        parent=section,
        text="Beta",
        type="TEXT_NODE"
    )
    section.children.append(section_text)
    # A non-highlighted element (div) with one text child.
    inner_div = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name='div',
        xpath='/div/div',
        attributes={},
        children=[]
    )
    inner_div_text = DOMTextNode(
        is_visible=True,
        parent=inner_div,
        text="Gamma",
        type="TEXT_NODE"
    )
    inner_div.children.append(inner_div_text)
    # Another direct text node.
    text_delta = DOMTextNode(
        is_visible=True,
        parent=root,
        text="Delta",
        type="TEXT_NODE"
    )
    
    # Assemble the tree in order.
    root.children.extend([text_alpha, section, inner_div, text_delta])
    
    # Call clickable_elements_to_string on the root.
    clickable_output = root.clickable_elements_to_string()
    
    # Expected order:
    # 1) The direct text node "Alpha": "[]Alpha"
    # 2) The highlighted section element: "[10]<section>Beta</section>" 
    #    (its own child text "Beta" is added into this clickable representation)
    # 3) The non-highlighted inner div's text node "Gamma": "[]Gamma"
    # 4) The direct text node "Delta": "[]Delta"
    expected = "[]Alpha\n[10]<section>Beta</section>\n[]Gamma\n[]Delta"
    assert clickable_output == expected
def test_invalid_nested_child_in_tree():
    """
    Test that get_all_text_till_next_clickable_element safely ignores invalid nested child types.
    This builds a DOM tree where a nested DOMElementNode has both a valid DOMTextNode and an invalid
    child (an integer). The test verifies that only valid DOMTextNode texts are included in the output.
    """
    # Create the root node with a direct text child.
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name="div",
        xpath="/div",
        attributes={},
        children=[]
    )
    root_text = DOMTextNode(
        is_visible=True,
        parent=root,
        text="RootText",
        type="TEXT_NODE"
    )
    root.children.append(root_text)
    
    # Create a nested element.
    nested_elem = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name="section",
        xpath="/div/section",
        attributes={},
        children=[]
    )
    # Valid nested text node.
    nested_text = DOMTextNode(
        is_visible=True,
        parent=nested_elem,
        text="Valid Nested",
        type="TEXT_NODE"
    )
    nested_elem.children.append(nested_text)
    # Append an invalid child type (e.g., an integer) to the nested element.
    nested_elem.children.append(123)
    
    # Add the nested element to the root.
    root.children.append(nested_elem)
    
    # Call get_all_text_till_next_clickable_element to collect texts.
    collected_text = root.get_all_text_till_next_clickable_element()
    # Expected output: both the root text and the valid nested text, joined by newline.
    expected_output = "RootText\nValid Nested"
    assert collected_text == expected_output, f"Expected '{expected_output}', got '{collected_text}'"
def test_clickable_elements_with_invalid_child():
    """
    Test that clickable_elements_to_string safely ignores invalid child types in the DOM tree.
    The test creates a DOMElementNode with both valid children (DOMTextNode) and invalid children
    (an integer, a string, and None). It then verifies that only the valid children are included in the output.
    """
    # Create a root element.
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    # Create a valid text node.
    valid_text = DOMTextNode(
        is_visible=True,
        parent=root,
        text="Valid",
        type="TEXT_NODE"
    )
    # Append the valid text node and some invalid children.
    root.children.extend([valid_text, 42, "invalid", None])
    
    # Call clickable_elements_to_string.
    output = root.clickable_elements_to_string()
    
    # Verify that the output only contains the valid text node's representation.
    # As no element is highlighted, the text node should be represented with "[]" prefixed.
    assert "[]Valid" in output
    # Confirm that invalid children did not appear in the output.
    assert "42" not in output
    assert "invalid" not in output
def test_repr_with_special_characters():
    """
    Test that __repr__ correctly outputs attributes containing special characters (e.g., quotes, angle brackets)
    without escaping them.
    """
    special_attrs = {
        'data-value': 'some "quoted" value',
        'data-note': 'value with <tags>'
    }
    node = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='span',
        xpath='/span',
        attributes=special_attrs,
        children=[]
    )
    rep = repr(node)
    # Check that the repr string starts with the tag, contains both attribute strings,
    # and does not include any extra flags because none were set.
    assert rep.startswith('<span')
    assert 'data-value="some "quoted" value"' in rep
    assert 'data-note="value with <tags>"' in rep
    # Since no extra flags are set, the repr should simply end with '>'
    assert rep.endswith('>')
def test_zero_highlight_index_behavior():
    """
    Test the behavior when an element's highlight_index is set to 0.
    When the highlighted element appears as a child of a parent (which is not self),
    its entire subtree is skipped in get_all_text_till_next_clickable_element.
    However, when rendering the clickable representation using clickable_elements_to_string,
    the highlighted element's own text is collected (since get_all_text_till_next_clickable_element
    is called with self as the starting node) and rendered with its highlight index.
    """
    # Build the tree:
    #    root (div)
    #      ├── TextNode: "RootText"
    #      ├── Element with highlight_index=0 (child_elem)
    #      │       └── TextNode: "HiddenText"
    #      └── TextNode: "SiblingText"
    
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name="div",
        xpath="/div",
        attributes={},
        children=[]
    )
    
    text_root = DOMTextNode(
        is_visible=True,
        parent=root,
        text="RootText",
        type="TEXT_NODE"
    )
    root.children.append(text_root)
    
    # Create a child element with a highlight_index of 0.
    child_elem = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name="child_elem",
        xpath="/div/child_elem",
        attributes={},
        children=[],
        highlight_index=0
    )
    root.children.append(child_elem)
    
    hidden_text = DOMTextNode(
        is_visible=True,
        parent=child_elem,
        text="HiddenText",
        type="TEXT_NODE"
    )
    child_elem.children.append(hidden_text)
    
    sibling_text = DOMTextNode(
        is_visible=True,
        parent=root,
        text="SiblingText",
        type="TEXT_NODE"
    )
    root.children.append(sibling_text)
    
    # When calling get_all_text_till_next_clickable_element on the root,
    # the branch corresponding to child_elem should be skipped.
    collected_text = root.get_all_text_till_next_clickable_element()
    # Expected to collect text from text_root and sibling_text, but not from child_elem.
    assert collected_text == "RootText\nSiblingText"
    
    # For clickable_elements_to_string, the child_elem should be rendered specially since it is highlighted.
    clickable_output = root.clickable_elements_to_string()
    # Expected clickable representation:
    # - The non-highlighted text nodes are rendered as: "[]RootText" and "[]SiblingText".
    # - The highlighted child_elem is rendered with its own text using get_all_text_till_next_clickable_element,
    #   which in that case collects "HiddenText", resulting in "[0]<child_elem>HiddenText</child_elem>".
    expected_clickable = "[]RootText\n[0]<child_elem>HiddenText</child_elem>\n[]SiblingText"
    assert clickable_output == expected_clickable
def test_text_node_parent_highlight_flag():
    """
    Test that DOMTextNode.has_parent_with_highlight_index returns:
      - False when the immediate parent (or any ancestor) has no highlight_index set.
      - True when any ancestor in the parent chain has a highlight_index set.
    This verifies the proper traversal of the parent chain in the method.
    """
    # Case 1: Text node with no parent at all.
    lone_text = DOMTextNode(
        is_visible=True,
        parent=None,
        text="Lone text",
        type="TEXT_NODE"
    )
    assert lone_text.has_parent_with_highlight_index() is False
    # Case 2: Text node with a parent that has no highlight.
    parent = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name="div",
        xpath="/div",
        attributes={},
        children=[]
    )
    child_text = DOMTextNode(
        is_visible=True,
        parent=parent,
        text="Child text",
        type="TEXT_NODE"
    )
    # No highlight on parent: expectation is False.
    assert child_text.has_parent_with_highlight_index() is False
    # Case 3: Text node with a parent that gets a highlight later.
    parent.highlight_index = 7
    assert child_text.has_parent_with_highlight_index() is True
    # Case 4: Text node with a deeper ancestry where immediate parent has no highlight,
    # but a grandparent does.
    root = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name="section",
        xpath="/section",
        attributes={},
        children=[]
    )
    mid = DOMElementNode(
        is_visible=True,
        parent=root,
        tag_name="div",
        xpath="/section/div",
        attributes={},
        children=[]
    )
    deep_child = DOMTextNode(
        is_visible=True,
        parent=mid,
        text="Deep child text",
        type="TEXT_NODE"
    )
    # Initially, no highlight in chain.
    assert deep_child.has_parent_with_highlight_index() is False
    # Set highlight on the root (grandparent)
    root.highlight_index = 10
    assert deep_child.has_parent_with_highlight_index() is True
def test_clickable_elements_empty_highlight_text():
    """
    Test that clickable_elements_to_string outputs the expected clickable representation
    for a highlighted element that has no text in its subtree. This verifies that even when
    get_all_text_till_next_clickable_element returns an empty string, the clickable output
    correctly shows the element's tag and attributes.
    """
    # Create a highlighted DOM element (with no children/text).
    node = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={'class': 'empty'},
        children=[],
        highlight_index=99
    )
    
    # Verify that get_all_text_till_next_clickable_element returns an empty string.
    assert node.get_all_text_till_next_clickable_element() == ""
    
    # clickable_elements_to_string with an attribute filter should produce a clickable representation.
    clickable_output = node.clickable_elements_to_string(include_attributes=['class'])
    expected_output = '[99]<div class="empty"></div>'
    assert clickable_output == expected_output
def test_hash_immutable_after_change(monkeypatch):
    """
    Test that once the hash property is computed for a DOMElementNode,
    changes to the node (e.g. modifying tag_name) do not affect the cached hash value.
    """
    from browser_use.dom.views import DOMElementNode
    # Create a node with tag_name 'div'
    node = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    # Monkey-patch the hash function to return "hash_" concatenated with the current tag_name.
    monkeypatch.setattr(
        "browser_use.dom.history_tree_processor.service.HistoryTreeProcessor._hash_dom_element",
        lambda elem: f"hash_{elem.tag_name}"
    )
    # Trigger the computation of the hash. It should compute to "hash_div".
    initial_hash = node.hash
    assert initial_hash == "hash_div"
    
    # Change the node's tag_name after the hash is already computed.
    node.tag_name = "span"
    
    # The cached hash should remain unchanged.
    assert node.hash == "hash_div"
def test_advanced_css_selector_none(monkeypatch):
    """
    Test that get_advanced_css_selector returns None when the BrowserContext's _enhanced_css_selector_for_element
    method (monkey-patched here) returns None.
    """
    monkeypatch.setattr(
        "browser_use.browser.context.BrowserContext._enhanced_css_selector_for_element",
        lambda elem: None
    )
    node = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='p',
        xpath='/p',
        attributes={'class': 'test'},
        children=[]
    )
    selector = node.get_advanced_css_selector()
    assert selector is None
def test_circular_reference_handling():
    """
    Test that get_all_text_till_next_clickable_element with a max_depth limit prevents infinite recursion
    even when the DOM tree contains a circular reference. This constructs a cycle and verifies that text from
    nodes beyond the max_depth are not processed.
    """
    # Create node A.
    A = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={},
        children=[]
    )
    # Add a text node to A.
    text_A = DOMTextNode(
        is_visible=True,
        parent=A,
        text="A_text",
        type="TEXT_NODE"
    )
    A.children.append(text_A)
    
    # Create node B as a child element of A.
    B = DOMElementNode(
        is_visible=True,
        parent=A,
        tag_name='span',
        xpath='/div/span',
        attributes={},
        children=[]
    )
    # Add a text node to B.
    text_B = DOMTextNode(
        is_visible=True,
        parent=B,
        text="B_text",
        type="TEXT_NODE"
    )
    B.children.append(text_B)
    
    # Append B to A's children.
    A.children.append(B)
    
    # Introduce a circular reference: add A as a child of B.
    B.children.append(A)
    
    # Call get_all_text_till_next_clickable_element with max_depth=2.
    # Expected:
    #   - At depth 0: processing node A.
    #   - At depth 1: processing A's children: the text node "A_text" and node B.
    #   - At depth 2: processing node B's children: the text node "B_text" and then A (cyclic) is reached
    #     but further recursion from A would be at depth 3 which exceeds max_depth and is skipped.
    # Therefore, the expected concatenated text is "A_text\nB_text".
    result = A.get_all_text_till_next_clickable_element(max_depth=2)
    expected = "A_text\nB_text"
    assert result == expected
def test_repr_dynamic_attribute_change():
    """
    Test that a DOMElementNode's __repr__ dynamically reflects changes in its attributes.
    The test creates a node with an initial attribute, then updates the attributes dictionary,
    and checks that the __repr__ output reflects the updated values.
    """
    # Create a DOMElementNode with an initial attribute.
    node = DOMElementNode(
        is_visible=True,
        parent=None,
        tag_name='div',
        xpath='/div',
        attributes={"class": "initial"},
        children=[]
    )
    
    # Obtain the initial __repr__ and verify the initial attribute.
    repr_initial = repr(node)
    assert 'class="initial"' in repr_initial, f"Initial repr did not contain expected attribute: {repr_initial}"
    
    # Modify the attributes: update existing and add a new one.
    node.attributes["class"] = "updated"
    node.attributes["data-new"] = "value"
    
    # Now, when __repr__ is called it should reflect these new attributes.
    repr_updated = repr(node)
    assert 'class="updated"' in repr_updated, f"Updated repr did not reflect updated class attribute: {repr_updated}"
    assert 'data-new="value"' in repr_updated, f"Updated repr did not include the new attribute: {repr_updated}"