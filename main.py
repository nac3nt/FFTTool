import sys
from pathlib import Path
from turtle import position
from unicodedata import name

import numpy as np
import pandas as pd
import pyqtgraph as pg
import qtawesome as qta
from scipy.signal import find_peaks, windows
from PyQt6.QtCore import QEvent, QSize, Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
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

def apply_icon_hover(button, theme, icon_name):
    import qtawesome as qta

    def set_default():
        button.setIcon(qta.icon(icon_name, color=theme.colors["text"]))

    def set_active():
        button.setIcon(qta.icon(icon_name, color=theme.accent_text))

    def update_icon():
        if button.isChecked():
            set_active()
        else:
            set_default()

    def enterEvent(e):
        set_active()

    def leaveEvent(e):
        update_icon()

    def toggled(_):
        update_icon()

    button.enterEvent = enterEvent
    button.leaveEvent = leaveEvent
    button.toggled.connect(toggled)

    update_icon()

class AppTheme:
    def __init__(self, is_dark):
        self.is_dark = is_dark

        if is_dark:
            self.colors = {
                "bg": "#1e1e1e",
                "surface": "#252526",
                "surface_alt": "#2d2d30",
                "text_primary": "#ffffff",
                "text_secondary": "#c8c8c8",
                "accent": "#0078d4",
                "accent_hover": "#2893ff",
                "border": "#2f2f2f",
                "danger": "#e81123",
                "success": "#107c10",
                "crosshair": "#ffffff",
            }
        else:
            self.colors = {
                "bg": "#f3f3f3",
                "surface": "#ffffff",
                "surface_alt": "#f0f0f0",
                "text_primary": "#1a1a1a",
                "text_secondary": "#555555",
                "accent": "#0078d4",
                "accent_hover": "#005a9e",
                "border": "#e5e5e5",
                "danger": "#d13438",
                "success": "#107c10",
                "crosshair": "#000000",
            }

        self.accent_text = "#ffffff"

        self.plot = {
            "panel": self.colors["surface"],
            "background": self.colors["surface_alt"],
            "text": self.colors["text_primary"],
            "axis": self.colors["text_secondary"],
            "curve": self.colors["accent"],
            "peak": self.colors["accent_hover"],
        }

        self.fonts = {
            "title": 13,
            "label": 11,
            "small": 9,
        }

        self.spacing = {
            "xs": 4,
            "sm": 8,
            "md": 12,
            "lg": 16,
        }

        self.colors["panel"] = self.colors["surface"]
        self.colors["text"] = self.colors["text_primary"]
        self.colors["muted"] = self.colors["text_secondary"]

    @staticmethod
    def current():
        import winreg

        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
            )
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            is_dark = (value == 0)
        except:
            is_dark = True

        return AppTheme(is_dark)

    def icon(self, name):
        return qta.icon(
            name,
            color=self.colors["text"],
            color_active=self.accent_text,
            color_selected=self.accent_text,
            color_disabled=self.colors["muted"],
        )

    def icon_active(self, name):
        return qta.icon(name, color=self.accent_text)

    def button_style(self):
        return f"""
            QPushButton {{
                color: {self.colors["text_primary"]};
                background-color: {self.colors["surface"]};
                border: 1px solid {self.colors["border"]};
                border-radius: 4px;
                padding: {self.spacing["xs"]}px {self.spacing["md"]}px;
            }}

            QPushButton:hover {{
                color: {self.accent_text};
                background-color: {self.colors["accent"]};
                border: 1px solid {self.colors["accent"]};
            }}

            QPushButton:checked {{
                color: {self.accent_text};
                background-color: {self.colors["accent"]};
                border: 1px solid {self.colors["accent"]};
            }}

            QPushButton:pressed {{
                background-color: {self.colors["accent_hover"]};
            }}
        """

    def panel_style(self):
        return f"""
            QWidget {{
                background-color: {self.colors["surface"]};
                color: {self.colors["text_primary"]};
            }}
        """

    def main_style(self):
        return f"""
            QWidget {{
                background-color: {self.colors["bg"]};
                color: {self.colors["text_primary"]};
            }}
        """

    def checkbox_style(self):
        return f"""
            QCheckBox {{
                color: {self.colors["text_primary"]};
                spacing: {self.spacing["sm"]}px;
            }}

            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
                border: 1px solid {self.colors["border"]};
                border-radius: 3px;
                background-color: {self.colors["surface_alt"]};
            }}

            QCheckBox::indicator:checked {{
                background-color: {self.colors["accent"]};
                border: 1px solid {self.colors["accent"]};
            }}
        """

    def input_style(self):
        return f"""
            QLabel {{
                color: {self.colors["text_primary"]};
                background-color: {self.colors["surface_alt"]};
                border: 1px solid {self.colors["border"]};
                border-radius: 4px;
                padding: 4px;
            }}
        """
    
    def segmented_button_style(self, position):
        radius = {
            "first": "4px 0 0 4px",
            "middle": "0",
            "last": "0 4px 4px 0",
        }[position]

        return f"""
            QPushButton {{
                color: {self.colors["text_primary"]};
                background-color: {self.colors["surface"]};
                border: 1px solid {self.colors["border"]};
                border-right: none;
                border-radius: {radius};
                padding: 4px 10px;
            }}

            QPushButton:last-child {{
                border-right: 1px solid {self.colors["border"]};
            }}

            QPushButton:hover {{
                color: {self.accent_text};
                background-color: {self.colors["accent"]};
                border-color: {self.colors["accent"]};
            }}

            QPushButton:checked {{
                color: {self.accent_text};
                background-color: {self.colors["accent"]};
                border-color: {self.colors["accent"]};
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
        self.cursor_locked = False
        self.lock_x = None
        self.lock_y = None

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumWidth(0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(0, 0, 0, 0)
        title_bar.setSpacing(6)

        self.title_label = QLabel("")
        title_bar.addWidget(self.title_label)

        self.window_select = QComboBox()
        self.window_select.addItems(["Hann", "Hamming", "Blackman"])
        self.window_select.setCurrentText("Hann")
        self.window_select.setFixedHeight(28)
        self.window_select.setFixedWidth(110)
        self.window_select.setToolTip(
            "FFT Window Function\n\n"
            "Controls spectral leakage behavior.\n"
            "Hann: balanced default\n"
            "Hamming: stronger main peak amplitude\n"
            "Blackman: best leakage suppression"
        )

        self.zero_btn = QPushButton()
        self.zero_btn.setCheckable(True)
        self.zero_btn.setChecked(False)
        self.zero_btn.setFixedSize(28, 28)
        self.zero_btn.setToolTip(
            "Zero Padding\n\n"
            "Adds zeros before FFT to increase frequency bin density.\n"
            "Makes peaks smoother and easier to estimate.\n"
            "Does not add real signal information."
        )

        self.dc_btn = QPushButton()
        self.dc_btn.setCheckable(True)
        self.dc_btn.setChecked(False)
        self.dc_btn.setFixedSize(28, 28)
        self.dc_btn.setToolTip(
            "Remove DC Offset\n\n"
            "Subtracts signal mean before FFT.\n"
            "Useful when baseline offset creates a strong 0 Hz peak."
        )

        self.snap_btn = QPushButton()
        self.snap_btn.setCheckable(True)
        self.snap_btn.setChecked(False)
        self.snap_btn.setFixedSize(28, 28)
        self.snap_btn.setToolTip(
            "Snap Cursor to FFT Bins\n\n"
            "When enabled, cursor readout locks to nearest FFT frequency bin.\n"
            "Useful for precise peak inspection.\n\n"
            "When disabled, cursor moves freely."
        )

        title_bar.addWidget(self.window_select)
        title_bar.addWidget(self.zero_btn)
        title_bar.addWidget(self.dc_btn)
        title_bar.addWidget(self.snap_btn)

        self.window_select.currentTextChanged.connect(self.recompute_and_redraw)
        self.zero_btn.clicked.connect(self.recompute_and_redraw)
        self.dc_btn.clicked.connect(self.recompute_and_redraw)

        self.save_btn = QPushButton()
        self.save_btn.setFixedSize(28, 28)
        self.save_btn.setToolTip("Save plot as image")
        self.save_btn.clicked.connect(self.save_plot)

        title_bar.addWidget(self.save_btn)
        layout.addLayout(title_bar)

        self.plot_widget = self.create_plot_widget(sync_inputs=True)

        self.proxy = pg.SignalProxy(
            self.plot_widget.scene().sigMouseMoved,
            rateLimit=60,
            slot=self.mouse_moved,
        )

        self.plot_widget.scene().sigMouseClicked.connect(self.mouse_clicked)

        self.plot_item = self.plot_widget.getPlotItem()
        self.view_box = self.plot_item.getViewBox()
        layout.addWidget(self.plot_widget)
        layout.setStretchFactor(self.plot_widget, 1)

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
        axis_bar.addWidget(QLabel("-"))
        axis_bar.addWidget(self.x_max_input)
        axis_bar.addSpacing(5)

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
        axis_bar.addWidget(QLabel("-"))
        axis_bar.addWidget(self.y_max_input)

        self.reset_btn = QPushButton()
        self.reset_btn.setFixedSize(28, 28)
        self.reset_btn.setToolTip("Reset axis limits")
        self.reset_btn.clicked.connect(self.reset_axis_limits)
        axis_bar.addWidget(self.reset_btn)
        axis_bar.addStretch()
        layout.addLayout(axis_bar)
        self.apply_theme(AppTheme.current())

    def mouse_clicked(self, evt):
        vb = self.plot_widget.getPlotItem().vb
        pos = evt.scenePos()

        if not vb.sceneBoundingRect().contains(pos):
            return

        if self.cursor_locked:
            self.cursor_locked = False
            self.lock_x = None
            self.lock_y = None
            return

        self.cursor_locked = True
        self.lock_x = self.v_line.value()
        self.lock_y = self.h_line.value()

        self.title_label.setText(
            f"Locked {self.lock_x:,.2f} Hz | {self.lock_y:,.2f} dB"
        )

    def mouse_moved(self, evt):
        if self.cursor_locked:
            return

        if self.freqs is None or len(self.freqs) == 0:
            return

        pos = evt[0]

        vb = self.plot_widget.getPlotItem().vb
        view_rect = vb.sceneBoundingRect()

        if not view_rect.contains(pos):
            self.hide_crosshair()
            return

        point = vb.mapSceneToView(pos)

        x_mouse = float(point.x())
        y_mouse = float(point.y())

        if self.snap_btn.isChecked():
            idx = int(np.abs(self.freqs - x_mouse).argmin())

            x = float(self.freqs[idx])
            y = float(self.fft_db[idx])
        else:
            x = x_mouse
            y = y_mouse

        self.v_line.setPos(x)
        self.h_line.setPos(y)

        self.v_line.show()
        self.h_line.show()

        self.title_label.setText(
            f"{x:,.2f} Hz | {y:,.2f} dB"
        )
        
    def hide_crosshair(self):
        if hasattr(self, "v_line"):
            self.v_line.hide()

        if hasattr(self, "h_line"):
            self.h_line.hide()

        self.title_label.setText(self.signal_name)

    def setup_crosshair(self):
        plot_item = self.plot_widget.getPlotItem()
        theme = AppTheme.current()
        accent = theme.colors["crosshair"]

        self.v_line = pg.InfiniteLine(
            angle=90,
            movable=False,
            pen=pg.mkPen(accent, width=1)
        )

        self.h_line = pg.InfiniteLine(
            angle=0,
            movable=False,
            pen=pg.mkPen(accent, width=1)
        )

        plot_item.addItem(self.v_line, ignoreBounds=True)
        plot_item.addItem(self.h_line, ignoreBounds=True)

        self.v_line.hide()
        self.h_line.hide()

    def recompute_and_redraw(self):
        if self.raw_signal is None:
            return

        vb = self.plot_widget.getPlotItem().vb
        x_range, y_range = vb.viewRange()

        self.freqs, self.fft_db = self.compute_spectrum(
            self.raw_signal,
            self.sampling_rate,
            window_type=self.window_select.currentText(),
            zero_pad=self.zero_btn.isChecked(),
            remove_dc=self.dc_btn.isChecked(),
        )

        self.redraw_plot()

        self.plot_widget.setXRange(
            x_range[0], x_range[1], padding=0
        )

        self.plot_widget.setYRange(
            y_range[0], y_range[1], padding=0
        )

    def detect_harmonics(self, tolerance=0.05):
        if self.peak_indices is None or len(self.peak_indices) < 2:
            return []

        base_freq = self.freqs[self.peak_indices[0]]
        harmonics = []

        for idx in self.peak_indices[1:]:
            freq = self.freqs[idx]
            ratio = freq / base_freq

            if abs(ratio - round(ratio)) < tolerance:
                harmonics.append((freq, int(round(ratio))))

        return harmonics

    def apply_theme(self, theme):
        self.window_select.setStyleSheet(theme.input_style())

        for button in (self.zero_btn, self.snap_btn, self.dc_btn, self.save_btn, self.reset_btn,):
            button.setStyleSheet(theme.button_style())
            button.setIconSize(QSize(16, 16))

        apply_icon_hover(self.zero_btn, theme, "fa6s.0")
        apply_icon_hover(self.dc_btn, theme, "msc.diff-removed")
        apply_icon_hover(self.save_btn, theme, "fa5s.download")
        apply_icon_hover(self.reset_btn, theme, "fa5s.undo")
        apply_icon_hover(self.snap_btn, theme, "fa5s.magnet")

        if hasattr(self, "plot_widget"):
            self.plot_widget.setBackground(theme.plot["panel"])
            self.plot_widget.getViewBox().setBackgroundColor(theme.plot["background"])

        if hasattr(self, "plot_item"):
            self.configure_plot_item(self.plot_item, self.signal_name or "")

        self.redraw_plot(preserve_range=True)

    def create_plot_widget(self, sync_inputs):
        theme = AppTheme.current()
        plot_widget = pg.PlotWidget(background=theme.plot["panel"])
        plot_widget.setMinimumWidth(0)
        plot_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        plot_widget.setMenuEnabled(False)

        plot_item = plot_widget.getPlotItem()
        view_box = plot_item.getViewBox()
        view_box.setMouseMode(pg.ViewBox.PanMode)
        view_box.setDefaultPadding(0.0)
        view_box.setBackgroundColor(theme.plot["background"])

        if sync_inputs:
            view_box.sigRangeChanged.connect(self.on_view_range_changed)

        self.configure_plot_item(plot_item, "")
        return plot_widget

    def configure_plot_item(self, plot_item, title):
        theme = AppTheme.current()

        plot_item.clear()
        plot_item.hideButtons()

        grid_alpha = 0.12 if theme.is_dark else 0.06
        plot_item.showGrid(x=True, y=True, alpha=grid_alpha)

        plot_item.getViewBox().setBackgroundColor(theme.plot["background"])

        plot_item.setLabel("bottom", "Frequency (Hz)", color=theme.plot["text"])
        plot_item.setLabel("left", "Magnitude (dB)", color=theme.plot["text"])

        if title:
            plot_item.setTitle(
                f"<span style='color: {theme.plot['text']}; font-size: {theme.fonts['title']}pt; font-weight: 500'>{title}</span>"
            )
        else:
            plot_item.setTitle("")

        for axis_name in ("bottom", "left"):
            axis = plot_item.getAxis(axis_name)
            axis.setPen(pg.mkPen(theme.plot["axis"]))
            axis.setTextPen(pg.mkPen(theme.plot["text"]))

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

    def compute_spectrum(self, signal, sampling_rate, window_type="Hann", zero_pad=False, remove_dc=True,):
        signal = np.asarray(signal, dtype=float)

        if signal.size == 0:
            return np.array([]), np.array([])

        if remove_dc:
            signal = signal - np.mean(signal)

        N = len(signal)

        if window_type == "Hann":
            window = np.hanning(N)
        elif window_type == "Hamming":
            window = np.hamming(N)
        elif window_type == "Blackman":
            window = np.blackman(N)
        else:
            window = np.ones(N)

        signal = signal * window

        if zero_pad:
            N_fft = int(2 ** np.ceil(np.log2(N))) * 2
        else:
            N_fft = N

        fft_vals = np.fft.rfft(signal, n=N_fft)
        freqs = np.fft.rfftfreq(N_fft, d=1.0 / sampling_rate)

        magnitude = np.abs(fft_vals)
        magnitude_db = 20 * np.log10(magnitude + 1e-12)

        return freqs, magnitude_db

    def find_dominant_peaks(self, fft_db, count=3):
        if fft_db is None or len(fft_db) == 0:
            return np.array([], dtype=int)

        peak_indices, properties = find_peaks(
            fft_db,
            prominence=6,
            distance=10
        )

        if peak_indices.size == 0:
            return np.array([], dtype=int)

        sorted_idx = peak_indices[np.argsort(fft_db[peak_indices])[::-1]]
        return sorted_idx[:count]

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
            color=theme.plot["peak"],
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
            pen=pg.mkPen(theme.plot["curve"], width=2.5),
        )
        curve.setClipToView(True)
        curve.setDownsampling(auto=True, method="peak")

        if self.peak_indices.size:
            peak_x = self.freqs[self.peak_indices]
            peak_y = self.fft_db[self.peak_indices]

            markers = pg.ScatterPlotItem(
                x=peak_x,
                y=peak_y,
                symbol="o",
                size=marker_size + 3,
                brush=pg.mkBrush(theme.plot["peak"]),
                pen=pg.mkPen("#00000000"),
            )
            plot_item.addItem(markers)

            y_offset = max((self.default_y_range[1] - self.default_y_range[0]) * 0.04, 2.0)

            for i, idx in enumerate(self.peak_indices):
                label = pg.TextItem(
                    text=f"{self.freqs[idx]:.1f} Hz",
                    color=theme.plot["peak"],
                    anchor=(0.5, 1.2),
                )

                font = QFont()
                font.setPointSize(annotation_fontsize)
                font.setBold(i == 0)
                label.setFont(font)

                label.setPos(float(self.freqs[idx]), float(self.fft_db[idx] + y_offset))
                plot_item.addItem(label)

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
        self.setup_crosshair()

    def plot_fft(self, signal, signal_name, sampling_rate, window_type=None, zero_pad=None, remove_dc=None,):
        self.raw_signal = np.asarray(signal, dtype=float)
        self.signal_name = signal_name
        self.sampling_rate = sampling_rate

        if window_type is None:
            window_type = self.window_select.currentText()

        if zero_pad is None:
            zero_pad = self.zero_btn.isChecked()

        if remove_dc is None:
            remove_dc = self.dc_btn.isChecked()

        self.freqs, self.fft_db = self.compute_spectrum(
            self.raw_signal,
            sampling_rate,
            window_type=window_type,
            zero_pad=zero_pad,
            remove_dc=remove_dc,
        )

        if len(self.freqs) == 0:
            return

        self.current_x_range = (
            float(self.freqs[0]),
            float(self.freqs[-1]),
        )

        self.current_y_range = (
            float(np.min(self.fft_db)),
            float(np.max(self.fft_db)),
        )

        self.default_x_range = self.current_x_range
        self.default_y_range = self.current_y_range

        self.title_label.setText(signal_name)

        self.redraw_plot()

        if self.current_x_range is not None:
            self.plot_widget.setXRange(
                self.current_x_range[0],
                self.current_x_range[1],
                padding=0
            )

        if self.current_y_range is not None:
            self.plot_widget.setYRange(
                self.current_y_range[0],
                self.current_y_range[1],
                padding=0
            )

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._last_theme_is_dark = AppTheme.current().is_dark

        self.theme_timer = QTimer()
        self.theme_timer.timeout.connect(self.check_theme_change)
        self.theme_timer.start(1000)
        m = AppTheme.current().spacing
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

        file_bar = QHBoxLayout()
        file_bar.setContentsMargins(m["md"], m["sm"], m["md"], m["sm"])
        file_bar.setSpacing(m["sm"])
        self.file_path_label = QLabel("Browse to a CSV file...")
        self.file_path_label.setMinimumWidth(0)
        self.file_path_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.file_path_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self.file_path_label.setMargin(4)
        self.browse_button = QPushButton("Browse")
        self.browse_button.setIconSize(QSize(16, 16))
        self.browse_button.setFixedHeight(28)
        self.browse_button.setFixedWidth(90)
        self.browse_button.clicked.connect(self.browse_file)
        file_bar.addWidget(self.file_path_label, 1)
        file_bar.addWidget(self.browse_button)
        main_layout.addLayout(file_bar)

        self.h_separator = QFrame()
        self.h_separator.setFrameShape(QFrame.Shape.HLine)
        self.h_separator.setFrameShadow(QFrame.Shadow.Plain)
        self.h_separator.setFixedHeight(1)
        main_layout.addWidget(self.h_separator)

        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(0)
        panels_layout.setContentsMargins(0, 0, 0, 0)

        self.left_panel = QWidget()
        self.left_panel.setFixedWidth(220)
        self.left_panel.setVisible(False)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)

        signals_header = QWidget()
        signals_header_layout = QHBoxLayout(signals_header)
        signals_header_layout.setContentsMargins(m["md"], m["xs"], m["sm"], m["xs"])
        signals_header_layout.setSpacing(m["xs"])

        signals_label = QLabel("Signals")
        signals_label.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )

        self.toggle_all_btn = QPushButton()
        self.toggle_all_btn.setFixedSize(28, 28)
        self.toggle_all_btn.setToolTip("Select all signals")
        self.toggle_all_btn.clicked.connect(self.toggle_all_signals)

        signals_header_layout.addWidget(signals_label)
        signals_header_layout.addStretch()
        signals_header_layout.addWidget(self.toggle_all_btn)
        left_layout.addWidget(signals_header)

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
        self.signal_list_layout.setContentsMargins(m["md"], m["sm"], m["md"], m["sm"])
        self.signal_list_layout.setSpacing(m["xs"])
        scroll_area.setWidget(self.signal_list_widget)
        left_layout.addWidget(scroll_area)
        left_layout.setStretchFactor(scroll_area, 1)

        self.left_sep_bottom = QFrame()
        self.left_sep_bottom.setFrameShape(QFrame.Shape.HLine)
        self.left_sep_bottom.setFrameShadow(QFrame.Shadow.Plain)
        self.left_sep_bottom.setFixedHeight(1)
        left_layout.addWidget(self.left_sep_bottom)

        self.plot_btn = QPushButton("Plot FFT")
        self.plot_btn.setIconSize(QSize(16, 16))
        self.plot_btn.setFixedHeight(28)
        self.plot_btn.clicked.connect(self.plot_fft)
        self.plot_btn.setContentsMargins(m["md"], m["sm"], m["md"], m["sm"])
        left_layout.addWidget(self.plot_btn)

        self.v_separator = QFrame()
        self.v_separator.setFrameShape(QFrame.Shape.VLine)
        self.v_separator.setFrameShadow(QFrame.Shadow.Plain)
        self.v_separator.setFixedWidth(1)
        self.v_separator.setVisible(False)

        right_panel = QWidget()
        right_panel.setMinimumWidth(0)
        self.right_layout = QVBoxLayout(right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)

        self.top_bar_widget = QWidget()
        self.top_bar_widget.setVisible(False)
        top_bar = QHBoxLayout(self.top_bar_widget)
        top_bar.setContentsMargins(m["md"], m["sm"], m["md"], m["sm"])
        top_bar.setSpacing(m["xs"])

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
        top_bar.addSpacing(m["xs"])

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

        self.plot_area = QWidget()
        self.plot_area.setMinimumWidth(0)
        self.plot_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.plot_grid = QVBoxLayout(self.plot_area)
        self.plot_grid.setContentsMargins(m["md"], m["md"], m["md"], m["md"])
        self.plot_grid.setSpacing(m["md"])
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
    
    def check_theme_change(self):
        current_theme = AppTheme.current()

        if current_theme.is_dark != self._last_theme_is_dark:
            self._last_theme_is_dark = current_theme.is_dark
            self.refresh_theme()

    def changeEvent(self, event):
        super().changeEvent(event)

        if event.type() in {
            QEvent.Type.ApplicationPaletteChange,
            QEvent.Type.PaletteChange,
            QEvent.Type.StyleChange,
        }:
            self.refresh_theme()

    def refresh_theme(self):
        theme = AppTheme.current()

        self.apply_theme()
        self.render_page()
        self.apply_theme()

        self.update_toggle_all_button()
        self.repaint()

    def apply_theme(self):
        if not hasattr(self, "aa_btn"):
            return

        theme = AppTheme.current()

        self.centralWidget().setStyleSheet(theme.main_style())
        self.left_panel.setStyleSheet(theme.panel_style())
        self.top_bar_widget.setStyleSheet(theme.panel_style())

        separator_style = f"background-color: {theme.colors['border']};"
        for separator in (
            self.h_separator,
            self.left_sep_top,
            self.left_sep_bottom,
            self.v_separator,
            self.top_sep,
        ):
            separator.setStyleSheet(separator_style)

        self.browse_button.setStyleSheet(theme.button_style())
        self.plot_btn.setStyleSheet(theme.button_style())
        self.toggle_all_btn.setStyleSheet(theme.button_style())

        for button in (self.prev_btn, self.next_btn):
            button.setStyleSheet(theme.button_style())

        self.aa_btn.setStyleSheet(f"""
            QPushButton {{
                color: {theme.colors["text"]};
                background-color: {theme.colors["panel"]};
                border: 1px solid {theme.colors["border"]};
                border-radius: 4px;
            }}

            QPushButton:hover {{
                color: {theme.accent_text};
                background-color: {theme.colors["accent"]};
                border: 1px solid {theme.colors["accent"]};
            }}

            QPushButton:checked {{
                color: {theme.accent_text};
                background-color: {theme.colors["accent"]};
                border: 1px solid {theme.colors["accent"]};
            }}

            QPushButton:pressed {{
                background-color: {theme.colors["accent_hover"]};
            }}
        """)

        apply_icon_hover(self.browse_button, theme, "fa5s.folder-open")
        apply_icon_hover(self.plot_btn, theme, "fa5s.chart-line")
        apply_icon_hover(self.aa_btn, theme, "fa5s.wave-square")
        apply_icon_hover(self.prev_btn, theme, "fa5s.chevron-left")
        apply_icon_hover(self.next_btn, theme, "fa5s.chevron-right")

        self.file_path_label.setStyleSheet(theme.input_style())

        positions = {1: "first", 2: "middle", 3: "middle", 4: "last"}
        for btn_id, button in self.page_buttons.items():
            button.setStyleSheet(theme.segmented_button_style(positions[btn_id]))

        for i in range(self.signal_list_layout.count()):
            widget = self.signal_list_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox):
                widget.setStyleSheet(theme.checkbox_style())

        for plot in self.canvas_widgets:
            plot.apply_theme(theme)

        self.update_toggle_all_button()
        self.repaint()

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.file_path_label.setText(file_path)
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
            self.file_path_label.setText("Browse to a CSV file...")
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
        self.update_toggle_all_button()

    def populate_signals(self):
        theme = AppTheme.current()

        self.clear_signal_list()

        signal_columns = self.df.columns[1:]

        for col in signal_columns:
            checkbox = QCheckBox(col)
            checkbox.setStyleSheet(theme.checkbox_style())
            checkbox.stateChanged.connect(self.update_toggle_all_button)
            self.signal_list_layout.addWidget(checkbox)

        self.update_toggle_all_button()
        self.repaint()

    def toggle_all_signals(self):
        checkboxes = []
        checked_count = 0
        for i in range(self.signal_list_layout.count()):
            checkbox = self.signal_list_layout.itemAt(i).widget()
            if isinstance(checkbox, QCheckBox):
                checkboxes.append(checkbox)
                if checkbox.isChecked():
                    checked_count += 1

        if not checkboxes:
            return

        set_checked = checked_count == 0
        for checkbox in checkboxes:
            checkbox.setChecked(set_checked)

        self.update_toggle_all_button()

    def update_toggle_all_button(self):
        theme = AppTheme.current()

        checkboxes = []
        checked_count = 0

        for i in range(self.signal_list_layout.count()):
            widget = self.signal_list_layout.itemAt(i).widget()
            if isinstance(widget, QCheckBox):
                checkboxes.append(widget)
                if widget.isChecked():
                    checked_count += 1

        if not checkboxes:
            return

        total = len(checkboxes)

        if checked_count == 0:
            icon_name = "fa5s.plus-square"
            tooltip = "Select all signals"
        else:
            icon_name = "fa5s.minus-square"
            tooltip = "Deselect all signals"

        apply_icon_hover(self.toggle_all_btn, theme, icon_name)
        self.toggle_all_btn.setToolTip(tooltip)

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
        m = AppTheme.current().spacing
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

        count = len(page_signals)

        if count == 1:
            rows = [[0]]

        elif count == 2:
            rows = [[0], [1]]

        elif count == 3:
            rows = [[0, 1], [2]]

        else:
            rows = [[0, 1], [2, 3]]

        for row in rows:
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(m["md"])

            for idx in row:
                signal_name = page_signals[idx]

                canvas = PlotCanvas()
                signal_data = self.df[signal_name].values
                canvas.plot_fft(signal_data, signal_name, self.sampling_rate)

                canvas.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Expanding
                )

                self.canvas_widgets.append(canvas)
                row_layout.addWidget(canvas, 1)

            self.plot_grid.addLayout(row_layout, 1)

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
