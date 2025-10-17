from __future__ import annotations
import json
from datetime import datetime
from typing import List

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Input, Static
from textual.containers import Horizontal, Vertical
from textual import on
from textual.reactive import reactive
from textual.timer import Timer
from rich.syntax import Syntax
from kafka import TopicPartition

from kafka_client import KafkaClient
from ui.modal import MessageModal


class KafkaTUI(App):
    CSS = """
    .label { padding: 0 1; }
    #search { border: round $accent; }
    """
    BINDINGS = [
        ("r", "reload", "Reload"),
        ("a", "toggle_auto_refresh", "Auto refresh"),
        ("/", "focus_search", "Search"),
        ("escape", "clear_search", "Clear search"),
        ("enter", "open_message_modal", "Show message details"),
        ("q", "quit", "Quit"),
    ]

    auto_refresh_enabled: reactive[bool] = reactive(False)
    refresh_timer: Timer | None = None

    topics_all: reactive[List[str]] = reactive([])
    filter_text: reactive[str] = reactive("")
    selected_topic: reactive[str | None] = reactive(None)

    message_payloads: dict[str, dict] = {}

    def __init__(self, bootstrap_servers: str, kafka_kwargs: dict):
        super().__init__()
        self.client = KafkaClient(bootstrap_servers, **kafka_kwargs)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical():
            yield Static("Filter topics:", classes="label")
            yield Input(placeholder="Type to filter… (shortcut: /)", id="search")
            yield DataTable(id="topics")
        with Horizontal():
            yield DataTable(id="info")
            yield DataTable(id="messages")
        yield Footer()

    def on_mount(self) -> None:
        topics_tbl = self.query_one("#topics", DataTable)
        topics_tbl.add_columns("Topics")
        topics_tbl.cursor_type = "row"
        topics_tbl.zebra_stripes = True

        info_tbl = self.query_one("#info", DataTable)
        info_tbl.add_columns("Property", "Value")
        info_tbl.zebra_stripes = True

        msg_tbl = self.query_one("#messages", DataTable)
        msg_tbl.add_columns("Part", "Offset", "Time", "Key", "Value")
        msg_tbl.zebra_stripes = True
        msg_tbl.cursor_type = "row"

        self.load_topics()

    # ---------- topics load/filter ----------
    def load_topics(self) -> None:
        try:
            self.topics_all = self.client.list_topics()
        except Exception as e:
            self.notify(f"Failed to load topics: {e}", severity="error")
            self.topics_all = []
        self.refresh_topics_table()

    def refresh_topics_table(self) -> None:
        table = self.query_one("#topics", DataTable)
        table.clear()
        q = self.filter_text.lower().strip()
        data = (t for t in self.topics_all if q in t.lower()) if q else self.topics_all
        for t in data:
            table.add_row(t, key=t)

    @on(Input.Changed, "#search")
    def on_search_changed(self, event: Input.Changed) -> None:
        self.filter_text = event.value
        self.refresh_topics_table()

    def action_focus_search(self) -> None:
        self.query_one("#search", Input).focus()

    def action_clear_search(self) -> None:
        self.filter_text = ""
        search = self.query_one("#search", Input)
        search.value = ""
        self.refresh_topics_table()

    def action_reload(self) -> None:
        self.load_topics()

    # ---------- topic selection ----------
    @on(DataTable.RowSelected, "#topics")
    def on_topic_selected(self, event: DataTable.RowSelected) -> None:
        rk = event.row_key
        topic = getattr(rk, "value", rk)
        if not topic:
            self.notify("No topic selected.", severity="warning")
            return
        self.selected_topic = str(topic)
        self.show_topic(self.selected_topic)

        if self.auto_refresh_enabled:
            if self.refresh_timer:
                self.refresh_timer.pause()
                self.refresh_timer = None
            self.refresh_timer = self.set_interval(2.0, self._tick_refresh, pause=False)

    # ---------- info/messages panels ----------
    def refresh_topic_info(self, topic: str) -> None:
        info_tbl = self.query_one("#info", DataTable)
        info_tbl.clear()
        try:
            partitions = self.client.partitions_for_topic(topic)
            earliest, latest = self.client.topic_offsets(topic)
        except Exception as e:
            self.notify(f"Failed to fetch topic info: {e}", severity="error")
            return

        total_msgs = sum(
            max(latest.get(TopicPartition(topic, p), 0) - earliest.get(TopicPartition(topic, p), 0), 0)
            for p in partitions
        )

        info_tbl.add_row("Topic", topic)
        info_tbl.add_row("Partitions", str(len(partitions)))
        info_tbl.add_row("Total messages (approx.)", str(total_msgs))
        for p in partitions:
            tp = TopicPartition(topic, p)
            e = earliest.get(tp, 0)
            l = latest.get(tp, 0)
            info_tbl.add_row(f"p{p} earliest", str(e))
            info_tbl.add_row(f"p{p} latest", str(l))
            info_tbl.add_row(f"p{p} count", str(max(l - e, 0)))
        
        lag = self.client.topic_total_lag(topic)
        info_tbl.add_row("Total lag (all groups)", str(lag))
    
    def refresh_messages_only(self, topic: str) -> None:
        msg_tbl = self.query_one("#messages", DataTable)
        msg_tbl.clear()

        try:
            tail = self.client.read_tail(topic, max_messages=50)
        except Exception as e:
            self.notify(f"Failed to read messages: {e}", severity="error")
            return

        new_payloads: dict[str, dict] = {}
        for part, offset, ts_ms, key, val in tail:
            dt = datetime.fromtimestamp(ts_ms / 1000.0).strftime("%Y-%m-%d %H:%M:%S") if ts_ms else "-"
            row_key = f"{part}:{offset}"
            new_payloads[row_key] = {
                "partition": part,
                "offset": offset,
                "timestamp_ms": ts_ms,
                "key": key or "",
                "value": val or "",
                "time_str": dt,
            }
            msg_tbl.add_row(str(part), str(offset), dt, key or "", (val or "")[:500], key=row_key)

        self.message_payloads = new_payloads
        if msg_tbl.row_count and msg_tbl.cursor_row is None:
            msg_tbl.move_cursor(row=0)

    def show_topic(self, topic: str) -> None:
        self.refresh_topic_info(topic)
        self.refresh_messages_only(topic)

    # ---------- open modal ----------
    @on(DataTable.RowSelected, "#messages")
    def on_message_row_selected(self, event: DataTable.RowSelected) -> None:
        tbl = self.query_one("#messages", DataTable)
        rk = event.row_key
        if rk is None and tbl.row_count and tbl.cursor_row is not None:
            rk = list(tbl.rows.keys())[tbl.cursor_row]
        if rk is None:
            self.notify("No message row selected.", severity="warning")
            return

        row_key = str(getattr(rk, "value", rk))
        data = self.message_payloads.get(row_key)
        if not data:
            self.notify(f"Message not found for key {row_key}.", severity="warning")
            return

        raw = data["value"]
        try:
            pretty = json.dumps(json.loads(raw), indent=2, ensure_ascii=False)
            renderable = Syntax(pretty, "json", word_wrap=True)
        except Exception:
            renderable = Syntax(raw, "text", word_wrap=True)

        title = f"Topic: {self.selected_topic} | p{data['partition']}@{data['offset']} | {data['time_str']}"
        if self.refresh_timer:
            self.refresh_timer.pause()
        self.push_screen(MessageModal(title=title, renderable=renderable))

    def action_open_message_modal(self) -> None:
        msg_tbl = self.query_one("#messages", DataTable)
        if self.focused is not msg_tbl:
            msg_tbl.focus()
        if not msg_tbl.row_count or msg_tbl.cursor_row is None:
            self.notify("Select a message first.", severity="warning")
            return
        rk = list(msg_tbl.rows.keys())[msg_tbl.cursor_row]
        row_key = str(getattr(rk, "value", rk))
        data = self.message_payloads.get(row_key)
        if not data:
            self.notify(f"Message not found for key {row_key}.", severity="warning")
            return

        raw = data["value"]
        try:
            pretty = json.dumps(json.loads(raw), indent=2, ensure_ascii=False)
            renderable = Syntax(pretty, "json", word_wrap=True)
        except Exception:
            renderable = Syntax(raw, "text", word_wrap=True)

        title = f"Topic: {self.selected_topic} | p{data['partition']}@{data['offset']} | {data['time_str']}"
        self.push_screen(MessageModal(title=title, renderable=renderable))

    # ---------- timers & helpers ----------
    def _tick_refresh(self) -> None:
        if self.selected_topic:
            self.refresh_messages_only(self.selected_topic)

    def action_toggle_auto_refresh(self) -> None:
        self.auto_refresh_enabled = not self.auto_refresh_enabled
        if self.auto_refresh_enabled:
            if self.refresh_timer:
                self.refresh_timer.pause()
                self.refresh_timer = None
            self.refresh_timer = self.set_interval(2.0, self._tick_refresh, pause=False)
            self.notify("Auto refresh: ON", severity="information")
        else:
            if self.refresh_timer:
                self.refresh_timer.pause()
                self.refresh_timer = None
            self.notify("Auto refresh: OFF", severity="information")

    def action_refresh_messages(self) -> None:
        if self.selected_topic:
            self.refresh_messages_only(self.selected_topic)
        else:
            self.notify("Select a topic first.", severity="warning")

    def on_screen_resume(self, event) -> None:
        if self.auto_refresh_enabled and self.refresh_timer:
            self.refresh_timer.resume()
