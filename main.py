try:
    from kivy_config_helper import config_kivy
    APP_WINDOW_WIDTH, APP_WINDOW_HEIGHT, DEVICE_DENSITY = config_kivy(
        window_width=1200,
        window_height=760,
        simulate_device=False,
    )
except Exception:
    APP_WINDOW_WIDTH, APP_WINDOW_HEIGHT, DEVICE_DENSITY = 1200, 760, 1.0

import math
import os
import re
from bisect import bisect_left

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.gesture import Gesture, GestureDatabase
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty,
    DictProperty,
    ListProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout

try:
    import freetype
except Exception:
    freetype = None

try:
    import uharfbuzz  # noqa: F401
except Exception:
    uharfbuzz = None

KV = r'''
#:import dp kivy.metrics.dp

<RoundedPanel@BoxLayout>:
    canvas.before:
        Color:
            rgba: 0.12, 0.12, 0.15, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(16)]

<ReaderCanvas>:
    canvas.before:
        Color:
            rgba: 0.07, 0.07, 0.09, 1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(18)]
        Color:
            rgba: 0.23, 0.23, 0.28, 1
        Line:
            rounded_rectangle: (self.x, self.y, self.width, self.height, dp(18))
            width: dp(1.2)
        Color:
            rgba: 0.36, 0.36, 0.42, 0.65
        Rectangle:
            pos: self.x + dp(30), self.baseline_y - dp(1)
            size: max(0, self.width - dp(60)), dp(2)
        Color:
            rgba: 0.88, 0.25, 0.25, 0.95
        Line:
            points: self.center_x, self.baseline_y + dp(16), self.center_x, self.baseline_y + dp(38)
            width: dp(1.6)
        Line:
            points: self.center_x, self.baseline_y - dp(16), self.center_x, self.baseline_y - dp(38)
            width: dp(1.6)

<GestureOverlay>:
    canvas.after:
        Color:
            rgba: 0.72, 0.72, 0.8, 0.28
        Line:
            points: self._flat_points
            width: dp(2.5)
            cap: 'round'
            joint: 'round'

<SettingsPopup>:
    title: 'RSVP Settings'
    title_align: 'center'
    separator_height: dp(1)
    size_hint: None, None
    size: dp(500), dp(500)
    auto_dismiss: True
    BoxLayout:
        orientation: 'vertical'
        spacing: dp(14)
        padding: dp(20)
        canvas.before:
            Color:
                rgba: 0.11, 0.11, 0.14, 1
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [dp(16)]

        Label:
            text: 'Playback and display settings'
            font_size: dp(22)
            size_hint_y: None
            height: dp(34)
            bold: True
            halign: 'left'
            valign: 'middle'
            text_size: self.size

        GridLayout:
            cols: 1
            size_hint_y: 1
            spacing: dp(10)
            row_force_default: True
            row_default_height: dp(58)

            BoxLayout:
                orientation: 'vertical'
                spacing: dp(4)
                Label:
                    text: 'Font'
                    size_hint_y: None
                    height: dp(18)
                    halign: 'left'
                    valign: 'middle'
                    text_size: self.size
                Spinner:
                    id: font_spinner
                    text: root.font_value
                    values: root.font_options
                    size_hint_y: None
                    height: dp(36)

            BoxLayout:
                orientation: 'vertical'
                spacing: dp(4)
                Label:
                    text: 'Font size'
                    size_hint_y: None
                    height: dp(18)
                    halign: 'left'
                    valign: 'middle'
                    text_size: self.size
                Spinner:
                    id: size_spinner
                    text: root.size_value
                    values: root.size_options
                    size_hint_y: None
                    height: dp(36)

            BoxLayout:
                orientation: 'vertical'
                spacing: dp(4)
                Label:
                    text: 'Words per minute'
                    size_hint_y: None
                    height: dp(18)
                    halign: 'left'
                    valign: 'middle'
                    text_size: self.size
                Spinner:
                    id: wpm_spinner
                    text: root.wpm_value
                    values: root.wpm_options
                    size_hint_y: None
                    height: dp(36)

        BoxLayout:
            size_hint_y: None
            height: dp(46)
            spacing: dp(10)
            Button:
                text: 'Cancel'
                on_release: root.dismiss()
            Button:
                text: 'Apply'
                on_release: root.apply_and_close()

<MainRoot>:
    orientation: 'vertical'
    spacing: dp(12)
    padding: dp(12)
    canvas.before:
        Color:
            rgba: 0.08, 0.085, 0.1, 1
        Rectangle:
            pos: self.pos
            size: self.size

    RoundedPanel:
        orientation: 'horizontal'
        size_hint_y: None
        height: dp(82)
        padding: dp(14)
        spacing: dp(10)

        Button:
            id: file_button
            text: root.file_button_text
            size_hint_x: 0.44
            on_release: root.open_file_chooser()

        ToggleButton:
            id: play_pause
            text: root.play_button_text
            disabled: not root.file_loaded
            size_hint_x: 0.20
            on_release: root.on_play_pause_pressed(self)

        Button:
            id: restart_button
            text: 'Restart'
            disabled: not root.file_loaded
            size_hint_x: 0.16
            on_release: root.restart_playback()

        Button:
            text: 'Settings'
            size_hint_x: 0.20
            on_release: root.open_settings()

    RoundedPanel:
        orientation: 'vertical'
        padding: dp(16)
        spacing: dp(10)

        BoxLayout:
            size_hint_y: None
            height: dp(26)
            spacing: dp(10)
            Label:
                text: root.status_text
                halign: 'left'
                valign: 'middle'
                text_size: self.size
            Label:
                text: root.meta_text
                halign: 'right'
                valign: 'middle'
                text_size: self.size

        BoxLayout:
            orientation: 'vertical'
            ReaderCanvas:
                id: reader_canvas
                size_hint_y: 1
                overlay: gesture_overlay

                Label:
                    Label:
                        id: word_label
                        text: root.marked_up_word
                        markup: True
                        font_name: root.current_font_path
                        font_size: root.current_font_size_px
                        size_hint: None, None
                        text_size: None, None
                        size: self.texture_size
                        x: reader_canvas.word_x
                        y: reader_canvas.baseline_y - self.texture_size[1] / 2 + reader_canvas.word_center_y_offset
                        color: 0.97, 0.97, 0.98, 1

                GestureOverlay:
                    id: gesture_overlay
                    root_widget: root
                    size: self.parent.size
                    pos: self.parent.pos

        BoxLayout:
            size_hint_y: None
            height: dp(54)
            spacing: dp(10)

            Label:
                text: 'Keys: Left = back,  Right = forward,  Up = faster,  Down = slower,  spacebar = pause,  + = bigger,  - = smaller'
                halign: 'left'
                valign: 'middle'
                text_size: self.size

<FileChooserPopup>:
    title: 'Choose a text file'
    size_hint: 0.92, 0.92
    BoxLayout:
        orientation: 'vertical'
        spacing: dp(8)
        padding: dp(10)
        FileChooserListView:
            id: chooser
            path: root.start_path
            filters: ['*.txt']
            multiselect: False
        BoxLayout:
            size_hint_y: None
            height: dp(48)
            spacing: dp(8)
            Button:
                text: 'Cancel'
                on_release: root.dismiss()
            Button:
                text: 'Load File'
                on_release: root.load_selected()
'''


def euclidean_distance(p1, p2):
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)


def better_unistroke_normalizer(pts, total_pts=32):
    if len(pts) < 2:
        raise ValueError("At least two distinct points are required.")
    total_length = sum(euclidean_distance(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    if total_length == 0:
        raise ValueError("Total length of stroke is zero.")
    segment_length = total_length / (total_pts - 1)
    new_pts = [pts[0]]
    accumulated_dist = 0.0
    for i in range(1, len(pts)):
        p1, p2 = pts[i - 1], pts[i]
        dist = euclidean_distance(p1, p2)
        if dist == 0:
            continue
        while accumulated_dist + dist >= segment_length and len(new_pts) < total_pts - 1:
            t = (segment_length - accumulated_dist) / dist
            new_x = p1[0] + t * (p2[0] - p1[0])
            new_y = p1[1] + t * (p2[1] - p1[1])
            new_pt = (new_x, new_y)
            new_pts.append(new_pt)
            accumulated_dist = 0.0
            p1 = new_pt
            dist = euclidean_distance(p1, p2)
        accumulated_dist += dist
    while len(new_pts) < total_pts - 1:
        new_pts.append(new_pts[-1])
    new_pts.append(pts[-1])
    return new_pts[:total_pts]


class SimpleTextMetrics:
    def __init__(self, font_name, font_size):
        self.font_name = font_name
        self.font_size = max(1, int(round(font_size)))
        self.face = None
        if freetype and font_name and os.path.exists(font_name):
            try:
                self.face = freetype.Face(font_name)
                self.face.set_char_size(self.font_size * 64)
            except Exception:
                self.face = None

    def _measure_with_corelabel(self, text):
        lbl = CoreLabel(text=text or ' ', font_name=self.font_name, font_size=self.font_size)
        lbl.refresh()
        return lbl.texture.size

    def text_size(self, text):
        if not text:
            return 0.0, float(self.font_size)
        if self.face:
            width = 0.0
            for ch in text:
                try:
                    self.face.load_char(ch)
                    width += self.face.glyph.advance.x / 64.0
                except Exception:
                    pass
            _, h = self._measure_with_corelabel(text)
            return width, h
        return self._measure_with_corelabel(text)

    def char_width(self, ch):
        return self.text_size(ch)[0]


class ReaderCanvas(FloatLayout):
    baseline_y = NumericProperty(0)
    word_x = NumericProperty(0)
    word_center_y_offset = NumericProperty(0)
    overlay = ObjectProperty(None)

    def on_size(self, *args):
        self._update_geometry()

    def on_pos(self, *args):
        self._update_geometry()

    def _update_geometry(self):
        self.baseline_y = self.y + self.height * 0.48
        self.word_center_y_offset = dp(8)
        app = App.get_running_app()
        if app and app.root:
            Clock.schedule_once(lambda dt: app.root.refresh_word_layout(), 0)


class GestureOverlay(Widget):
    root_widget = ObjectProperty(None)
    _points = ListProperty([])
    _flat_points = ListProperty([])

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        touch.grab(self)
        self._points = [touch.pos]
        self._flat_points = [touch.x, touch.y]
        return True

    def on_touch_move(self, touch):
        if touch.grab_current is not self:
            return False
        self._points.append(touch.pos)
        flat = []
        for x, y in self._points:
            flat.extend([x, y])
        self._flat_points = flat
        return True

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return False
        touch.ungrab(self)
        if len(self._points) >= 6 and self.root_widget:
            self.root_widget.handle_gesture(self._points)
        self._points = []
        self._flat_points = []
        return True


class SettingsPopup(Popup):
    root_widget = ObjectProperty(None)
    font_options = ListProperty([])
    size_options = ListProperty([])
    wpm_options = ListProperty([])
    font_value = StringProperty('')
    size_value = StringProperty('')
    wpm_value = StringProperty('')

    def apply_and_close(self):
        if self.root_widget:
            self.root_widget.apply_settings(
                self.ids.font_spinner.text,
                self.ids.size_spinner.text,
                self.ids.wpm_spinner.text,
            )
        self.dismiss()


class FileChooserPopup(Popup):
    root_widget = ObjectProperty(None)
    start_path = StringProperty(os.getcwd())

    def load_selected(self):
        selection = self.ids.chooser.selection
        if selection and self.root_widget:
            self.root_widget.load_transcript(selection[0])
            self.dismiss()


class MainRoot(BoxLayout):
    file_button_text = StringProperty('Choose Text File')
    play_button_text = StringProperty('Play')
    status_text = StringProperty('Load a .txt transcript to begin.')
    meta_text = StringProperty('')
    marked_up_word = StringProperty('[color=#ffffff]Ready[/color]')
    current_font_path = StringProperty('Roboto')
    current_font_size_px = NumericProperty(dp(52))
    file_loaded = BooleanProperty(False)
    is_playing = BooleanProperty(False)
    chosen_file = StringProperty('')
    font_map = DictProperty({})
    font_order = ListProperty([])
    transcript = ListProperty([])
    word_index = NumericProperty(0)
    elapsed_units = ListProperty([])
    total_units = NumericProperty(0.0)
    current_wpm = NumericProperty(300)
    jump_seconds = NumericProperty(3.0)
    min_wpm = NumericProperty(100)
    max_wpm = NumericProperty(800)
    scheduled_event = ObjectProperty(None, allownone=True)
    current_elapsed_unit = NumericProperty(0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ignore_toggle_callback = False
        self.size_presets = ['36', '44', '52', '60', '72']
        self.wpm_presets = ['200', '250', '300', '350', '400', '500']
        self.font_map, self.font_order = self.discover_fonts()
        default_font = 'OpenDyslexic' if 'OpenDyslexic' in self.font_map else self.font_order[0]
        self.selected_font_label = default_font
        self.selected_font_path = self.font_map[default_font]
        self.current_font_path = self.selected_font_path
        self.current_font_size_px = dp(52)
        self.current_wpm = 300
        self.gdb = GestureDatabase()
        self._build_gesture_database()
        Window.bind(on_key_down=self.on_key_down)
        Clock.schedule_once(lambda dt: self.refresh_word_layout(), 0)

    def discover_fonts(self):
        candidates = [
            os.getcwd(),
            os.path.join(os.getcwd(), 'fonts'),
            os.path.dirname(os.path.abspath(__file__)),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fonts'),
        ]
        font_map = {'Roboto': 'Roboto'}
        checks = {
            'OpenDyslexic': [
                'OpenDyslexic-Regular.otf',
                'OpenDyslexic-Regular.ttf',
                'OpenDyslexic.otf',
                'OpenDyslexic.ttf',
            ],
            'APHont': [
                'APHont-Regular.ttf',
                'APHont-Regular.otf',
                'APHont.ttf',
                'APHont.otf',
            ],
        }
        for label, names in checks.items():
            for base in candidates:
                for name in names:
                    path = os.path.join(base, name)
                    if os.path.exists(path):
                        font_map[label] = path
                        break
                if label in font_map:
                    break
        order = []
        for label in ['OpenDyslexic', 'APHont', 'Roboto']:
            if label in font_map:
                order.append(label)
        for key in font_map:
            if key not in order:
                order.append(key)
        return font_map, order

    def open_file_chooser(self):
        popup = FileChooserPopup(root_widget=self, start_path=os.getcwd())
        popup.open()

    def open_settings(self):
        popup = SettingsPopup(
            root_widget=self,
            font_options=self.font_order,
            size_options=self.size_presets,
            wpm_options=self.wpm_presets,
            font_value=self.selected_font_label,
            size_value=str(int(round(self.current_font_size_px / dp(1)))),
            wpm_value=str(int(self.current_wpm)),
        )
        popup.open()

    def apply_settings(self, font_label, size_value, wpm_value):
        self.selected_font_label = font_label
        self.selected_font_path = self.font_map.get(font_label, 'Roboto')
        self.current_font_path = self.selected_font_path
        self.current_font_size_px = dp(int(size_value))
        self.current_wpm = int(wpm_value)
        self.refresh_word_layout()
        if self.file_loaded:
            self.update_meta_text()
            self.status_text = f'Settings updated. Font: {self.selected_font_label}, size: {int(size_value)}, WPM: {int(wpm_value)}.'
        if self.is_playing:
            self.reschedule_from_current_word()

    def load_transcript(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                raw = f.read()
        except UnicodeDecodeError:
            with open(filepath, 'r', encoding='latin-1') as f:
                raw = f.read()
        tokens = self.parse_plain_text(raw)
        if not tokens:
            self.status_text = 'The selected file did not contain readable words.'
            return
        self.transcript = tokens
        self.elapsed_units = self.build_elapsed_units(tokens)
        self.total_units = self.elapsed_units[-1] + tokens[-1]['units']
        self.word_index = 0
        self.current_elapsed_unit = 0.0
        self.file_loaded = True
        self.chosen_file = filepath
        short_name = os.path.basename(filepath)
        self.file_button_text = short_name
        self.play_button_text = 'Play'
        self.is_playing = False
        self._set_toggle_state('normal')
        self.cancel_scheduled_event()
        self.update_current_word_display()
        self.update_meta_text()
        self.status_text = f'Loaded {short_name}. Draw a gesture over the reader or use the keyboard controls.'

    def parse_plain_text(self, raw_text):
        normalized = raw_text.replace('\r\n', ' ').replace('\n', ' ')
        parts = re.findall(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*|[.,!?;:]", normalized)
        tokens = []
        for item in parts:
            if re.search(r'[A-Za-z0-9]', item):
                tokens.append({'word': item, 'units': self.word_units(item)})
            elif tokens:
                tokens[-1]['word'] += item
                tokens[-1]['units'] += self.punctuation_bonus(item)
        return tokens

    def punctuation_bonus(self, punctuation):
        if punctuation in '.!?':
            return 0.55
        if punctuation in ',;:':
            return 0.25
        return 0.0

    def word_units(self, word):
        core = re.sub(r"[^A-Za-z0-9]", '', word)
        length = max(1, len(core))
        if length <= 3:
            units = 0.82
        elif length <= 5:
            units = 1.0
        elif length <= 8:
            units = 1.16
        elif length <= 11:
            units = 1.32
        else:
            units = 1.52
        vowel_groups = re.findall(r'[aeiouyAEIOUY]+', core)
        units += max(0, len(vowel_groups) - 1) * 0.03
        return units

    def build_elapsed_units(self, tokens):
        elapsed = []
        running = 0.0
        for token in tokens:
            elapsed.append(running)
            running += token['units']
        return elapsed

    def base_seconds_per_unit(self):
        return 60.0 / max(1.0, self.current_wpm)

    def current_word_duration(self):
        if not self.transcript:
            return 0.0
        units = self.transcript[self.word_index]['units']
        return units * self.base_seconds_per_unit()

    def focus_index(self, word):
        core = re.sub(r'[^A-Za-z0-9]', '', word)
        if not core:
            return 0
        n = len(core)
        if n == 1:
            return 0
        if n <= 5:
            return 1
        if n <= 9:
            return 2
        if n <= 13:
            return 3
        return 4

    def split_for_focus(self, word):
        match = re.search(r'[A-Za-z0-9]', word)
        if not match:
            return '', word[:1], word[1:]
        letters = [i for i, ch in enumerate(word) if re.match(r'[A-Za-z0-9]', ch)]
        target_letter_pos = min(self.focus_index(word), len(letters) - 1)
        target_idx = letters[target_letter_pos]
        return word[:target_idx], word[target_idx], word[target_idx + 1:]

    def escape_markup(self, text):
        return text.replace('&', '&amp;').replace('[', '&bl;').replace(']', '&br;')

    def update_current_word_display(self):
        if not self.transcript:
            self.marked_up_word = '[color=#ffffff]Ready[/color]'
            return
        word = self.transcript[self.word_index]['word']
        left, focus, right = self.split_for_focus(word)
        self.marked_up_word = (
            f"[color=#f5f5f8]{self.escape_markup(left)}[/color]"
            f"[color=#ff4d4d]{self.escape_markup(focus)}[/color]"
            f"[color=#f5f5f8]{self.escape_markup(right)}[/color]"
        )
        self.refresh_word_layout()
        position = self.word_index + 1
        total = len(self.transcript)
        mode = 'Playing' if self.is_playing else 'Paused'
        self.meta_text = f'{mode}  |  {position}/{total} words  |  {int(self.current_wpm)} WPM  |  {self.selected_font_label}'

    def refresh_word_layout(self):
        if not self.ids or 'reader_canvas' not in self.ids or 'word_label' not in self.ids:
            return
        canvas = self.ids.reader_canvas
        label = self.ids.word_label
        if self.transcript:
            word = self.transcript[self.word_index]['word']
        else:
            word = 'Ready'
        left, focus, right = self.split_for_focus(word)
        metrics = SimpleTextMetrics(self.current_font_path, self.current_font_size_px)
        left_w, _ = metrics.text_size(left)
        focus_w, _ = metrics.text_size(focus)
        label.texture_update()
        label.size = label.texture_size
        anchor_x = canvas.center_x
        desired_left_x = anchor_x - left_w - (focus_w / 2.0)
        canvas.word_x = desired_left_x

    def update_meta_text(self):
        if not self.transcript:
            self.meta_text = ''
            return
        mode = 'Playing' if self.is_playing else 'Paused'
        self.meta_text = (
            f'{mode}  |  {self.word_index + 1}/{len(self.transcript)} words  |  '
            f'{int(self.current_wpm)} WPM  |  {self.selected_font_label}'
        )

    def on_play_pause_pressed(self, toggle):
        if self._ignore_toggle_callback:
            return
        if toggle.state == 'down':
            self.start_playback()
        else:
            self.pause_playback(manual=True)

    def _set_toggle_state(self, state):
        self._ignore_toggle_callback = True
        self.ids.play_pause.state = state
        self._ignore_toggle_callback = False

    def start_playback(self):
        if not self.file_loaded:
            self._set_toggle_state('normal')
            return
        if self.word_index >= len(self.transcript):
            self.word_index = 0
            self.current_elapsed_unit = 0.0
        self.is_playing = True
        self.play_button_text = 'Pause'
        self._set_toggle_state('down')
        self.status_text = 'Playback started. Draw a gesture in the reading panel or use the keyboard.'
        self.update_current_word_display()
        self.reschedule_from_current_word()

    def pause_playback(self, manual=False):
        self.is_playing = False
        self.play_button_text = 'Play'
        self._set_toggle_state('normal')
        self.cancel_scheduled_event()
        self.update_current_word_display()
        if manual and self.file_loaded:
            self.status_text = 'Playback paused.'

    def restart_playback(self):
        if not self.file_loaded:
            return
        self.word_index = 0
        self.current_elapsed_unit = 0.0
        self.update_current_word_display()
        self.status_text = 'Playback restarted from the beginning.'
        if self.is_playing:
            self.reschedule_from_current_word()

    def cancel_scheduled_event(self):
        if self.scheduled_event is not None:
            try:
                self.scheduled_event.cancel()
            except Exception:
                pass
            self.scheduled_event = None

    def reschedule_from_current_word(self):
        self.cancel_scheduled_event()
        if self.is_playing and self.file_loaded:
            self.scheduled_event = Clock.schedule_once(self.advance_word, self.current_word_duration())

    def advance_word(self, dt):
        self.scheduled_event = None
        if not self.is_playing or not self.file_loaded:
            return
        if self.word_index < len(self.transcript) - 1:
            self.word_index += 1
            self.current_elapsed_unit = self.elapsed_units[self.word_index]
            self.update_current_word_display()
            self.reschedule_from_current_word()
        else:
            self.word_index = len(self.transcript) - 1
            self.current_elapsed_unit = self.elapsed_units[self.word_index]
            self.update_current_word_display()
            self.pause_playback(manual=False)
            self.status_text = 'Playback complete.'

    def jump_by_seconds(self, delta_seconds):
        if not self.file_loaded:
            return
        unit_delta = delta_seconds / self.base_seconds_per_unit()
        target_unit = min(max(0.0, self.elapsed_units[self.word_index] + unit_delta), self.total_units)
        new_index = bisect_left(self.elapsed_units, target_unit)
        new_index = min(max(0, new_index), len(self.transcript) - 1)
        self.word_index = new_index
        self.current_elapsed_unit = self.elapsed_units[self.word_index]
        self.update_current_word_display()
        direction = 'forward' if delta_seconds > 0 else 'back'
        self.status_text = f'Jumped {direction} {abs(int(delta_seconds))} seconds in the playback timeline.'
        if self.is_playing:
            self.reschedule_from_current_word()

    def adjust_wpm(self, delta):
        new_wpm = min(self.max_wpm, max(self.min_wpm, int(self.current_wpm + delta)))
        if new_wpm == self.current_wpm:
            return
        self.current_wpm = new_wpm
        self.update_current_word_display()
        self.status_text = f'Playback speed set to {int(self.current_wpm)} WPM.'
        if self.is_playing:
            self.reschedule_from_current_word()

    def adjust_font_size(self, delta):
        current = int(round(self.current_font_size_px / dp(1)))
        new_size = min(96, max(24, current + delta))
        if new_size == current:
            return
        self.current_font_size_px = dp(new_size)
        self.refresh_word_layout()
        self.update_current_word_display()
        self.status_text = f'Font size set to {new_size}.'

    def toggle_pause(self):
        if not self.file_loaded:
            return
        if self.is_playing:
            self.pause_playback(manual=True)
        else:
            self.start_playback()

    def on_key_down(self, window, key, scancode, codepoint, modifiers):
        if key == 276:
            self.jump_by_seconds(-self.jump_seconds)
            return True
        if key == 275:
            self.jump_by_seconds(self.jump_seconds)
            return True
        if key == 273:
            self.adjust_wpm(25)
            return True
        if key == 274:
            self.adjust_wpm(-25)
            return True
        if key == 32:
            self.toggle_pause()
            return True
        if codepoint in ('+', '='):
            self.adjust_font_size(4)
            return True
        if codepoint == '-':
            self.adjust_font_size(-4)
            return True
        return False

    def _build_gesture_database(self):
        templates = {
            'jump_back': [(100, 50), (70, 50), (40, 50), (15, 50)],
            'jump_forward': [(15, 50), (40, 50), (70, 50), (100, 50)],
            'speed_up': [(50, 15), (50, 40), (50, 70), (50, 100)],
            'slow_down': [(50, 100), (50, 70), (50, 40), (50, 15)],
            'font_bigger': [(15, 20), (50, 85), (85, 20)],
            'font_smaller': [(15, 85), (50, 20), (85, 85)],
            'pause_toggle': [
                (50, 10), (65, 12), (78, 20), (88, 35), (90, 50),
                (88, 65), (78, 80), (65, 88), (50, 90),
                (35, 88), (22, 80), (12, 65), (10, 50),
                (12, 35), (22, 20), (35, 12), (50, 10)
            ],
        }
        for name, pts in templates.items():
            g = Gesture()
            g.add_stroke(better_unistroke_normalizer(pts, total_pts=32))
            g.normalize()
            g.name = name
            self.gdb.add_gesture(g)

    def is_circle_like(self, points):
        if len(points) < 10:
            return False
        start_x, start_y = points[0]
        end_x, end_y = points[-1]
        closure = math.sqrt((end_x - start_x) ** 2 + (end_y - start_y) ** 2)
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        width = max(xs) - min(xs)
        height = max(ys) - min(ys)
        if width < dp(30) or height < dp(30):
            return False
        aspect_ratio = width / max(height, 1)
        return closure < max(width, height) * 0.35 and 0.65 <= aspect_ratio <= 1.35

    def handle_gesture(self, points):
        if not self.file_loaded:
            self.status_text = 'Load a file first, then use gestures in the reading panel.'
            return
        local_points = [(x - self.ids.reader_canvas.x, y - self.ids.reader_canvas.y) for x, y in points]
        if self.is_circle_like(local_points):
            self.toggle_pause()
            self.status_text = 'Pause toggled via circle gesture.'
            return
        try:
            normalized = better_unistroke_normalizer(local_points, total_pts=32)
        except ValueError:
            return
        gesture = Gesture()
        gesture.add_stroke(normalized)
        gesture.normalize()
        result = self.gdb.find(gesture, minscore=0.65)
    
        if not result:
            self.status_text = 'Gesture not recognized. Try a cleaner stroke.'
            return
        name = result[1].name
        if name == 'jump_back':
            self.jump_by_seconds(-self.jump_seconds)
        elif name == 'jump_forward':
            self.jump_by_seconds(self.jump_seconds)
        elif name == 'speed_up':
            self.adjust_wpm(25)
        elif name == 'slow_down':
            self.adjust_wpm(-25)
        elif name == 'font_bigger':
            self.adjust_font_size(4)
        elif name == 'font_smaller':
            self.adjust_font_size(-4)
        elif name == 'pause_toggle':
            self.toggle_pause()


class RSVPApp(App):
    def build(self):
        self.title = 'RSVP Reader HW4'
        Builder.load_string(KV)
        Window.size = (APP_WINDOW_WIDTH, APP_WINDOW_HEIGHT)
        return MainRoot()


if __name__ == '__main__':
    RSVPApp().run()
