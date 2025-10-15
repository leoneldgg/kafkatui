from textual.screen import ModalScreen
from textual.widgets import Button, Static
from textual.containers import Vertical, VerticalScroll

class MessageModal(ModalScreen[None]):
    """Modal centered over the main app — smaller window"""
    CSS = """
    MessageModal { align: center middle; }
    #modal-container {
        width: 80%;
        max-width: 100;
        height: 70%;
        background: $surface;
        border: round $accent;
        padding: 1 2;
        overflow: hidden;
    }
    #modal-title {
        content-align: center middle;
        height: 3;
        color: $text;
        text-style: bold;
    }
    #modal-scroll { height: 1fr; border: none; background: $boost; }
    #modal-body { padding: 1; }
    #close {
        dock: bottom; width: 100%; height: 3;
        content-align: center middle; background: $accent; color: black; text-style: bold;
    }
    """

    def __init__(self, title: str, renderable):
        super().__init__()
        self._title = title
        self._renderable = renderable

    def compose(self):
        with Vertical(id="modal-container"):
            yield Static(self._title, id="modal-title")
            with VerticalScroll(id="modal-scroll"):
                yield Static(self._renderable, id="modal-body")
            yield Button("Close", id="close")

    def on_button_pressed(self, event: Button.Pressed):
        self.dismiss()

    BINDINGS = [("escape", "dismiss", "Close"), ("q", "dismiss", "Close")]

    def action_dismiss(self):
        self.dismiss()
