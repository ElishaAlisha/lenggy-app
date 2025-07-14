from kivy.core.window import Window

Window.minimum_width = 720
Window.minimum_height = 960
Window.size = (720, 960)

import json
import os
from datetime import datetime, date, timedelta
from calendar import monthrange
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget
from kivy.metrics import dp, sp
from kivy.clock import Clock
from kivy.uix.dropdown import DropDown
from kivy.uix.spinner import Spinner
from kivy.uix.modalview import ModalView
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import Image
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, RoundedRectangle, Rectangle


class StyledSpinner(Spinner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""


PRIMARY_COLOR = [0.36, 0.19, 0.55, 1]
SECONDARY_COLOR = [0.56, 0.27, 0.68, 1]
ACCENT_COLOR = [0.98, 0.82, 0.37, 1]
TODAY_COLOR = [1, 0.75, 0.796, 1]
EVENT_COLOR = [0.75, 0.796, 1, 1]
CARD_COLOR = [1, 1, 1, 1]
HEADER_TEXT_COLOR = [0.23, 0.16, 0.32, 1]
CAL_CELL_COLOR = [0.96, 0.93, 0.99, 1]
EVENT_FILE = "events.json"

BASE_FONT_SIZE = sp(22)
SMALL_FONT_SIZE = sp(16)
BUTTON_FONT_SIZE = sp(22)
TITLE_FONT_SIZE = sp(32)
HEADER_FONT_SIZE = sp(26)
MODAL_TITLE_SIZE = sp(26)
LABEL_FONT_SIZE = sp(20)
MEMO_FONT_SIZE = sp(18)


def format_time(time_str):
    try:
        t = datetime.strptime(time_str, "%H:%M")
        return t.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return ""


def work_time_string(segment):
    tin = format_time(segment.get("time_in", ""))
    tout = format_time(segment.get("time_out", ""))
    if tin and tout:
        return f"{tin} - {tout}"
    elif tin:
        return f"{tin}"
    elif tout:
        return f"{tout}"
    else:
        return ""


class RoundedIconButton(ButtonBehavior, BoxLayout):
    def __init__(
        self, icon_path, bg_color=(0.5, 0.3, 0.8, 1), radius=18, padding=10, **kwargs
    ):
        super().__init__(orientation="vertical", **kwargs)
        self.padding = (0, 0, 0, padding)
        self.bg_color = bg_color
        self.radius = radius
        self.icon = Image(
            source=icon_path,
            size_hint=(1, 1),
            allow_stretch=True,
            keep_ratio=True,
        )
        self.add_widget(self.icon)
        with self.canvas.before:
            Color(*self.bg_color)
            self.bg_rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[self.radius]
            )
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size


class AnimatedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = [0, 0, 0, 0]

    def on_press(self):
        self.background_color = [1, 0.93, 0.3, 1]
        self.canvas.ask_update()
        Clock.schedule_once(lambda dt: self._reset_color(), 0.15)

    def _reset_color(self):
        self.background_color = [0, 0, 0, 0]
        self.canvas.ask_update()

    def on_release(self):
        pass


class CalendarDayCell(BoxLayout):
    def __init__(self, day, date_str, is_today, has_event, events, on_press, **kwargs):
        super().__init__(
            orientation="vertical",
            spacing=dp(2),
            size_hint_y=None,
            height=dp(88),
            padding=(0, dp(10), 0, dp(2)),
            **kwargs,
        )
        self.on_press_callback = on_press
        self.date_str = date_str
        self.bind(on_touch_down=self._on_touch_down)
        self._draw_bg(is_today, has_event)
        self._add_content(day, date_str, is_today, has_event, events)

    def _on_touch_down(self, instance, touch):
        if self.collide_point(*touch.pos):
            if not hasattr(touch, "button") or touch.button in ("left", "touch"):
                self.on_press_callback(self.date_str)
                return True

    def _draw_bg(self, is_today, has_event):
        with self.canvas.before:
            if is_today:
                Color(*TODAY_COLOR)
            elif has_event:
                Color(*EVENT_COLOR)
            else:
                Color(*CAL_CELL_COLOR)
            self.bg_rect = RoundedRectangle(
                pos=self.pos, size=self.size, radius=[dp(10)]
            )
        self.bind(
            pos=lambda inst, val: setattr(self.bg_rect, "pos", inst.pos),
            size=lambda inst, val: setattr(self.bg_rect, "size", inst.size),
        )

    def _add_content(self, day, date_str, is_today, has_event, events):
        btn = AnimatedButton(
            text=f"{day}*" if is_today else f"{day}",
            background_color=[0, 0, 0, 0],
            color=[1, 1, 1, 1] if is_today else HEADER_TEXT_COLOR,
            font_size=LABEL_FONT_SIZE,
            size_hint_y=None,
            height=dp(30),
            bold=True,
            background_normal="",
            background_down="",
            markup=True,
        )
        self.add_widget(btn)
        font_size_work = int(LABEL_FONT_SIZE * 0.7)
        font_size_memo = int(LABEL_FONT_SIZE * 0.6)
        cell_width = self.width if self.width > 1 else dp(88)

        event_segments = events.get(date_str, [])
        if isinstance(event_segments, dict):  # backward compatibility
            event_segments = [event_segments]

        if has_event and event_segments:
            work_lines = []
            for idx, seg in enumerate(event_segments):
                tin = format_time(seg.get("time_in", ""))
                tout = format_time(seg.get("time_out", ""))
                work_line = f"{tin} - {tout}" if tin or tout else ""
                if work_line:
                    work_lines.append(work_line)
            memo = event_segments[0].get("memo", "") if event_segments else ""
            work_lbl = Label(
                text="\n".join(work_lines),
                font_size=font_size_work,
                color=[0.22, 0.17, 0.32, 1],
                size_hint_y=None,
                height=dp(20),
                text_size=(cell_width - dp(4), dp(20)),
                halign="center",
                valign="middle",
                shorten=True,
                shorten_from="right",
            )
            self.add_widget(work_lbl)
            max_memo_chars = max(6, int((cell_width - 10) / (font_size_memo * 0.55)))
            if memo.strip():
                display_memo = (
                    memo[:max_memo_chars] + "..."
                    if len(memo) > max_memo_chars
                    else memo
                )
                memo_lbl = Label(
                    text=f"[size={font_size_memo}][b]Memo:[/b] {display_memo}[/size]",
                    markup=True,
                    font_size=font_size_memo,
                    color=[0.27, 0.21, 0.36, 1],
                    size_hint_y=None,
                    height=dp(14),
                    text_size=(cell_width - dp(8), dp(14)),
                    halign="center",
                    valign="middle",
                    shorten=True,
                    shorten_from="right",
                )
                self.add_widget(memo_lbl)
            else:
                self.add_widget(Label(text="", size_hint_y=None, height=dp(14)))
        else:
            self.add_widget(Label(text="", size_hint_y=None, height=dp(20)))
            self.add_widget(Label(text="", size_hint_y=None, height=dp(14)))


class CalendarWidget(BoxLayout):
    def __init__(self, events, on_day_press, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(5), **kwargs)
        self.events = events
        self.on_day_press = on_day_press
        self.current_year = datetime.today().year
        self.current_month = datetime.today().month
        self._build_ui()

    def _build_ui(self):
        self._build_nav()
        self._build_week_header()
        self._build_calendar_grid()
        self.update_calendar(self.current_year, self.current_month)

    def _build_nav(self):
        nav_layout = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=dp(64), spacing=dp(10)
        )
        prev_btn = Button(
            text="<",
            background_color=SECONDARY_COLOR,
            color=[1, 1, 1, 1],
            size_hint_x=None,
            width=dp(52),
            font_size=HEADER_FONT_SIZE,
            bold=True,
            background_normal="",
            background_down="",
        )
        next_btn = Button(
            text=">",
            background_color=SECONDARY_COLOR,
            color=[1, 1, 1, 1],
            size_hint_x=None,
            width=dp(52),
            font_size=HEADER_FONT_SIZE,
            bold=True,
            background_normal="",
            background_down="",
        )
        prev_btn.bind(on_press=self._goto_prev_month)
        next_btn.bind(on_press=self._goto_next_month)
        self.month_lbl = Label(
            text="",
            markup=True,
            font_size=HEADER_FONT_SIZE,
            color=PRIMARY_COLOR,
            size_hint_x=1,
            halign="center",
            valign="middle",
        )
        self.month_lbl.bind(size=self._update_month_label)
        nav_layout.add_widget(prev_btn)
        nav_layout.add_widget(self.month_lbl)
        nav_layout.add_widget(next_btn)
        self.add_widget(nav_layout)

    def _build_week_header(self):
        week_header = GridLayout(cols=7, size_hint_y=None, height=dp(38), spacing=dp(2))
        for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            week_header.add_widget(
                Label(
                    text=d,
                    font_size=LABEL_FONT_SIZE,
                    color=HEADER_TEXT_COLOR,
                    bold=True,
                )
            )
        self.add_widget(week_header)

    def _build_calendar_grid(self):
        self.scroll = ScrollView(size_hint=(1, 0.78))
        self.grid_container = BoxLayout(orientation="vertical", size_hint_y=None)
        self.scroll.add_widget(self.grid_container)
        self.add_widget(self.scroll)

    def _update_month_label(self, instance, value):
        self.month_lbl.text_size = (self.month_lbl.width, None)
        self.month_lbl.halign = "center"
        self.month_lbl.valign = "middle"

    def update_calendar(self, year, month):
        self.month_lbl.text = f"[b]{date(year, month, 1).strftime('%B %Y')}[/b]"
        self.grid_container.clear_widgets()
        first_weekday, num_days = monthrange(year, month)
        grid = GridLayout(cols=7, spacing=dp(3), size_hint_y=None)
        num_rows = (first_weekday + num_days + 6) // 7
        grid.height = num_rows * dp(94)
        grid.bind(minimum_height=grid.setter("height"))

        blanks = first_weekday
        today_str = date.today().strftime("%Y-%m-%d")
        for _ in range(blanks):
            grid.add_widget(Widget(size_hint_y=None, height=dp(94)))
        for day in range(1, num_days + 1):
            this_date = date(year, month, day)
            date_str = this_date.strftime("%Y-%m-%d")
            has_event = date_str in self.events
            cell = CalendarDayCell(
                day,
                date_str,
                date_str == today_str,
                has_event,
                self.events,
                self.on_day_press,
            )
            grid.add_widget(cell)
        total_cells = blanks + num_days
        for _ in range((7 - total_cells % 7) % 7):
            grid.add_widget(Widget(size_hint_y=None, height=dp(94)))
        self.grid_container.add_widget(grid)
        self.grid_container.height = grid.height

    def _goto_prev_month(self, inst):
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.update_calendar(self.current_year, self.current_month)

    def _goto_next_month(self, inst):
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.update_calendar(self.current_year, self.current_month)


class TimePicker(BoxLayout):
    def __init__(self, initial_time="", **kwargs):
        super().__init__(orientation="vertical", spacing=dp(6), **kwargs)

        # Parse initial time
        if initial_time and ":" in initial_time:
            hour, minute = initial_time.split(":")
        else:
            hour, minute = "09", "00"

        # Labels row
        labels_row = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=dp(16)
        )
        labels_row.add_widget(
            Label(
                text="Hour", font_size=sp(12), color=HEADER_TEXT_COLOR, size_hint_x=0.45
            )
        )
        labels_row.add_widget(Label(text="", size_hint_x=0.1))
        labels_row.add_widget(
            Label(
                text="Min", font_size=sp(12), color=HEADER_TEXT_COLOR, size_hint_x=0.45
            )
        )
        self.add_widget(labels_row)

        # Spinners row
        spinners_row = BoxLayout(orientation="horizontal", spacing=dp(6))
        self.hour_spinner = StyledSpinner(
            text=hour,
            values=[f"{i:02d}" for i in range(24)],
            size_hint_x=0.45,
            font_size=sp(14),
            background_color=PRIMARY_COLOR,
            color=[1, 1, 1, 1],
        )
        self.minute_spinner = StyledSpinner(
            text=minute,
            values=[f"{i:02d}" for i in range(0, 60, 15)],
            size_hint_x=0.45,
            font_size=sp(14),
            background_color=PRIMARY_COLOR,
            color=[1, 1, 1, 1],
        )

        spinners_row.add_widget(self.hour_spinner)
        spinners_row.add_widget(Label(text=":", size_hint_x=0.1, font_size=sp(14)))
        spinners_row.add_widget(self.minute_spinner)
        self.add_widget(spinners_row)

    def get_time(self):
        return f"{self.hour_spinner.text}:{self.minute_spinner.text}"


class DatePicker(BoxLayout):
    def __init__(self, initial_date="", **kwargs):
        super().__init__(orientation="vertical", spacing=dp(6), **kwargs)

        # Parse initial date or use current date
        if initial_date and "-" in initial_date:
            year, month, day = initial_date.split("-")
        else:
            today = date.today()
            year, month, day = str(today.year), f"{today.month:02d}", f"{today.day:02d}"

        # Labels row
        labels_row = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=dp(16)
        )
        labels_row.add_widget(
            Label(
                text="Day", font_size=sp(12), color=HEADER_TEXT_COLOR, size_hint_x=0.33
            )
        )
        labels_row.add_widget(
            Label(
                text="Month",
                font_size=sp(12),
                color=HEADER_TEXT_COLOR,
                size_hint_x=0.33,
            )
        )
        labels_row.add_widget(
            Label(
                text="Year", font_size=sp(12), color=HEADER_TEXT_COLOR, size_hint_x=0.34
            )
        )
        self.add_widget(labels_row)

        # Spinners row
        spinners_row = BoxLayout(orientation="horizontal", spacing=dp(8))
        self.day_spinner = StyledSpinner(
            text=day,
            values=[f"{i:02d}" for i in range(1, 32)],
            size_hint_x=0.33,
            font_size=sp(14),
            background_color=PRIMARY_COLOR,
            color=[1, 1, 1, 1],
        )
        self.month_spinner = StyledSpinner(
            text=month,
            values=[f"{i:02d}" for i in range(1, 13)],
            size_hint_x=0.33,
            font_size=sp(14),
            background_color=PRIMARY_COLOR,
            color=[1, 1, 1, 1],
        )
        self.year_spinner = StyledSpinner(
            text=year,
            values=[str(i) for i in range(2020, 2030)],
            size_hint_x=0.34,
            font_size=sp(14),
            background_color=PRIMARY_COLOR,
            color=[1, 1, 1, 1],
        )

        spinners_row.add_widget(self.day_spinner)
        spinners_row.add_widget(self.month_spinner)
        spinners_row.add_widget(self.year_spinner)
        self.add_widget(spinners_row)

    def get_date(self):
        return f"{self.year_spinner.text}-{self.month_spinner.text}-{self.day_spinner.text}"


def modal_background(parent, radius=22):
    with parent.canvas:
        # Background image
        img = Rectangle(source="assets/purple.jpg", pos=parent.pos, size=parent.size)
        # Light overlay to show background image
        Color(0.92, 0.88, 0.98, 0.3)
        overlay = RoundedRectangle(
            pos=parent.pos, size=parent.size, radius=[dp(radius)]
        )
        # Subtle border
        Color(0.9, 0.85, 0.95, 0.6)
        border = RoundedRectangle(
            pos=(parent.x + dp(1), parent.y + dp(1)),
            size=(parent.width - dp(2), parent.height - dp(2)),
            radius=[dp(radius - 1)],
        )
    parent.bind(
        pos=lambda inst, val: [
            setattr(img, "pos", inst.pos),
            setattr(overlay, "pos", inst.pos),
            setattr(border, "pos", (inst.x + dp(1), inst.y + dp(1))),
        ],
        size=lambda inst, val: [
            setattr(img, "size", inst.size),
            setattr(overlay, "size", inst.size),
            setattr(border, "size", (inst.width - dp(2), inst.height - dp(2))),
        ],
    )


class DateRangeHoursPopup(ModalView):
    def __init__(self, compute_callback, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.7, 0.35)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.6}
        self.auto_dismiss = True
        self.background = ""
        self.background_color = (0, 0, 0, 0)
        self.overlay_color = [0, 0, 0, 0]
        self.compute_callback = compute_callback
        self._build_content()

    def _build_content(self):
        root = FloatLayout()
        modal_background(root, radius=22)

        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=[dp(20), dp(16), dp(20), dp(20)],
            size_hint=(1, None),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        layout.bind(minimum_height=layout.setter("height"))

        title = Label(
            text="[b]Hours Calculator[/b]",
            markup=True,
            font_size=sp(22),
            color=PRIMARY_COLOR,
            size_hint_y=None,
            height=dp(32),
            padding=(0, dp(12)),
        )
        layout.add_widget(title)

        input_row = BoxLayout(
            orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(50)
        )
        from_label = Label(
            text="From:",
            font_size=sp(16),
            size_hint_x=0.18,
            color=HEADER_TEXT_COLOR,
            halign="right",
            valign="middle",
        )
        self.from_input = DatePicker(size_hint_x=0.38)
        to_label = Label(
            text="To:",
            font_size=sp(16),
            size_hint_x=0.13,
            color=HEADER_TEXT_COLOR,
            halign="right",
            valign="middle",
        )
        self.to_input = DatePicker(size_hint_x=0.38)
        input_row.add_widget(from_label)
        input_row.add_widget(self.from_input)
        input_row.add_widget(to_label)
        input_row.add_widget(self.to_input)
        layout.add_widget(input_row)

        compute_btn = Button(
            text="Calculate",
            background_color=PRIMARY_COLOR,
            font_size=sp(18),
            color=[1, 1, 1, 1],
            bold=True,
            size_hint_y=None,
            height=dp(40),
            background_normal="",
            background_down="",
        )
        compute_btn.bind(on_press=self.on_compute)
        layout.add_widget(compute_btn)

        self.result_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(60),
            padding=[dp(12), dp(8), dp(12), dp(8)],
        )
        with self.result_container.canvas.before:
            Color(0.96, 0.96, 1, 1)
            self.bg_rect2 = RoundedRectangle(
                pos=self.result_container.pos,
                size=self.result_container.size,
                radius=[dp(16)],
            )
        self.result_container.bind(
            pos=lambda inst, val: setattr(self.bg_rect2, "pos", inst.pos),
            size=lambda inst, val: setattr(self.bg_rect2, "size", inst.size),
        )
        self.result_label = Label(
            text="",
            font_size=sp(18),
            color=PRIMARY_COLOR,
            bold=True,
            size_hint=(1, 1),
            halign="center",
            valign="middle",
            markup=True,
        )
        self.result_label.bind(
            size=lambda inst, val: setattr(inst, "text_size", (inst.width, inst.height))
        )
        self.result_container.add_widget(self.result_label)
        layout.add_widget(self.result_container)

        root.add_widget(layout)
        self.add_widget(root)

    def on_compute(self, instance):
        date_from = self.from_input.get_date()
        date_to = self.to_input.get_date()
        try:
            hours = self.compute_callback(date_from, date_to)
            self.result_label.text = f"Total: [b]{hours}[/b] hours"
        except Exception as e:
            self.result_label.text = (
                "[color=ff0000]Invalid input or error computing hours.[/color]"
            )


class AddEditModal(ModalView):
    def __init__(self, date_key, events, save_callback, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.85, 0.5)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.6}
        self.auto_dismiss = False
        self.background = ""
        self.background_color = (0, 0, 0, 0)
        self.overlay_color = [0, 0, 0, 0]
        self.date_key = date_key
        self.events = events
        self.save_callback = save_callback

        self.segments = []
        existing = events.get(date_key, [])
        if isinstance(existing, dict):
            self.segments = [existing]
        elif isinstance(existing, list):
            self.segments = [seg.copy() for seg in existing]
        else:
            self.segments = []

        self._setup_content()

    def _setup_content(self):
        root = FloatLayout()
        modal_background(root, radius=20)

        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=[dp(20), dp(16), dp(20), dp(20)],
            size_hint=(1, None),
            pos_hint={"center_x": 0.5, "center_y": 0.5},
        )
        layout.bind(minimum_height=layout.setter("height"))

        title_label = Label(
            text=f"[b]{self.date_key}[/b]",
            font_size=sp(22),
            color=PRIMARY_COLOR,
            size_hint_y=None,
            height=dp(32),
            halign="center",
            valign="middle",
            markup=True,
            padding=(0, dp(12)),
        )
        title_label.bind(
            size=lambda inst, val: setattr(inst, "text_size", (inst.width, inst.height))
        )
        layout.add_widget(title_label)

        self.segment_boxes = []
        self.segments_container = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            size_hint_y=None,
            padding=[dp(8), dp(8), dp(8), dp(8)],
        )
        self._refresh_segments_ui()
        layout.add_widget(self.segments_container)

        add_btn = Button(
            text="+ Add Shift",
            background_color=ACCENT_COLOR,
            font_size=sp(16),
            color=[0.22, 0.17, 0.32, 1],
            bold=True,
            background_normal="",
            background_down="",
            size_hint_y=None,
            height=dp(40),
        )
        add_btn.bind(on_press=self.add_blank_segment)
        layout.add_widget(add_btn)

        btn_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(12))
        save_btn = Button(
            text="Save",
            background_color=PRIMARY_COLOR,
            font_size=sp(16),
            color=[1, 1, 1, 1],
            bold=True,
            background_normal="",
            background_down="",
        )
        cancel_btn = Button(
            text="Cancel",
            background_color=SECONDARY_COLOR,
            font_size=sp(16),
            color=[1, 1, 1, 1],
            bold=True,
            background_normal="",
            background_down="",
        )
        save_btn.bind(on_press=self.on_save)
        cancel_btn.bind(on_press=self.dismiss)
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)

        if self.date_key in self.events:
            delete_btn = Button(
                text="Delete",
                background_color=[1, 0.2, 0.2, 1],
                font_size=sp(16),
                color=[1, 1, 1, 1],
                bold=True,
                background_normal="",
                background_down="",
            )
            delete_btn.bind(on_press=self.on_delete)
            btn_layout.add_widget(delete_btn)

        layout.add_widget(btn_layout)
        root.add_widget(layout)
        self.add_widget(root)

    def _refresh_segments_ui(self):
        self.segments_container.clear_widgets()
        self.segment_boxes = []
        for idx, segment in enumerate(self.segments):
            s_box = self._make_segment_box(idx, segment)
            self.segments_container.add_widget(s_box)
            self.segment_boxes.append(s_box)
        self.segments_container.height = dp(50) * max(len(self.segments), 1)

    def _make_segment_box(self, idx, segment):
        box = BoxLayout(
            orientation="horizontal", spacing=dp(8), size_hint_y=None, height=dp(52)
        )

        in_input = TimePicker(initial_time=segment.get("time_in", ""), size_hint_x=0.22)
        out_input = TimePicker(
            initial_time=segment.get("time_out", ""), size_hint_x=0.22
        )
        memo_input = TextInput(
            text=segment.get("memo", ""),
            hint_text="Memo",
            multiline=False,
            size_hint_x=0.45,
            font_size=sp(14),
        )
        remove_btn = Button(
            text="X",
            size_hint_x=0.11,
            font_size=sp(16),
            background_color=(
                [1, 0.7, 0.7, 1] if len(self.segments) > 1 else [0.96, 0.93, 0.99, 1]
            ),
            color=[0.7, 0.1, 0.1, 1],
            background_normal="",
            background_down="",
            disabled=len(self.segments) <= 1,
        )
        remove_btn.bind(on_press=lambda inst, i=idx: self.remove_segment(i))

        box.add_widget(in_input)
        box.add_widget(out_input)
        box.add_widget(memo_input)
        box.add_widget(remove_btn)
        box.in_input = in_input
        box.out_input = out_input
        box.memo_input = memo_input
        return box

    def add_blank_segment(self, instance):
        self.segments.append({"time_in": "", "time_out": "", "memo": ""})
        self._refresh_segments_ui()

    def remove_segment(self, idx):
        if len(self.segments) > 1:
            self.segments.pop(idx)
            self._refresh_segments_ui()

    def on_save(self, instance):
        new_segments = []
        for s_box in self.segment_boxes:
            t_in = s_box.in_input.get_time()
            t_out = s_box.out_input.get_time()
            memo = s_box.memo_input.text.strip()
            if not t_in and not t_out and not memo:
                continue
            new_segments.append({"time_in": t_in, "time_out": t_out, "memo": memo})
        if new_segments:
            self.events[self.date_key] = new_segments
        elif self.date_key in self.events:
            del self.events[self.date_key]
        self.save_callback()
        self.dismiss()

    def on_delete(self, instance):
        if self.date_key in self.events:
            del self.events[self.date_key]
            self.save_callback()
        self.dismiss()


class AllEventsPopup(ModalView):
    def __init__(self, events, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.99, 0.99)
        self.auto_dismiss = True
        self.background = ""
        self.background_color = (0, 0, 0, 0)
        self.overlay_color = [0, 0, 0, 0]
        self._setup_content(events)

    def _setup_content(self, events):
        root = FloatLayout()
        modal_background(root, radius=14)

        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=[dp(16), dp(12), dp(16), dp(16)],
            size_hint=(1, 1),
            pos_hint={"x": 0, "y": 0},
        )

        title_label = Label(
            text="[b]Events For This Month[/b]",
            font_size=sp(20),
            color=PRIMARY_COLOR,
            bold=True,
            size_hint_y=None,
            height=dp(36),
            halign="center",
            valign="middle",
            markup=True,
            padding=sp(12),
        )
        title_label.bind(
            size=lambda inst, val: setattr(inst, "text_size", (inst.width, inst.height))
        )
        layout.add_widget(title_label)

        scroll = ScrollView()
        box = BoxLayout(
            orientation="vertical", spacing=dp(12), size_hint_y=None, padding=(dp(8), dp(8))
        )
        box.bind(minimum_height=box.setter("height"))

        card_height = dp(90)
        card_font = sp(16)
        max_card_width = dp(600)

        if not events or len(events) == 0:
            card = BoxLayout(
                orientation="vertical",
                size_hint_y=None,
                height=card_height,
                padding=dp(8),
            )
            lbl = Label(
                text="No events logged for this month.",
                font_size=card_font,
                color=HEADER_TEXT_COLOR,
                halign="left",
                valign="middle",
                text_size=(max_card_width, card_height - dp(20)),
                shorten=True,
                shorten_from="right",
            )
            card.add_widget(lbl)
            box.add_widget(card)
        else:

            def date_key_fn(ds):
                try:
                    return datetime.strptime(ds, "%Y-%m-%d")
                except Exception:
                    return datetime(1900, 1, 1)

            sorted_dates = sorted(events.keys(), key=date_key_fn)
            for date_str in sorted_dates:
                segments = events[date_str]
                if isinstance(segments, dict):
                    segments = [segments]
                card = BoxLayout(
                    orientation="vertical",
                    size_hint_y=None,
                    height=max(card_height, dp(36) * len(segments) + dp(40)),
                    padding=dp(16),
                    spacing=dp(6),
                )
                with card.canvas.before:
                    Color(0.62, 0.49, 0.93, 1)
                    card.bg_rect = RoundedRectangle(
                        pos=card.pos, size=card.size, radius=[dp(20)]
                    )
                    Color(0, 0, 0, 0.10)
                    card.shadow_rect = RoundedRectangle(
                        pos=(card.x + dp(2), card.y - dp(2)),
                        size=(card.width, card.height),
                        radius=[dp(20)],
                    )

                def update_card_rects(inst, val):
                    inst.bg_rect.pos = inst.pos
                    inst.bg_rect.size = inst.size
                    inst.shadow_rect.pos = (inst.x + dp(2), inst.y - dp(2))
                    inst.shadow_rect.size = (inst.width, inst.height)

                card.bind(pos=update_card_rects, size=update_card_rects)

                date_lbl = Label(
                    text=f"[b]Date:[/b] {date_str}",
                    markup=True,
                    font_size=sp(16),
                    color=HEADER_TEXT_COLOR,
                    size_hint_y=None,
                    height=dp(24),
                    halign="left",
                    valign="middle",
                )
                date_lbl.bind(
                    size=lambda inst, val: setattr(
                        inst, "text_size", (inst.width, inst.height)
                    )
                )
                card.add_widget(date_lbl)
                for idx, segment in enumerate(segments):
                    work = work_time_string(segment)
                    shift_lbl = Label(
                        text=(
                            f"[b]Shift {idx+1}:[/b] {work}"
                            if work
                            else f"[b]Shift {idx+1}:[/b] -"
                        ),
                        markup=True,
                        font_size=sp(15),
                        color=HEADER_TEXT_COLOR,
                        size_hint_y=None,
                        height=dp(20),
                        halign="left",
                        valign="middle",
                    )
                    shift_lbl.bind(
                        size=lambda inst, val: setattr(
                            inst, "text_size", (inst.width, inst.height)
                        )
                    )
                    card.add_widget(shift_lbl)
                    memo = segment.get("memo", "")
                    if memo:
                        memo_lbl = Label(
                            text=f"[b]Memo:[/b] {memo}",
                            markup=True,
                            font_size=sp(14),
                            color=HEADER_TEXT_COLOR,
                            size_hint_y=None,
                            height=dp(20),
                            halign="left",
                            valign="middle",
                        )
                        memo_lbl.bind(
                            size=lambda inst, val: setattr(
                                inst, "text_size", (inst.width, inst.height)
                            )
                        )
                        card.add_widget(memo_lbl)
                box.add_widget(card)

        scroll.add_widget(box)
        layout.add_widget(scroll)
        close_btn = Button(
            text="Close",
            size_hint_y=None,
            height=dp(44),
            background_color=SECONDARY_COLOR,
            color=[1, 1, 1, 1],
            font_size=sp(16),
            bold=True,
            background_normal="",
            background_down="",
            on_press=self.dismiss,
        )
        layout.add_widget(close_btn)
        root.add_widget(layout)
        self.add_widget(root)


class EventsApp(App):
    def build(self):
        self.icon = 'assets/app_icon.png'
        Window.clearcolor = (1, 1, 1, 1)
        self.events = self._load_events()
        self.root_layout = BoxLayout(
            orientation="vertical",
            spacing=dp(5),
            padding=[dp(16), dp(12), dp(16), dp(12)],
        )
        with self.root_layout.canvas.before:
            self.bg_image = Rectangle(
                source="assets/purple.jpg",
                pos=self.root_layout.pos,
                size=self.root_layout.size,
            )
        self.root_layout.bind(
            pos=lambda inst, val: setattr(self.bg_image, "pos", inst.pos),
            size=lambda inst, val: setattr(self.bg_image, "size", inst.size),
        )
        self._add_header()
        self._add_calendar()
        self._add_summary_and_view()
        return self.root_layout

    def _load_events(self):
        if os.path.exists(EVENT_FILE):
            with open(EVENT_FILE, "r") as f:
                data = json.load(f)
                for k, v in list(data.items()):
                    if isinstance(v, dict):
                        data[k] = [v]
                return data
        return {}

    def _add_header(self):
        header = Label(
            text="Lenggy's App",
            font_size=TITLE_FONT_SIZE,
            size_hint_y=None,
            height=dp(60),
            color=PRIMARY_COLOR,
            bold=True,
            markup=True,
        )
        self.root_layout.add_widget(header)

    def _add_calendar(self):
        self.calendar = CalendarWidget(self.events, self.open_popup_for_date)
        self.calendar.size_hint_y = 0.78
        self.root_layout.add_widget(self.calendar)

    def _add_summary_and_view(self):
        container = BoxLayout(
            orientation="horizontal", size_hint_y=None, height=dp(120), spacing=dp(0)
        )
        label_box = BoxLayout(
            orientation="vertical",
            size_hint_x=0.7,
            size_hint_y=1,
            padding=(dp(10), 0, dp(10), 0),
        )
        self.summary_label = Label(
            text=self.get_summary_text(),
            markup=True,
            font_size=LABEL_FONT_SIZE,
            color=HEADER_TEXT_COLOR,
            halign="left",
            valign="top",
            text_size=(0, None),
            size_hint_y=1,
            shorten=False,
        )
        self.summary_label.bind(
            size=lambda inst, val: setattr(inst, "text_size", (inst.width, inst.height))
        )
        label_box.add_widget(self.summary_label)

        button_box = BoxLayout(
            orientation="horizontal",
            size_hint_x=0.3,
            spacing=dp(16),
            padding=(0, 0, dp(16), 0),
        )
        view_btn = RoundedIconButton(
            icon_path="assets/notes.png",
            bg_color=(0.56, 0.27, 0.68, 1),
            radius=18,
            size_hint=(None, None),
            size=(64, 64),
            padding=10,
        )
        view_btn.bind(on_press=self.open_all_events)
        compute_btn = RoundedIconButton(
            icon_path="assets/time.png",
            bg_color=(0.56, 0.27, 0.68, 1),
            radius=18,
            size_hint=(None, None),
            size=(64, 64),
            padding=10,
        )
        compute_btn.bind(on_press=lambda inst: self.open_compute_hours_popup())
        button_box.add_widget(view_btn)
        button_box.add_widget(compute_btn)
        container.add_widget(label_box)
        container.add_widget(button_box)
        self.root_layout.add_widget(container)

    def get_summary_text(self):
        today = datetime.today().strftime("%Y-%m-%d")
        event_segments = self.events.get(today)
        if not event_segments:
            return "[b]Date:[/b] Today\n[i]No event logged.[/i]"
        if isinstance(event_segments, dict):
            event_segments = [event_segments]
        summary_lines = [f"[b]Date:[/b] Today"]
        for idx, segment in enumerate(event_segments):
            shift_label = f"Shift {idx+1}"
            tin = format_time(segment.get("time_in", ""))
            tout = format_time(segment.get("time_out", ""))
            if tin or tout:
                summary_lines.append(f"[b]{shift_label}:[/b] {tin} - {tout}")
            memo = segment.get("memo", "")
            if memo:
                summary_lines.append(f"[b]Memo:[/b] {memo}")
        return "\n".join(summary_lines)

    def open_popup_for_date(self, date_key):
        modal = AddEditModal(date_key, self.events, self.save_events)
        modal.open()

    def open_all_events(self, instance):
        year = self.calendar.current_year
        month = self.calendar.current_month
        filtered = {}
        for date_str, ev in self.events.items():
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if dt.year == year and dt.month == month:
                filtered[date_str] = ev
        modal = AllEventsPopup(filtered)
        modal.open()

    def save_events(self):
        with open(EVENT_FILE, "w") as f:
            json.dump(self.events, f, indent=2)
        self.summary_label.text = self.get_summary_text()
        self.calendar.events = self.events
        self.calendar.update_calendar(
            self.calendar.current_year, self.calendar.current_month
        )

    def compute_total_work_hours(self, date_from, date_to):
        start = datetime.strptime(date_from, "%Y-%m-%d").date()
        end = datetime.strptime(date_to, "%Y-%m-%d").date()
        total = timedelta()
        for date_str, ev in self.events.items():
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
            except Exception:
                continue
            if start <= d <= end:
                segments = ev if isinstance(ev, list) else [ev]
                for segment in segments:
                    tin = segment.get("time_in", "")
                    tout = segment.get("time_out", "")
                    if tin and tout:
                        try:
                            t_in = datetime.strptime(tin, "%H:%M")
                            t_out = datetime.strptime(tout, "%H:%M")
                            if t_out < t_in:
                                t_out += timedelta(days=1)
                            total += t_out - t_in
                        except Exception:
                            continue
        total_hours = total.total_seconds() / 3600.0
        return round(total_hours, 2)

    def open_compute_hours_popup(self):
        popup = DateRangeHoursPopup(self.compute_total_work_hours)
        popup.open()


if __name__ == "__main__":
    EventsApp().run()
