"""Interaction Recorder Watchdog for Browser Use Sessions."""

from typing import ClassVar
from bubus import BaseEvent
from cdp_use.cdp.input import DispatchKeyEventEvent, DispatchMouseEventEvent

from browser_use.browser.events import (
    BrowserConnectedEvent,
    BrowserStopEvent,
    RecordableEvent,
)
from browser_use.browser.watchdog_base import BaseWatchdog


class InteractionRecorderWatchdog(BaseWatchdog):
    """
    Manages recording of user interactions and converting them to browser-use actions.
    """

    LISTENS_TO: ClassVar[list[type[BaseEvent]]] = [
        BrowserConnectedEvent,
        BrowserStopEvent,
        DispatchMouseEventEvent,
        DispatchKeyEventEvent,
    ]
    EMITS: ClassVar[list[type[BaseEvent]]] = [RecordableEvent]

    _is_recording: bool = False

    async def on_BrowserConnectedEvent(self, event: BrowserConnectedEvent) -> None:
        """
        Enable input domain tracking when browser is connected.
        """
        if not self.browser_session.agent_focus:
            return

        await self.browser_session.agent_focus.cdp_client.send.Input.enable(
            session_id=self.browser_session.agent_focus.session_id
        )
        self.logger.info("🎙️ Interaction recorder enabled.")

    async def on_BrowserStopEvent(self, event: BrowserStopEvent) -> None:
        """
        Disable input domain tracking when browser is stopped.
        """
        if not self.browser_session.agent_focus:
            return

        await self.browser_session.agent_focus.cdp_client.send.Input.disable(
            session_id=self.browser_session.agent_focus.session_id
        )
        self.logger.info("🎙️ Interaction recorder disabled.")

    def start_recording(self):
        self._is_recording = True
        self.logger.info("▶️ Started recording user interactions.")

    def stop_recording(self):
        self._is_recording = False
        self.logger.info("⏹️ Stopped recording user interactions.")

    async def on_DispatchMouseEvent(self, event: DispatchMouseEventEvent, session_id: str | None) -> None:
        """
        Handles mouse events and converts them to recordable actions.
        """
        if not self._is_recording:
            return

        if event["type"] == "mousePressed":
            # This is a click event. We need to find the element that was clicked.
            # We can use the x and y coordinates to find the element.
            x = event["x"]
            y = event["y"]

            # Get the DOM state to find the element at the given coordinates.
            dom_state = await self.browser_session.get_browser_state_summary(include_screenshot=False)
            element = self._find_element_at(dom_state, x, y)

            if element:
                # We found the element. Now, create a recordable event.
                self.event_bus.dispatch(
                    RecordableEvent(
                        action="click",
                        params={"index": element.element_index},
                        element=element,
                    )
                )

    async def on_DispatchKeyEvent(self, event: DispatchKeyEventEvent, session_id: str | None) -> None:
        """
        Handles keyboard events and converts them to recordable actions.
        """
        if not self._is_recording:
            return

        if event["type"] == "char":
            # This is a key press event. We need to find the active element.
            dom_state = await self.browser_session.get_browser_state_summary(include_screenshot=False)
            active_element = self._find_active_element(dom_state)

            if active_element:
                self.event_bus.dispatch(
                    RecordableEvent(
                        action="type",
                        params={"index": active_element.element_index, "text": event["text"]},
                        element=active_element,
                    )
                )

    def _find_element_at(self, dom_state, x, y):
        if not dom_state or not dom_state.dom_state or not dom_state.dom_state.selector_map:
            return None

        for element in dom_state.dom_state.selector_map.values():
            if element.bounding_box_rect:
                x1, y1, x2, y2 = (
                    element.bounding_box_rect["x"],
                    element.bounding_box_rect["y"],
                    element.bounding_box_rect["x"] + element.bounding_box_rect["width"],
                    element.bounding_box_rect["y"] + element.bounding_box_rect["height"],
                )
                if x1 <= x <= x2 and y1 <= y <= y2:
                    return element
        return None

    def _find_active_element(self, dom_state):
        if not dom_state or not dom_state.dom_state or not dom_state.dom_state.selector_map:
            return None

        for element in dom_state.dom_state.selector_map.values():
            if element.focused:
                return element
        return None
