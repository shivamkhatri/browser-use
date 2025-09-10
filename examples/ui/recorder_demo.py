# pyright: reportMissingImports=false
import asyncio
import os
import sys
import json
from collections import deque
from typing import Deque

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv

load_dotenv()

import gradio as gr
from browser_use import Agent, BrowserSession
from browser_use.browser.events import RecordableEvent

recorded_steps: Deque[RecordableEvent] = deque()
modules: dict = {}
MODULES_FILE = "modules.json"

browser_session: BrowserSession | None = None


def load_modules():
    global modules
    if os.path.exists(MODULES_FILE):
        with open(MODULES_FILE, "r") as f:
            modules = json.load(f)


def save_modules():
    with open(MODULES_FILE, "w") as f:
        json.dump(modules, f, indent=2)


async def start_recording(url: str):
    global browser_session
    browser_session = BrowserSession(headless=False)
    await browser_session.start()
    browser_session.event_bus.on(RecordableEvent, on_recordable_event)
    browser_session.start_recording()
    await browser_session.navigate_to(url)
    return "Recording started..."


def on_recordable_event(event: RecordableEvent):
    recorded_steps.append(event)


def stop_recording():
    if browser_session:
        browser_session.stop_recording()
    return "Recording stopped."


def get_recorded_steps():
    return [[step.action, str(step.params)] for step in recorded_steps]


def create_module(name: str, description: str, selected_indices: list[int]):
    if not name:
        return "Module name cannot be empty."
    if not selected_indices:
        return "No steps selected."

    module_steps = [recorded_steps[i] for i in selected_indices]
    modules[name] = {"description": description, "steps": [
        {"action": step.action, "params": step.params} for step in module_steps
    ]}
    save_modules()
    return f"Module '{name}' created."


def get_module_names():
    return list(modules.keys())


def insert_module(module_name: str):
    if module_name not in modules:
        return "Module not found."

    module = modules[module_name]
    for step in module["steps"]:
        # This is a simplified way of re-creating the event.
        # In a real application, you might need a more robust way to serialize/deserialize events.
        event = RecordableEvent(action=step["action"], params=step["params"])
        recorded_steps.append(event)
    return "Module inserted."


def create_ui():
    with gr.Blocks(title="Browser-use Recorder") as interface:
        gr.Markdown("# Browser-use Interaction Recorder")

        with gr.Row():
            with gr.Column():
                url_input = gr.Textbox(label="Initial URL", placeholder="https://example.com")
                start_btn = gr.Button("Start Recording")
                stop_btn = gr.Button("Stop Recording")

            with gr.Column():
                recorded_steps_display = gr.DataFrame(headers=["Action", "Parameters"], datatype=["str", "str"], row_count=10, col_count=2, interactive=True)

        with gr.Row():
            with gr.Column():
                module_name = gr.Textbox(label="Module Name")
                module_desc = gr.Textbox(label="Module Description")
                create_module_btn = gr.Button("Create Module")
            with gr.Column():
                module_dropdown = gr.Dropdown(label="Select Module", choices=get_module_names())
                insert_module_btn = gr.Button("Insert Module")

        start_btn.click(
            fn=lambda url: asyncio.run(start_recording(url)),
            inputs=[url_input],
            outputs=None,
        )

        stop_btn.click(fn=stop_recording, outputs=None)

        def update_steps_and_modules():
            steps = get_recorded_steps()
            module_names = get_module_names()
            return steps, gr.update(choices=module_names)

        timer = gr.Timer(1)
        timer.tick(update_steps_and_modules, None, [recorded_steps_display, module_dropdown])

        def on_select(evt: gr.SelectData):
            return [evt.index]

        selected_indices = gr.State([])
        recorded_steps_display.select(on_select, None, selected_indices)

        create_module_btn.click(
            fn=create_module,
            inputs=[module_name, module_desc, selected_indices],
            outputs=None,
        )

        insert_module_btn.click(
            fn=insert_module,
            inputs=[module_dropdown],
            outputs=None,
        )

    return interface


if __name__ == "__main__":
    load_modules()
    demo = create_ui()
    demo.launch()
