import sys
import numpy as np
import pandas as pd
from scipy.signal import windows
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog,
    QFrame, QScrollArea, QCheckBox, QButtonGroup, QDialog
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class PlotCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.sampling_rate = None
        self.freqs = None
        self.fft_db = None
        self.signal_name = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Title bar with signal name and buttons
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(4, 4, 4, 0)

        self.title_label = QLabel("")
        title_bar.addWidget(self.title_label)
        title_bar.addStretch()

        expand_btn = QPushButton("⤢")
        expand_btn.setFixedSize(24, 24)
        expand_btn.setToolTip("Expand plot")
        expand_btn.clicked.connect(self.expand_plot)

        save_btn = QPushButton("💾")
        save_btn.setFixedSize(24, 24)
        save_btn.setToolTip("Save plot as image")
        save_btn.clicked.connect(self.save_plot)

        title_bar.addWidget(expand_btn)
        title_bar.addWidget(save_btn)
        layout.addLayout(title_bar)

        # Canvas
        self.fig = Figure(tight_layout=True)
        self.canvas = FigureCanvas(self.fig)
        self.ax = None
        layout.addWidget(self.canvas)

        # Axis limit inputs
        axis_bar = QHBoxLayout()
        axis_bar.setSpacing(4)

        axis_bar.addWidget(QLabel("X:"))
        self.x_min_input = QLineEdit()
        self.x_max_input = QLineEdit()
        self.x_min_input.setFixedWidth(60)
        self.x_max_input.setFixedWidth(60)
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
        self.y_min_input.setFixedWidth(60)
        self.y_max_input.setFixedWidth(60)
        self.y_min_input.setPlaceholderText("min")
        self.y_max_input.setPlaceholderText("max")
        self.y_min_input.returnPressed.connect(self.apply_axis_limits)
        self.y_max_input.returnPressed.connect(self.apply_axis_limits)

        axis_bar.addWidget(self.y_min_input)
        axis_bar.addWidget(QLabel("to"))
        axis_bar.addWidget(self.y_max_input)

        reset_btn = QPushButton("↺")
        reset_btn.setFixedWidth(28)
        reset_btn.setToolTip("Reset axis limits")
        reset_btn.clicked.connect(self.reset_axis_limits)
        axis_bar.addWidget(reset_btn)
        axis_bar.addStretch()
        layout.addLayout(axis_bar)

        # Scroll and pan
        self.canvas.mpl_connect("scroll_event", self.on_scroll)
        self.canvas.mpl_connect("button_press_event", self.on_mouse_press)
        self.canvas.mpl_connect("button_release_event", self.on_mouse_release)
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)

        self._panning = False
        self._pan_start = None

    def expand_plot(self):
        if self.ax is None:
            return

        popup = QDialog(self)
        popup.setWindowTitle(f"FFT — {self.signal_name}")
        popup.setMinimumSize(900, 600)
        layout = QVBoxLayout(popup)

        # Create a new larger figure with same data
        expanded_fig = Figure(tight_layout=True)
        expanded_canvas = FigureCanvas(expanded_fig)
        ax = expanded_fig.add_subplot(111)

        ax.plot(self.freqs, self.fft_db, linewidth=0.8, color="#00bfff")
        ax.set_xlabel("Frequency (Hz)")
        ax.set_ylabel("Magnitude (dB)")
        ax.set_title(self.signal_name)
        ax.grid(True, linestyle="--", alpha=0.4)
        ax.set_facecolor("#1e1e1e")
        expanded_fig.patch.set_facecolor("#2a2a2a")
        ax.tick_params(colors="white")
        ax.xaxis.label.set_color("white")
        ax.yaxis.label.set_color("white")
        ax.title.set_color("white")
        ax.spines[:].set_color("#444444")

        # Re-draw peaks
        peak_indices = np.argsort(self.fft_db)[-3:][::-1]
        for idx in peak_indices:
            ax.annotate(
                f"{self.freqs[idx]:.1f} Hz",
                xy=(self.freqs[idx], self.fft_db[idx]),
                xytext=(5, 5),
                textcoords="offset points",
                color="yellow",
                fontsize=9
            )
            ax.plot(self.freqs[idx], self.fft_db[idx], "y^", markersize=6)

        layout.addWidget(expanded_canvas)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(popup.close)
        layout.addWidget(close_btn)

        expanded_canvas.draw()
        popup.exec()

    def save_plot(self):
        if self.ax is None:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Plot",
            f"{self.signal_name}_fft.png",
            "PNG Image (*.png);;JPEG Image (*.jpg);;All Files (*)"
        )

        if file_path:
            self.fig.savefig(
                file_path,
                dpi=150,
                bbox_inches="tight",
                facecolor=self.fig.get_facecolor()
            )
            print(f"Saved: {file_path}")

    def on_scroll(self, event):
        if self.ax is None or event.inaxes != self.ax:
            return
        zoom_factor = 1.2
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()
        x_range = x_max - x_min
        y_range = y_max - y_min
        x_mouse = event.xdata
        y_mouse = event.ydata
        if event.button == "up":
            new_x_range = x_range / zoom_factor
            new_y_range = y_range / zoom_factor
        else:
            new_x_range = x_range * zoom_factor
            new_y_range = y_range * zoom_factor
        ratio_x = (x_mouse - x_min) / x_range
        ratio_y = (y_mouse - y_min) / y_range
        self.ax.set_xlim([
            x_mouse - ratio_x * new_x_range,
            x_mouse + (1 - ratio_x) * new_x_range
        ])
        self.ax.set_ylim([
            y_mouse - ratio_y * new_y_range,
            y_mouse + (1 - ratio_y) * new_y_range
        ])
        self.update_axis_inputs()
        self.canvas.draw()

    def on_mouse_press(self, event):
        if self.ax is None or event.inaxes != self.ax:
            return
        if event.button == 1:
            self._panning = True
            self._pan_start = (event.xdata, event.ydata)

    def on_mouse_release(self, event):
        self._panning = False
        self._pan_start = None

    def on_mouse_move(self, event):
        if not self._panning or self._pan_start is None:
            return
        if self.ax is None or event.inaxes != self.ax:
            return
        dx = event.xdata - self._pan_start[0]
        dy = event.ydata - self._pan_start[1]
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()
        self.ax.set_xlim([x_min - dx, x_max - dx])
        self.ax.set_ylim([y_min - dy, y_max - dy])
        self.update_axis_inputs()
        self.canvas.draw()

    def apply_axis_limits(self):
        if self.ax is None:
            return
        try:
            x_min = float(self.x_min_input.text())
            x_max = float(self.x_max_input.text())
            self.ax.set_xlim([x_min, x_max])
        except ValueError:
            pass
        try:
            y_min = float(self.y_min_input.text())
            y_max = float(self.y_max_input.text())
            self.ax.set_ylim([y_min, y_max])
        except ValueError:
            pass
        self.canvas.draw()

    def reset_axis_limits(self):
        if self.ax is None or self.freqs is None:
            return
        self.ax.set_xlim([self.freqs[0], self.freqs[-1]])
        self.ax.relim()
        self.ax.autoscale_view()
        self.update_axis_inputs()
        self.canvas.draw()

    def update_axis_inputs(self):
        if self.ax is None:
            return
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()
        self.x_min_input.setText(f"{x_min:.1f}")
        self.x_max_input.setText(f"{x_max:.1f}")
        self.y_min_input.setText(f"{y_min:.1f}")
        self.y_max_input.setText(f"{y_max:.1f}")

    def plot_fft(self, signal, signal_name, sampling_rate):
        self.signal_name = signal_name
        self.title_label.setText(signal_name)
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)

        n = len(signal)
        window = windows.hann(n)
        windowed = signal * window

        fft_vals = np.fft.rfft(windowed)
        fft_mag = np.abs(fft_vals)
        self.fft_db = 20 * np.log10(fft_mag + 1e-10)
        self.freqs = np.fft.rfftfreq(n, d=1.0 / sampling_rate)

        self.ax.plot(self.freqs, self.fft_db, linewidth=0.8, color="#00bfff")
        self.ax.set_xlabel("Frequency (Hz)")
        self.ax.set_ylabel("Magnitude (dB)")
        self.ax.set_title(signal_name)
        self.ax.grid(True, linestyle="--", alpha=0.4)
        self.ax.set_facecolor("#1e1e1e")
        self.fig.patch.set_facecolor("#2a2a2a")
        self.ax.tick_params(colors="white")
        self.ax.xaxis.label.set_color("white")
        self.ax.yaxis.label.set_color("white")
        self.ax.title.set_color("white")
        self.ax.spines[:].set_color("#444444")

        peak_indices = np.argsort(self.fft_db)[-3:][::-1]
        for idx in peak_indices:
            self.ax.annotate(
                f"{self.freqs[idx]:.1f} Hz",
                xy=(self.freqs[idx], self.fft_db[idx]),
                xytext=(5, 5),
                textcoords="offset points",
                color="yellow",
                fontsize=7
            )
            self.ax.plot(self.freqs[idx], self.fft_db[idx], "y^", markersize=5)

        self.update_axis_inputs()
        self.canvas.draw()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FFT Signal Analyzer")
        self.setMinimumSize(1200, 900)
        self.df = None
        self.sampling_rate = None
        self.current_page = 0
        self.plots_per_page = 4
        self.selected_signals = []
        self.canvases = []
        self.canvas_widgets = []

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # --- File Browser Bar ---
        file_bar = QHBoxLayout()
        file_label = QLabel("File:")
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Browse to a CSV file...")
        self.file_path_input.setReadOnly(True)
        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.browse_file)
        file_bar.addWidget(file_label)
        file_bar.addWidget(self.file_path_input)
        file_bar.addWidget(browse_button)
        main_layout.addLayout(file_bar)

        # --- Two Panel Layout ---
        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(10)

        # Left Panel
        left_panel = QFrame()
        left_panel.setFrameShape(QFrame.Shape.StyledPanel)
        left_panel.setFixedWidth(220)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_layout.setSpacing(8)

        signals_label = QLabel("Signals")
        signals_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(signals_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.signal_list_widget = QWidget()
        self.signal_list_layout = QVBoxLayout(self.signal_list_widget)
        self.signal_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_area.setWidget(self.signal_list_widget)
        left_layout.addWidget(scroll_area)

        plots_label = QLabel("Plots per page:")
        plots_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(plots_label)

        plots_per_page_layout = QHBoxLayout()
        self.page_btn_group = QButtonGroup()
        for i in range(1, 5):
            btn = QPushButton(str(i))
            btn.setCheckable(True)
            btn.setFixedWidth(40)
            if i == 4:
                btn.setChecked(True)
            self.page_btn_group.addButton(btn, i)
            plots_per_page_layout.addWidget(btn)
        self.page_btn_group.idClicked.connect(self.on_plots_per_page_changed)
        left_layout.addLayout(plots_per_page_layout)

        plot_btn = QPushButton("Plot FFT")
        plot_btn.clicked.connect(self.plot_fft)
        left_layout.addWidget(plot_btn)

        # Right Panel
        right_panel = QFrame()
        right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        self.right_layout = QVBoxLayout(right_panel)
        self.right_layout.setContentsMargins(8, 8, 8, 8)
        self.right_layout.setSpacing(8)

        # Plot grid area
        self.plot_area = QWidget()
        self.plot_grid = QVBoxLayout(self.plot_area)
        self.right_layout.addWidget(self.plot_area)

        # Pagination bar
        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton("←")
        self.prev_btn.clicked.connect(self.prev_page)
        self.page_label = QLabel("Page 1 of 1")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_btn = QPushButton("→")
        self.next_btn.clicked.connect(self.next_page)
        pagination_layout.addStretch()
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addStretch()
        self.right_layout.addLayout(pagination_layout)

        # Placeholder
        self.plot_placeholder = QLabel("Load a CSV file and select signals to plot")
        self.plot_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.plot_grid.addWidget(self.plot_placeholder)

        panels_layout.addWidget(left_panel)
        panels_layout.addWidget(right_panel)
        main_layout.addLayout(panels_layout)

    def browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if file_path:
            self.file_path_input.setText(file_path)
            self.load_csv(file_path)

    def load_csv(self, file_path):
        try:
            self.df = pd.read_csv(file_path)
            self.df.columns = self.df.columns.str.strip()
            time_col = self.df.columns[0]
            time_values = self.df[time_col].values
            time_step = time_values[1] - time_values[0]
            self.sampling_rate = 1.0 / time_step
            print(f"Sampling rate detected: {self.sampling_rate} Hz")
            self.populate_signals()
        except Exception as e:
            print(f"Error loading CSV: {e}")

    def populate_signals(self):
        for i in reversed(range(self.signal_list_layout.count())):
            self.signal_list_layout.itemAt(i).widget().deleteLater()
        signal_columns = self.df.columns[1:]
        for col in signal_columns:
            checkbox = QCheckBox(col)
            self.signal_list_layout.addWidget(checkbox)

    def on_plots_per_page_changed(self, id):
        self.plots_per_page = id
        self.current_page = 0
        self.render_page()

    def get_selected_signals(self):
        selected = []
        for i in range(self.signal_list_layout.count()):
            checkbox = self.signal_list_layout.itemAt(i).widget()
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                selected.append(checkbox.text())
        return selected

    def plot_fft(self):
        self.selected_signals = self.get_selected_signals()
        if not self.selected_signals:
            print("No signals selected")
            return
        self.current_page = 0
        self.render_page()

    def clear_layout(self, layout):
        # First explicitly delete all tracked canvas widgets
        for widget in self.canvas_widgets:
            widget.setParent(None)
            widget.hide()
            widget.deleteLater()
        self.canvas_widgets = []

        # Then clear the layout
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

        if not self.selected_signals:
            return

        total_pages = max(1, -(-len(self.selected_signals) // self.plots_per_page))
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
                row_layout.setSpacing(8)
                self.plot_grid.addLayout(row_layout)

            canvas = PlotCanvas()
            signal_data = self.df[signal_name].values
            canvas.plot_fft(signal_data, signal_name, self.sampling_rate)
            self.canvas_widgets.append(canvas)
            row_layout.addWidget(canvas)

        if len(page_signals) % cols != 0 and row_layout:
            row_layout.addWidget(QWidget())

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