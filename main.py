import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyqtgraph as pg
import qtawesome as qta
from scipy.signal import find_peaks, windows
from PyQt6.QtCore import QEvent, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


pg.setConfigOptions(antialias=False)


def color_hex(color):
    return color.name(QColor.NameFormat.HexRgb)


def color_luminance(color):
    return 0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()


class AppTheme:
    def __init__(self, palette):
        self.palette = palette
        self.window = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Window)
        self.window_text = palette.color(
            QPalette.ColorGroup.Active, QPalette.ColorRole.WindowText
        )
        self.base = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Base)
        self.text = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Text)
        self.button = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Button)
        self.button_text = palette.color(
            QPalette.ColorGroup.Active, QPalette.ColorRole.ButtonText
        )
        self.highlight = palette.color(
            QPalette.ColorGroup.Active, QPalette.ColorRole.Highlight
        )
        self.highlighted_text = palette.color(
            QPalette.ColorGroup.Active, QPalette.ColorRole.HighlightedText
        )
        self.border = palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Mid)
        self.disabled_text = palette.color(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.ButtonText,
        )
        self.disabled_button = palette.color(
            QPalette.ColorGroup.Disabled,
            QPalette.ColorRole.Button,
        )

        self.is_dark = color_luminance(self.window) < 128
        self.separator = (
            self.window.lighter(140) if self.is_dark else self.window.darker(130)
        )
        self.accent_hover = self.highlight.lighter(112) if self.is_dark else self.highlight.darker(108)
        self.accent_pressed = self.highlight.darker(112)
        self.accent_text = QColor("#ffffff") if color_luminance(self.highlight) < 150 else QColor("#111111")
        self.panel_surface = (
            self.window.darker(108) if self.is_dark else self.window.darker(104)
        )
        self.panel_text = self.window_text
        self.input_surface = self.base
        self.checkbox_border = self.border.lighter(145) if self.is_dark else self.border
        self.checkbox_check_icon = (
            Path(__file__).resolve().parent / "assets" / "checkmark_white.svg"
        ).as_posix()
        self.plot_panel = "#252525"
        self.plot_background = "#1e1e1e"
        self.plot_text = "#ffffff"
        self.plot_axis = "#777777"
        self.plot_grid_alpha = 0.22
        self.peak = "#ffff00"
        self.curve = self.visible_plot_accent()

    @classmethod
    def current(cls):
        return cls(QApplication.instance().palette())

    def visible_plot_accent(self):
        accent = QColor(self.highlight)
        for _ in range(8):
            if color_luminance(accent) >= 150:
                return color_hex(accent)
            accent = accent.lighter(125)
        return "#00bfff"

    def icon(self, name):
        return qta.icon(
            name,
            color=color_hex(self.button_text),
            color_off=color_hex(self.button_text),
            color_on=color_hex(self.accent_text),
            color_active=color_hex(self.accent_text),
            color_selected=color_hex(self.accent_text),
            color_off_active=color_hex(self.accent_text),
            color_on_active=color_hex(self.accent_text),
            color_off_selected=color_hex(self.accent_text),
            color_on_selected=color_hex(self.accent_text),
            color_disabled=color_hex(self.disabled_text),
        )

    def segmented_button_style(self, position):
        radius = {
            "first": "border-top-left-radius: 4px; border-bottom-left-radius: 4px;",
            "middle": "border-radius: 0px;",
            "last": "border-top-right-radius: 4px; border-bottom-right-radius: 4px;",
            "single": "border-radius: 4px;",
        }[position]
        right_border = "border-right: none;" if position in {"first", "middle"} else ""

        return f"""
            QPushButton {{
                color: {color_hex(self.button_text)};
                background-color: {color_hex(self.button)};
                border: 1px solid {color_hex(self.border)};
                {right_border}
                {radius}
            }}
            QPushButton:hover {{
                color: {color_hex(self.accent_text)};
                background-color: {color_hex(self.accent_hover)};
                border-color: {color_hex(self.highlight)};
            }}
            QPushButton:pressed {{
                color: {color_hex(self.accent_text)};
                background-color: {color_hex(self.accent_pressed)};
                border-color: {color_hex(self.highlight)};
            }}
            QPushButton:checked {{
                color: {color_hex(self.accent_text)};
                background-color: {color_hex(self.highlight)};
                border-color: {color_hex(self.highlight)};
            }}
            QPushButton:disabled {{
                color: {color_hex(self.disabled_text)};
                background-color: {color_hex(self.disabled_button)};
                border-color: {color_hex(self.border)};
            }}
        """

    def tool_button_style(self):
        return f"""
            QPushButton {{
                color: {color_hex(self.button_text)};
                background-color: {color_hex(self.button)};
                border: 1px solid {color_hex(self.border)};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                color: {color_hex(self.accent_text)};
                background-color: {color_hex(self.accent_hover)};
                border-color: {color_hex(self.highlight)};
            }}
            QPushButton:pressed {{
                color: {color_hex(self.accent_text)};
                background-color: {color_hex(self.accent_pressed)};
                border-color: {color_hex(self.highlight)};
            }}
            QPushButton:checked {{
                color: {color_hex(self.accent_text)};
                background-color: {color_hex(self.highlight)};
                border-color: {color_hex(self.highlight)};
            }}
            QPushButton:disabled {{
                color: {color_hex(self.disabled_text)};
                background-color: {color_hex(self.disabled_button)};
                border-color: {color_hex(self.border)};
            }}
        """

    def plot_canvas_style(self):
        return f"""
            PlotCanvas {{
                background-color: {color_hex(self.window)};
                border: 1px solid {color_hex(self.border)};
            }}
            PlotCanvas QLabel {{
                color: {color_hex(self.window_text)};
            }}
        """

    def separator_style(self):
        return f"background-color: {color_hex(self.separator)};"

    def panel_style(self):
        return f"background-color: {color_hex(self.panel_surface)};"

    def left_panel_style(self):
        return f"""
            QWidget {{
                background-color: {color_hex(self.panel_surface)};
                color: {color_hex(self.panel_text)};
            }}
            QLabel {{
                color: {color_hex(self.panel_text)};
            }}
            QCheckBox {{
                color: {color_hex(self.panel_text)};
                spacing: 6px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 1px solid {color_hex(self.checkbox_border)};
                border-radius: 3px;
                background-color: {color_hex(self.input_surface)};
            }}
            QCheckBox::indicator:checked {{
                border-color: {color_hex(self.highlight)};
                background-color: {color_hex(self.highlight)};
                image: url("{self.checkbox_check_icon}");
            }}
            QCheckBox::indicator:disabled {{
                border-color: {color_hex(self.disabled_text)};
                background-color: {color_hex(self.disabled_button)};
            }}
        """

    def top_bar_style(self):
        return f"""
            QWidget {{
                background-color: {color_hex(self.panel_surface)};
                color: {color_hex(self.panel_text)};
            }}
            QLabel {{
                color: {color_hex(self.panel_text)};
            }}
        """


class PlotCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.sampling_rate = None
        self.freqs = None
        self.fft_db = None
        self.peak_indices = np.array([], dtype=int)
        self.signal_name = None
        self.default_x_range = (0.0, 1.0)
        self.default_y_range = (-1.0, 1.0)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumWidth(0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Title bar
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(4, 4, 4, 0)

        self.title_label = QLabel("")
        title_bar.addWidget(self.title_label)
        title_bar.addStretch()

        self.expand_btn = QPushButton()
        self.expand_btn.setFixedSize(28, 24)
        self.expand_btn.setToolTip("Expand plot")
        self.expand_btn.clicked.connect(self.expand_plot)

        self.save_btn = QPushButton()
        self.save_btn.setFixedSize(28, 24)
        self.save_btn.setToolTip("Save plot as image")
        self.save_btn.clicked.connect(self.save_plot)

        title_bar.addWidget(self.expand_btn)
        title_bar.addWidget(self.save_btn)
        layout.addLayout(title_bar)

        self.plot_widget = self.create_plot_widget(sync_inputs=True)
        self.plot_item = self.plot_widget.getPlotItem()
        self.view_box = self.plot_item.getViewBox()
        layout.addWidget(self.plot_widget)
        layout.setStretchFactor(self.plot_widget, 1)

        # Axis limit inputs
        axis_bar = QHBoxLayout()
        axis_bar.setSpacing(4)

        axis_bar.addWidget(QLabel("X:"))
        self.x_min_input = QLineEdit()
        self.x_max_input = QLineEdit()
        self.x_min_input.setFixedWidth(56)
        self.x_max_input.setFixedWidth(56)
        self.x_min_input.setPlaceholderText("min")
        self.x_max_input.setPlaceholderText("max")
        self.x_min_input.returnPressed.connect(self.apply_axis_limits)
        self.x_max_input.returnPressed.connect(self.apply_axis_limits)

        axis_bar.addWidget(self.x_min_input)
        axis_bar.addWidget(QLabel("to"))
        axis_bar.addWidget(self.x_max_input)
        axis_bar.addSpacing(10)

        axis_bar.addWidget(QLabel("Y:"))
        self.y_min_input = QLineEdit()
        self.y_max_input = QLineEdit()
        self.y_min_input.setFixedWidth(56)
        self.y_max_input.setFixedWidth(56)
        self.y_min_input.setPlaceholderText("min")
        self.y_max_input.setPlaceholderText("max")
        self.y_min_input.returnPressed.connect(self.apply_axis_limits)
        self.y_max_input.returnPressed.connect(self.apply_axis_limits)

        axis_bar.addWidget(self.y_min_input)
        axis_bar.addWidget(QLabel("to"))
        axis_bar.addWidget(self.y_max_input)

        self.reset_btn = QPushButton()
        self.reset_btn.setFixedSize(28, 24)
        self.reset_btn.setToolTip("Reset axis limits")
        self.reset_btn.clicked.connect(self.reset_axis_limits)
        axis_bar.addWidget(self.reset_btn)
        axis_bar.addStretch()
        layout.addLayout(axis_bar)
        self.apply_theme(AppTheme.current())

    def apply_theme(self, theme):
        self.setStyleSheet(theme.plot_canvas_style())
        self.expand_btn.setIcon(theme.icon("fa5s.expand"))
        self.save_btn.setIcon(theme.icon("fa5s.download"))
        self.reset_btn.setIcon(theme.icon("fa5s.undo"))
        for button in (self.expand_btn, self.save_btn, self.reset_btn):
            button.setStyleSheet(theme.tool_button_style())

        if hasattr(self, "plot_item"):
            self.configure_plot_item(self.plot_item, self.signal_name or "")
            self.redraw_plot(preserve_range=True)

    def create_plot_widget(self, sync_inputs):
        theme = AppTheme.current()
        plot_widget = pg.PlotWidget(background=theme.plot_panel)
        plot_widget.setMinimumWidth(0)
        plot_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        plot_widget.setMenuEnabled(False)

        plot_item = plot_widget.getPlotItem()
        view_box = plot_item.getViewBox()
        view_box.setMouseMode(pg.ViewBox.PanMode)
        view_box.setDefaultPadding(0.0)
        view_box.setBackgroundColor(theme.plot_background)

        if sync_inputs:
            view_box.sigRangeChanged.connect(self.on_view_range_changed)

        self.configure_plot_item(plot_item, "")
        return plot_widget

    def configure_plot_item(self, plot_item, title):
        theme = AppTheme.current()
        plot_item.clear()
        plot_item.hideButtons()
        plot_item.showGrid(x=True, y=True, alpha=theme.plot_grid_alpha)
        plot_item.getViewBox().setBackgroundColor(theme.plot_background)
        plot_item.setLabel("bottom", "Frequency (Hz)", color=theme.plot_text)
        plot_item.setLabel("left", "Magnitude (dB)", color=theme.plot_text)

        if title:
            plot_item.setTitle(f"<span style='color: {theme.plot_text}; font-size: 14pt'>{title}</span>")
        else:
            plot_item.setTitle("")

        for axis_name in ("bottom", "left"):
            axis = plot_item.getAxis(axis_name)
            axis.setPen(pg.mkPen(theme.plot_axis))
            axis.setTextPen(pg.mkPen(theme.plot_text))

    def expand_plot(self):
        if self.freqs is None or self.fft_db is None:
            return

        popup = QDialog(self)
        popup.setWindowTitle(f"FFT - {self.signal_name}")
        popup.setMinimumSize(900, 600)
        layout = QVBoxLayout(popup)

        expanded_plot = self.create_plot_widget(sync_inputs=False)
        x_range, y_range = self.current_ranges()
        self.populate_plot_widget(
            expanded_plot,
            marker_size=12,
            annotation_fontsize=10,
            x_range=x_range,
            y_range=y_range,
        )
        layout.addWidget(expanded_plot)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(popup.close)
        layout.addWidget(close_btn)

        popup.exec()

    def save_plot(self):
        if self.freqs is None or self.fft_db is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Plot",
            f"{self.signal_name}_fft.png",
            "PNG Image (*.png);;JPEG Image (*.jpg);;All Files (*)",
        )

        if file_path:
            self.plot_widget.grab().save(file_path)
            print(f"Saved: {file_path}")

    def on_view_range_changed(self, *_):
        self.update_axis_inputs()

    def apply_axis_limits(self):
        if self.freqs is None:
            return

        range_kwargs = {"padding": 0.0}

        try:
            x_min = float(self.x_min_input.text())
            x_max = float(self.x_max_input.text())
            if x_min < x_max:
                range_kwargs["xRange"] = (x_min, x_max)
        except ValueError:
            pass

        try:
            y_min = float(self.y_min_input.text())
            y_max = float(self.y_max_input.text())
            if y_min < y_max:
                range_kwargs["yRange"] = (y_min, y_max)
        except ValueError:
            pass

        if len(range_kwargs) == 1:
            return

        self.view_box.setRange(**range_kwargs)
        self.update_axis_inputs()

    def reset_axis_limits(self):
        if self.freqs is None:
            return

        self.view_box.setRange(
            xRange=self.default_x_range,
            yRange=self.default_y_range,
            padding=0.0,
        )
        self.update_axis_inputs()

    def current_ranges(self):
        x_range, y_range = self.view_box.viewRange()
        return tuple(x_range), tuple(y_range)

    def update_axis_inputs(self):
        if self.freqs is None:
            return

        x_range, y_range = self.current_ranges()
        self.x_min_input.setText(f"{x_range[0]:.1f}")
        self.x_max_input.setText(f"{x_range[1]:.1f}")
        self.y_min_input.setText(f"{y_range[0]:.1f}")
        self.y_max_input.setText(f"{y_range[1]:.1f}")

    def minimumSizeHint(self):
        return QSize(360, 220)

    def compute_spectrum(self, signal, sampling_rate):
        samples = np.asarray(signal, dtype=float)
        if samples.size < 2:
            raise ValueError("Signal must contain at least two samples")

        centered = samples - np.mean(samples)
        window = windows.hann(samples.size, sym=False)
        windowed = centered * window

        fft_vals = np.fft.rfft(windowed)
        fft_mag = np.abs(fft_vals)
        fft_db = 20 * np.log10(fft_mag + 1e-10)
        freqs = np.fft.rfftfreq(samples.size, d=1.0 / sampling_rate)
        return freqs, fft_db

    def find_dominant_peaks(self, fft_db, count=3):
        if fft_db is None or len(fft_db) == 0:
            return np.array([], dtype=int)

        peak_indices, _ = find_peaks(fft_db)
        if peak_indices.size == 0:
            if len(fft_db) <= 1:
                return np.array([], dtype=int)
            candidate_indices = np.arange(1, len(fft_db))
        else:
            candidate_indices = peak_indices

        candidate_levels = fft_db[candidate_indices]
        significant = candidate_indices[candidate_levels >= candidate_levels.max() - 25.0]
        ordered = significant[np.argsort(fft_db[significant])][::-1]
        return ordered[:count]

    def default_y_limits(self):
        y_min = float(np.min(self.fft_db))
        y_max = float(np.max(self.fft_db))
        y_range = y_max - y_min
        bottom_padding = max(y_range * 0.05, 1.0)
        top_padding = max(y_range * 0.18, 4.0)
        return (y_min - bottom_padding, y_max + top_padding)

    def peak_label_item(self, idx, font_size, y_offset):
        theme = AppTheme.current()
        label = pg.TextItem(
            text=f"{self.freqs[idx]:.1f} Hz",
            color=theme.peak,
            anchor=(0, 1),
        )
        font = QFont()
        font.setPointSize(font_size)
        label.setFont(font)
        label.setPos(float(self.freqs[idx]), float(self.fft_db[idx] + y_offset))
        return label

    def populate_plot_widget(self, plot_widget, marker_size, annotation_fontsize, x_range=None, y_range=None):
        theme = AppTheme.current()
        plot_item = plot_widget.getPlotItem()
        view_box = plot_item.getViewBox()

        self.configure_plot_item(plot_item, self.signal_name)

        curve = plot_item.plot(
            self.freqs,
            self.fft_db,
            pen=pg.mkPen(theme.curve, width=1),
        )
        curve.setClipToView(True)
        curve.setDownsampling(auto=True, method="peak")

        if self.peak_indices.size:
            peak_x = self.freqs[self.peak_indices]
            peak_y = self.fft_db[self.peak_indices]
            markers = pg.ScatterPlotItem(
                x=peak_x,
                y=peak_y,
                symbol="t",
                size=marker_size,
                brush=pg.mkBrush(theme.peak),
                pen=pg.mkPen(theme.peak),
            )
            plot_item.addItem(markers)

            y_offset = max((self.default_y_range[1] - self.default_y_range[0]) * 0.03, 1.5)
            for idx in self.peak_indices:
                plot_item.addItem(self.peak_label_item(idx, annotation_fontsize, y_offset))

        if x_range is None:
            x_range = self.default_x_range
        if y_range is None:
            y_range = self.default_y_range

        view_box.setRange(xRange=x_range, yRange=y_range, padding=0.0)

    def redraw_plot(self, preserve_range=False):
        if self.freqs is None or self.fft_db is None:
            return

        if preserve_range:
            x_range, y_range = self.current_ranges()
        else:
            x_range, y_range = self.default_x_range, self.default_y_range

        self.populate_plot_widget(
            self.plot_widget,
            marker_size=10,
            annotation_fontsize=9,
            x_range=x_range,
            y_range=y_range,
        )
        self.update_axis_inputs()

    def plot_fft(self, signal, signal_name, sampling_rate):
        self.sampling_rate = sampling_rate
        self.signal_name = signal_name
        self.title_label.setText(signal_name)
        self.freqs, self.fft_db = self.compute_spectrum(signal, sampling_rate)
        self.peak_indices = self.find_dominant_peaks(self.fft_db)
        self.default_x_range = (float(self.freqs[0]), float(self.freqs[-1]))
        self.default_y_range = self.default_y_limits()

        self.redraw_plot()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FFT Signal Analyzer")
        self.setMinimumSize(1200, 900)
        self.df = None
        self.sampling_rate = None
        self.current_page = 0
        self.plots_per_page = 1
        self.selected_signals = []
        self.canvas_widgets = []

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- File Browser Bar ---
        file_bar = QHBoxLayout()
        file_bar.setContentsMargins(8, 6, 8, 6)
        file_label = QLabel("File:")
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Browse to a CSV file...")
        self.file_path_input.setReadOnly(True)
        self.browse_button = QPushButton("Browse")
        self.browse_button.setFixedHeight(28)
        self.browse_button.clicked.connect(self.browse_file)
        file_bar.addWidget(file_label)
        file_bar.addWidget(self.file_path_input)
        file_bar.addWidget(self.browse_button)
        main_layout.addLayout(file_bar)

        # Horizontal separator below file bar
        self.h_separator = QFrame()
        self.h_separator.setFrameShape(QFrame.Shape.HLine)
        self.h_separator.setFrameShadow(QFrame.Shadow.Plain)
        self.h_separator.setFixedHeight(1)
        main_layout.addWidget(self.h_separator)

        # --- Two Panel Layout ---
        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(0)
        panels_layout.setContentsMargins(0, 0, 0, 0)

        # --- Left Panel ---
        self.left_panel = QWidget()
        self.left_panel.setFixedWidth(220)
        self.left_panel.setVisible(False)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        signals_label = QLabel("Signals")
        signals_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        signals_label.setContentsMargins(8, 6, 8, 6)
        left_layout.addWidget(signals_label)

        self.left_sep_top = QFrame()
        self.left_sep_top.setFrameShape(QFrame.Shape.HLine)
        self.left_sep_top.setFrameShadow(QFrame.Shadow.Plain)
        self.left_sep_top.setFixedHeight(1)
        left_layout.addWidget(self.left_sep_top)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.signal_list_widget = QWidget()
        self.signal_list_layout = QVBoxLayout(self.signal_list_widget)
        self.signal_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.signal_list_layout.setContentsMargins(8, 6, 8, 6)
        self.signal_list_layout.setSpacing(4)
        scroll_area.setWidget(self.signal_list_widget)
        left_layout.addWidget(scroll_area)

        self.left_sep_bottom = QFrame()
        self.left_sep_bottom.setFrameShape(QFrame.Shape.HLine)
        self.left_sep_bottom.setFrameShadow(QFrame.Shadow.Plain)
        self.left_sep_bottom.setFixedHeight(1)
        left_layout.addWidget(self.left_sep_bottom)

        self.plot_btn = QPushButton("Plot FFT")
        self.plot_btn.setFixedHeight(28)
        self.plot_btn.clicked.connect(self.plot_fft)
        self.plot_btn.setContentsMargins(8, 8, 8, 8)
        left_layout.addWidget(self.plot_btn)

        # Vertical separator between panels
        self.v_separator = QFrame()
        self.v_separator.setFrameShape(QFrame.Shape.VLine)
        self.v_separator.setFrameShadow(QFrame.Shadow.Plain)
        self.v_separator.setFixedWidth(1)
        self.v_separator.setVisible(False)

        # --- Right Panel ---
        right_panel = QWidget()
        right_panel.setMinimumWidth(0)
        self.right_layout = QVBoxLayout(right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)

        # Top bar: plots per page, anti-alias, and pagination.
        self.top_bar_widget = QWidget()
        self.top_bar_widget.setVisible(False)
        top_bar = QHBoxLayout(self.top_bar_widget)
        top_bar.setContentsMargins(8, 6, 8, 6)
        top_bar.setSpacing(6)

        plots_label = QLabel("Plots per page:")
        top_bar.addWidget(plots_label)

        plots_per_page_widget = QWidget()
        plots_per_page_layout = QHBoxLayout(plots_per_page_widget)
        plots_per_page_layout.setContentsMargins(0, 0, 0, 0)
        plots_per_page_layout.setSpacing(0)

        self.page_btn_group = QButtonGroup()
        self.page_buttons = {}
        for i in range(1, 5):
            btn = QPushButton(str(i))
            btn.setCheckable(True)
            btn.setFixedWidth(32)
            btn.setFixedHeight(28)
            if i == 1:
                btn.setChecked(True)
            self.page_buttons[i] = btn
            self.page_btn_group.addButton(btn, i)
            plots_per_page_layout.addWidget(btn)

        self.page_btn_group.idClicked.connect(self.on_plots_per_page_changed)
        top_bar.addWidget(plots_per_page_widget)
        top_bar.addSpacing(6)

        self.aa_btn = QPushButton()
        self.aa_btn.setFixedWidth(32)
        self.aa_btn.setFixedHeight(28)
        self.aa_btn.setCheckable(True)
        self.aa_btn.setChecked(False)
        self.aa_btn.setToolTip("Toggle Anti-Aliasing")
        self.aa_btn.clicked.connect(self.toggle_antialias)
        top_bar.addWidget(self.aa_btn)

        top_bar.addStretch()

        self.prev_btn = QPushButton()
        self.prev_btn.setFixedWidth(28)
        self.prev_btn.setFixedHeight(28)
        self.prev_btn.clicked.connect(self.prev_page)

        self.page_label = QLabel("Page 1 of 1")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_btn = QPushButton()
        self.next_btn.setFixedWidth(28)
        self.next_btn.setFixedHeight(28)
        self.next_btn.clicked.connect(self.next_page)

        top_bar.addWidget(self.prev_btn)
        top_bar.addWidget(self.page_label)
        top_bar.addWidget(self.next_btn)

        self.right_layout.addWidget(self.top_bar_widget)

        self.top_sep = QFrame()
        self.top_sep.setFrameShape(QFrame.Shape.HLine)
        self.top_sep.setFrameShadow(QFrame.Shadow.Plain)
        self.top_sep.setFixedHeight(1)
        self.top_sep.setVisible(False)
        self.right_layout.addWidget(self.top_sep)

        # Plot area
        self.plot_area = QWidget()
        self.plot_area.setMinimumWidth(0)
        self.plot_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.plot_grid = QVBoxLayout(self.plot_area)
        self.plot_grid.setContentsMargins(8, 8, 8, 8)
        self.plot_grid.setSpacing(8)
        self.right_layout.addWidget(self.plot_area)

        self.plot_placeholder = QLabel("Load a CSV file and select signals to plot")
        self.plot_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.plot_grid.addWidget(self.plot_placeholder)

        panels_layout.addWidget(self.left_panel)
        panels_layout.addWidget(self.v_separator)
        panels_layout.addWidget(right_panel)
        panels_layout.setStretch(2, 1)
        main_layout.addLayout(panels_layout)
        self.apply_theme()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() in {
            QEvent.Type.ApplicationPaletteChange,
            QEvent.Type.PaletteChange,
            QEvent.Type.StyleChange,
        }:
            self.apply_theme()

    def apply_theme(self):
        if not hasattr(self, "aa_btn"):
            return

        theme = AppTheme.current()
        self.left_panel.setStyleSheet(theme.left_panel_style())
        self.top_bar_widget.setStyleSheet(theme.top_bar_style())

        separator_style = theme.separator_style()
        for separator in (
            self.h_separator,
            self.left_sep_top,
            self.left_sep_bottom,
            self.v_separator,
            self.top_sep,
        ):
            separator.setStyleSheet(separator_style)

        self.aa_btn.setIcon(theme.icon("fa5s.wave-square"))
        self.prev_btn.setIcon(theme.icon("fa5s.chevron-left"))
        self.next_btn.setIcon(theme.icon("fa5s.chevron-right"))
        self.browse_button.setStyleSheet(theme.tool_button_style())
        self.plot_btn.setStyleSheet(theme.tool_button_style())

        for button in (self.aa_btn, self.prev_btn, self.next_btn):
            button.setStyleSheet(theme.tool_button_style())

        positions = {1: "first", 2: "middle", 3: "middle", 4: "last"}
        for btn_id, button in self.page_buttons.items():
            button.setStyleSheet(theme.segmented_button_style(positions[btn_id]))

        for plot in self.canvas_widgets:
            plot.apply_theme(theme)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.file_path_input.setText(file_path)
            self.load_csv(file_path)

    def load_csv(self, file_path):
        try:
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip()
            if df.shape[1] < 2:
                raise ValueError("CSV must contain a time column and at least one signal column")

            time_col = df.columns[0]
            time_values = pd.to_numeric(df[time_col], errors="raise").to_numpy(dtype=float)
            if len(time_values) < 2:
                raise ValueError("CSV must contain at least two rows")

            time_deltas = np.diff(time_values)
            if np.any(~np.isfinite(time_deltas)) or np.any(time_deltas <= 0):
                raise ValueError("Time column must be strictly increasing")

            time_step = float(np.median(time_deltas))
            if time_step <= 0:
                raise ValueError("Time step must be positive")
            time_tolerance = max(abs(time_step) * 1e-3, 1e-12)
            if np.any(np.abs(time_deltas - time_step) > time_tolerance):
                raise ValueError("Time column must be evenly spaced for FFT analysis")

            signal_columns = df.columns[1:]
            df[signal_columns] = df[signal_columns].apply(pd.to_numeric, errors="raise")
            signal_values = df[signal_columns].to_numpy(dtype=float)
            if np.any(~np.isfinite(signal_values)):
                raise ValueError("Signal columns must contain finite numeric values")

            self.df = df
            self.sampling_rate = 1.0 / time_step
            self.reset_analysis_state()
            print(f"Sampling rate detected: {self.sampling_rate} Hz")
            self.populate_signals()
            self.left_panel.setVisible(True)
            self.v_separator.setVisible(True)

        except Exception as e:
            print(f"Error loading CSV: {e}")
            self.df = None
            self.sampling_rate = None
            self.clear_signal_list()
            self.reset_analysis_state("Load a valid CSV file")
            self.left_panel.setVisible(False)
            self.v_separator.setVisible(False)

    def reset_analysis_state(self, message="Select signals and click Plot FFT"):
        self.selected_signals = []
        self.current_page = 0
        self.clear_layout(self.plot_grid)
        self.show_placeholder(message)
        self.page_label.setText("Page 1 of 1")
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self.top_bar_widget.setVisible(False)
        self.top_sep.setVisible(False)

    def clear_signal_list(self):
        for i in reversed(range(self.signal_list_layout.count())):
            widget = self.signal_list_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

    def populate_signals(self):
        self.clear_signal_list()
        signal_columns = self.df.columns[1:]
        for col in signal_columns:
            checkbox = QCheckBox(col)
            self.signal_list_layout.addWidget(checkbox)

    def show_placeholder(self, message):
        placeholder = QLabel(message)
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.plot_grid.addWidget(placeholder)
        self.plot_placeholder = placeholder

    def on_plots_per_page_changed(self, id):
        self.plots_per_page = id
        self.current_page = 0
        self.render_page()

    def toggle_antialias(self):
        enabled = self.aa_btn.isChecked()
        pg.setConfigOptions(antialias=enabled)
        self.render_page()

    def get_selected_signals(self):
        selected = []
        for i in range(self.signal_list_layout.count()):
            checkbox = self.signal_list_layout.itemAt(i).widget()
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                selected.append(checkbox.text())
        return selected

    def update_page_buttons(self):
        total = len(self.selected_signals)
        for btn_id in range(1, 5):
            btn = self.page_btn_group.button(btn_id)
            btn.setEnabled(btn_id <= total)

        if total == 0:
            return

        if self.plots_per_page > total:
            self.plots_per_page = total
            self.page_btn_group.button(total).setChecked(True)

    def plot_fft(self):
        if self.df is None:
            return
        self.selected_signals = self.get_selected_signals()
        if not self.selected_signals:
            print("No signals selected")
            self.clear_layout(self.plot_grid)
            self.show_placeholder("Select at least one signal to plot")
            self.page_label.setText("Page 1 of 1")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.top_bar_widget.setVisible(False)
            self.top_sep.setVisible(False)
            self.update_page_buttons()
            return

        self.top_bar_widget.setVisible(True)
        self.top_sep.setVisible(True)
        self.update_page_buttons()
        self.current_page = 0
        self.render_page()

    def clear_layout(self, layout):
        for widget in self.canvas_widgets:
            widget.setParent(None)
            widget.hide()
            widget.deleteLater()
        self.canvas_widgets = []

        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.hide()
                widget.deleteLater()
            elif item.layout() is not None:
                self.clear_layout_recursive(item.layout())

    def clear_layout_recursive(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.hide()
                widget.deleteLater()
            elif item.layout() is not None:
                self.clear_layout_recursive(item.layout())

    def render_page(self):
        self.clear_layout(self.plot_grid)

        if self.df is None:
            self.show_placeholder("Load a CSV file and select signals to plot")
            self.page_label.setText("Page 1 of 1")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return

        available_columns = set(self.df.columns[1:])
        self.selected_signals = [
            s for s in self.selected_signals if s in available_columns
        ]

        if not self.selected_signals:
            self.show_placeholder("Select at least one signal to plot")
            self.page_label.setText("Page 1 of 1")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return

        total_pages = max(1, -(-len(self.selected_signals) // self.plots_per_page))
        self.current_page = min(self.current_page, total_pages - 1)
        self.page_label.setText(f"Page {self.current_page + 1} of {total_pages}")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < total_pages - 1)

        start = self.current_page * self.plots_per_page
        end = start + self.plots_per_page
        page_signals = self.selected_signals[start:end]

        cols = 2 if self.plots_per_page > 1 else 1
        row_layout = None
        for i, signal_name in enumerate(page_signals):
            if i % cols == 0:
                row_layout = QHBoxLayout()
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(8)
                self.plot_grid.addLayout(row_layout)

            canvas = PlotCanvas()
            signal_data = self.df[signal_name].values
            canvas.plot_fft(signal_data, signal_name, self.sampling_rate)
            self.canvas_widgets.append(canvas)
            row_layout.addWidget(canvas, 1)

        # Let a final single plot fill the row naturally.
        if len(page_signals) > 1 and len(page_signals) % cols != 0 and row_layout:
            filler = QWidget()
            filler.setMinimumWidth(0)
            filler.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            row_layout.addWidget(filler, 1)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.render_page()

    def next_page(self):
        total_pages = -(-len(self.selected_signals) // self.plots_per_page)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.render_page()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
