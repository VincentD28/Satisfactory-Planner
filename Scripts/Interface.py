# ==================================================== IMPORTS =====================================================
import sys
import os
import json
import math
import time
import html
from PySide6.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QMainWindow,
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QTabBar, QPushButton,
    QLineEdit, QListWidget, QListWidgetItem, QStackedWidget, QGraphicsOpacityEffect, QScrollArea,
    QToolButton,
    QGraphicsItem, QGraphicsRectItem, QGraphicsTextItem, QGraphicsPixmapItem, QGraphicsPathItem,
    QAbstractScrollArea,
    QGraphicsPolygonItem, QComboBox, QGraphicsDropShadowEffect, QSlider, QSizePolicy, QStyledItemDelegate,
    QGridLayout, QFileDialog
)
from PySide6.QtGui import (
    QPainter, QPainterPath, QPen, QBrush, QColor, QShortcut, QKeySequence, QIcon, QPixmap, QFont,
    QPolygonF, QTextOption, QImage, QFontMetrics, QRegularExpressionValidator, QLinearGradient,
    QTextCursor, QTextCharFormat, QCursor, QTransform, QPainterPathStroker
)
from PySide6.QtCore import (
    Qt, QTimer, QPoint, QPointF, QSize, QObject, QEvent, QLineF, QRect, QRectF, QItemSelectionModel,
    QPropertyAnimation, QVariantAnimation, QAbstractAnimation, QEasingCurve, QRegularExpression
)
import search
from search import (
    Node, Output_Node, Recipe_Node, Manual_Node, Power_Node, All_Items, All_Machines, All_Recipes,
    set_miner_mark, construction_report, recipes_report, supplied_items, POWER_ITEM, is_power_node,
    power_for, power_range_for
)
import data_maker
from data_maker import Machine


# ================================================== PANEL OPTIONS ===================================================
DEFAULT_MINER_MARK = 1
DEFAULT_CONVEYOR_LVL = 1
DEFAULT_PIPE_LVL = 1
MINER_MARK_OPTIONS = [1, 2, 3]
CONVEYOR_LVL_OPTIONS = [1, 2, 3, 4, 5, 6]
PIPE_LVL_OPTIONS = [1, 2]
MINER_MARK_PICTURES = {mark: All_Machines[f"Build_MinerMk{mark}_C"].picture for mark in MINER_MARK_OPTIONS}
CONVEYOR_LVL_PICTURES = {lvl: f"img/ConveyorMk{lvl}_512.png" for lvl in CONVEYOR_LVL_OPTIONS}
PIPE_LVL_PICTURES = {lvl: f"img/Pipeline_Mk.{lvl}.png" for lvl in PIPE_LVL_OPTIONS}

# ex.: outputs = [
#     {"item": All_Items["Desc_SpaceElevatorPart_9_C"], "rate": 1000},
#     {"item": All_Items["Desc_SpaceElevatorPart_10_C"], "rate": 1000},
#     {"item": All_Items["Desc_SpaceElevatorPart_11_C"], "rate": 256},
#     {"item": All_Items["Desc_SpaceElevatorPart_12_C"], "rate": 250}
# ]
test_output = {"item": All_Items["Desc_SpaceElevatorPart_1_C"], "rate": 1000}

DEFAULT_COMPACT = False      # boxes carry their name and numbers, not the picture alone
DEFAULT_LOCKED = False       # the graph can be dragged about and rebuilt
DEFAULT_QUICK_DONE = False   # a box is ticked off as built by double clicking it
DEFAULT_ARROW_MODE = "new"   # "new": fixed arrows built into the node; "old": one floating arrow per line
DEFAULT_SNAP = True        # dragged nodes land on the grid instead of anywhere
DEFAULT_PICTURE_MODE = "item"      # "machine": a recipe shows the building it runs in; "item": what it makes
DEFAULT_BUILD_REVEAL = "play"      # after Confirm: "start" on the first step, "play" through them, "skip" to the end
DEFAULT_SHOW_POWER = True          # the whole system's power draw shown on the graph

panel_options = {
    "output": [test_output],
    "miners_mark": DEFAULT_MINER_MARK,       # 1, 2, 3
    "conveyor_lvl": DEFAULT_CONVEYOR_LVL,    # 1, 2, 3, 4, 5, 6
    "pipe_lvl": DEFAULT_PIPE_LVL,            # 1, 2
    "arrow_mode": DEFAULT_ARROW_MODE,        # "new", "old"
    "snap": DEFAULT_SNAP,                    # True, False
    "picture_mode": DEFAULT_PICTURE_MODE,    # "machine", "item"
    "build_reveal": DEFAULT_BUILD_REVEAL,    # "start", "play", "skip"
    "show_power": DEFAULT_SHOW_POWER,        # True, False
    "compact": DEFAULT_COMPACT,              # True, False - boxes as just their picture
    "locked": DEFAULT_LOCKED,                # True, False - the graph held as it stands
    "quick_done": DEFAULT_QUICK_DONE,        # True, False - one click marks a box built
    "recipe_choices": {},                    # Item -> Recipe, picked on the Recipes page
    "node_recipe_choices": {},               # (Item, mother's Recipe) -> Recipe, picked on one node
}


# ====================================================== TEXT =======================================================
# Every piece of text in the app takes its color from these few levels, so the
# same importance always reads the same everywhere. None is pure white - that
# glares on the dark grounds - and each step down is a quieter, less important
# kind of text. The accent blue marks text that informs rather than labels.
TEXT_STRONG = "#e2e2e2"     # what matters most: titles, what is selected, typed values, node names
TEXT_NORMAL = "#bababa"     # ordinary reading text: labels, recipe names, list items
TEXT_MUTED = "#8a8a8a"      # supporting text: section titles, options not picked, idle symbols
TEXT_FAINT = "#6c6c6c"      # the quietest still worth reading: units, coordinates, small captions
TEXT_DISABLED = "#4f4f4f"   # something that cannot be used right now
TEXT_ACCENT = "#6fb3e3"     # the accent, softened for text: stats and other information
TEXT_ON_ACCENT = "#f0f0f0"  # text sitting on the solid accent, a button's label

# the one typeface for all of it, set on the app so every widget and every
# piece of text in the graph takes it without asking. Bahnschrift comes with
# Windows 10 and 11 - a plain engineering face, at home in a factory planner;
# on a machine without it, the next one down is used.
APP_FONT_FAMILIES = ["Bahnschrift", "Segoe UI", "Arial"]

def apply_app_font(app):
    font = QFont(app.font())
    font.setFamilies(APP_FONT_FAMILIES)
    app.setFont(font)

# =================================================== ANIMATIONS ====================================================
ANIMATION_MS = 140          # anything appearing, moving or leaving
ANIMATION_CURVE = QEasingCurve.OutCubic
ZOOM_MS = 110
RECENTER_MS = 260
CAMERA_AT_START_PX = 4       # how near the reset framing, on screen, still counts as at it
CAMERA_AT_START_ZOOM = 0.01  # ...and how near its zoom, as a share of it
MOVING_SETTLE_MS = 90       # how soon after the last move the view redraws in full
ROLL_MS = 180               # a card unrolling into its list, or rolling up out of it
PULSE_MS = 220              # a control flashing as it changes mode
PULSE_LOW = 0.35            # the opacity it dips to
QWIDGETSIZE_MAX = 16777215  # Qt's "no maximum" for a widget's size
TAB_SLIDE_MS = 170          # a project tab sliding open or shut
RENAME_SLIDE_MS = 160       # the rename box dropping out of the tab bar
RENAME_GAP = 2              # space between the tab and the rename box
RENAME_MIN_WIDTH = 90       # so a short name still gets a usable box
RENAME_PADDING = 28         # room around the text inside the box

# An animation with no reference is garbage collected mid flight and simply stops,
# so every one of these is parented to the widget it animates and told to delete
# itself once finished.
def run(animation, curve=ANIMATION_CURVE):
    animation.setEasingCurve(curve)
    animation.start(QAbstractAnimation.DeleteWhenStopped)
    return animation

def fade_in(widget, duration=ANIMATION_MS):
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    widget.show()
    animation = QPropertyAnimation(effect, b"opacity", widget)
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    # dropping the effect afterwards keeps the widget rendering normally
    animation.finished.connect(lambda: widget.setGraphicsEffect(None))
    return run(animation)

def fade_out(widget, duration=ANIMATION_MS, on_done=None):
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    animation = QPropertyAnimation(effect, b"opacity", widget)
    animation.setDuration(duration)
    animation.setStartValue(1.0)
    animation.setEndValue(0.0)

    def finish():
        widget.setGraphicsEffect(None)
        if on_done is None:
            widget.hide()
        else:
            on_done()

    animation.finished.connect(finish)
    return run(animation)

# a widget coming in by unrolling: its height grows from nothing to its own
# while it fades in, the rows under it easing down to make room instead of
# jumping. Its height is let go again once there.
def unroll(widget, duration=ROLL_MS):
    target = max(1, widget.sizeHint().height())
    widget.setMaximumHeight(0)
    grow = QPropertyAnimation(widget, b"maximumHeight", widget)
    grow.setDuration(duration)
    grow.setStartValue(0)
    grow.setEndValue(target)
    grow.finished.connect(lambda: widget.setMaximumHeight(QWIDGETSIZE_MAX))
    fade_in(widget, duration)
    return run(grow)

# the other way: rolled up to nothing as it fades, `on_done` once gone
def roll_up(widget, on_done, duration=ROLL_MS):
    shrink = QPropertyAnimation(widget, b"maximumHeight", widget)
    shrink.setDuration(duration)
    shrink.setStartValue(widget.height())
    shrink.setEndValue(0)
    shrink.finished.connect(on_done)
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    fade = QPropertyAnimation(effect, b"opacity", widget)
    fade.setDuration(duration)
    fade.setStartValue(1.0)
    fade.setEndValue(0.0)
    run(fade)
    return run(shrink)

# a quick dip and return of a widget's opacity, for something that just
# changed where it stands - a toggle flipping to its next mode
def pulse(widget, duration=PULSE_MS):
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    animation = QPropertyAnimation(effect, b"opacity", widget)
    animation.setDuration(duration)
    animation.setKeyValueAt(0.0, PULSE_LOW)
    animation.setKeyValueAt(1.0, 1.0)
    animation.finished.connect(lambda: widget.setGraphicsEffect(None))
    return run(animation)

# a top level popup window fading in as it opens (a window fades through its
# own opacity, not through a graphics effect)
def fade_window_in(window, duration=ANIMATION_MS):
    window.setWindowOpacity(0.0)
    animation = QPropertyAnimation(window, b"windowOpacity", window)
    animation.setDuration(duration)
    animation.setStartValue(0.0)
    animation.setEndValue(1.0)
    return run(animation)

# for values that are not Qt properties, such as scroll offsets or a zoom level
def animate_value(owner, start, end, on_step, duration=ANIMATION_MS, curve=ANIMATION_CURVE):
    animation = QVariantAnimation(owner)
    animation.setDuration(duration)
    animation.setStartValue(float(start))
    animation.setEndValue(float(end))
    animation.valueChanged.connect(on_step)
    return run(animation, curve)


# ================================================ THE APP'S ACCENT =================================================
# Blue while you are planning what to make, the power yellow while you are
# planning how to power it: the whole of the app's chrome turns with the
# panel's own tabs, so which half you are working in reads at a glance.
#
# Every accent-colored stylesheet is written with the blue shades below, and
# switching swaps those four strings for the yellow ones wherever they appear,
# rather than every button having to be built again. Anything made after a
# switch is painted on the spot (see paint_accent).
# The yellow is a softened amber rather than the map's own power yellow: a
# screenful of chrome in that is hard on the eye, where one node in it is not.
ACCENT_SHADES = {
    "blue":   {"base": "#3498db", "hover": "#2f88c4", "press": "#2a79ad", "text": "#6fb3e3",
               "active": "rgba(52, 152, 219, 0.35)", "active_hover": "rgba(52, 152, 219, 0.50)",
               "banner": "#2c3e50"},
    # the banner shades are the same dark, unsaturated version of each hue, so
    # the bar reads the same weight in either
    "yellow": {"base": "#e0b23c", "hover": "#c99d31", "press": "#a88027", "text": "#f0cf7a",
               "active": "rgba(224, 178, 60, 0.35)", "active_hover": "rgba(224, 178, 60, 0.50)",
               "banner": "#4f462b"},
}
# The switch is made in one go rather than eased from the one color to the
# other. A fade has to rewrite every accent-colored stylesheet in the window on
# every one of its frames, and Qt re-polishes each widget it is set on - a
# tab that answers at once reads cleaner than a screenful of chrome crawling
# between two hues, and costs one repaint instead of a dozen.
_accent = {"name": "blue", "shades": dict(ACCENT_SHADES["blue"])}

def accent_name():
    return _accent["name"]

# the accent as it stands now, for a drawn icon: a stylesheet's shades are
# swapped for it (see swap_shades), but a painted glyph has to ask
def accent_shade(shade="base"):
    return _accent["shades"][shade]

# swaps one set of accent shades for another wherever they are written, over
# the widgets given
def swap_shades(widgets, old, new):
    for widget in widgets:
        sheet = widget.styleSheet()
        swapped = sheet
        for shade in old:
            swapped = swapped.replace(old[shade], new[shade])
        if swapped != sheet:
            widget.setStyleSheet(swapped)

# anything marked fixed_accent keeps the color it was built with - a tab's own
# count badge, which says which list it belongs to rather than which one is open
def accent_widgets(root, shades):
    return [widget for widget in [root] + root.findChildren(QWidget)
            if widget.styleSheet() and not widget.property("fixed_accent")
            and any(shade in widget.styleSheet() for shade in shades.values())]

# every widget of the tree given the accent as it stands now - for anything
# built after a switch
def paint_accent(root):
    if root is None or _accent["shades"] == ACCENT_SHADES["blue"]:
        return
    swap_shades(accent_widgets(root, ACCENT_SHADES["blue"]), ACCENT_SHADES["blue"], _accent["shades"])

# the whole app's accent, switched to the one asked for
def set_accent(name, root):
    if name == accent_name() or root is None:
        return
    start, end = _accent["shades"], ACCENT_SHADES[name]
    swap_shades(accent_widgets(root, start), start, end)
    _accent.update(name=name, shades=dict(end))

# ================================================== SAVED APP STATE ================================================
# Everything the app was showing when it was last closed, kept in a file beside
# it: the options, and every project with its outputs, where its boxes were
# dragged to and which step it was parked on. Reopening reads it back and puts
# the same thing on screen.
#
# A build is reproducible - the same outputs always come out the same graph
# (see generate_node_graph) - so a project is saved as what was asked for
# rather than as the tree that came of it, and rebuilt on the way back in.
# Only what was moved by hand has to be remembered on top of that, node by node.
# beside the exe when this is a built app, beside the scripts when it is not
APPDATA_FILE = data_maker.kept_file("appdata.json")
APPDATA_SAVE_DELAY = 700   # ms of quiet before a change is written out

# What a node is, apart from the objects of one build: a build makes its nodes
# again from scratch, so the one running a recipe in the new tree is a
# different object from the one that ran it in the old. A recipe is only ever
# run by one node (they merge), an output is its item, and a hand source the
# item it brings in - and the same key twice over is numbered, so two outputs
# of one item keep their own spots.
def node_key(node):
    if is_power_node(node):
        return "power"
    if isinstance(node, Recipe_Node):
        return f"recipe:{node.recipe.full_name}"
    item = getattr(node, "item", None)
    name = item.full_name if item is not None else "?"
    if isinstance(node, Output_Node):
        return f"{'byproduct' if node.is_byproduct else 'output'}:{name}"
    return f"source:{name}"

def node_positions(nodes):
    spots, seen = {}, {}
    for node in nodes:
        key = node_key(node)
        seen[key] = seen.get(key, 0) + 1
        spots[f"{key}#{seen[key]}"] = [node.coordinate[0], node.coordinate[1]]
    return spots

# the nodes of a fresh build put back where the saved ones stood
def apply_positions(nodes, spots):
    seen = {}
    for node in nodes:
        key = node_key(node)
        seen[key] = seen.get(key, 0) + 1
        spot = spots.get(f"{key}#{seen[key]}")
        if spot:
            node.coordinate = (spot[0], spot[1])

# items and recipes travel as their own names: the objects are rebuilt from the
# game data on every run, so nothing but a name means the same thing twice
def saved_options():
    return {
        "miners_mark": panel_options["miners_mark"],
        "conveyor_lvl": panel_options["conveyor_lvl"],
        "pipe_lvl": panel_options["pipe_lvl"],
        "arrow_mode": panel_options["arrow_mode"],
        "snap": panel_options["snap"],
        "picture_mode": panel_options["picture_mode"],
        "build_reveal": panel_options["build_reveal"],
        "show_power": panel_options["show_power"],
        "compact": panel_options["compact"],
        "locked": panel_options["locked"],
        "quick_done": panel_options["quick_done"],
        "recipe_choices": {item.full_name: recipe.full_name
                           for item, recipe in panel_options["recipe_choices"].items()},
        "node_recipe_choices": [[item.full_name, mother.full_name, recipe.full_name]
                                for (item, mother), recipe in panel_options["node_recipe_choices"].items()],
    }

def load_options(saved):
    for key in ("miners_mark", "conveyor_lvl", "pipe_lvl", "arrow_mode",
                "snap", "picture_mode", "build_reveal", "show_power",
                "locked", "quick_done", "compact"):
        if key in saved:
            panel_options[key] = saved[key]
    panel_options["recipe_choices"] = {
        All_Items[item]: All_Recipes[recipe]
        for item, recipe in saved.get("recipe_choices", {}).items()
        if item in All_Items and recipe in All_Recipes}
    panel_options["node_recipe_choices"] = {
        (All_Items[item], All_Recipes[mother]): All_Recipes[recipe]
        for item, mother, recipe in saved.get("node_recipe_choices", [])
        if item in All_Items and mother in All_Recipes and recipe in All_Recipes}

def saved_project(page):
    if not page.loaded():
        return {**page.saved, "name": page.project_name, "color": page.tab_color}
    cards =[{"item": entry["item"].full_name,
              "rate": entry["get_rate"](),
              "recipe": entry["get_recipe"]().full_name if entry["get_recipe"]() else None,
              "side": entry["side"]}
             for entry in page.panel.cards()]
    view = page.view
    steps = getattr(view, "build_steps", None)
    project = {"name": page.project_name, "color": page.tab_color,
               "outputs": cards, "built": bool(steps)}
    if steps:
        project["positions"] = node_positions(steps[-1]["nodes"])
        project["step"] = view.build_step
        # how far in it was zoomed as well as where it was looking: a graph
        # put back at the zoom its new scene happens to be fitted to is not
        # the view that was left behind
        project["camera"] = [view.horizontalScrollBar().value(),
                             view.verticalScrollBar().value(), view.zoom]
    # what has been built already outlives the tree it was ticked off on, so it
    # is kept whether or not this project has a build standing
    done = getattr(view, "completed", None)
    if done:
        project["built_nodes"] = sorted(done)
    return project

def save_appdata(window):
    try:
        pages = window.project_pages()
        data = {"options": saved_options(),
                "game_path": window.game_path(),
                "window": [window.width(), window.height()],
                "current": window.current_project(),
                "projects": [saved_project(page) for page in pages]}
        with open(APPDATA_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=1)
    except Exception:
        pass   # a planner that cannot write its file still has a factory to draw

def read_appdata():
    try:
        with open(APPDATA_FILE, encoding="utf-8") as file:
            return json.load(file) or {}
    except Exception:
        return {}   # nothing saved yet, or a file that is no longer readable

# every change asks for a save and the last one within APPDATA_SAVE_DELAY does
# it: a drag would otherwise write the file on every pixel of the way
_save_timer = [None]

def schedule_save():
    window = next((w for w in QApplication.topLevelWidgets() if isinstance(w, MainWindow)), None)
    if window is None:
        return
    if _save_timer[0] is None:
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: save_appdata(window))
        _save_timer[0] = timer
    _save_timer[0].start(APPDATA_SAVE_DELAY)

# ================================================= FULL SCREEN ====================================================
# It rides at the right end of the tab row rather than on a band of its own:
# the row already runs the width of the window and has the height to hold it,
# and one strip of chrome over the page reads quieter than two. F11 does the
# same thing (see MainWindow).
# It is built like a tab of its own: the same square as home at the other
# end of the row, sitting under the same gap, with the same rounded top and
# the ground a closed tab stands on.
def full_screen_width():      # the tab constants are written further down
    return PROJECT_TABS_HEIGHT - TAB_TOP_GAP + 2
FULL_SCREEN_SYMBOL_SIZE = 18
FULL_SCREEN_SIDE_MARGIN = 9     # the same room either side of the button

# A tab of its own at the far end of the row: the same square as home, cut
# to the same shape, with the plain color line along its top. Switched on -
# the window in full screen - that color runs into the button itself, the way
# a project's color fills its tab when it is the one open.
class FullScreenButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.on = False
        # how far its color has run down from the line, 0 to 1, exactly as a
        # tab's does when it is picked (see ReleaseTabBar.tab_ground)
        self.spread = 0.0
        self.spreading = None
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedSize(full_screen_width(), PROJECT_TABS_HEIGHT)
        self.setAttribute(Qt.WA_Hover, True)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        box = QRectF(self.rect()).adjusted(1, TAB_TOP_GAP, -1, 0)
        shape = tab_shape_of(box)
        # it stands on the corner's grey, so it is the darker of the two at
        # rest and lights up under the mouse
        if self.isDown():
            ground = blend_color(TAB_CLOSED_GROUND, QColor(TAB_DEFAULT_COLOR), 0.4)
        elif self.underMouse():
            ground = blend_color(TAB_CLOSED_GROUND, QColor(TAB_DEFAULT_COLOR), 0.7)
        else:
            ground = QColor(TAB_CLOSED_GROUND)
        painter.fillPath(shape, ground)

        # switched on, its color runs down out of that line and fills it, and
        # back up out of it when it is switched off
        if self.spread > 0:
            box = shape.boundingRect()
            filling = QPainterPath()
            filling.addRect(QRectF(box.left(), box.top(), box.width(), box.height() * self.spread))
            painter.fillPath(shape.intersected(filling), QColor(TAB_DEFAULT_COLOR))
        painter.fillPath(tab_line_of(shape.boundingRect()), QColor(TAB_DEFAULT_COLOR))

        # the corners point out to go full screen, and in to come back from it
        painter.save()
        scale = FULL_SCREEN_SYMBOL_SIZE / SYMBOL_CANVAS
        middle = shape.boundingRect().center()
        painter.translate(middle.x() - FULL_SCREEN_SYMBOL_SIZE / 2,
                          middle.y() - FULL_SCREEN_SYMBOL_SIZE / 2)
        painter.scale(scale, scale)
        draw_corners(painter, QColor(TEXT_STRONG if self.underMouse() or self.on else TAB_SYMBOL_COLOR),
                     self.on)
        painter.restore()
        painter.end()


    # the color easing down the button, or back up off it
    def ease_spread(self, to):
        if self.spreading is not None:
            try:
                self.spreading.stop()   # Qt drops a finished one on its own
            except RuntimeError:
                pass
            self.spreading = None

        def step(value):
            self.spread = float(value)
            self.update()

        self.spreading = animate_value(self, self.spread, to, step, TAB_GROW_MS, TAB_GROW_CURVE)


# The right end of the row, kept for the full screen button: the row's own
# ground, parted from the tabs by a line and nothing else, and the row of
# tabs stopped short of it so no tab can ever run under the button.
FULL_SCREEN_WALL = "#3d3d3d"        # the line parting the two
FULL_SCREEN_WALL_WIDTH = 1

class FullScreenCorner(QWidget):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(TAB_BAR_BG))
        painter.fillRect(0, 0, FULL_SCREEN_WALL_WIDTH, self.height(), QColor(FULL_SCREEN_WALL))
        painter.end()


def corner_width():
    return full_screen_width() + 2 * FULL_SCREEN_SIDE_MARGIN + FULL_SCREEN_WALL_WIDTH


def make_full_screen_button(parent=None):
    button = FullScreenButton(parent)

    def show_state(eased=True):
        button.on = button.window().isFullScreen()
        button.setToolTip("Leave full screen (F11)" if button.on else "Full screen (F11)")
        if eased:
            button.ease_spread(1.0 if button.on else 0.0)
        else:
            button.spread = 1.0 if button.on else 0.0
        button.update()

    # back to whatever it was before: a maximized window comes back maximized
    def toggle():
        window = button.window()
        if window.isFullScreen():
            if getattr(window, "was_maximized", False):
                window.showMaximized()
            else:
                window.showNormal()
        else:
            window.was_maximized = window.isMaximized()
            window.showFullScreen()
        show_state()

    button.clicked.connect(toggle)
    button.toggle_full_screen = toggle
    button.show_full_screen_state = show_state
    show_state(eased=False)
    return button

# =================================================== PROJECT TABS ==================================================
PROJECT_TABS_HEIGHT = 44
PLUS_TAB_LABEL = "+"
HOME_TAB_KEY = "home"          # its tabData: the one tab that is neither a project nor the "+"
HOME_ICON_SIZE = 18
TAB_SYMBOL_SIZE = 18
TAB_CLOSE_SYMBOL_SIZE = 14      # the drawn cross closing a tab, near its whole button
CLOSE_SYMBOL_STROKE = 1.8       # on the 16 unit square the cross is drawn on
TAB_SYMBOL_COLOR = TEXT_MUTED
TAB_SYMBOL_HOVER_COLOR = TEXT_NORMAL
TAB_SYMBOL_HOVER_BG = "rgba(255, 255, 255, 0.12)"
TAB_SYMBOL_PRESS_BG = "rgba(0, 0, 0, 0.18)"        # flat buttons, darkened while held down
ACCENT_PRESS_BG = ACCENT_SHADES["blue"]["press"]   # filled accent buttons, darkened while held down
TAB_PRESS_OVERLAY = (0, 0, 0, 90)                  # RGBA painted over a held down tab
TAB_DIVIDER = (255, 255, 255, 36)                  # RGBA of the line parting two tabs
TAB_DIVIDER_HEIGHT = 18                            # shorter than the tab, centred on it
CLOSE_BUTTON_MARGIN = 8  # spacing on both sides of the "-" button
CLOSE_BUTTON_HOVER_BG = "rgba(255, 255, 255, 0.3)"  # stronger than the tab's own hover, so it stands out
CLOSE_BUTTON_HOVER_COLOR = TEXT_STRONG
TAB_FONT_SIZE = 15
TAB_SELECTED_FONT_SIZE = 15
TAB_SELECTED_COLOR = TEXT_STRONG
TAB_UNSELECTED_COLOR = TEXT_MUTED
TAB_INDICATOR_COLOR = ACCENT_SHADES["blue"]["base"]
# The row is a shade under the canvas, and the open tab is cut from the canvas
# itself: the same ground, rounded over the top and running straight on into
# the page under it, so it reads as the front of that page rather than as a
# label sitting over it. The accent runs along its top edge.
TAB_BAR_BG = "#1a1a1a"
TAB_OPEN_BG = "#2a2a2a"             # the right panel's own ground (PANEL_BG)
TAB_HOVER_BG = "rgba(255, 255, 255, 0.05)"
TAB_TOP_GAP = 10                    # the row's ground left showing over each tab
TAB_SELECTED_TOP_GAP = TAB_TOP_GAP  # the open tab stands no taller            # less over the open one: it stands taller than the rest
# The open tab stands taller than the rest, and that is what is eased when
# the tab changes: the one being left settles back down while the one picked
# rises. Its width answers at once, so a click is never waited on.
TAB_GROW_MS = 200
# Most of the move is made in the first instants and the rest closes on the
# end: t(1+k) / (1+kt), a rational curve with the ceiling built in. A tab
# clicked answers at once - which is what makes the row feel quick - while
# nothing lands with a snap. Raise TAB_GROW_SNAP for a sharper answer.
TAB_GROW_SNAP = 7

def snap_curve(snap):
    curve = QEasingCurve(QEasingCurve.Custom)
    curve.setCustomType(lambda t: t * (1 + snap) / (1 + snap * t))
    return curve
TAB_GROW_CURVE = snap_curve(TAB_GROW_SNAP)
# Every tab carries a color of its own, picked beside its name (see
# start_rename). The tabs themselves stay grey - the open one a step brighter
# than the rest - and the color is worn by the band under the row, which is
# where the project it belongs to begins.
TAB_CLOSED_GROUND = TAB_BAR_BG      # a closed tab sits on the row's own ground
TAB_DEFAULT_COLOR = TAB_OPEN_BG     # the plain grey of an uncolored tab, and of its band
TAB_LINE_WIDTH = 5                  # the color a tab wears along its top, at its thickest
TAB_LINE_TAIL = 3                   # how far past the corner it runs before it has thinned away
TAB_LINE_TAPER = 1.0                # the share of each corner it thins over: all of it
TAB_LINE_STEPS = 48                 # points it is drawn from, along the tab's own top edge
TAB_PAGE_FADE_MS = 120              # the page left behind, fading off the one opened
TAB_COLOR_SQUARE = 20               # the swatch beside the name box
TAB_COLOR_SWATCH_GAP = 6
# The colors to pick from: the whole rainbow along one slider, held to a
# lightness that sits well on the dark chrome. Its first step is the plain
# grey, for a project that wants no color of its own.
TAB_COLOR_SATURATION = 120
TAB_COLOR_VALUE = 140      # kept dark, so a name on it stays easy to read
TAB_COLOR_SLIDER_WIDTH = 190
TAB_COLOR_SLIDER_HEIGHT = 18

# A tab's color is picked on three sliders: its hue, how much of that hue it
# carries (contrast: none of it is a plain grey), and how light it is. The
# greys come of the contrast slider at rest, so the whole grey scale is there
# without a palette of its own.
TAB_HUE_STEPS = 359
TAB_CONTRAST_STEPS = 255
TAB_BRIGHTNESS_LOW = 40         # never black: a tab has to carry its name

def tab_color_from(hue, contrast, brightness):
    return QColor.fromHsv(max(0, min(hue, TAB_HUE_STEPS)),
                          max(0, min(contrast, TAB_CONTRAST_STEPS)),
                          max(TAB_BRIGHTNESS_LOW, min(brightness, 255))).name()

# where a color stands on the three of them, for them to open where the tab is
def tab_color_parts(color):
    color = QColor(color)
    return max(color.hue(), 0), color.saturation(), max(color.value(), TAB_BRIGHTNESS_LOW)

# what each slider's own ground shows: the hue's whole rainbow, the contrast
# from grey to the hue in full, and the brightness from near-black up to it
def tab_slider_gradient(which, hue, contrast, brightness):
    stops = []
    for step in range(13):
        at = step / 12
        if which == "hue":
            shown = tab_color_from(round(at * TAB_HUE_STEPS), max(contrast, 90), brightness)
        elif which == "contrast":
            shown = tab_color_from(hue, round(at * TAB_CONTRAST_STEPS), brightness)
        else:
            shown = tab_color_from(hue, contrast, round(TAB_BRIGHTNESS_LOW + at * (255 - TAB_BRIGHTNESS_LOW)))
        stops.append(f"stop: {at:.3f} {shown}")
    return "qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, " + ", ".join(stops) + ")"
TAB_CORNER_RADIUS = 14
TAB_INDICATOR_WIDTH = 2
TAB_PAGE_LINE_WIDTH = PROJECT_TABS_HEIGHT // 3   # the open tab's grey, run along under the whole row
TAB_SIDE_PADDING = 12               # room either side of a project's name
TAB_PLUS_FONT_SIZE = 24             # the "+" that opens a new project: a button, sized like one
TAB_MAX_WIDTH = 170                 # past this a long name is cut short rather than the tab growing
TAB_MIN_WIDTH = 92                  # name and the room after it: a short name still gets a proper tab
TAB_SELECTED_MIN_WIDTH = 132
HOVER_BORDER_RADIUS = 4  # rounded-square, not a full circle
EMPTY_STATE_BG = "#3a3a3a"  # shown on the "+" tab when there are no projects
HOME_BG = TAB_OPEN_BG
HOME_COG_COLOR = "#3d3d3d"
HOME_COG_SIZE = 0.5        # of the page's shorter side
HOME_COG_TEETH = 10


def paint_home_cog(painter, center, radius, turned=0.0):
    if radius < 8:
        return
    cog = QPainterPath()
    cog.addEllipse(QPointF(0, 0), radius * 0.78, radius * 0.78)
    tooth_width = radius * 0.28
    for tooth in range(HOME_COG_TEETH):
        shape = QPainterPath()
        shape.addRoundedRect(QRectF(-tooth_width / 2, -radius, tooth_width, radius * 0.4),
                             tooth_width * 0.2, tooth_width * 0.2)
        cog = cog.united(QTransform().rotate(tooth * 360 / HOME_COG_TEETH).map(shape))
    hole = QPainterPath()
    hole.addEllipse(QPointF(0, 0), radius * 0.34, radius * 0.34)
    painter.save()
    painter.translate(center)
    painter.rotate(turned)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(HOME_COG_COLOR))
    painter.drawPath(cog.subtracted(hole))
    painter.restore()


# Where the game keeps the file this planner is built from, under whatever
# was pointed at: the file itself, the Docs folder, the install, or the Steam
# library above it. Whichever it is, the walk down to en-CA.json is the same.
GAME_DOCS_TAIL = ("CommunityResources", "Docs", "en-CA.json")
GAME_DOCS_FOLDERS = (
    (),
    ("Satisfactory",),
    ("common", "Satisfactory"),
    ("steamapps", "common", "Satisfactory"),
    ("steamapps", "common", "Satisfactory"),
)

def find_game_docs(pointed_at):
    pointed_at = (pointed_at or "").strip().strip('"')
    if not pointed_at:
        return ""
    if os.path.isfile(pointed_at):
        return pointed_at if pointed_at.lower().endswith(".json") else ""
    if not os.path.isdir(pointed_at):
        return ""
    # the Docs folder itself, or anything above it down to the library root
    for above in GAME_DOCS_FOLDERS:
        whole = os.path.join(pointed_at, *above, *GAME_DOCS_TAIL)
        if os.path.isfile(whole):
            return whole
    beside = os.path.join(pointed_at, "en-CA.json")
    return beside if os.path.isfile(beside) else ""

# what the cleaned data now in use was built from, and whether that is still
# what the game holds
def data_source_record():
    return data_maker.source_record()

def data_is_current(docs):
    if not docs or not os.path.isfile(docs):
        return None      # nothing to compare against
    record = data_source_record()
    if not record.get("fingerprint"):
        return False     # never built from a file we can name
    try:
        return data_maker.fingerprint(docs) == record["fingerprint"]
    except OSError:
        return None


HOME_TITLE_SIZE = 22
HOME_LABEL_SIZE = 13
HOME_FIELD_WIDTH = 520
HOME_ROW_HEIGHT = 30


class HomePage(QWidget):
    def __init__(self):
        super().__init__()
        self.build_data_box()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(HOME_BG))
        paint_home_cog(painter, QRectF(self.rect()).center(), min(self.width(), self.height()) * HOME_COG_SIZE / 2)
        painter.end()

    # The game's own files, and whether what this planner knows still matches
    # them: a box to say where the game is, and a button that lights up when
    # the game has been updated since the data was last made from it.
    def build_data_box(self):
        around = QVBoxLayout(self)
        around.setContentsMargins(40, 40, 40, 40)
        around.addStretch()

        box = QVBoxLayout()
        box.setSpacing(8)
        title = QLabel("Game data")
        title.setStyleSheet(f"color: {TEXT_STRONG}; font-size: {HOME_TITLE_SIZE}px; font-weight: bold;"
                            " background: transparent;")
        box.addWidget(title, 0, Qt.AlignHCenter)

        told = QLabel("Point to the Satisfactory folder")
        told.setStyleSheet(f"color: {TEXT_MUTED}; font-size: {HOME_LABEL_SIZE}px; background: transparent;")
        box.addWidget(told, 0, Qt.AlignHCenter)

        row = QHBoxLayout()
        row.setSpacing(8)
        row.addStretch()      # the field and its button sit in the middle
        self.path_field = QLineEdit()
        self.path_field.setFixedSize(HOME_FIELD_WIDTH, HOME_ROW_HEIGHT)
        self.path_field.setPlaceholderText(data_maker.GAME_DOCS)
        self.path_field.setStyleSheet(
            "QLineEdit {"
            f"  background: {MENU_BG}; color: {TEXT_NORMAL};"
            f"  border: 1px solid {OUTPUT_FIELD_BORDER}; border-radius: {HOVER_BORDER_RADIUS}px;"
            f"  padding: 0 8px; font-size: {HOME_LABEL_SIZE}px;"
            "}"
        )
        self.path_field.textChanged.connect(self.look_again)
        row.addWidget(self.path_field)

        browse = QPushButton("Browse...")
        browse.setFixedHeight(HOME_ROW_HEIGHT)
        browse.setCursor(Qt.PointingHandCursor)
        browse.setStyleSheet(
            "QPushButton {"
            f"  background: {CANCEL_BUTTON_BG}; color: {TEXT_STRONG};"
            f"  border: none; border-radius: {HOVER_BORDER_RADIUS}px; padding: 0 14px;"
            f"  font-size: {HOME_LABEL_SIZE}px;"
            "}"
            f"QPushButton:hover {{ background: {CANCEL_BUTTON_HOVER_BG}; }}"
            f"QPushButton:pressed {{ background: {CANCEL_BUTTON_PRESS_BG}; }}"
        )
        browse.clicked.connect(self.go_looking)
        row.addWidget(browse)
        row.addStretch()
        box.addLayout(row)

        # what the planner's own data was made from, whatever the field says
        self.built_from = QLabel("")
        self.built_from.setStyleSheet(
            f"color: {TEXT_FAINT}; font-size: {HOME_LABEL_SIZE}px; background: transparent;")
        box.addWidget(self.built_from, 0, Qt.AlignHCenter)

        self.state = QLabel("")
        self.state.setStyleSheet(f"color: {TEXT_MUTED}; font-size: {HOME_LABEL_SIZE}px; background: transparent;")
        box.addWidget(self.state, 0, Qt.AlignHCenter)

        self.update_button = QPushButton("Update data")
        self.update_button.setFixedHeight(HOME_ROW_HEIGHT + 4)
        self.update_button.setCursor(Qt.PointingHandCursor)
        self.update_button.clicked.connect(self.update_data)
        box.addWidget(self.update_button, 0, Qt.AlignHCenter)

        around.addLayout(box)
        around.addStretch()

        self.found = ""
        self.path_field.setText(read_appdata().get("game_path", ""))
        self.look_again()

    def go_looking(self):
        start = self.path_field.text().strip() or os.path.dirname(data_maker.GAME_DOCS)
        picked = QFileDialog.getExistingDirectory(self, "Where Satisfactory is installed", start)
        if picked:
            self.path_field.setText(picked)

    # what the field points at now, and what that means for the data
    def look_again(self):
        self.found = find_game_docs(self.path_field.text())
        typed = self.path_field.text().strip()
        # the three it can be in: nothing to work from, the game found but
        # holding the same data as this planner already has, or the game
        # holding something new - the only one worth pressing the button for
        # what this planner's own data came from, said plainly whatever the
        # field holds. Data made before the version was noted has it filled
        # in here, while the file it was made from is still there to ask.
        if self.found and data_is_current(self.found):
            data_maker.remember_version(self.found)
        record = data_source_record()
        was = record.get("version")
        self.built_from.setText(f"This planner's data: game {was}" if was
                                else "This planner's data: version unknown")

        if not typed:
            self.say("No folder given yet", level="off")
        elif not self.found:
            self.say("No game data in that folder", level="off")
        else:
            current = data_is_current(self.found)
            found = data_maker.game_version(self.found).get("version")
            named = f"game {found}" if found else "that game"
            if current:
                self.say(f"Up to date with {named} - an update would read the same data again",
                         level="dim")
            elif current is None:
                self.say("Game found, but its data cannot be read", level="off")
            elif found and was and found != was:
                self.say(f"An update moves this planner from game {was} to {found}", level="on")
            else:
                self.say(f"An update reads new data from {named}", level="on")
        schedule_save()

    # `level` is the state the button is in: "off" with nothing to work from,
    # "dim" with the game found but nothing new in it, and "on" - the accent,
    # and the only one that can be pressed - when its data has moved on.
    def say(self, words, level):
        self.state.setText(words)
        self.update_button.setEnabled(level == "on")
        if level == "on":
            ground, hover, ink = accent_shade("base"), accent_shade("hover"), TEXT_ON_ACCENT
        elif level == "dim":
            ground = hover = blend_color(MENU_BG, QColor(accent_shade("base")), 0.28).name()
            ink = TEXT_MUTED
        else:
            ground = hover = MENU_BG
            ink = TEXT_DISABLED
        self.update_button.setStyleSheet(
            "QPushButton {"
            f"  background: {ground}; color: {ink};"
            f"  border: none; border-radius: {HOVER_BORDER_RADIUS}px; padding: 0 22px;"
            f"  font-size: {HOME_LABEL_SIZE + 1}px; font-weight: bold;"
            "}"
            f"QPushButton:hover {{ background: {hover}; }}"
            # the same colors when it cannot be pressed: the state it is in is
            # what its color says, not whether Qt has greyed it out
            f"QPushButton:disabled {{ background: {ground}; color: {ink}; }}"
        )

    # the game's file read again and cleaned into the planner's own: it takes
    # a moment and holds the window while it runs, so the button says so
    def update_data(self):
        if not self.found:
            return
        self.update_button.setEnabled(False)
        self.update_button.setText("Updating...")
        self.say("Reading the game's files...", level="dim")
        QApplication.processEvents()
        try:
            data_maker.clean_data(self.found)
        except Exception as trouble:
            self.update_button.setText("Update data")
            self.say(f"Could not read it: {trouble}", level="on")
            return
        # ...and straight into use: the data is read again and every project
        # built back from what it asked for, so the trees on screen are the
        # new game's (see reload_game_data)
        self.say("Putting the projects back on the new data...", level="dim")
        QApplication.processEvents()
        try:
            reload_game_data(self.window())
        except Exception as trouble:
            self.update_button.setText("Update data")
            self.say(f"Data updated, but the projects could not be rebuilt: {trouble}", level="off")
            return
        self.update_button.setText("Update data")
        self.look_again()
        self.state.setText("Data updated")


# The band between the tab row and the page: the page's own grey, plain
# across the whole row. A tab's color fades out inside the tab itself, just
# above this, so nothing of it runs on into the page.
class PageBand(QWidget):
    def __init__(self, tabs):
        super().__init__(tabs)
        self.tabs = tabs

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(PANEL_BG))
        painter.end()


# A tab's own shape, from the box it stands in: rounded over the top,
# straight on down into the page. Out here rather than on the bar, so the
# full screen button at the far end of the row can be cut the same way.
def tab_shape_of(rect):
    shape = QPainterPath()
    shape.addRoundedRect(rect.adjusted(0, 0, 0, TAB_CORNER_RADIUS),
                         TAB_CORNER_RADIUS, TAB_CORNER_RADIUS)
    clip = QPainterPath()
    clip.addRect(rect)
    return shape.intersected(clip)


# The color a tab wears along its top: it runs the width of the tab, turns
# down around both corners with it and thins away to nothing as it goes, so
# it ends in a point rather than being cut off. A plain stroke is the one
# width all the way round, so it is built as a ribbon instead: the tab's own
# top edge, stepped along, with a width that tapers at the ends.
def tab_line_of(rect):
    radius = TAB_CORNER_RADIUS
    edge = QPainterPath(QPointF(rect.left(), rect.top() + radius + TAB_LINE_TAIL))
    edge.lineTo(rect.left(), rect.top() + radius)
    edge.arcTo(QRectF(rect.left(), rect.top(), radius * 2, radius * 2), 180, -90)
    edge.lineTo(rect.right() - radius, rect.top())
    edge.arcTo(QRectF(rect.right() - radius * 2, rect.top(), radius * 2, radius * 2), 90, -90)
    edge.lineTo(rect.right(), rect.top() + radius + TAB_LINE_TAIL)

    # the three parts of that edge, by length: the tail past each corner, the
    # corner itself, and the flat top between them. The line is one thickness
    # the whole way across the flat and thins only once it is turning the
    # corner, so the top reads as a straight line.
    corner = radius * math.pi / 2
    turning = (TAB_LINE_TAIL + corner) * TAB_LINE_TAPER
    along = 2 * (TAB_LINE_TAIL + corner) + max(rect.width() - 2 * radius, 0)

    # each step: where the edge is, which way it faces, and how thick the line
    # is there - full across the top, easing away to nothing by the time it
    # reaches the end of its tail
    outer, inner = [], []
    for step in range(TAB_LINE_STEPS + 1):
        at = step / TAB_LINE_STEPS
        point = edge.pointAtPercent(at)
        ahead = edge.pointAtPercent(min(at + 0.01, 1.0))
        behind = edge.pointAtPercent(max(at - 0.01, 0.0))
        run_x, run_y = ahead.x() - behind.x(), ahead.y() - behind.y()
        length = math.hypot(run_x, run_y) or 1
        away_x, away_y = run_y / length, -run_x / length   # outward, off the tab
        reached = at * along
        into = min(min(reached, along - reached) / turning, 1.0) if turning else 1.0
        thick = TAB_LINE_WIDTH * into * into * (3 - 2 * into)   # eased, not a straight ramp
        outer.append(QPointF(point.x() + away_x * thick, point.y() + away_y * thick))
        inner.append(point)
    ribbon = QPainterPath()
    ribbon.addPolygon(QPolygonF(outer + inner[::-1]))
    ribbon.closeSubpath()
    return ribbon


# QTabBar switches tabs on mouse press. This one swallows the press and acts on
# release instead, so a press that drags off the tab changes nothing. Qt only
# marks a tab sunken from its own press handling, so the held-down look is
# painted here rather than through a :pressed stylesheet rule.
class ReleaseTabBar(QTabBar):
    def __init__(self, on_plus, parent=None):
        super().__init__(parent)
        self.on_plus = on_plus
        self.pressed_on = -1
        # called when the wheel has moved the row along: an open rename box
        # hangs under its tab, and is shut rather than left under another
        self.on_scrolled = None

        # A tab is painted by the bar, not a widget of its own, so it cannot be
        # faded. It slides instead: this holds "how wide should this tab be right
        # now", from 0.0 (closed) to 1.0 (its natural width). A tab is only listed
        # here while it is animating; everything else uses Qt's own size.
        self.width_factor = {}
        # ...and how tall each tab stands, 0 closed to 1 open, while that is
        # changing (see ease_growth). A tab not listed is wherever it belongs.
        self.grow_factor = {}
        self.grow_animations = {}     # the one running per tab, to be taken over
        # a tab's own color, by its key, for the ground it is painted on
        self.tab_colors = {}
        # called whenever the row is redrawn, for the band under it to follow
        self.on_repaint = None

    # ---- sliding a tab open or shut ----

    # Qt asks for this whenever the bar relayouts, which is what makes the
    # animation visible: shrink the answer, and the tab and its neighbours move.
    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        # the full height of the row, so the open tab runs down into the page
        # under it - and the page starts where the row ends, rather than at a
        # tab's own height with the row's bottom hanging over it
        size.setHeight(PROJECT_TABS_HEIGHT)
        # home is square: as wide as the part of it showing under the gap is
        # tall, plus the 1px each side every tab keeps from its neighbours.
        # It rises like any other tab, so its width follows that (the row is
        # laid out again on every step of it, see ease_growth).
        if self.tab_key(index) == HOME_TAB_KEY:
            size.setWidth(round(PROJECT_TABS_HEIGHT - self.top_gap(index)) + 2)
        else:
            # a long name is cut short rather than pushing every other tab
            # off the row. A tab is the same width open or shut - only how
            # tall it stands answers to being picked (see top_gap)
            size.setWidth(min(size.width(), TAB_MAX_WIDTH))
        factor = self.width_factor.get(self.tab_key(index))
        if factor is not None:
            size.setWidth(max(1, round(size.width() * factor)))
        return size

    # how far a tab is toward standing open, 0 to 1
    def grown(self, index):
        held = self.grow_factor.get(self.tab_key(index))
        if held is not None:
            return held
        return 1.0 if index == self.currentIndex() else 0.0

    # the tab just left settling back down while the one just picked rises
    def ease_growth(self, was_key, now_key):
        moving = [(key, first, last) for key, first, last in ((was_key, 1.0, 0.0), (now_key, 0.0, 1.0))
                  if key is not None]
        for key, first, _ in moving:
            self.grow_factor.setdefault(key, first)
        self.update()
        for key, first, last in moving:

            def step(value, key=key):
                self.grow_factor[key] = float(value)
                if key == HOME_TAB_KEY:
                    self.relayout_tabs()   # home is square: its width rises with it
                self.update()
                if self.on_repaint is not None:
                    self.on_repaint()

            def finish(key=key):
                self.grow_animations.pop(key, None)
                self.grow_factor.pop(key, None)
                self.update()

            # from wherever it stands - a tab picked again while it is still
            # settling carries on from there instead of starting over
            held = self.grow_factor.get(key)
            running = self.grow_animations.pop(key, None)
            if running is not None:
                running.stop()
            animation = animate_value(self, held if held is not None else first, last, step,
                                      TAB_GROW_MS, TAB_GROW_CURVE)
            animation.finished.connect(finish)
            self.grow_animations[key] = animation

    # the grey a tab is painted on, under whatever of its color has spread
    # over it: the row's own ground, a step lighter as the tab rises
    def tab_ground(self, index):
        return blend_color(TAB_CLOSED_GROUND, QColor(TAB_OPEN_BG), self.grown(index))

    # Indexes shift as tabs are added and removed, so an animation started on
    # index 2 could end up resizing a different tab. Each tab carries its own
    # key in tabData instead, which stays with it for life.
    def tab_key(self, index):
        return self.tabData(index)

    def set_tab_key(self, index, key):
        self.setTabData(index, key)

    # the row's ground left showing over a tab: less over the open one, which
    # is what makes it stand taller - eased, so it rises rather than jumps
    def top_gap(self, index):
        return TAB_TOP_GAP + (TAB_SELECTED_TOP_GAP - TAB_TOP_GAP) * self.grown(index)

    # the color a tab wears along its top: the top of its own outline, drawn
    # thick, ending a little way down each side
    def tab_line(self, index):
        return tab_line_of(self.tab_shape(index).boundingRect())

    # a tab's own shape: rounded over the top, straight on down into the page
    def tab_shape(self, index):
        return tab_shape_of(QRectF(self.tabRect(index)).adjusted(1, self.top_gap(index), -1, 0))

    # updateGeometry alone is not enough: QTabBar caches its tab rects and will
    # not re-ask tabSizeHint until something marks that cache dirty. setIconSize
    # does exactly that and has no other effect when given the current size.
    def relayout_tabs(self):
        self.setIconSize(self.iconSize())
        self.updateGeometry()

    def slide_tab(self, key, start, end, on_done=None):
        def step(value):
            self.width_factor[key] = float(value)
            self.relayout_tabs()

        def finish():
            self.width_factor.pop(key, None)   # back to Qt's natural width
            self.relayout_tabs()
            if on_done is not None:
                on_done()

        self.width_factor[key] = float(start)  # apply before the first frame
        animate_value(self, start, end, step, TAB_SLIDE_MS).finished.connect(finish)

    def slide_tab_open(self, key):
        self.slide_tab(key, 0.0, 1.0)

    def slide_tab_shut(self, key, on_done):
        self.slide_tab(key, 1.0, 0.0, on_done)

    # ---- the wheel ----

    # QTabBar's own wheel steps through the tabs, opening each in turn - a
    # scroll over the bar is not a pick. Here it only moves the row along,
    # and only when there is more of it than fits: the bar's own scroll
    # arrows are there then, and the wheel presses them.
    def wheelEvent(self, event):
        delta = event.angleDelta().y() or event.angleDelta().x()
        if delta:
            toward = Qt.LeftArrow if delta > 0 else Qt.RightArrow
            for arrow in self.findChildren(QToolButton):
                if arrow.isVisible() and arrow.isEnabled() and arrow.arrowType() == toward:
                    arrow.click()
                    if self.on_scrolled is not None:
                        self.on_scrolled()
                    break
        event.accept()

    # ---- selection on release ----

    def mousePressEvent(self, event):
        self.pressed_on = self.tabAt(event.position().toPoint())
        self.update()
        event.accept()

    def mouseReleaseEvent(self, event):
        index = self.tabAt(event.position().toPoint())
        if index != -1 and index == self.pressed_on:
            if self.tabText(index) == PLUS_TAB_LABEL:
                self.on_plus()
            else:
                self.setCurrentIndex(index)
        self.pressed_on = -1
        self.update()
        event.accept()

    def paintEvent(self, event):
        # the grounds first, under Qt's own pass: a stylesheet has one ground
        # for every tab, and each of these carries its project's color
        grounds = QPainter(self)
        grounds.setRenderHint(QPainter.Antialiasing)
        for index in range(self.count()):
            if self.tab_key(index) is None:
                continue        # the "+" is a button, and stands on the bar itself
            grounds.fillPath(self.tab_shape(index), QColor(self.tab_ground(index)))
            color = QColor(self.tab_colors.get(self.tab_key(index), TAB_DEFAULT_COLOR))
            # a tab picked fills with its own color from that line down, so
            # the color reads as spreading out of it into the tab and on into
            # the band under the row (see place_page_line)
            spread = self.grown(index)
            if spread > 0:
                shape = self.tab_shape(index)
                rect = shape.boundingRect()
                filling = QPainterPath()
                filling.addRect(QRectF(rect.left(), rect.top(), rect.width(), rect.height() * spread))
                grounds.fillPath(shape.intersected(filling), color)
            # ...and the line itself: straight across the top edge, the way
            # the accent used to mark whichever tab was open - the tab's own
            # rounded corners are all that shape it
            grounds.fillPath(self.tab_line(index), color)
        grounds.end()

        super().paintEvent(event)
        painter = QPainter(self)

        # a short line on a tab's right edge, so one tab reads as ending where
        # the next begins - only between two closed ones: the open tab's own
        # ground already sets it apart, and a line against it is clutter. Drawn
        # here rather than as a border in the stylesheet, which would run the
        # full height and follow the rounded corners.
        top = TAB_TOP_GAP + (self.height() - TAB_TOP_GAP - TAB_DIVIDER_HEIGHT) // 2
        current = self.currentIndex()
        for index in range(self.count() - 1):
            if current in (index, index + 1):
                continue
            rect = self.tabRect(index)
            if rect.width() > 1:
                painter.fillRect(rect.right(), top, 1, TAB_DIVIDER_HEIGHT, QColor(*TAB_DIVIDER))

        # home's house, drawn here rather than as the tab's icon: Qt keeps an
        # icon to the left of where a name would go, even with no name. Lit
        # while home is showing or under the mouse, quiet otherwise.
        for index in range(self.count()):
            if self.tab_key(index) != HOME_TAB_KEY:
                continue
            rect = QRectF(self.tabRect(index)).adjusted(0, self.top_gap(index), 0, 0)
            lit = index == current or rect.contains(self.mapFromGlobal(QCursor.pos()))
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            scale = HOME_ICON_SIZE / SYMBOL_CANVAS
            painter.translate(rect.center().x() - HOME_ICON_SIZE / 2, rect.center().y() - HOME_ICON_SIZE / 2)
            painter.scale(scale, scale)
            draw_home(painter, QColor(TAB_SELECTED_COLOR if lit else TAB_UNSELECTED_COLOR))
            painter.restore()

        if self.pressed_on != -1:
            # over the tab's own shape, rounded top and all
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillPath(self.tab_shape(self.pressed_on), QColor(*TAB_PRESS_OVERLAY))

def make_close_button():
    button = QPushButton()
    button.setFixedSize(TAB_SYMBOL_SIZE, TAB_SYMBOL_SIZE)
    button.setFlat(True)
    button.setCursor(Qt.PointingHandCursor)
    button.setFocusPolicy(Qt.NoFocus)
    button.setToolTip("Close this project")
    button.setStyleSheet(
        "QPushButton {"
        "  border: none;"
        "  background: transparent;"
        "  padding: 0;"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "}"
        "QPushButton:hover {"
        f"  background: {CLOSE_BUTTON_HOVER_BG};"
        "}"
        "QPushButton:pressed {"
        f"  background: {TAB_SYMBOL_PRESS_BG};"
        "}"
    )
    set_close_symbol(button, TAB_CLOSE_SYMBOL_SIZE)

    # wrapper gives the button breathing room from the tab text without
    # shrinking the button's own clickable area (margin on a fixed-size
    # widget eats into its hit box instead of adding space around it)
    wrapper = QWidget()
    wrapper.setAttribute(Qt.WA_StyledBackground, True)
    wrapper_layout = QHBoxLayout(wrapper)
    # the bar centers it on the whole tab, gap over the top included, while
    # the label is centered under that gap: the same room on top brings the
    # two level again
    wrapper_layout.setContentsMargins(CLOSE_BUTTON_MARGIN, TAB_TOP_GAP + TAB_INDICATOR_WIDTH,
                                      CLOSE_BUTTON_MARGIN, 0)
    wrapper_layout.setSpacing(0)
    wrapper_layout.addWidget(button)

    return wrapper, button

def make_project_tabs():
    tabs = QTabWidget()
    tabs.setTabPosition(QTabWidget.North)
    # add_project_tab is defined further down; the closure resolves it at click time
    tabs.setTabBar(ReleaseTabBar(lambda: add_project_tab()))
    tabs.tabBar().setFixedHeight(PROJECT_TABS_HEIGHT)
    tabs.tabBar().setDrawBase(False)   # the line QTabBar draws under the whole bar
    # expanding tabs stretch to fill the bar, which overrides the width a sliding
    # tab asks for; sized to their label instead, the slide is honoured
    tabs.tabBar().setExpanding(False)
    # the row's ground: the QTabWidget is what shows beside and behind the
    # tabs, and without one it was the light default strip across a dark app
    tabs.setAttribute(Qt.WA_StyledBackground, True)
    tabs.setStyleSheet(
        f"QTabWidget {{ background: {TAB_BAR_BG}; }}"
        "QTabWidget::pane {"           # and the frame QTabWidget draws around the page
        "  border: none;"
        # the band under the row is painted over this, in the open tab's
        # color (see place_page_line); the border keeps the room for it
        f"  border-top: {TAB_PAGE_LINE_WIDTH}px solid transparent;"
        "}"
    )
    # the bar's own rules go on the bar, not on the QTabWidget around it: the
    # accent is in here, and re-setting a stylesheet re-polishes everything
    # under that widget - which for the QTabWidget would be the whole project
    # page, graph and all, on every accent switch.
    tabs.tabBar().setStyleSheet(
        f"QTabBar {{ background: {TAB_BAR_BG}; }}"
        # the arrows Qt puts up when the row is too long for its width: left
        # white and square by default, which stood out of a dark row
        "QTabBar QToolButton {"
        f"  background: {TAB_BAR_BG};"
        f"  border: 1px solid {TAB_BAR_BG};"
        "  margin: 0;"
        "}"
        "QTabBar QToolButton:hover {"
        f"  background: {TAB_OPEN_BG};"
        "}"
        "QTabBar::tab {"
        f"  font-size: {TAB_FONT_SIZE}px;"
        f"  padding: 4px {TAB_SIDE_PADDING}px;"
        f"  margin: {TAB_TOP_GAP}px 1px 0 1px;"
        "  background: transparent;"
        "  border: none;"
        f"  border-top: {TAB_INDICATOR_WIDTH}px solid transparent;"
        f"  border-top-left-radius: {TAB_CORNER_RADIUS}px;"
        f"  border-top-right-radius: {TAB_CORNER_RADIUS}px;"
        f"  color: {TAB_UNSELECTED_COLOR};"
        "}"
        "QTabBar::tab:hover {"
        f"  color: {TAB_SYMBOL_HOVER_COLOR};"
        f"  background: {TAB_HOVER_BG};"
        "}"
        # the same weight open or shut: a bold label is a wider one, and the
        # tabs after it shuffled over every time another was picked
        # its ground and how tall it stands are painted, not styled, so both
        # can be eased (see tab_ground). Its name is the same size as every
        # other tab's: a bigger one made it a wider tab.
        "QTabBar::tab:selected {"
        f"  color: {TAB_SELECTED_COLOR};"
        "  background: transparent;"
        "}"
        # home is a square with its house in it (sized in tabSizeHint)
        "QTabBar::tab:first {"
        "  padding: 0;"
        "}"
        # the "+" is a button more than a tab: a narrow one
        "QTabBar::tab:last {"
        "  padding: 0 12px 2px 12px;"
        f"  font-size: {TAB_PLUS_FONT_SIZE}px;"
        "}"
    )

    project_count = [0]     # only ever a tab's identity for animations, not its name

    # The name a new project is given: "Project 1", or the first number after
    # that no project is already called. Closing Project 2 of three and making
    # another gives that name back, rather than counting on to "Project 4"
    # and leaving a hole - and a project renamed by hand frees its number.
    def next_default_name():
        taken = {tabs.tabText(index) for index in range(tabs.count())}
        number = 1
        while f"Project {number}" in taken:
            number += 1
        return f"Project {number}"

    def plus_tab_index():
        for i in range(tabs.count()):
            if tabs.tabText(i) == PLUS_TAB_LABEL:
                return i
        return -1

    def remove_project_tab(page):
        index = tabs.indexOf(page)
        if index == -1:
            return

        def do_remove():
            bar = tabs.tabBar()
            closing = tabs.indexOf(page)
            if closing == -1:
                return

            # the tab slides shut first, and is only really removed afterwards
            def drop_the_tab():
                gone = tabs.indexOf(page)
                if gone == -1:
                    return
                tabs.removeTab(gone)
                page.deleteLater()
                schedule_save()
                # back home, whatever is left: a project deleted is done with,
                # and the one beside it is no more where you were than any other
                tabs.setCurrentIndex(tabs.indexOf(home_page))

            bar.slide_tab_shut(bar.tab_key(closing), drop_the_tab)

        show_confirm_dialog(
            tabs.window(),
            "Delete project",
            f"Are you sure you want to delete \"{tabs.tabText(index)}\"?",
            do_remove,
        )

    # `rename` opens the name box on the new tab, so a project made by hand can
    # be named straight away. The one the app opens with is left alone: a box
    # dropping out of the bar on startup asks a question nobody asked for.
    # Qt always centers a tab's name in the room it has, and a stylesheet has
    # no say in that. So the room is given after the name instead: the close
    # button's wrapper takes whatever a short name leaves short of the tab's
    # least width, which sits the name on the left and the cross on the right.
    # Worked out again whenever the name changes.
    # The open tab is bigger than the rest, so every tab is fitted again
    # whenever another is picked.
    def fit_tab(index):
        bar = tabs.tabBar()
        wrapper = bar.tabButton(index, QTabBar.RightSide)
        if wrapper is None:
            return
        # the same room open or shut: a tab that changed width as it was
        # picked shuffled every tab after it along the row
        font = QFont(QApplication.font())
        font.setPixelSize(TAB_FONT_SIZE)
        name_width = QFontMetrics(font).horizontalAdvance(tabs.tabText(index))
        room = max(CLOSE_BUTTON_MARGIN, TAB_MIN_WIDTH - name_width)
        wrapper.layout().setContentsMargins(room, round(bar.top_gap(index)) + TAB_INDICATOR_WIDTH,
                                            CLOSE_BUTTON_MARGIN, 0)
        wrapper.adjustSize()
        bar.relayout_tabs()

    # `saved` is a project from the save file: its page stays empty until the
    # tab is first opened. `select` is False for those, so putting back a whole
    # session does not open, and so load, every one of them on the way.
    def add_project_tab(rename=True, name=None, saved=None, select=True):
        project_count[0] += 1
        label = name or next_default_name()
        page = ProjectPage(label, saved)
        if saved is None:
            page.load()
        plus_index = plus_tab_index()
        if plus_index == -1:
            index = tabs.addTab(page, label)
        else:
            index = tabs.insertTab(plus_index, page, label)

        close_wrapper, close_button = make_close_button()
        close_button.clicked.connect(lambda: remove_project_tab(page))

        bar = tabs.tabBar()
        bar.setTabButton(index, QTabBar.RightSide, close_wrapper)
        fit_tab(index)
        bar.set_tab_key(index, project_count[0])   # its identity for animations
        bar.tab_colors[project_count[0]] = page.tab_color
        if not select:
            return page
        bar.slide_tab_open(project_count[0])
        tabs.setCurrentIndex(index)
        if rename:
            # once the tab has finished sliding open: its rect is what the name
            # box is sized and placed against
            QTimer.singleShot(TAB_SLIDE_MS + ANIMATION_MS,
                              lambda: start_rename(tabs.indexOf(page)))
        schedule_save()
        return page

    # the color of one tab, taken up by its tab and by the band under the row
    def set_tab_color(index, color):
        page = tabs.widget(index)
        bar = tabs.tabBar()
        page.tab_color = color
        bar.tab_colors[bar.tab_key(index)] = color
        bar.update()
        place_page_line()
        schedule_save()

    # a square of the tab's color beside its name box: clicking it drops the
    # colors to choose from under it, and picking one paints the tab
    def make_color_square(index, on_pick):
        square = QPushButton()
        square.setFixedSize(TAB_COLOR_SQUARE, TAB_COLOR_SQUARE)
        square.setCursor(Qt.PointingHandCursor)
        square.setFocusPolicy(Qt.NoFocus)
        square.setToolTip("The color of this tab")

        def wear(color):
            try:
                square.styleSheet()       # gone with its box already?
            except RuntimeError:
                return
            square.setStyleSheet(
                "QPushButton {"
                f"  background: {color};"
                f"  border: 1px solid {OUTPUT_FIELD_BORDER};"
                f"  border-radius: {HOVER_BORDER_RADIUS}px;"
                "}"
                "QPushButton:hover { border: 1px solid " + TEXT_NORMAL + "; }"
            )

        wear(tabs.widget(index).tab_color)

        # the whole rainbow along one slider, grey at its near end: dragging
        # it paints the band under the row as it goes, so a color is chosen
        # by looking at it rather than by opening and shutting a menu
        # the three of them together: moving any one re-colors the tab at
        # once, and re-grounds the other two - what a hue looks like depends
        # on how much of it there is and how light it stands
        def open_colors():
            picker = QWidget(square.window(), Qt.Popup)
            picker.setAttribute(Qt.WA_StyledBackground, True)
            picker.setStyleSheet(
                f"QWidget {{ background-color: {MENU_BG};"
                f" border: 1px solid {OUTPUT_FIELD_BORDER};"
                f" border-radius: {HOVER_BORDER_RADIUS}px; }}"
                f"QLabel {{ border: none; color: {TEXT_MUTED};"
                f" font-size: {TAB_FONT_SIZE - 2}px; background: transparent; }}"
            )
            around = QVBoxLayout(picker)
            around.setContentsMargins(TAB_COLOR_SWATCH_GAP, TAB_COLOR_SWATCH_GAP,
                                      TAB_COLOR_SWATCH_GAP, TAB_COLOR_SWATCH_GAP)
            around.setSpacing(2)

            hue, contrast, brightness = tab_color_parts(tabs.widget(index).tab_color)
            standing = {"hue": hue, "contrast": contrast, "brightness": brightness}
            sliders = {}

            def ground(which):
                sliders[which].setStyleSheet(
                    "QSlider { border: none; background: transparent; }"
                    "QSlider::groove:horizontal {"
                    f"  height: {TAB_COLOR_SLIDER_HEIGHT}px;"
                    f"  border-radius: {HOVER_BORDER_RADIUS}px;"
                    f"  background: {tab_slider_gradient(which, **standing)};"
                    "}"
                    "QSlider::handle:horizontal {"
                    "  width: 6px;"
                    "  margin: -2px 0;"
                    "  border-radius: 3px;"
                    f"  background: {TEXT_STRONG};"
                    f"  border: 1px solid {GRID_BG};"
                    "}"
                )

            def slid(which, value):
                standing[which] = value
                color = tab_color_from(**standing)
                set_tab_color(index, color)
                wear(color)
                for other in sliders:
                    ground(other)

            for which, title, most in (("hue", "Color", TAB_HUE_STEPS),
                                       ("contrast", "Contrast", TAB_CONTRAST_STEPS),
                                       ("brightness", "Brightness", 255)):
                around.addWidget(QLabel(title, picker))
                slider = QSlider(Qt.Horizontal, picker)
                slider.setRange(TAB_BRIGHTNESS_LOW if which == "brightness" else 0, most)
                slider.setFixedSize(TAB_COLOR_SLIDER_WIDTH, TAB_COLOR_SLIDER_HEIGHT)
                slider.setFocusPolicy(Qt.NoFocus)
                slider.setValue(standing[which])
                slider.valueChanged.connect(lambda value, which=which: slid(which, value))
                sliders[which] = slider
                ground(which)
                around.addWidget(slider)

            picker.adjustSize()
            picker.move(square.mapToGlobal(QPoint(0, square.height() + TAB_COLOR_SWATCH_GAP)))
            owner = square.window()
            for parent in (square.parentWidget(), square.parentWidget().parentWidget()):
                if parent is not None and hasattr(parent, "outside_click"):
                    owner = parent
            owner.color_picker = picker      # so clicking it does not close the name box
            picker.show()
            # the name box keeps the caret: picking a color is not leaving it
            on_pick()

        square.clicked.connect(open_colors)
        return square

    def start_rename(index):
        if index == -1 or tabs.tabText(index) == PLUS_TAB_LABEL or tabs.widget(index) is home_page:
            return   # closed again before the box could open - or home, which has no name to change

        def open_editor():
            # deferred a tick so the tab's selected/bold layout has
            # already settled before we read its rect
            bar = tabs.tabBar()
            window = tabs.window()
            tab_rect = bar.tabRect(index)

            popup = QWidget(window)
            popup.setAttribute(Qt.WA_StyledBackground, True)
            popup.setStyleSheet(f"background-color: {DIALOG_BG}; border-radius: {HOVER_BORDER_RADIUS}px;")

            editor = QLineEdit(popup)
            editor.setText(tabs.tabText(index))
            editor.setStyleSheet(
                "QLineEdit {"
                f"  font-size: {TAB_SELECTED_FONT_SIZE}px;"
                f"  color: {TAB_SELECTED_COLOR};"
                "  background: transparent;"
                "  border: none;"
                f"  selection-background-color: {TAB_INDICATOR_COLOR};"
                "}"
            )

            popup_layout = QHBoxLayout(popup)
            popup_layout.setContentsMargins(6, 6, 6, 6)
            popup_layout.setSpacing(TAB_COLOR_SWATCH_GAP)
            # picking a color is not typing a name: the box stays open, and
            # the caret goes back to it
            popup_layout.addWidget(make_color_square(index, lambda: editor.setFocus()))
            popup_layout.addWidget(editor, 1)

            # exactly as wide as the tab, and lined up with it
            popup.setFixedWidth(tab_rect.width())
            popup.adjustSize()

            # hangs just under the tab, not under the whole bar
            anchor = bar.mapTo(window, tab_rect.bottomLeft())
            resting = QRect(anchor.x(), anchor.y() + RENAME_GAP,
                            popup.width(), popup.height())
            folded = QRect(resting.x(), resting.y(), resting.width(), 0)

            # unrolls downward out of the tab bar rather than appearing on the spot
            popup.setGeometry(folded)
            popup.show()
            popup.raise_()
            unroll = QPropertyAnimation(popup, b"geometry", popup)
            unroll.setDuration(RENAME_SLIDE_MS)
            unroll.setStartValue(folded)
            unroll.setEndValue(resting)
            run(unroll)

            editor.selectAll()
            editor.setFocus()

            closed = [False]   # returnPressed also triggers a focus out, only act once

            def slide_up_and_delete():
                roll_up = QPropertyAnimation(popup, b"geometry", popup)
                roll_up.setDuration(RENAME_SLIDE_MS)
                roll_up.setStartValue(popup.geometry())
                roll_up.setEndValue(folded)
                roll_up.finished.connect(popup.deleteLater)
                run(roll_up)

            def close_editor():
                if closed[0]:
                    return
                closed[0] = True
                if bar.on_scrolled is close_editor:
                    bar.on_scrolled = None
                QApplication.instance().removeEventFilter(popup.outside_click)
                editor.clearFocus()          # no caret while it slides away
                slide_up_and_delete()

            def commit():
                new_name = editor.text().strip()
                if new_name and not closed[0]:
                    tabs.setTabText(index, new_name)
                    fit_tab(index)
                    page = tabs.widget(index)
                    if page is not None:
                        page.project_name = new_name
                    schedule_save()
                close_editor()

            # editingFinished cannot be used: it fires on Enter and on focus out
            # alike, and clicking away has to discard the edit rather than keep it
            class CancelOnFocusOut(QObject):
                def eventFilter(self, watched, event):
                    if event.type() == QEvent.FocusOut:
                        close_editor()
                    return False

            # a focus out only fires when something focusable takes the focus,
            # and most of what can be clicked here is Qt.NoFocus - so presses
            # are watched application wide to catch a click anywhere else
            class CancelOnOutsideClick(QObject):
                def eventFilter(self, watched, event):
                    if event.type() == QEvent.MouseButtonPress:
                        under = QApplication.widgetAt(event.globalPosition().toPoint())
                        # the color sliders stand in a window of their own, but
                        # they belong to this box: working them is not leaving it
                        picker = getattr(popup, "color_picker", None)
                        inside = [popup] + ([picker] if picker is not None else [])
                        if under is None or not any(under is one or one.isAncestorOf(under)
                                                    for one in inside):
                            close_editor()
                    return False

            editor.canceller = CancelOnFocusOut(editor)   # kept alive by the editor
            editor.installEventFilter(editor.canceller)
            popup.outside_click = CancelOnOutsideClick(popup)
            QApplication.instance().installEventFilter(popup.outside_click)
            editor.returnPressed.connect(commit)
            QShortcut(QKeySequence(Qt.Key_Escape), editor, activated=close_editor)
            # the wheel over the bar leaves it be, unless the row really moves
            bar.on_scrolled = close_editor

        QTimer.singleShot(0, open_editor)

    # The page swapped in outright read as a flicker between two full screens
    # of chrome. The one being left is held as a picture over the new one and
    # faded off it instead, quickly - a picture rather than the widget itself,
    # since an opacity effect on a live graph view repaints all of it every
    # frame.
    showing = [None]

    def fade_out_old_page():
        old = showing[0]
        new = tabs.currentWidget()
        showing[0] = new
        if old is None or old is new or not tabs.isVisible() or not old.size().isValid():
            return
        ghost = QLabel(tabs)
        ghost.setPixmap(old.grab())
        ghost.setGeometry(QRect(old.mapTo(tabs, QPoint(0, 0)), old.size()))
        fade = QGraphicsOpacityEffect(ghost)
        ghost.setGraphicsEffect(fade)
        ghost.show()
        ghost.raise_()
        animate_value(ghost, 1.0, 0.0, fade.setOpacity,
                      TAB_PAGE_FADE_MS).finished.connect(ghost.deleteLater)

    # the tab left behind, so it can settle back down as the new one rises
    was_on = [None]

    def on_current_changed(new_index):
        # wheel-scrolling over the tab bar can land on the "+" tab; bounce
        # back to the tab before it - the last project, or home when there
        # are none - instead of sitting on it
        if tabs.count() > 1 and tabs.tabText(new_index) == PLUS_TAB_LABEL:
            tabs.setCurrentIndex(tabs.count() - 2)
            return
        bar = tabs.tabBar()
        now_key = bar.tab_key(new_index)
        if was_on[0] != now_key:
            bar.ease_growth(was_on[0], now_key)
            was_on[0] = now_key
        fade_out_old_page()
        for index in range(tabs.count()):
            fit_tab(index)
        place_page_line()
        schedule_save()

    # Home: a small square tab at the far left, always there and never closed
    # or renamed. It holds no project - the projects' own lookups pass it by
    # (see MainWindow.project_pages).
    home_page = HomePage()
    tabs.home_page = home_page
    home_index = tabs.addTab(home_page, "")
    tabs.tabBar().set_tab_key(home_index, HOME_TAB_KEY)
    tabs.tabBar().tab_colors[HOME_TAB_KEY] = TAB_DEFAULT_COLOR
    tabs.setTabToolTip(home_index, "Home")

    empty_state = QWidget()
    empty_state.setAttribute(Qt.WA_StyledBackground, True)
    empty_state.setStyleSheet(f"background-color: {EMPTY_STATE_BG};")

    tabs.addTab(empty_state, PLUS_TAB_LABEL)
    # the band between the row and the page, in the color of the tab that is
    # open and fading into the page's own grey where the two meet - so the
    # color reads as belonging to that project rather than as a stripe
    corner = FullScreenCorner(tabs)
    full_screen = make_full_screen_button(corner)
    # centered in the room the corner keeps, so it sits as far from the wall
    # as it does from the window's edge
    full_screen.move(round((corner_width() + FULL_SCREEN_WALL_WIDTH - full_screen_width()) / 2), 0)
    tabs.full_screen = full_screen

    page_line = PageBand(tabs)
    page_line.setAttribute(Qt.WA_TransparentForMouseEvents, True)
    # the band is redrawn along with the row, so the color reaching it keeps
    # step with the color spreading down the tab
    tabs.tabBar().on_repaint = page_line.update

    def place_page_line():
        bar = tabs.tabBar()
        # the corner at the far end of the row, and the tabs held short of
        # it: a row too long for its own width scrolls (see wheelEvent)
        # rather than running on under the button
        corner.setGeometry(tabs.width() - corner_width(), 0, corner_width(), PROJECT_TABS_HEIGHT)
        corner.raise_()
        bar.setMaximumWidth(max(tabs.width() - corner_width(), 1))
        page_line.setGeometry(0, bar.height(), tabs.width(), TAB_PAGE_LINE_WIDTH)
        page_line.raise_()   # over the page being faded off, too
        page_line.update()

    # it is not in a layout - the tab widget lays out its own bar and pages -
    # so it is put back in place whenever the window changes size
    class KeepPageLine(QObject):
        def eventFilter(self, watched, event):
            if event.type() in (QEvent.Resize, QEvent.Show):
                place_page_line()
            return False

    tabs.keep_page_line = KeepPageLine(tabs)
    tabs.installEventFilter(tabs.keep_page_line)
    tabs.place_page_line = place_page_line

    tabs.tabBarDoubleClicked.connect(start_rename)
    tabs.currentChanged.connect(on_current_changed)

    tabs.add_project_tab = add_project_tab   # the window restores saved projects through it
    # the app opens on Project 1, not on the bare "+" state - unless there are
    # saved projects to put back, which the window does instead
    if not read_appdata().get("projects"):
        add_project_tab(rename=False)

    return tabs

# ================================================== CONFIRM DIALOG =================================================
OVERLAY_BG = "rgba(0, 0, 0, 0.6)"
DIALOG_BG = "#2c2c2c"
DIALOG_TEXT_COLOR = TEXT_STRONG
DIALOG_WIDTH = 320
CONFIRM_BUTTON_BG = TAB_INDICATOR_COLOR
CANCEL_BUTTON_BG = "#555"
CANCEL_BUTTON_HOVER_BG = "#646464"
CANCEL_BUTTON_PRESS_BG = "#454545"

def show_confirm_dialog(parent, title, message, on_confirm):
    overlay = QWidget(parent)
    overlay.setAttribute(Qt.WA_StyledBackground, True)
    overlay.setStyleSheet(f"background-color: {OVERLAY_BG};")
    overlay.setGeometry(parent.rect())

    box = QWidget(overlay)
    box.setAttribute(Qt.WA_StyledBackground, True)
    box.setFixedWidth(DIALOG_WIDTH)
    box.setStyleSheet(f"background-color: {DIALOG_BG}; border-radius: 8px;")

    box_layout = QVBoxLayout(box)
    box_layout.setContentsMargins(20, 20, 20, 20)
    box_layout.setSpacing(16)

    title_label = QLabel(title)
    title_label.setStyleSheet(f"color: {DIALOG_TEXT_COLOR}; font-size: 16px; font-weight: bold;")
    message_label = QLabel(message)
    message_label.setStyleSheet(f"color: {DIALOG_TEXT_COLOR}; font-size: 13px;")
    message_label.setWordWrap(True)

    cancel_button = QPushButton("Cancel")
    cancel_button.setCursor(Qt.PointingHandCursor)
    cancel_button.setStyleSheet(
        "QPushButton {"
        f"  background-color: {CANCEL_BUTTON_BG};"
        f"  color: {DIALOG_TEXT_COLOR};"
        "  border: none;"
        "  border-radius: 4px;"
        "  padding: 6px 16px;"
        "}"
        "QPushButton:hover {"
        f"  background-color: {CANCEL_BUTTON_HOVER_BG};"
        "}"
        "QPushButton:pressed {"
        f"  background-color: {CANCEL_BUTTON_PRESS_BG};"
        "}"
    )
    confirm_button = QPushButton("Delete")
    confirm_button.setCursor(Qt.PointingHandCursor)
    confirm_button.setStyleSheet(
        "QPushButton {"
        f"  background-color: {CONFIRM_BUTTON_BG};"
        f"  color: {DIALOG_TEXT_COLOR};"
        "  border: none;"
        "  border-radius: 4px;"
        "  padding: 6px 16px;"
        "}"
        "QPushButton:hover {"
        f"  background-color: {ADD_OUTPUT_HOVER_BG};"
        "}"
        "QPushButton:pressed {"
        f"  background-color: {ACCENT_PRESS_BG};"
        "}"
    )

    button_row = QHBoxLayout()
    button_row.addStretch()
    button_row.addWidget(cancel_button)
    button_row.addWidget(confirm_button)

    box_layout.addWidget(title_label)
    box_layout.addWidget(message_label)
    box_layout.addLayout(button_row)

    box.adjustSize()
    box.move((overlay.width() - box.width()) // 2, (overlay.height() - box.height()) // 2)

    def close_overlay():
        fade_out(overlay, on_done=overlay.deleteLater)

    def confirm():
        close_overlay()
        on_confirm()

    cancel_button.clicked.connect(close_overlay)
    confirm_button.clicked.connect(confirm)

    fade_in(overlay)
    overlay.raise_()

# ====================================================== GRAPH ======================================================
FULLSCREEN_BUTTON_SIZE = 28   # the size of every view toolbar button
FULLSCREEN_MARGIN = 10        # the view toolbar's distance from the view's corner
FULLSCREEN_BUTTON_BG = "rgba(255, 255, 255, 0.10)"
FULLSCREEN_BUTTON_HOVER_BG = "rgba(255, 255, 255, 0.20)"

GRID_BG = "#333333"
GRID_LINE_COLOR = "#3d3d3d"     # the fine subdivision lines
GRID_SQUARE_COLOR = "#4a4a4a"   # the square itself, brighter than its subdivisions
GRID_AXIS_ALPHA = 70        # the x=0/y=0 lines, in the accent color faded to this alpha (out of 255)
GRID_STEP = 30              # scene units between two of the fine lines
GRID_MAJOR_EVERY = 4        # every n-th line closes a square
# what a node is measured and snapped in: a node is a whole number of squares
# wide and tall (see NODE_WIDTH / NODE_HEIGHT), so a snapped node lands flush
# on the bright lines instead of floating somewhere inside a square.
GRID_SQUARE = GRID_STEP * GRID_MAJOR_EVERY   # 120
SNAP_STEP = GRID_SQUARE
# below this the fine lines are packed too close together to read as a grid,
# so only the squares are drawn - which is most of the new zoom-out range
GRID_MINOR_MIN_ZOOM = 0.5

ZOOM_MIN = 0.05             # 20x zoomed out - far enough to take in a whole large factory
ZOOM_MAX = 8.0              # 8x zoomed in
ZOOM_STEP = 1.15            # per wheel notch

COORDINATES_FONT_SIZE = 10
COORDINATES_MARGIN = 8
COORDINATES_COLOR = TEXT_FAINT

SCENE_EXTENT = 100000       # how far the grid can be panned from the origin

PAN_RING_RADIUS = 16        # screen pixels, kept constant by dividing by the zoom
PAN_RING_FILL = (255, 255, 255, 26)
PAN_RING_BORDER = (255, 255, 255, 90)


# drawn in drawBackground rather than as scene items, so the grid is infinite,
# costs nothing to pan over and only paints the part of the scene on screen
class GridGraphicsView(QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.zoom = 1.0
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)  # zoom towards the cursor
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.panning = False
        self.pan_cursor = QPoint()   # viewport position of the grab, for the ring
        self.ring_opacity = 0.0      # animated, so the ring fades instead of popping
        self.zoom_target = 1.0
        self.zoom_animation = None

        # anything that floats over the scene at a fixed screen position tied
        # to a scene point (the node info panel, say) needs to know whenever
        # panning, zooming or resizing could have moved that point on screen
        self.view_changed_callbacks = []

        # scene position under the cursor, bottom left, only while the mouse is over the grid
        self.setMouseTracking(True)      # move events without a button held down
        self.coordinates = QLabel(self)
        self.coordinates.setStyleSheet(
            f"color: {COORDINATES_COLOR};"
            f"font-size: {COORDINATES_FONT_SIZE}px;"
            "background: transparent;"
        )
        self.coordinates.hide()

        # the part of the scene the camera started on, for reset_camera to go
        # back to: what the last confirm fitted, None before any (zoom 1 on 0, 0)
        self.start_rect = None

        # True while the view is being panned or zoomed, or a build is playing:
        # what moves is drawn cheaply (see SceneText), and the moment it stops
        # the whole thing is drawn again properly
        self.moving = False
        self.draw_scale = 0.0   # set from the zoom, see refresh_draw_scale
        self.settle = QTimer(self)
        self.settle.setSingleShot(True)
        self.settle.setInterval(MOVING_SETTLE_MS)
        self.settle.timeout.connect(self.stop_moving)
        self.refresh_draw_scale()

    # called by anything that moves the view or the graph: while they keep
    # coming the view stays in its cheap mode, and settles once they stop
    def keep_moving(self):
        if not self.moving:
            self.moving = True
            # taken out of the scene rather than left to skip their own paint:
            # a few hundred calls that do nothing still cost a whole frame
            self.show_text(False)
        self.settle.start()

    # the scene's labels, hidden while the view moves and back when it settles
    def show_text(self, visible):
        for text in getattr(self.scene(), "text_items", ()):
            text.setVisible(visible)

    # how many device pixels one scene unit covers, for every item of a frame
    # to read instead of working it out from its own painter
    def refresh_draw_scale(self):
        self.draw_scale = self.zoom * self.viewport().devicePixelRatioF()

    def stop_moving(self):
        if not self.moving:
            return
        self.moving = False
        self.show_text(True)
        self.viewport().update()   # now at full quality

    def place_coordinates(self):
        self.coordinates.adjustSize()
        self.coordinates.move(COORDINATES_MARGIN,
                              self.height() - COORDINATES_MARGIN - self.coordinates.height())

    def notify_view_changed(self):
        for callback in self.view_changed_callbacks:
            callback()

    # the box under the cursor, if there is one - a line, a label or an arrow
    # belongs to whatever box it hangs off, and none of them can be grabbed
    def box_at(self, position):
        for item in self.items(position):
            while item is not None:
                if isinstance(item, (NodeItem, PowerNodeItem)):
                    return item
                item = item.parentItem()
        return None

    # grabbing the grid drags the view around. Middle button always pans, left
    # button whenever it did not land on a box, so nodes stay draggable. Asking
    # for a box rather than for any item at all is what lets a graph thick with
    # lines still be dragged: a line lying under the cursor is not something to
    # grab, and the map was refusing to move wherever one crossed.
    def mousePressEvent(self, event):
        grabbing = event.button() == Qt.MiddleButton or (
            event.button() == Qt.LeftButton and self.box_at(event.position().toPoint()) is None
        )
        if grabbing:
            self.panning = True
            self.pan_cursor = event.position().toPoint()
            self.viewport().setCursor(Qt.ClosedHandCursor)
            self.fade_ring(1.0)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        position = event.position().toPoint()

        if self.panning:
            self.keep_moving()
            moved = position - self.pan_cursor
            self.pan_cursor = position
            horizontal = self.horizontalScrollBar()
            vertical = self.verticalScrollBar()
            horizontal.setValue(horizontal.value() - moved.x())
            vertical.setValue(vertical.value() - moved.y())
            self.viewport().update()      # keep the ring under the cursor
            self.notify_view_changed()

        point = self.mapToScene(position)
        self.coordinates.setText(f"x {point.x():.0f}    y {point.y():.0f}")
        self.place_coordinates()
        if not self.coordinates.isVisible():
            fade_in(self.coordinates)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.panning:
            self.panning = False
            self.stop_moving()   # let go: back to full quality at once
            self.viewport().unsetCursor()
            self.fade_ring(0.0)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    # painted in scene coordinates, so the radius is divided by the zoom to keep
    # the ring the same size on screen at any zoom level
    def drawForeground(self, painter, rect):
        super().drawForeground(painter, rect)
        if self.ring_opacity <= 0.01:
            return
        center = self.mapToScene(self.pan_cursor)
        radius = PAN_RING_RADIUS / self.zoom
        border = QColor(*PAN_RING_BORDER)
        fill = QColor(*PAN_RING_FILL)
        border.setAlpha(round(border.alpha() * self.ring_opacity))
        fill.setAlpha(round(fill.alpha() * self.ring_opacity))
        painter.setPen(QPen(border, 0))
        painter.setBrush(fill)
        painter.drawEllipse(center, radius, radius)

    def leaveEvent(self, event):
        if self.coordinates.isVisible():
            fade_out(self.coordinates)
        super().leaveEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.place_coordinates()
        self.refresh_draw_scale()   # a move to another screen changes it
        self.notify_view_changed()

    def apply_zoom(self, value):
        factor = float(value) / self.zoom
        if factor != 1.0:
            self.keep_moving()
            self.scale(factor, factor)
            self.zoom = float(value)
            self.refresh_draw_scale()
            self.notify_view_changed()

    def clear_zoom_animation(self):
        self.zoom_animation = None

    def wheelEvent(self, event):
        step = ZOOM_STEP if event.angleDelta().y() > 0 else 1 / ZOOM_STEP
        # stepping from the target, not the current value, lets quick notches stack.
        # A huge tree can be fitted below ZOOM_MIN; the floor then sits where
        # the view already is, so zooming out stays put instead of snapping in.
        floor = min(ZOOM_MIN, self.zoom_target)
        target = min(max(self.zoom_target * step, floor), ZOOM_MAX)
        if target != self.zoom_target:
            self.zoom_target = target
            if self.zoom_animation is not None:
                self.zoom_animation.stop()
            self.zoom_animation = animate_value(self, self.zoom, target,
                                                self.apply_zoom, ZOOM_MS)
            # DeleteWhenStopped means the animation deletes its C++ side once it
            # finishes on its own; without this, the next wheel notch would call
            # .stop() on a Python handle to an already-deleted object and crash
            self.zoom_animation.finished.connect(self.clear_zoom_animation)
        event.accept()

    # glides back to the starting camera, zoom and position together. The fit
    # is worked out again from start_rect rather than remembered, so it still
    # shows the whole tree after the view was resized or went full screen.
    # whether the camera is where Reset would put it, framing the whole graph -
    # to within a few pixels on screen, which a glide can land short of
    def at_start_camera(self):
        if self.start_rect is None:
            return False
        zoom, center = fit_camera(self, self.start_rect)
        here = self.mapToScene(self.viewport().rect().center())
        near = CAMERA_AT_START_PX / max(self.zoom, 1e-9)   # those pixels, in scene units
        return (abs(self.zoom - zoom) <= zoom * CAMERA_AT_START_ZOOM
                and abs(here.x() - center.x()) <= near and abs(here.y() - center.y()) <= near)

    # `duration` lets a glide keep pace with something else moving at the same
    # time - the boxes of a compact switch, say - rather than its own
    def reset_camera(self, duration=RECENTER_MS):
        if self.start_rect is None:
            end_zoom, end_center = 1.0, QPointF(0, 0)
        else:
            end_zoom, end_center = fit_camera(self, self.start_rect)
        if self.zoom_animation is not None:
            self.zoom_animation.stop()
            self.zoom_animation = None
        self.zoom_target = end_zoom
        start_zoom = self.zoom
        start_center = self.mapToScene(self.viewport().rect().center())

        # zoom eased by ratio, so zooming in and out feel alike
        def step(progress):
            self.apply_zoom(start_zoom * (end_zoom / start_zoom) ** progress)
            self.centerOn(start_center + (end_center - start_center) * progress)
            self.notify_view_changed()

        animate_value(self, 0.0, 1.0, step, duration)

    def fade_ring(self, to):
        def step(value):
            self.ring_opacity = float(value)
            self.viewport().update()
        animate_value(self, self.ring_opacity, to, step)

    def drawBackground(self, painter, rect):
        painter.fillRect(rect, QColor(GRID_BG))

        # zoomed far out the fine lines would be a solid wash, so past
        # GRID_MINOR_MIN_ZOOM only the squares are drawn. Further out still,
        # even those close up, so the square itself is coarsened by a factor of
        # GRID_MAJOR_EVERY at a time - the lines left on screen are always ones
        # the finer grid had too, just fewer of them, and never closer together
        # than the fine lines were at the moment they were dropped
        show_minor = self.zoom >= GRID_MINOR_MIN_ZOOM
        square_step = GRID_SQUARE
        while square_step * self.zoom < GRID_STEP * GRID_MINOR_MIN_ZOOM:
            square_step *= GRID_MAJOR_EVERY
        step = GRID_STEP if show_minor else square_step

        minor_lines, square_lines = [], []
        x_axis = y_axis = None

        first_x = int(rect.left()) - (int(rect.left()) % step)
        x = first_x
        while x < rect.right():
            line = QLineF(x, rect.top(), x, rect.bottom())
            if x == 0:
                x_axis = line
            elif x % square_step == 0:
                square_lines.append(line)
            else:
                minor_lines.append(line)
            x += step

        first_y = int(rect.top()) - (int(rect.top()) % step)
        y = first_y
        while y < rect.bottom():
            line = QLineF(rect.left(), y, rect.right(), y)
            if y == 0:
                y_axis = line
            elif y % square_step == 0:
                square_lines.append(line)
            else:
                minor_lines.append(line)
            y += step

        painter.setPen(QPen(QColor(GRID_LINE_COLOR), 0))   # width 0 : stays 1px when zoomed
        painter.drawLines(minor_lines)
        painter.setPen(QPen(QColor(GRID_SQUARE_COLOR), 0))
        painter.drawLines(square_lines)

        # x=0/y=0 stand out from the rest of the grid in the accent color,
        # faded so they still read as part of the grid rather than an overlay
        axis_color = QColor(TAB_INDICATOR_COLOR)
        axis_color.setAlpha(GRID_AXIS_ALPHA)
        painter.setPen(QPen(axis_color, 0))
        painter.drawLines([line for line in (x_axis, y_axis) if line is not None])

def make_graphics_view():
    scene = QGraphicsScene()
    # without a scene rect the scrollable area is only as big as the items, and
    # an empty grid could not be panned at all
    scene.setSceneRect(-SCENE_EXTENT, -SCENE_EXTENT, SCENE_EXTENT * 2, SCENE_EXTENT * 2)
    view = GridGraphicsView(scene)
    scene.setParent(view)
    view.setRenderHint(QPainter.Antialiasing)
    # icons are drawn at whatever the current zoom is, so they are resampled on
    # every paint: without this they are nearest-neighbour and go visibly blocky
    # as soon as the view is zoomed in past 1:1
    view.setRenderHint(QPainter.SmoothPixmapTransform)
    view.setRenderHint(QPainter.TextAntialiasing)
    view.setBackgroundBrush(QColor(GRID_BG))
    view.setFrameShape(QGraphicsView.NoFrame)
    return view

# Full screen pulls the view out of the stack and lays it over the whole app
# window, so nothing else of the app can remain visible. Leaving it puts the view
# back where it was. Its button lives in the view toolbar, a child of the view,
# so it travels along. Returns the toggle; `on_change` is called whenever the
# state flips - Escape included - so that button can redraw its icon.
class FullscreenToggle:
    def __init__(self, view, stack):
        self.view = view
        self.stack = stack
        self.home_index = None   # where the view sits in the stack while not full screen
        self.on_change = lambda: None

        toggle = self

        class WindowAnchor(QObject):
            def eventFilter(self, watched, event):
                if event.type() in (QEvent.Resize, QEvent.Show) and toggle.is_on():
                    toggle.view.setGeometry(watched.rect())   # the app window resized
                return False

        self.anchor = WindowAnchor(view)   # kept alive by the view
        QShortcut(QKeySequence(Qt.Key_Escape), view,
                  activated=lambda: self.toggle() if self.is_on() else None)

    def is_on(self):
        return self.home_index is not None

    def toggle(self):
        view, stack = self.view, self.stack
        window = view.window()
        if not self.is_on():
            self.home_index = stack.indexOf(view)
            # remember where it sat, in window coordinates, to grow out of it
            start = QRect(stack.mapTo(window, stack.rect().topLeft()), stack.size())
            view.setParent(window)        # out of the stack, over the whole app
            view.setGeometry(start)
            view.show()
            view.raise_()
            grow = QPropertyAnimation(view, b"geometry", view)
            grow.setDuration(ANIMATION_MS)
            grow.setStartValue(start)
            grow.setEndValue(window.rect())
            run(grow)
            window.installEventFilter(self.anchor)   # follow the window's size
        else:
            window.removeEventFilter(self.anchor)
            end = QRect(stack.mapTo(window, stack.rect().topLeft()), stack.size())

            def restore():
                stack.insertWidget(self.home_index, view)    # back into the layout
                stack.setCurrentIndex(self.home_index)
                self.home_index = None
                self.on_change()

            shrink = QPropertyAnimation(view, b"geometry", view)
            shrink.setDuration(ANIMATION_MS)
            shrink.setStartValue(view.geometry())
            shrink.setEndValue(end)
            shrink.finished.connect(restore)
            run(shrink)
        self.on_change()

# the view toolbar's tooltips, one per state of each option
ARROW_MODE_LABELS = {"new": "Arrows: New", "old": "Arrows: Old"}
SNAP_MODE_LABELS = {True: "Snap: On", False: "Snap: Off"}
LOCK_MODE_LABELS = {True: "Graph: Locked", False: "Graph: Free"}
NODE_SIZE_LABELS = {True: "Nodes: Compact", False: "Nodes: Detailed"}
LOCKED_TOOLTIP = "The graph is locked - unlock it in the view bar to change this"
QUICK_DONE_LABELS = {True: "Tick: 1 click", False: "Tick: 2 clicks"}
PICTURE_MODE_LABELS = {"machine": "Pictures: Machine", "item": "Pictures: Item"}
BUILD_REVEAL_LABELS = {"start": "Build: Start", "play": "Build: Play", "skip": "Build: Skip"}
BUILD_REVEAL_ORDER = ["start", "play", "skip"]   # the order a click steps through them
POWER_MODE_LABELS = {True: "Power: On", False: "Power: Off"}
FULLSCREEN_MODE_LABELS = {True: "Full screen: On", False: "Full screen: Off"}
CAMERA_RESET_LABEL = "Camera: Reset"

STEP_BAR_MARGIN = 10   # from the top of the view
STEP_BAR_GAP = 6       # between the arrows and the counter between them
STEP_BAR_ARROW_SIZE = 22
STEP_BAR_FONT_SIZE = 12
SYMBOL_CANVAS = 16               # every drawn symbol is laid out on a 16 unit square
STEP_BAR_ICON_SIZE = 16          # the drawn symbols, laid out on a 16 unit square
STEP_BAR_ICON_SCALE = 2          # drawn at twice that, so they stay crisp on a high DPI screen
STEP_BAR_CHEVRON_WIDTH = 2
STEP_BAR_PLAY_GAP = 14           # extra room setting the play button apart from the arrows
STEP_BAR_PLAY_DURATION_MS = 3000 # a full run, first step to last, at the speed slider's middle
STEP_BAR_SPEED_RANGE = 4         # the slider's ends: this many times slower, or faster
STEP_BAR_SPEED_STEPS = 100
STEP_BAR_SPEED_WIDTH = 64
STEP_BAR_SPEED_GROOVE = "#4a4a4a"
STEP_BAR_SPEED_FILL = "#6e6e6e"      # the groove up to the handle
STEP_BAR_DISABLED_COLOR = TEXT_FAINT   # dimmer than the arrows at rest, still seen on the bar's grey   # an arrow off while a playback runs

# the step bar's symbols, drawn rather than typed: a text arrow depends on the
# font and came out thin and uneven. Stepping is a chevron - once to move a
# step, twice to jump to an end - and playback the filled media shapes, so a
# step and "play" never look alike. Each takes a painter already scaled to a
# 16 unit square, and the color to draw in.
def draw_chevron(painter, color, center_x, pointing, width=STEP_BAR_CHEVRON_WIDTH):
    pen = QPen(color, width)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    back = center_x - 2.5 * pointing
    painter.drawPolyline(QPolygonF([QPointF(back, 3.5), QPointF(center_x + 2.5 * pointing, 8),
                                    QPointF(back, 12.5)]))

# the same chevron as a disclosure arrow, drawn at `angle`: 0 points right, at
# what it would open, and 180 points back left at the panel it would close.
# Turned by hand rather than flipped, so the swing between the two can be eased.
# (its stroke, heading and timing are with the other node info constants)
def draw_caret(p, c, angle):
    p.save()
    p.translate(SYMBOL_CANVAS / 2, SYMBOL_CANVAS / 2)
    p.rotate(angle)
    p.translate(-SYMBOL_CANVAS / 2, -SYMBOL_CANVAS / 2)
    draw_chevron(p, c, SYMBOL_CANVAS / 2, 1, NODE_INFO_CARET_WIDTH)
    p.restore()

STEP_BAR_SYMBOLS = {
    "first": lambda p, c: (draw_chevron(p, c, 5.5, -1), draw_chevron(p, c, 10.5, -1)),
    "previous": lambda p, c: draw_chevron(p, c, 8, -1),
    "next": lambda p, c: draw_chevron(p, c, 8, 1),
    "last": lambda p, c: (draw_chevron(p, c, 5.5, 1), draw_chevron(p, c, 10.5, 1)),
    "play": lambda p, c: (p.setPen(Qt.NoPen), p.setBrush(c),
                          p.drawPolygon(QPolygonF([QPointF(4.5, 2.5), QPointF(4.5, 13.5),
                                                   QPointF(13.5, 8)]))),
    "pause": lambda p, c: (p.setPen(Qt.NoPen), p.setBrush(c),
                           p.drawRoundedRect(QRectF(3.5, 3, 3, 10), 1, 1),
                           p.drawRoundedRect(QRectF(9.5, 3, 3, 10), 1, 1)),
}

# paints one symbol - a function drawing on a 16 unit square - into an icon
# the same drawn symbol as a plain pixmap, `side` px across - for anywhere a
# QIcon is not what is wanted (a label in the info panel, say)
def symbol_pixmap(draw, color, side):
    scale = 4   # drawn large and marked as such, so it stays sharp
    pixmap = QPixmap(side * scale, side * scale)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.scale(side * scale / SYMBOL_CANVAS, side * scale / SYMBOL_CANVAS)
    draw(painter, QColor(color))
    painter.end()
    pixmap.setDevicePixelRatio(scale)
    return pixmap

def symbol_icon(draw, color):
    side = STEP_BAR_ICON_SIZE * STEP_BAR_ICON_SCALE
    pixmap = QPixmap(side, side)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.scale(STEP_BAR_ICON_SCALE, STEP_BAR_ICON_SCALE)
    draw(painter, QColor(color))
    painter.end()
    pixmap.setDevicePixelRatio(STEP_BAR_ICON_SCALE)
    icon = QIcon(pixmap)
    # drawn as is on a disabled button too: Qt's own disabled look would
    # repaint it lighter, undoing a greyed-out color picked on purpose
    icon.addPixmap(pixmap, QIcon.Disabled)
    return icon

def step_bar_icon(symbol, color):
    return symbol_icon(STEP_BAR_SYMBOLS[symbol], color)

# a close cross, drawn on the square's exact middle - a text "×" rides the
# font's baseline and never quite sits in the middle of its button
def draw_close(p, c):
    pen = QPen(c, CLOSE_SYMBOL_STROKE)
    pen.setCapStyle(Qt.RoundCap)
    p.setPen(pen)
    p.drawLine(QPointF(4, 4), QPointF(12, 12))
    p.drawLine(QPointF(12, 4), QPointF(4, 12))

# a house: its roof a peak, its door cut out of the front
def draw_home(p, c):
    pen = QPen(c, 1.6)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawPolyline(QPolygonF([QPointF(1.5, 8), QPointF(8, 2), QPointF(14.5, 8)]))
    p.drawPolyline(QPolygonF([QPointF(3.5, 6.5), QPointF(3.5, 14), QPointF(6.5, 14), QPointF(6.5, 10),
                              QPointF(9.5, 10), QPointF(9.5, 14), QPointF(12.5, 14), QPointF(12.5, 6.5)]))

# puts the drawn cross on `button`, centered, `size` px across: dim at rest,
# bright under the mouse, back a step while held - an icon does not follow a
# stylesheet's :hover, so it is swapped by hand
def set_close_symbol(button, size):
    set_drawn_symbol(button, draw_close, size)

# the same for any drawn symbol. Called again on the same button to change
# what it shows - the full screen button's corners turning in or out - it
# takes the old swapping off first.
def set_drawn_symbol(button, draw, size):
    icons = {state: symbol_icon(draw, color) for state, color in
             (("rest", TAB_SYMBOL_COLOR), ("hover", TEXT_STRONG), ("pressed", TEXT_NORMAL))}
    old = getattr(button, "symbol_swap", None)
    if old is not None:
        button.removeEventFilter(old)
    button.setText("")
    button.setIconSize(QSize(size, size))
    button.setIcon(icons["hover" if button.underMouse() else "rest"])

    class Swap(QObject):
        def eventFilter(self, watched, event):
            try:
                kind = event.type()
                if kind == QEvent.Enter:
                    button.setIcon(icons["hover"])
                elif kind == QEvent.Leave:
                    button.setIcon(icons["rest"])
                elif kind == QEvent.MouseButtonPress:
                    button.setIcon(icons["pressed"])
                elif kind == QEvent.MouseButtonRelease:
                    button.setIcon(icons["hover" if button.underMouse() else "rest"])
                return False
            except RuntimeError:
                return False   # a widget gone while the app closes

    button.symbol_swap = Swap(button)   # kept alive by the button
    button.installEventFilter(button.symbol_swap)

# ---- the view toolbar's symbols, on the same 16 unit square ----

# `base` moved `amount` of the way toward `target`, for a color that comes up
# rather than snapping on
def blend_color(base, target, amount):
    base, target = QColor(base), QColor(target)
    if amount >= 1:
        return target
    if amount <= 0:
        return base
    return QColor(*(round(a + (b - a) * amount) for a, b in
                    ((base.red(), target.red()), (base.green(), target.green()),
                     (base.blue(), target.blue()), (base.alpha(), target.alpha()))))

def outline_pen(color, width=1.5):
    pen = QPen(color, width)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    return pen

def filled(painter, color):
    painter.setPen(Qt.NoPen)
    painter.setBrush(color)

# power: a lightning bolt
def draw_power(p, c):
    filled(p, c)
    p.drawPolygon(QPolygonF([QPointF(9.5, 1), QPointF(3, 9), QPointF(7.5, 9), QPointF(6.5, 15),
                             QPointF(13, 7), QPointF(8.5, 7)]))

# a picture the image folder does not carry: an empty frame with a question
# mark in it, so a missing icon reads as missing rather than as a blank gap
def draw_missing_picture(p, c):
    p.setPen(outline_pen(c, 1.3))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(QRectF(1.5, 2.5, 13, 11), 1.8, 1.8)
    font = p.font()
    font.setPixelSize(9)
    font.setBold(True)
    p.setFont(font)
    p.drawText(QRectF(1.5, 2.5, 13, 11), Qt.AlignCenter, "?")

# how a build shows after Confirm, each a staircase of steps:
# start - only the first step up, the rest left for later
def draw_build_start(p, c):
    p.setPen(outline_pen(c, 1.2))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(QRectF(6.85, 6.6, 2.3, 7.3), 0.6, 0.6)
    p.drawRoundedRect(QRectF(11.6, 2.6, 2.3, 11.3), 0.6, 0.6)
    filled(p, c)
    p.drawRoundedRect(QRectF(1.5, 10, 3.5, 4.5), 0.8, 0.8)

# play - the steps played through on their own
def draw_build_play(p, c):
    filled(p, c)
    p.drawPolygon(QPolygonF([QPointF(4, 2), QPointF(4, 14), QPointF(13.5, 8)]))

# skip - straight past them to the finished end
def draw_build_skip(p, c):
    filled(p, c)
    p.drawPolygon(QPolygonF([QPointF(2, 2.5), QPointF(2, 13.5), QPointF(10, 8)]))
    p.drawRoundedRect(QRectF(11, 2.5, 2.8, 11), 0.8, 0.8)

# machine pictures: a gear
def draw_pictures_machine(p, c):
    filled(p, c)
    for tooth in range(8):
        p.save()
        p.translate(8, 8)
        p.rotate(tooth * 45)
        p.drawRoundedRect(QRectF(-1.3, -7.5, 2.6, 4), 0.6, 0.6)
        p.restore()
    p.drawEllipse(QPointF(8, 8), 5, 5)
    p.setCompositionMode(QPainter.CompositionMode_Clear)
    p.drawEllipse(QPointF(8, 8), 2, 2)
    p.setCompositionMode(QPainter.CompositionMode_SourceOver)

# item pictures: a crate, seen corner on
def draw_pictures_item(p, c):
    p.setPen(outline_pen(c))
    p.setBrush(Qt.NoBrush)
    p.drawPolygon(QPolygonF([QPointF(8, 1.5), QPointF(14, 4.75), QPointF(14, 11.25),
                             QPointF(8, 14.5), QPointF(2, 11.25), QPointF(2, 4.75)]))
    p.drawPolyline(QPolygonF([QPointF(2, 4.75), QPointF(8, 8), QPointF(14, 4.75)]))
    p.drawLine(QPointF(8, 8), QPointF(8, 14.5))

# what the build button is about to do, one glyph each:
# generate - the tree it makes, two boxes feeding a third
def draw_build_generate(p, c):
    p.setPen(outline_pen(c, 1.2))
    p.setBrush(Qt.NoBrush)
    p.drawLine(QPointF(6, 3.5), QPointF(10, 8))
    p.drawLine(QPointF(6, 12.5), QPointF(10, 8))
    filled(p, c)
    p.drawRoundedRect(QRectF(10, 6, 4.5, 4), 1, 1)
    p.drawRoundedRect(QRectF(1.5, 1.5, 4.5, 4), 1, 1)
    p.drawRoundedRect(QRectF(1.5, 10.5, 4.5, 4), 1, 1)

# add - a plus, for the outputs going on top of what is already built
def draw_build_add(p, c):
    filled(p, c)
    p.drawRoundedRect(QRectF(7, 2.5, 2, 11), 1, 1)
    p.drawRoundedRect(QRectF(2.5, 7, 11, 2), 1, 1)

# change - two arrows passing each other, one recipe for another
def draw_build_change(p, c):
    p.setPen(outline_pen(c, 1.5))
    p.setBrush(Qt.NoBrush)
    p.drawLine(QPointF(2.5, 5.5), QPointF(11, 5.5))
    p.drawLine(QPointF(5, 10.5), QPointF(13.5, 10.5))
    filled(p, c)
    p.drawPolygon(QPolygonF([QPointF(14, 5.5), QPointF(10.5, 3.6), QPointF(10.5, 7.4)]))
    p.drawPolygon(QPolygonF([QPointF(2, 10.5), QPointF(5.5, 8.6), QPointF(5.5, 12.4)]))

# cancel - the ring arrow of regenerate, turned back on itself: what was
# changed since the last build put back the way it was
def draw_build_cancel(p, c):
    p.setPen(outline_pen(c, 1.7))
    p.setBrush(Qt.NoBrush)
    ring = QRectF(3.5, 3.5, 9, 9)
    path = QPainterPath()
    path.arcMoveTo(ring, 110)
    path.arcTo(ring, 110, -250)
    p.drawPath(path)
    filled(p, c)
    p.drawPolygon(QPolygonF([QPointF(4.4, 2.6), QPointF(8.6, 3.9), QPointF(5.6, 6.6)]))

# clear - the plus turned over: every output taken off the list, so pressing it
# takes the factory off the map rather than building one
def draw_build_clear(p, c):
    p.save()
    p.translate(SYMBOL_CANVAS / 2, SYMBOL_CANVAS / 2)
    p.rotate(45)
    p.translate(-SYMBOL_CANVAS / 2, -SYMBOL_CANVAS / 2)
    draw_build_add(p, c)
    p.restore()

# regenerate - the same thing round again
def draw_build_regenerate(p, c):
    p.setPen(outline_pen(c, 1.7))
    p.setBrush(Qt.NoBrush)
    ring = QRectF(3.5, 3.5, 9, 9)
    path = QPainterPath()
    path.arcMoveTo(ring, 70)
    path.arcTo(ring, 70, 250)
    p.drawPath(path)
    filled(p, c)
    # the head at the open end of the ring, pointing on round it
    p.drawPolygon(QPolygonF([QPointF(11.6, 2.6), QPointF(7.4, 3.9), QPointF(10.4, 6.6)]))

BUILD_SYMBOLS = {
    "generate": draw_build_generate,
    "add": draw_build_add,
    "change": draw_build_change,
    "regenerate": draw_build_regenerate,
    "clear": draw_build_clear,
}

# detail / compact: a box with its column of text beside the picture, against
# the same box holding the picture alone
def draw_node_size(p, c, compact):
    p.setPen(outline_pen(c, 1.3))
    p.setBrush(Qt.NoBrush)
    if compact:
        p.drawRoundedRect(QRectF(4.5, 4.5, 7, 7), 1.2, 1.2)
        filled(p, c)
        p.drawRoundedRect(QRectF(6.3, 6.3, 3.4, 3.4), 0.8, 0.8)
        return
    p.drawRoundedRect(QRectF(1.5, 3.5, 13, 9), 1.4, 1.4)
    filled(p, c)
    p.drawRoundedRect(QRectF(3, 5.5, 4, 5), 0.8, 0.8)      # the picture
    for row, width in ((6.4, 6), (8.6, 5), (10.3, 3.5)):   # and its lines of text
        p.drawRoundedRect(QRectF(8, row, width, 1.1), 0.5, 0.5)

# lock: a padlock, its shackle standing up when the graph is held and swung
# open to one side when it is free to be moved about and built again
def draw_lock(p, c, locked):
    p.setPen(outline_pen(c, 1.6))
    p.setBrush(Qt.NoBrush)
    shackle = QPainterPath(QPointF(5, 8))
    shackle.lineTo(5, 5.5)
    if locked:
        shackle.arcTo(QRectF(5, 2, 6, 6), 180, -180)
        shackle.lineTo(11, 8)
    else:
        # open: the same hook, swung up and off to the right
        shackle.arcTo(QRectF(5, 1.5, 6, 6), 180, -180)
        shackle.lineTo(11, 6)
    p.drawPath(shackle)
    filled(p, c)
    p.drawRoundedRect(QRectF(2.5, 7.5, 11, 7), 1.4, 1.4)
    p.setCompositionMode(QPainter.CompositionMode_Clear)
    p.drawRoundedRect(QRectF(7.2, 9.6, 1.6, 3), 0.8, 0.8)   # the keyhole
    p.setCompositionMode(QPainter.CompositionMode_SourceOver)

# already done: a tick, the mark a box takes when it is built
def draw_done_tick(p, c):
    pen = QPen(c, 2.2)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    p.drawPolyline(QPolygonF([QPointF(2.5, 8.5), QPointF(6.3, 12.5), QPointF(13.5, 3.5)]))

# snap: a horseshoe magnet
def draw_snap(p, c):
    pen = QPen(c, 3.2)
    pen.setCapStyle(Qt.FlatCap)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    arc = QPainterPath(QPointF(4, 2))
    arc.lineTo(4, 8)
    arc.arcTo(QRectF(4, 4, 8, 8), 180, 180)
    arc.lineTo(12, 2)
    p.drawPath(arc)

# new arrows: a box with the arrow built into its edge, where the line lands
def draw_arrows_new(p, c):
    p.setPen(outline_pen(c))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(QRectF(6.5, 2.5, 8, 11), 1.5, 1.5)
    p.drawLine(QPointF(1, 8), QPointF(6.5, 8))
    filled(p, c)
    p.drawPolygon(QPolygonF([QPointF(6.5, 5), QPointF(6.5, 11), QPointF(10.5, 8)]))

# old arrows: a plain line with its own arrow riding along it
def draw_arrows_old(p, c):
    p.setPen(outline_pen(c))
    p.setBrush(Qt.NoBrush)
    p.drawLine(QPointF(1.5, 14.5), QPointF(14.5, 1.5))
    filled(p, c)
    p.drawPolygon(QPolygonF([QPointF(10.5, 5.5), QPointF(4.8, 7.2), QPointF(8.8, 11.2)]))

# full screen: four corners opening out; leaving it, the same corners turned in
def draw_corners(p, c, inward):
    p.setPen(outline_pen(c, 1.8))
    p.setBrush(Qt.NoBrush)
    if inward:
        corners = [((6, 1.5), (6, 6), (1.5, 6)), ((10, 1.5), (10, 6), (14.5, 6)),
                   ((14.5, 10), (10, 10), (10, 14.5)), ((1.5, 10), (6, 10), (6, 14.5))]
    else:
        corners = [((1.5, 6), (1.5, 1.5), (6, 1.5)), ((10, 1.5), (14.5, 1.5), (14.5, 6)),
                   ((14.5, 10), (14.5, 14.5), (10, 14.5)), ((6, 14.5), (1.5, 14.5), (1.5, 10))]
    for corner in corners:
        p.drawPolyline(QPolygonF([QPointF(x, y) for x, y in corner]))

# starting camera: a camera, its lens a ring
def draw_camera(p, c):
    p.setPen(outline_pen(c))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(QRectF(1.5, 4.5, 13, 9.5), 1.8, 1.8)
    p.drawEllipse(QPointF(8, 9.25), 2.6, 2.6)
    filled(p, c)
    p.drawRoundedRect(QRectF(5, 2, 6, 3), 0.8, 0.8)

VIEW_TOOLBAR_SYMBOLS = {
    "size_detail": lambda p, c: draw_node_size(p, c, False),
    "size_compact": lambda p, c: draw_node_size(p, c, True),
    "lock_on": lambda p, c: draw_lock(p, c, True),
    "lock_off": lambda p, c: draw_lock(p, c, False),
    "done_tick": draw_done_tick,
    "camera": draw_camera,
    "power": draw_power,
    "build_start": draw_build_start,
    "build_play": draw_build_play,
    "build_skip": draw_build_skip,
    "pictures_machine": draw_pictures_machine,
    "pictures_item": draw_pictures_item,
    "snap": draw_snap,
    "arrows_new": draw_arrows_new,
    "arrows_old": draw_arrows_old,
    "fullscreen_enter": lambda p, c: draw_corners(p, c, inward=False),
    "fullscreen_exit": lambda p, c: draw_corners(p, c, inward=True),
}

VIEW_TOOLBAR_PADDING = 3
VIEW_TOOLBAR_SPACING = 3              # on either side of the divider between two buttons
VIEW_TOOLBAR_BUTTON_WIDTH = 52        # room for the widest caption, "Machine"
VIEW_TOOLBAR_BUTTON_HEIGHT = 40       # the icon with its caption under it
VIEW_TOOLBAR_CAPTION_SIZE = 10
VIEW_TOOLBAR_DIVIDER_COLOR = "rgba(255, 255, 255, 0.14)"
VIEW_TOOLBAR_DIVIDER_INSET = 5        # how far short of the bar's edges a divider stops
VIEW_TOOLBAR_ACTIVE_BG = ACCENT_SHADES["blue"]["active"]              # the accent, faint: a toggle switched on
VIEW_TOOLBAR_ACTIVE_HOVER_BG = ACCENT_SHADES["blue"]["active_hover"]

# a column of icon buttons in the view's bottom right corner, one per view
# option plus the camera reset and full screen, each set off from the next by a thin divider. Every
# button spells out its option's current mode in a caption under the icon, so
# the state reads without hovering or knowing what each icon means. Each toggle
# is described by:
#   symbol_for  - the VIEW_TOOLBAR_SYMBOLS key for the option's current state,
#                 so a two-way choice shows which way it is set
#   tooltip_for - the words for that state, "Option: Mode" - shown whole on
#                 hover, the part after the colon as the caption
#   on_toggle   - flips the option
#   active_for  - for an on/off option, whether it is on: lit in the accent
# Anchored like the fullscreen button - its own event filter on the view, so
# it floats over the graph and travels with the view into full screen.
def add_view_toolbar(view):
    bar = QWidget(view)
    bar.setObjectName("view_toolbar")
    bar.setAttribute(Qt.WA_StyledBackground, True)
    bar.setStyleSheet(
        "QWidget#view_toolbar {"
        f"  background: {FULLSCREEN_BUTTON_BG};"
        f"  border-radius: {HOVER_BORDER_RADIUS + 2}px;"
        "}"
    )
    bar_layout = QVBoxLayout(bar)
    bar_layout.setContentsMargins(VIEW_TOOLBAR_PADDING, VIEW_TOOLBAR_PADDING,
                                  VIEW_TOOLBAR_PADDING, VIEW_TOOLBAR_PADDING)
    bar_layout.setSpacing(VIEW_TOOLBAR_SPACING)

    def reposition():
        bar.adjustSize()
        bar.move(view.width() - FULLSCREEN_MARGIN - bar.width(),
                 view.height() - FULLSCREEN_MARGIN - bar.height())
        bar.raise_()

    class Anchor(QObject):
        def eventFilter(self, watched, event):
            if event.type() in (QEvent.Resize, QEvent.Show):
                reposition()
            return False

    bar.anchor = Anchor(bar)   # kept alive by the bar
    view.installEventFilter(bar.anchor)

    icons = {symbol: (symbol_icon(draw, TAB_UNSELECTED_COLOR), symbol_icon(draw, TAB_SELECTED_COLOR))
             for symbol, draw in VIEW_TOOLBAR_SYMBOLS.items()}

    def add_divider():
        line = QWidget(bar)
        line.setAttribute(Qt.WA_StyledBackground, True)
        line.setFixedSize(VIEW_TOOLBAR_BUTTON_WIDTH - 2 * VIEW_TOOLBAR_DIVIDER_INSET, 1)
        line.setStyleSheet(f"background: {VIEW_TOOLBAR_DIVIDER_COLOR};")
        bar_layout.addWidget(line, 0, Qt.AlignHCenter)

    def add_toggle(symbol_for, tooltip_for, on_toggle, active_for=None):
        if bar.findChildren(QToolButton):
            add_divider()
        # a QToolButton rather than a QPushButton: it can lay text under its icon
        button = QToolButton(bar)
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setFixedSize(VIEW_TOOLBAR_BUTTON_WIDTH, VIEW_TOOLBAR_BUTTON_HEIGHT)
        button.setIconSize(QSize(STEP_BAR_ICON_SIZE, STEP_BAR_ICON_SIZE))
        button.setCursor(Qt.PointingHandCursor)
        button.setFocusPolicy(Qt.NoFocus)
        hovered = [False]

        # an icon does not follow a stylesheet's :hover the way text does, and
        # the background depends on the option, so both are set by hand
        def refresh():
            active = bool(active_for and active_for())
            bright = hovered[0] or active
            tooltip = tooltip_for()
            button.setIcon(icons[symbol_for()][1 if bright else 0])
            button.setToolTip(tooltip)
            button.setText(tooltip.split(": ", 1)[-1])
            background = (VIEW_TOOLBAR_ACTIVE_HOVER_BG if hovered[0] else VIEW_TOOLBAR_ACTIVE_BG) if active \
                else (FULLSCREEN_BUTTON_HOVER_BG if hovered[0] else "transparent")
            button.setStyleSheet(
                "QToolButton {"
                "  border: none;"
                "  padding: 3px 0 2px 0;"
                f"  border-radius: {HOVER_BORDER_RADIUS}px;"
                f"  background: {background};"
                f"  color: {TAB_SELECTED_COLOR if bright else TAB_UNSELECTED_COLOR};"
                f"  font-size: {VIEW_TOOLBAR_CAPTION_SIZE}px;"
                "}"
                "QToolButton:pressed {"
                f"  background: {TAB_SYMBOL_PRESS_BG};"
                "}"
            )

        class Hover(QObject):
            def eventFilter(self, watched, event):
                if event.type() in (QEvent.Enter, QEvent.Leave):
                    hovered[0] = event.type() == QEvent.Enter
                    refresh()
                return False

        button.hover = Hover(button)   # kept alive by the button
        button.installEventFilter(button.hover)

        def clicked():
            on_toggle()
            refresh()
            pulse(button)   # it just changed mode: a flash draws the eye to it

        button.clicked.connect(clicked)
        button.refresh = refresh
        bar_layout.addWidget(button)
        refresh()
        reposition()
        return button

    bar.add_toggle = add_toggle
    return bar

# a pair of arrows centered at the top of the view, with the step they are on
# between them, for walking the snapshots a build hands back. The
# arrows stop at the first and the last step rather than wrapping round. A
# double arrow on each end jumps straight to the first or the last step, and a
# play button past them walks the whole build on its own in
# STEP_BAR_PLAY_DURATION_MS.
#
# Anchored the same way the corner pills are: its own event filter on the view
# rather than a layout, so it floats over the graph instead of taking a row.
def add_build_step_bar(view, on_step):
    bar = QWidget(view)
    bar.setObjectName("step_bar")
    bar.setAttribute(Qt.WA_StyledBackground, True)
    bar.setStyleSheet(
        "QWidget#step_bar {"
        f"  background: {FULLSCREEN_BUTTON_BG};"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "}"
    )
    bar_layout = QHBoxLayout(bar)
    bar_layout.setContentsMargins(6, 4, 6, 4)
    bar_layout.setSpacing(STEP_BAR_GAP)

    # every symbol in the colors the bar's buttons use: dim at rest, bright
    # under the mouse - the same pair the counter and the corner pills follow -
    # and greyed right down while a button is off, during a playback
    icons = {symbol: (step_bar_icon(symbol, TAB_UNSELECTED_COLOR), step_bar_icon(symbol, TAB_SELECTED_COLOR),
                      step_bar_icon(symbol, STEP_BAR_DISABLED_COLOR))
             for symbol in STEP_BAR_SYMBOLS}

    # a stylesheet :hover recolors text but not an icon, so the icon is swapped
    # by hand as the mouse comes and goes
    class HoverIcon(QObject):
        def eventFilter(self, watched, event):
            if event.type() in (QEvent.Enter, QEvent.Leave):
                show_symbol(watched, watched.symbol, event.type() == QEvent.Enter)
            return False

    hover_icon = HoverIcon(bar)   # kept alive by the bar

    # hovered is known for certain inside Enter/Leave; anywhere else (the play
    # button flipping to pause under a still mouse) it is read off the button
    def show_symbol(button, symbol, hovered=None):
        button.symbol = symbol
        if hovered is None:
            hovered = button.underMouse()
        if not button.isEnabled():
            button.setIcon(icons[symbol][2])
            return
        button.setIcon(icons[symbol][1 if hovered else 0])

    def make_arrow(symbol):
        button = QPushButton(bar)
        button.setFixedSize(STEP_BAR_ARROW_SIZE, STEP_BAR_ARROW_SIZE)
        button.setIconSize(QSize(STEP_BAR_ICON_SIZE, STEP_BAR_ICON_SIZE))
        button.setCursor(Qt.PointingHandCursor)
        button.setFocusPolicy(Qt.NoFocus)
        button.setStyleSheet(
            "QPushButton {"
            "  border: none;"
            "  padding: 0;"
            f"  border-radius: {HOVER_BORDER_RADIUS}px;"
            "  background: transparent;"
            "}"
            "QPushButton:hover {"
            f"  background: {FULLSCREEN_BUTTON_HOVER_BG};"
            "}"
            "QPushButton:pressed {"
            f"  background: {TAB_SYMBOL_PRESS_BG};"
            "}"
        )
        button.installEventFilter(hover_icon)
        show_symbol(button, symbol)
        return button

    first_button = make_arrow("first")
    first_button.setToolTip("First step")
    previous_button = make_arrow("previous")
    previous_button.setToolTip("Previous step")
    next_button = make_arrow("next")
    next_button.setToolTip("Next step")
    last_button = make_arrow("last")
    last_button.setToolTip("Last step")
    counter = QLabel(bar)
    counter.setAlignment(Qt.AlignCenter)
    counter.setStyleSheet(f"color: {TAB_UNSELECTED_COLOR}; font-size: {STEP_BAR_FONT_SIZE}px;")

    bar_layout.addWidget(first_button)
    bar_layout.addWidget(previous_button)
    bar_layout.addWidget(counter)
    bar_layout.addWidget(next_button)
    bar_layout.addWidget(last_button)

    play_button = make_arrow("play")
    play_button.setToolTip("Play every step")
    bar_layout.addSpacing(STEP_BAR_PLAY_GAP)
    bar_layout.addWidget(play_button)

    # how fast a playback goes: the middle is a full run in
    # STEP_BAR_PLAY_DURATION_MS, each end STEP_BAR_SPEED_RANGE times slower
    # or faster. It stays live while playing.
    speed = QSlider(Qt.Horizontal, bar)
    speed.setObjectName("step_bar_speed")
    speed.setRange(0, STEP_BAR_SPEED_STEPS)
    speed.setValue(STEP_BAR_SPEED_STEPS // 2)
    speed.setFixedSize(STEP_BAR_SPEED_WIDTH, STEP_BAR_ARROW_SIZE)   # room for the handle at either end
    speed.setCursor(Qt.PointingHandCursor)
    speed.setFocusPolicy(Qt.NoFocus)
    speed.setToolTip("Playback speed")
    speed.setStyleSheet(
        "QSlider::groove:horizontal {"
        f"  height: 3px; background: {STEP_BAR_SPEED_GROOVE}; border-radius: 1px;"
        "}"
        "QSlider::sub-page:horizontal {"
        f"  height: 3px; background: {STEP_BAR_SPEED_FILL}; border-radius: 1px;"
        "}"
        "QSlider::handle:horizontal {"
        f"  width: 10px; height: 10px; margin: -4px 0; border-radius: 5px; background: {TAB_UNSELECTED_COLOR};"
        "}"
        "QSlider::handle:horizontal:hover {"
        f"  background: {TAB_INDICATOR_COLOR};"
        "}"
        "QSlider::handle:horizontal:pressed {"
        f"  background: {ACCENT_PRESS_BG};"
        "}"
    )
    bar_layout.addSpacing(2)
    bar_layout.addWidget(speed)

    play_timer = QTimer(bar)
    playing = {"steps": None}   # the build being played, to notice a new one replacing it

    # how long a run from the first step to the last takes at the slider's speed
    def run_duration():
        middle = STEP_BAR_SPEED_STEPS / 2
        return STEP_BAR_PLAY_DURATION_MS / STEP_BAR_SPEED_RANGE ** ((speed.value() - middle) / middle)

    # one tick per step, spaced so the whole run takes run_duration; each
    # step's animation is held to that too, to be done before the next
    def apply_speed():
        steps = playing["steps"]
        if not steps or len(steps) < 2:
            return
        play_timer.setInterval(max(1, round(run_duration() / (len(steps) - 1))))
        view.transition_limit_ms = play_timer.interval()

    # a Confirm that plays its build pushes the slider to full speed for that
    # run only: `auto` stays set while nobody touches the slider, and the run
    # ending puts it back in the middle. Moving it by hand keeps what was picked.
    speed_state = {"auto": False, "setting": False}

    def set_speed(value):
        speed_state["setting"] = True
        speed.setValue(value)
        speed_state["setting"] = False

    def speed_changed(_):
        if not speed_state["setting"]:
            speed_state["auto"] = False
        if play_timer.isActive():
            apply_speed()

    speed.valueChanged.connect(speed_changed)

    # while a playback runs, only its pause and its speed can be touched: the
    # arrows would fight it for the step
    def set_playing(on):
        for button in (first_button, previous_button, next_button, last_button):
            button.setEnabled(not on)
            show_symbol(button, button.symbol)

    def reposition():
        bar.adjustSize()
        bar.move((view.width() - bar.width()) // 2, STEP_BAR_MARGIN)
        bar.raise_()

    # hidden outright while there is nothing to step through, so an empty
    # canvas is not left with a dead control floating over it
    def refresh():
        steps = getattr(view, "build_steps", None)
        if not steps:
            stop()
            if bar.isVisible():
                fade_out(bar)
            return
        counter.setText(f"{view.build_step + 1} / {len(steps)}")
        if not bar.isVisible():
            fade_in(bar)   # the first build: the bar comes in rather than popping up
        reposition()

    def stop():
        play_timer.stop()
        playing["steps"] = None
        view.transition_limit_ms = None
        show_symbol(play_button, "play")
        play_button.setToolTip("Play every step")
        set_playing(False)
        if speed_state["auto"]:
            speed_state["auto"] = False
            set_speed(STEP_BAR_SPEED_STEPS // 2)

    # the whole run takes run_duration whatever the build's length. Starting
    # from the last step plays it again from the top; clicking while playing
    # pauses.
    def toggle_play():
        steps = getattr(view, "build_steps", None)
        if play_timer.isActive():
            stop()
            return
        if not steps or len(steps) < 2:
            return
        if view.build_step >= len(steps) - 1:
            go_to(0)
        playing["steps"] = steps
        apply_speed()
        play_timer.start()
        show_symbol(play_button, "pause")
        play_button.setToolTip("Pause")
        set_playing(True)

    def tick():
        steps = getattr(view, "build_steps", None)
        # a new confirm swapped the build out from under the playback
        if not steps or steps is not playing["steps"]:
            stop()
            return
        go_to(view.build_step + 1)
        if view.build_step >= len(steps) - 1:
            stop()

    play_timer.timeout.connect(tick)

    def go_to(index):
        steps = getattr(view, "build_steps", None)
        if not steps:
            return
        view.build_step = index % len(steps)
        on_step()
        refresh()

    def step(offset):
        # stops at either end instead of wrapping round to the other one
        steps = getattr(view, "build_steps", None)
        if not steps:
            return
        target = view.build_step + offset
        if not 0 <= target < len(steps):
            return
        go_to(target)

    class Anchor(QObject):
        def eventFilter(self, watched, event):
            if event.type() in (QEvent.Resize, QEvent.Show):
                reposition()
            return False

    bar.anchor = Anchor(bar)   # kept alive by the bar
    view.installEventFilter(bar.anchor)

    # taking a step by hand ends the playback rather than fighting it
    def by_hand(action):
        def run():
            stop()
            action()
        return run

    first_button.clicked.connect(by_hand(lambda: go_to(0)))
    previous_button.clicked.connect(by_hand(lambda: step(-1)))
    next_button.clicked.connect(by_hand(lambda: step(1)))
    last_button.clicked.connect(by_hand(lambda: go_to(-1)))
    play_button.clicked.connect(toggle_play)

    # a playback from the first step, for a Confirm set to play the build - at
    # full speed, the slider pushed to its end to show it: whatever was
    # playing is stopped first rather than toggled off
    def play_from_start():
        stop()
        set_speed(speed.maximum())
        speed_state["auto"] = True
        toggle_play()

    bar.refresh = refresh
    bar.play_from_start = play_from_start
    bar.hide()   # nothing built yet: the first build fades it in
    refresh()
    return bar

# =================================================== NODE GRAPH ====================================================
# Sized well above what fits on screen at zoom 1 - fit_view_to_rect zooms out
# to compensate, so the apparent on-screen size barely changes, but the icons
# get baked into much bigger QPixmaps from their source textures, so they are
# not stuck permanently downsampled to a tiny, blurry size.
# both are whole multiples of GRID_SQUARE, so a node dropped in snap mode
# covers an exact block of squares - 4 wide by 2 tall - rather than
# straddling the lines
NODE_WIDTH = GRID_SQUARE * 4   # 480
NODE_HEIGHT = GRID_SQUARE * 2  # 240, tall enough for the recipe name and the machine line
# Compact: a square box of nothing but the machine's picture, for reading a big
# factory as a shape rather than as a list of names. Half the width, so twice
# as many layers fit across the screen, and the layers close up behind them.
NODE_COMPACT_WIDTH = GRID_SQUARE * 2
# what a compact box says under itself, since it says nothing on itself
NODE_COMPACT_NAME_FONT_SIZE = 30
NODE_COMPACT_LINE_FONT_SIZE = 24
NODE_COMPACT_LINE_GAP = 2
NODE_RADIUS = 36             # corner rounding

def node_width():
    return NODE_COMPACT_WIDTH if panel_options["compact"] else NODE_WIDTH
# the view is fitted to the whole graph, so only the ratio between a node and
# its spacing decides how big the nodes come out on screen: tightening the
# spacing while growing the boxes is what reads as "closer and bigger"
NODE_LAYER_SPACING = 960     # horizontal gap between one layer and the next; leaves the
                             # connecting curve enough room to show its full label
NODE_COMPACT_LAYER_SPACING = NODE_COMPACT_WIDTH * 2   # the same gap again, at the smaller size

def layer_spacing():
    return NODE_COMPACT_LAYER_SPACING if panel_options["compact"] else NODE_LAYER_SPACING
NODE_MIN_GAP = GRID_SQUARE
NODE_ROW_SPACING = NODE_HEIGHT + NODE_MIN_GAP
NODE_BG = QColor(GRID_BG).lighter(140)
# a box the user has ticked off as built: its ground goes green, so what is
# standing in the world and what is still to put up read apart at a glance
# across the whole map, at any zoom, without reading a word of it
NODE_DONE_BG = QColor("#1f3b2a")
NODE_BORDER_COLOR = TAB_INDICATOR_COLOR
NODE_OUTPUT_BORDER_COLOR = "#2ecc71"   # the final products themselves
NODE_INPUT_BORDER_COLOR = "#f39c12"    # recipes fed straight from a raw resource, nothing crafted below them
NODE_MANUAL_BORDER_COLOR = "#e8603c"   # reddish orange: nothing any machine makes, brought in by hand
NODE_BYPRODUCT_BORDER_COLOR = "#16a085"
NODE_MERGING_BORDER_COLOR = "#bdc3c7"  # a duplicate recipe about to be folded into its twin next step
NODE_MERGING_GAP = GRID_SQUARE / 2  # the space left between it and its merger, above it
NODE_BORDER_WIDTH = 4
# the mother whose children a build is making right now: a lighter ground and
# a slightly heavier border, so it stands out whatever its type color without
# drowning out the rest of the graph (see NODE_PICKED_LIGHTER)
NODE_FOCUS_BORDER_WIDTH = 6
# every piece of text in the graph - a node's name, the caption under it, a
# line's label - in this one color. The map is read at a distance and over a
# busy ground, so its text runs brighter than the panels' does.
GRAPH_TEXT_COLOR = "#f4f4f4"
NODE_TEXT_COLOR = GRAPH_TEXT_COLOR
NODE_CAPTION_COLOR = "#d6d6d6"    # the caption under the box: a step greyer than the name
NODE_POWER_COLOR = "#a8a8a8"      # the power at the bottom of the box: greyer still
NODE_POWER_FONT_SIZE = 34
NODE_POWER_RANGE_COLOR = "#8a8a8a"   # the two ends of a swinging draw, under the average
NODE_POWER_RANGE_FONT_SIZE = 24
NODE_TEXT_AREA_GAP = 4           # between the name's area and the row kept under it
NODE_FONT_SIZE = 46        # the name inside the box, as big as it fits
NODE_FONT_MIN_SIZE = 16     # a line is shrunk down to this floor before it is just left to overflow
NODE_FONT_SHRINK_STEP = 2
NODE_LINE_COLOR = "#666666"
NODE_LINE_WIDTH = 4
NODE_HOVER_MS = 120          # a node's ground lifting under the mouse, and settling back
PORT_SLIDE_MS = 200          # a line easing across to the port a drag just gave it
NODE_HOVER_LIGHTER = 14      # percent lighter at full hover
NODE_PRESS_DARKER = 110      # while held: QColor.darker's factor
NODE_CLICK_DRAG_THRESHOLD = 4  # px moved; below this a press+release is a click, not a drag
# Two clicks on a box tick it off as built, but only when they come this close
# together - shorter than the system's own double click, which is slow enough
# that clicking one box and then clicking it again to put its panel away was
# ticking it off by accident. Past it the second click is just a click.
NODE_DOUBLE_CLICK_MS = 220
NODE_ICON_SIZE = 178        # the machine's (or item's) own icon, left of the text
NODE_ICON_MARGIN = 22
NODE_CAPTION_FONT_SIZE = 46      # the machine and its count, under the box
NODE_CAPTION_GAP = 6              # between the box's bottom edge and that caption

NODE_IDLE_OPACITY = 0.5     # a node carrying no rate is faded rather than hidden
NODE_MERGING_OPACITY = 0.6  # a temporary node, gone once the next step merges it

NODE_INFO_GAP = 8           # space between a node and its info panel
NODE_INFO_WIDTH = 300
NODE_INFO_TITLE_FONT_SIZE = 14
NODE_INFO_TEXT_FONT_SIZE = 12
NODE_INFO_SMALL_FONT_SIZE = 11   # the kind tag, section titles and the More info list
NODE_INFO_PICTURE_SIZE = 40      # the node's own picture, in the header
NODE_INFO_FLOW_PICTURE_SIZE = 20 # an item going in or coming out
NODE_INFO_TAG_ALPHA = 40         # how much of the node's color the kind tag is filled with
NODE_INFO_MORE_LABEL = "More info"
NODE_INFO_TO_BUILD_LABEL = "Mark as built"
NODE_INFO_BUILT_LABEL = "Built  ✓"
# the button in a node's top right corner that the panel hangs off. The info
# stays shut until it is pressed: a click on the box itself only picks the node
# out, so you can click your way around the map without a panel over it.
NODE_INFO_BUTTON_SIZE = 68
NODE_INFO_COMPACT_BUTTON_SIZE = 40   # on a compact box, which has nothing else on it
NODE_INFO_BUTTON_MARGIN = 14      # from the box's top and right borders
NODE_INFO_BUTTON_GAP = 8          # the name keeps this much clear of it
NODE_INFO_BUTTON_GROUND_ALPHA = 38   # its soft ground, under the mouse or while open
NODE_INFO_CARET_WIDTH = 0.95         # a lighter stroke than the step bar's own chevrons
NODE_INFO_CARET_OPEN_ANGLE = 180     # open, it points back left at the panel it would close
NODE_INFO_CARET_TURN_MS = 160        # the swing between the two
NODE_INFO_MARGIN = 8        # keeps the panel clear of the view's own edges
NODE_INFO_MIN_HEIGHT = 120  # never squeezed past this, however short the view gets
NODE_INFO_SKIP_FIELDS = {"coordinate", "possible_recipes"}   # layout bookkeeping / redundant with recipe

# a belt tier's throughput in items/min - the game's own mSpeed (cm/s), / 2
CONVEYOR_CAPACITY = {1: 60, 2: 120, 3: 270, 4: 480, 5: 780, 6: 1200}
# a pipeline tier's throughput in m³/min
PIPE_CAPACITY = {1: 300, 2: 600}
# what an amount of `item` is counted in, written after the number: cubic
# meters for anything moving in a pipe (data_maker divides the game's own
# liters down), a plain count for anything on a belt
def amount_unit(item):
    return " m³" if getattr(item, "is_fluid", False) else ""

def rate_unit(item):
    if item is POWER_ITEM:
        return "MW"      # power is not carried by the minute, it is just drawn
    return "m³/min" if getattr(item, "is_fluid", False) else "/min"
CONVEYOR_CURVE_STRENGTH = 0.32    # fraction of the horizontal gap used for the bezier control points
CONVEYOR_CURVE_MIN_PULL = 130     # control points never sit closer than this to their endpoint, so a line
                                  # always leaves its slot sideways instead of shooting straight at the node
# compact columns stand half as far apart, and the same pull bent every line
# there into a deep S: it is eased off so they run nearer straight across
CONVEYOR_COMPACT_CURVE_STRENGTH = 0.2
CONVEYOR_COMPACT_CURVE_MIN_PULL = 50

# how far over to the compact curve the lines are: 0 detailed, 1 compact, and
# in between while the switch is gliding the boxes over, so the lines ease
# into their new bend with them rather than snapping to it (see
# ease_line_curves). None follows the mode as it stands.
curve_compactness = [None]

def curve_blend():
    if curve_compactness[0] is None:
        return 1.0 if panel_options["compact"] else 0.0
    return curve_compactness[0]

def curve_strength():
    blend = curve_blend()
    return CONVEYOR_CURVE_STRENGTH + (CONVEYOR_COMPACT_CURVE_STRENGTH - CONVEYOR_CURVE_STRENGTH) * blend

def curve_min_pull():
    blend = curve_blend()
    return CONVEYOR_CURVE_MIN_PULL + (CONVEYOR_COMPACT_CURVE_MIN_PULL - CONVEYOR_CURVE_MIN_PULL) * blend

# the bend of every line on the map run over to the one the mode now asks for,
# alongside the boxes' own glide. Each frame lays the lines again between the
# ends they already have - the boxes moving are what move those.
def ease_line_curves(view, duration):
    target = 1.0 if panel_options["compact"] else 0.0
    running = getattr(view, "curve_animation", None)
    if running is not None:
        running.stop()
    start = curve_compactness[0] if curve_compactness[0] is not None else 1.0 - target

    def step(value):
        curve_compactness[0] = value
        scene = view.scene()
        if scene is None:
            return
        for item in scene.items():
            if isinstance(item, ConveyorEdge):
                item.set_endpoints(item.start, item.end)

    def done():
        view.curve_animation = None
        step(target)
        curve_compactness[0] = None

    curve_compactness[0] = start
    view.curve_animation = animate_value(view, start, target, step, duration)
    view.curve_animation.finished.connect(done)
CONVEYOR_LINE_WIDTH = 4           # a single belt's worth
CONVEYOR_ARROW_CLEARANCE = 2      # breathing room between a line's end and the input arrow it feeds
CONVEYOR_WIDTH_STEP = 1           # extra width per additional belt needed, a gentle grow rather than dramatic
CONVEYOR_MAX_WIDTH = 10
CONVEYOR_LABEL_COLOR = "#cfcfcf"   # a line reads a step under the boxes it joins
CONVEYOR_LABEL_FONT_SIZE = 27
CONVEYOR_LABEL_MIN_FONT_SIZE = 11   # shrunk past this a label is not worth reading anyway
CONVEYOR_LABEL_ROOM_MARGIN = 24     # clear air left at each end of a label's own run
# the lines whose node has its panel open turn the accent blue, to pick that
# node's own supply out of the rest of the map
CONVEYOR_LIVE_COLOR = TAB_INDICATOR_COLOR
# where a line sits in the stack. A picked-out one comes up over every other
# line - crossing the map, it would otherwise be buried under whatever happens
# to be drawn after it, and the color alone cannot be followed through that.
# It stops short of the boxes: a line still passes behind those, picked out or
# not, rather than over their icons and text.
CONVEYOR_Z = -1
CONVEYOR_LIVE_Z = -0.8
CONVEYOR_FADE_SPAN = 0.3   # how much of a two-colored line the change takes: the rest is one color or the other
CONVEYOR_GLOW_MS = 160     # the light coming up along a picked-out node's lines, and going off again
CONVEYOR_LOOP_FLIP_MS = 260   # a loop swinging from under its box to over it, or back
NODE_SELECTED_BORDER_WIDTH = 5   # the box whose panel is open, a touch heavier
# The box picked out of the map, and the one a build is making, are lit by
# their own ground going lighter rather than by a light around them: a glow
# spread over the boxes beside them, and had to be redrawn on every zoom.
NODE_PICKED_LIGHTER = 34        # percent lighter at full
NODE_GLOW_MS = 170              # coming up, and going off again

# The box lit, or put back: its ground comes up rather than switching, and
# goes back down the same way - `lit_level` is how far up it is. Written out
# here rather than on the boxes, since the power node is lit the same way and
# is a class of its own.
def set_node_lit(item, on):
    running = getattr(item, "lit_fade", None)
    if running is not None:
        try:
            running.stop()      # Qt drops a finished one on its own
        except RuntimeError:
            pass
        item.lit_fade = None
    scene = item.scene()
    if scene is None:           # nothing to run an animation on
        item.lit_level = 1.0 if on else 0.0
        item.update()
        return

    def step(value):
        item.lit_level = float(value)
        item.update()

    item.lit_fade = animate_value(scene, getattr(item, "lit_level", 0.0),
                                  1.0 if on else 0.0, step, NODE_GLOW_MS)
    item.lit_fade.finished.connect(lambda: setattr(item, "lit_fade", None))

# how much lighter a box's ground stands right now: the hover under the mouse
# and the light of being picked, both at once
def node_ground(color, hover=0.0, lit=0.0):
    ground = QColor(color)
    return ground.lighter(round(100 + NODE_HOVER_LIGHTER * hover + NODE_PICKED_LIGHTER * lit))


CONVEYOR_LABEL_GAP = 2       # tiny clearance so the label sits right on the curve, not straddling it

# the little filled arrow drawn at each point where a line meets a node,
# marking which way the item is flowing - equilateral, base flush with the
# border and tip pointing onward in the flow's direction (always rightward,
# the way this layout always flows): inward on the left/input side, and
# poking out past the border on the right/output side. The connecting line
# itself reaches all the way to that tip, not just the border.
#
# Shrunk to fit slot_height when that's tighter than the normal size, so a
# node with many inputs/outputs never has its arrows poke past the box's own
# top or bottom edge - entry_point/exit_point use the matching height below
# so the line always still lands exactly on the (possibly shrunk) tip.
NODE_ARROW_SIZE = 40         # side length of the equilateral triangle, at most
# how far a line runs on into the box it meets: past the arrow it lands on, so
# its round cap is hidden under the box and no blunt end shows
CONVEYOR_NODE_OVERLAP = NODE_ARROW_SIZE
# the ports share the node's height minus this much at the top and the bottom:
# spread over the full height, the outer arrows of a 3 or 4 port side land on
# the rounded corners and poke out past them
NODE_PORT_INSET = 24

# where the index-th of `count` ports sits down a node's side, and how tall a
# band each one gets - the one layout both the drawn arrows and the lines'
# endpoints read, so the two can never drift apart
def port_slot_height(count, node_height=NODE_HEIGHT):
    return (node_height - 2 * NODE_PORT_INSET) / count

def port_slot_y(index, count, node_height=NODE_HEIGHT):
    return NODE_PORT_INSET + (index + 0.5) * port_slot_height(count, node_height)

def flow_arrow_size(slot_height):
    return min(NODE_ARROW_SIZE, slot_height)

def flow_arrow_height(slot_height):
    return flow_arrow_size(slot_height) * math.sqrt(3) / 2

def flow_arrow_points(border_x, y, slot_height):
    half = flow_arrow_size(slot_height) / 2
    return QPolygonF([
        QPointF(border_x, y - half),
        QPointF(border_x, y + half),
        QPointF(border_x + flow_arrow_height(slot_height), y),
    ])

# the spots on the power node's bottom edge where its lines meet it: the power
# coming in from the generators on the right, the draw going back out to the
# machines on the left, side by side in the middle of it, each with its own
# triangle. Every line of a side runs to that side's one point. With only the
# one side in the graph - a factory with no generators, or generators alone -
# there is nothing to tell it apart from, so that port sits in the middle.
POWER_PORT_GAP = 40      # clear air between the two triangles' bases: an arrow's own width

def power_port_x(width, feeding, paired=True):
    if not paired:
        return width / 2
    step = (flow_arrow_size(NODE_ARROW_SIZE) + POWER_PORT_GAP) / 2
    return width / 2 + (step if feeding else -step)

# where a box's power line meets its top border: in a corner of the box rather
# than in the middle of everything else, and far enough in to clear the rounded
# corner it would otherwise sit on. The power a box draws comes in on the left
# and the power a generator makes leaves on the right, the way an ingredient
# comes in on the left of a box and a product leaves on its right.
POWER_ARROW_X = NODE_RADIUS + flow_arrow_size(NODE_ARROW_SIZE) / 2

def power_arrow_x(feeding, width=None):
    width = node_width() if width is None else width
    return width - POWER_ARROW_X if feeding else POWER_ARROW_X

# Where a run down the column meets a horizontal border: spread evenly about
# the middle of it, so one run sits dead center and any number of them reads as
# a group centered on the box. The span they spread over stops clear of the
# power arrow off to the left, and is cut back by as much on the right so the
# group stays centered rather than being pushed over by it.
STACK_PORT_GAP = 14

def stack_port_x(index, count, width=None):
    width = node_width() if width is None else width
    arrow = flow_arrow_size(NODE_ARROW_SIZE)
    first = POWER_ARROW_X + arrow / 2 + STACK_PORT_GAP + arrow / 2   # clear of the power arrow
    return first + (width - 2 * first) * (index + 0.5) / max(count, 1)

# the same triangle where a line meets a box on a top or bottom border rather
# than a side - a power line, or a run between two boxes standing in the one
# column. `upward` is the way the material itself goes, which puts the triangle
# inward on the border taking it in and outward on the border giving it,
# exactly as an ingredient's arrow sits on a side border.
# how far past the border line an arrow's base sits, and how far its tip
# reaches from that border. The base clears the border's own stroke - which is
# drawn centered on the edge, half of it either side - rather than landing in
# the middle of it: an arrow in a color of its own, as a power one is, ends up
# fused with the border it crosses otherwise, each eating half the other.
def border_arrow_step():
    return NODE_BORDER_WIDTH / 2

def border_arrow_reach():
    return border_arrow_step() + flow_arrow_height(NODE_ARROW_SIZE)

def border_arrow_points(x, border_y, upward):
    half = flow_arrow_size(NODE_ARROW_SIZE) / 2
    # the whole triangle is moved off the border the way it points, so the
    # border runs on unbroken behind it and the arrow starts where it ends
    base = border_y - border_arrow_step() if upward else border_y + border_arrow_step()
    tip = base - flow_arrow_height(NODE_ARROW_SIZE) if upward else base + flow_arrow_height(NODE_ARROW_SIZE)
    return QPolygonF([
        QPointF(x - half, base),
        QPointF(x + half, base),
        QPointF(x, tip),
    ])

# where the power node sits over a step's machines: the rail it turns on one
# block clear of the topmost box, the node itself centered over the whole graph
# above that. None when there is nothing to power.
def power_layout(nodes):
    boxes = [node.coordinate for node in nodes if not is_power_node(node)]
    if not boxes:
        return None
    top = min(y for _, y in boxes)
    left = min(x for x, _ in boxes)
    right = max(x for x, _ in boxes) + node_width()
    rail_y = top - POWER_RAIL_GAP
    return rail_y, QPointF((left + right - POWER_NODE_WIDTH) / 2,
                           rail_y - POWER_NODE_GAP - POWER_NODE_HEIGHT)

# the box at the top of the map: what every machine under it draws, added up.
# Clicking it brings its lines up out of the background (on_click), and it is
# drawn in the game's own power yellow.
class PowerNodeItem(QGraphicsRectItem):
    def __init__(self, node, on_click, on_info=None):
        super().__init__(0, 0, POWER_NODE_WIDTH, POWER_NODE_HEIGHT)
        self.setPos(*node.coordinate)
        self.node = node
        self.on_click = on_click
        self.live = False
        self.paired_ports = True   # both a feeding and a drawing port, see feed_point
        self.setPen(QPen(QColor(POWER_COLOR), NODE_BORDER_WIDTH))
        self.setBrush(QBrush(NODE_BG))
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Every machine's draw, added up - click to pick out its lines")
        self.setZValue(1)

        # the same caret every other box carries, opening this one's report.
        # It clears the spare/short total beside it, which rides the middle.
        self.info_button = None
        if on_info is not None:
            self.info_button = NodeInfoButton(NODE_INFO_BUTTON_SIZE, POWER_COLOR,
                                              lambda: on_info(node, self), self)
            self.info_button.setPos(POWER_NODE_WIDTH - NODE_INFO_BUTTON_MARGIN - NODE_INFO_BUTTON_SIZE,
                                    NODE_INFO_BUTTON_MARGIN)

        # the bolt the toolbar's own power button is drawn with, in place of
        # the picture the other nodes carry
        bolt = SymbolItem(draw_power, POWER_COLOR, POWER_BOLT_SIZE, self)
        bolt.setPos(NODE_ICON_MARGIN, (POWER_NODE_HEIGHT - POWER_BOLT_SIZE) / 2)
        text_x = NODE_ICON_MARGIN + POWER_BOLT_SIZE + NODE_ICON_MARGIN

        # the name, then what the factory makes and what it takes - the two
        # numbers the node is there to report. All fitted to the room left
        # beside the bolt, the way a node's own name is: a factory drawing
        # gigawatts must not run out of its box.
        # the right of the box is kept for the one number that answers the
        # question: is there power to spare, or is the factory short?
        room = (POWER_NODE_WIDTH - text_x - NODE_ICON_MARGIN) * (1 - POWER_TOTAL_SHARE)
        rows = (POWER_NODE_HEIGHT - 2 * NODE_ICON_MARGIN) / 3

        name = SceneText("Power", self)
        name.setDefaultTextColor(QColor(POWER_COLOR))
        fit_one_line(name, room, rows, POWER_NODE_FONT_SIZE)
        name.setPos(text_x, NODE_ICON_MARGIN)
        self.texts = [name]

        # what the generators make first, in green, and what the machines take
        # under it, in red
        for label, watts, color in ((POWER_MADE_LABEL, node.generated, POWER_MADE_COLOR),
                                    (POWER_DRAWN_LABEL, node.rate, POWER_DRAWN_COLOR)):
            line = SceneText(f"{label} {format_power(watts)}", self)
            line.setDefaultTextColor(QColor(color))
            fit_one_line(line, room, rows, POWER_NODE_VALUE_FONT_SIZE)
            line.setPos(text_x, NODE_ICON_MARGIN + rows * len(self.texts))
            self.texts.append(line)

        # the two of them added up, beside them: what is left over if the
        # generators are ahead, what is missing if they are not, in the color of
        # whichever side is winning
        spare = node.generated - node.rate
        total = SceneText(("+" if spare >= 0 else "−") + format_power(abs(spare)), self)
        total.setDefaultTextColor(QColor(POWER_MADE_COLOR if spare >= 0 else POWER_DRAWN_COLOR))
        total_room = (POWER_NODE_WIDTH - text_x - NODE_ICON_MARGIN) * POWER_TOTAL_SHARE
        fit_one_line(total, total_room, POWER_NODE_HEIGHT - 2 * NODE_ICON_MARGIN, POWER_TOTAL_FONT_SIZE)
        total.setPos(POWER_NODE_WIDTH - NODE_ICON_MARGIN - total.boundingRect().width(),
                     (POWER_NODE_HEIGHT - total.boundingRect().height()) / 2)
        self.texts.append(total)
        self.lines = []   # what transition_scene expects of a node's item

    def center(self):
        return self.pos() + self.rect().center()

    # where a line meets the node: the right of the two ports for one feeding
    # power in, the left for one drawing it back out (see power_port_x).
    # `paired_ports` is set by whoever draws the lines: false when the graph has
    # only the one kind, and that side's port takes the middle instead.
    def feed_point(self, feeding=False):
        return QPointF(self.pos().x() + power_port_x(POWER_NODE_WIDTH, feeding, self.paired_ports),
                       self.pos().y() + POWER_NODE_HEIGHT)

    def paint(self, painter, option, widget=None):
        view = painting_view(widget)
        if getattr(view, "moving", False):
            painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setPen(screen_pen(painter, self.pen(), view_scale(view, painter)))
        painter.setBrush(self.brush())
        painter.drawRoundedRect(self.rect(), NODE_RADIUS, NODE_RADIUS)

    # an item that is neither movable nor selectable ignores the press, and
    # then never sees the release either - so the press is taken here
    def mousePressEvent(self, event):
        event.accept()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.contains(event.pos()):   # released off the box again: not a click
            self.on_click(self.node, self)   # opens its panel, like any other node

    def set_live(self, live):
        self.live = live
        pen = self.pen()
        pen.setWidthF(NODE_FOCUS_BORDER_WIDTH if live else NODE_BORDER_WIDTH)
        self.setPen(pen)
        # ...and its ground lit while it is the one picked
        set_node_lit(self, live)

# The triangle where a power line meets a box, with a bolt cut out of it: the
# node borders come in every color the graph uses, so the bolt is drawn in the
# box's own ground rather than in a color of its own - dark against a yellow
# arrow, against a blue one and against a green one alike, the way a hole in
# the triangle would read. It marks the one arrow on a box that carries power
# rather than something on a belt.
POWER_ARROW_BOLT = 0.52       # the bolt's size against the arrow it sits in

class PowerArrowItem(QGraphicsItem):
    def __init__(self, points, color, parent=None):
        super().__init__(parent)
        self.points = points
        self.color = QColor(color)
        self.setAcceptedMouseButtons(Qt.NoButton)

    def boundingRect(self):
        return self.points.boundingRect()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.color)
        painter.drawPolygon(self.points)
        # centered on the triangle's own middle - the average of its corners,
        # which sits a third of the way from the border to the tip
        box = self.points.boundingRect()
        side = min(box.width(), box.height()) * POWER_ARROW_BOLT
        middle = sum((self.points[i] for i in range(1, 3)), self.points[0]) / 3
        painter.save()
        painter.translate(middle.x() - side / 2, middle.y() - side / 2)
        painter.scale(side / SYMBOL_CANVAS, side / SYMBOL_CANVAS)
        draw_power(painter, NODE_BG)
        painter.restore()

# a drawn symbol - the toolbar's power bolt, the missing picture's frame - put
# into the scene at any size. Drawn rather than loaded, so it is sharp at every
# zoom without a picture's chain of halvings.
class SymbolItem(QGraphicsItem):
    def __init__(self, draw, color, side, parent=None):
        super().__init__(parent)
        self.draw = draw
        self.color = QColor(color)
        self.box = QRectF(0, 0, side, side)
        self.setAcceptedMouseButtons(Qt.NoButton)

    def boundingRect(self):
        return self.box

    def paint(self, painter, option, widget=None):
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.scale(self.box.width() / SYMBOL_CANVAS, self.box.height() / SYMBOL_CANVAS)
        self.draw(painter, self.color)
        painter.restore()

# one machine's power line: straight up out of the box, then - a block clear of
# everything - a curve over to the power node.
class PowerEdge(QGraphicsPathItem):
    # `feeding` is a generator's line into the power node rather than a
    # machine's draw out of it: it is drawn in the green the node reports what
    # is made in, against the red of what is drawn, and its triangles point the
    # other way at both of its ends.
    def __init__(self, box_top, rail_y, power_point, feeding=False):
        super().__init__()
        self.feeding = feeding
        self.color = POWER_MADE_COLOR if feeding else POWER_DRAWN_COLOR
        self.live = False
        self.setZValue(POWER_LINE_Z)   # under the boxes and the supply lines
        # the faintness is in the color rather than the item's opacity: a thin
        # line that keeps out of the way until the power node is picked out
        self.setPen(QPen(self.shade(POWER_LINE_ALPHA), POWER_LINE_WIDTH, Qt.SolidLine, Qt.RoundCap))
        self.set_ends(box_top, rail_y, power_point)

    def shade(self, alpha):
        color = QColor(self.color)
        color.setAlpha(alpha)
        return color

    # laid again from scratch: its machine was dragged, or the graph grew and
    # took the power node with it
    def set_ends(self, box_top, rail_y, power_point):
        # a line starts at the tip of the arrow giving the power and stops at
        # the border where the arrow taking it in begins, the way a conveyor
        # runs between exit_point and entry_point: the triangle carries the
        # flow the rest of the way into the box it lands on.
        reach = border_arrow_reach()
        if self.feeding:
            box_top = QPointF(box_top.x(), box_top.y() - reach)   # off its generator's tip
        else:
            power_point = QPointF(power_point.x(), power_point.y() + reach)
        self.top = box_top          # where it leaves the machine
        self.end = power_point      # ...and where it meets the power node
        self.rail_y = min(rail_y, box_top.y())
        path = QPainterPath(box_top)
        path.lineTo(QPointF(box_top.x(), self.rail_y))
        # only now does it turn: the pull is the drop it has left to make, so
        # the curve leans over rather than kinking
        pull = max(abs(power_point.y() - self.rail_y), GRID_SQUARE)
        path.cubicTo(QPointF(box_top.x(), self.rail_y - pull),
                     QPointF(power_point.x(), self.rail_y - pull * 0.4), power_point)
        self.setPath(path)

    # a thin line held to a minimum width on screen spills past its own bounds
    def boundingRect(self):
        return super().boundingRect().adjusted(-MIN_LINE_BOUNDS_MARGIN, -MIN_LINE_BOUNDS_MARGIN,
                                               MIN_LINE_BOUNDS_MARGIN, MIN_LINE_BOUNDS_MARGIN)

    def set_live(self, live):
        self.live = live
        # over the power lines it crosses while it is the one being followed
        self.setZValue(POWER_LINE_LIVE_Z if live else POWER_LINE_Z)
        pen = self.pen()
        pen.setColor(self.shade(POWER_LINE_LIVE_ALPHA if live else POWER_LINE_ALPHA))
        pen.setWidthF(POWER_LINE_WIDTH * (POWER_LIVE_WIDEN if live else 1))
        self.setPen(pen)
        self.update()

    def paint(self, painter, option, widget=None):
        view = painting_view(widget)
        scale = view_scale(view, painter)
        if getattr(view, "moving", False):
            painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setPen(screen_pen(painter, self.pen(), scale))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path())
        # no head drawn here: the triangles belong to the boxes at either end,
        # where an ingredient's do, and are drawn over them rather than under

def node_label(node):
    if is_power_node(node):
        return "Power"
    if isinstance(node, (Output_Node, Manual_Node)):
        return node.item.display_name
    if isinstance(node, Recipe_Node):
        return node.recipe_name
    return f"Node {node.id}"

# a Recipe_Node carries both pictures - the building it runs in and the item it
# makes - and the current picture mode picks between them. An Output_Node is
# the item itself, so it has only the one either way.
# power has no picture in the game data: it is drawn a bolt of its own
def item_picture(item):
    if item is POWER_ITEM:
        return POWER_PICTURE
    return picture_or_missing(getattr(item, "picture", ""))

MISSING_PICTURE = "<missing>"      # stands in for a picture path: the frame is drawn, not loaded
MISSING_PICTURE_COLOR = TEXT_FAINT # quiet: a stand-in should not pull the eye like a real icon

# The data names each picture by where it sits beside the scripts ("img/..."),
# which is nothing to go on once this is an exe started from somewhere else:
# every path is taken from the folder the app is really running out of.
def picture_file(path):
    return data_maker.data_file(path) if path else path

# the game data names a picture for every item and every building, but the image
# folder does not carry them all. Asked once per path: loading a pixmap to find
# out it is missing is not free.
_loaded_pictures = {}
def loaded_picture(path):
    if path not in _loaded_pictures:
        _loaded_pictures[path] = QPixmap(picture_file(path))
    return _loaded_pictures[path]

def picture_exists(path):
    return bool(path) and not loaded_picture(path).isNull()

# a picture that is not there falls back to the drawn frame rather than leaving
# a blank where an icon belongs - every missing one, whatever it stands for
def picture_or_missing(path):
    return path if picture_exists(path) else MISSING_PICTURE

# how a picture path is drawn instead of loaded - the draw function and its
# color. None means the path is a real image the folder carries, to be loaded.
def picture_drawing(path):
    if path == POWER_PICTURE:
        return draw_power, POWER_COLOR
    if path == MISSING_PICTURE or not picture_exists(path):
        return draw_missing_picture, MISSING_PICTURE_COLOR
    return None

def node_picture(node):
    if is_power_node(node):
        return POWER_PICTURE
    if is_generator(node):
        # whatever else it makes, a generator is known by its building - what
        # it mainly makes is power, which has no picture of its own
        return picture_or_missing(node.machine_picture)
    if getattr(node, "item", None) is POWER_ITEM:
        return POWER_PICTURE   # an output asking for so many megawatts
    if isinstance(node, Recipe_Node):
        if panel_options["picture_mode"] == "item":
            return picture_or_missing(node.item_picture)
        return picture_or_missing(node.machine_picture)
    return picture_or_missing(getattr(node, "picture", ""))

# what a node moves per minute, asked of any kind of node: a recipe is driven
# by the demand handed down to it, the others carry their own rate
#
# `values` is a step's record of what this node's numbers were at that moment,
# from search.snapshot. The node object itself has moved on since - the build
# kept merging and renumbering it - so its numbers are always read from there.
def node_rate(node, values):
    return values["needed_rate"] if isinstance(node, Recipe_Node) else values["rate"]

# sets the name's font to the biggest size, from NODE_FONT_SIZE down, at which
# no single word runs past `width` (a wrap only happens between words) and all
# its rows stand inside `height`. Past NODE_FONT_MIN_SIZE it is left to overflow.
def fit_node_name(text, width, height):
    base = text.font()
    size = NODE_FONT_SIZE
    while True:
        text.setFont(scene_font(base, size))
        text.setTextWidth(width)
        # idealWidth past the text width means a word could not be broken to fit
        fits = (text.document().idealWidth() <= width + 0.5
                and text.boundingRect().height() <= height)
        if fits or size <= NODE_FONT_MIN_SIZE:
            return
        size = max(NODE_FONT_MIN_SIZE, size - NODE_FONT_SHRINK_STEP)

# sets the text's font to the biggest size, from `size` down, at which it stays
# on one line within `width` and `height` - a number wrapped mid-way reads wrong.
# Past NODE_FONT_MIN_SIZE it is left to overflow.
def fit_one_line(text, width, height, size):
    base = text.font()
    while True:
        text.setFont(scene_font(base, size))
        text.setTextWidth(-1)   # its natural width, unwrapped
        if (text.boundingRect().width() <= width and text.boundingRect().height() <= height) \
                or size <= NODE_FONT_MIN_SIZE:
            return
        size = max(NODE_FONT_MIN_SIZE, size - NODE_FONT_SHRINK_STEP)

# the power a recipe's machines draw, in MW, or None for a node with no
# machine. Worked out the way Recipe_Node.recalculate does, from the step's own
# recorded machine count, since the node has been renumbered since. The
# part-clocked last building draws less than its share: power goes with the
# clock to POWER_EXPONENT.
def node_power(node, values):
    if not isinstance(node, Recipe_Node):
        return None
    return power_for(node, values["machine_nb"])

# the two ends of that draw, for a recipe that swings over a range while it
# crafts rather than drawing a steady number. None for every other recipe.
def node_power_range(node, values):
    if not isinstance(node, Recipe_Node):
        return None
    return power_range_for(node, values["machine_nb"])

# the two ends written the way every other power figure is: "500 - 1500 MW"
# while both are in the one unit, "800 MW - 1.50 GW" where the range crosses
# from the one into the other and dropping a unit would read as the wrong number
def format_power_range(low, high):
    low_text, high_text = format_power(low), format_power(high)
    if low_text[-2:] == high_text[-2:]:
        low_text = low_text[:-3]
    return f"{low_text} - {high_text}"

# a number to so many decimals, less the ones that say nothing: "4" rather
# than "4.00", "1.5" rather than "1.50"
def trimmed(value, places):
    text = f"{value:.{places}f}"
    return text.rstrip("0").rstrip(".") if "." in text else text

def machine_count(machine_nb):
    return trimmed(machine_nb, 2)

# the "× 4" of a caption in bold: how many to build is the number looked for
# under a box. Done before the text is fitted, so the width it measures is
# the bold one.
def bold_machine_count(text):
    at = text.toPlainText().find("×")
    if at < 0:
        return
    cursor = QTextCursor(text.document())
    cursor.setPosition(at)
    cursor.movePosition(QTextCursor.End, QTextCursor.KeepAnchor)
    weight = QTextCharFormat()
    weight.setFontWeight(QFont.Bold)
    cursor.mergeCharFormat(weight)

def format_power(megawatts):
    # a recipe loop that can never settle runs the numbers off to nowhere
    # (see SOLVE_RUNAWAY): written out in full it would be a line of digits
    if megawatts >= 1e9:
        return f"{megawatts / 1000:.1e} GW"
    if megawatts >= 1000:
        return f"{trimmed(megawatts / 1000, 2)} GW"
    # a machine running at a few percent draws a fraction of a megawatt: at one
    # decimal every one of them read "0.0 MW" while the factory's total read
    # 0.2 MW, so a small draw is given the digits it needs
    if megawatts >= 1:
        return f"{trimmed(megawatts, 1)} MW"
    if megawatts >= 0.01:
        return f"{trimmed(megawatts, 2)} MW"
    return f"{trimmed(megawatts, 3)} MW" if megawatts else "0 MW"

# (name, caption): the name is all the box itself holds, the caption rests under it
def node_display_lines(node, values):
    if isinstance(node, Recipe_Node):
        return node.recipe_name, f"{node.machine.display_name}  × {machine_count(values['machine_nb'])}"
    if isinstance(node, (Output_Node, Manual_Node)):
        return node.item.display_name, f"{values['rate']:.2f} {rate_unit(node.item)}"
    return node_label(node), ""

def format_node_value(value):
    if isinstance(value, Node):
        return node_label(value)
    if isinstance(value, dict):
        # a flow entry reads as what moves, how much, and between which nodes
        if "item" in value and "rate" in value:
            text = f"{format_node_value(value['item'])} {value['rate']:.2f} {rate_unit(value['item'])}"
            ends = value.get("from") or value.get("to")
            if ends:
                arrow = "←" if "from" in value else "→"
                text += f" {arrow} " + ", ".join(format_node_value(node) for node in ends)
            return text
        return ", ".join(f"{format_node_value(k)}: {format_node_value(v)}" for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return "\n".join(format_node_value(v) for v in value) if value else "—"
    if isinstance(value, float):
        return f"{value:.2f}"
    if hasattr(value, "display_name"):
        return value.display_name
    return str(value)

# every attribute the node object carries, as (name, value) pairs
def node_info_fields(node):
    return [
        (key.replace('_', ' ').capitalize(), format_node_value(value))
        for key, value in vars(node).items()
        if key not in NODE_INFO_SKIP_FIELDS
    ]

# what kind of node it is, in a few words, for the tag under its name
def node_kind(node):
    if is_power_node(node):
        return "Power"
    if is_generator(node):
        return "Generator"
    if isinstance(node, Output_Node):
        return "Byproduct" if node.is_byproduct else "Final product"
    if isinstance(node, Manual_Node):
        return "Brought by hand"
    # extraction: nothing is fed to it. Power is an ingredient of every machine,
    # so it does not count as something being fed in (see input_items).
    if not input_items(node):
        return "Extraction recipe"
    return "Alternate recipe" if node.is_alternate else "Recipe"

# A dropdown left alone takes the wheel as a change of value, so a scroll over
# a panel silently switches whatever dropdown happened to be under the pointer
# - a recipe swapped, a conveyor level changed - while the list the user meant
# to scroll stays put. The wheel is dropped unless the dropdown is actually
# open, where it scrolls the list as it should.
class ClosedDropdownWheel(QObject):
    def eventFilter(self, watched, event):
        if event.type() != QEvent.Wheel or watched.view().isVisible():
            return False
        # handed on to the panel the dropdown sits in, so the list under the
        # pointer scrolls the way it would over any other row of it
        scroller = watched.parentWidget()
        while scroller is not None and not isinstance(scroller, QAbstractScrollArea):
            scroller = scroller.parentWidget()
        if scroller is not None:
            QApplication.sendEvent(scroller.viewport(), event)
        return True

def ignore_closed_wheel(combo):
    combo.setFocusPolicy(Qt.StrongFocus)   # no wheel through a click-focused box either
    combo.wheel_guard = ClosedDropdownWheel(combo)   # kept alive by the combo
    combo.installEventFilter(combo.wheel_guard)
    return combo

def picture_label(path, size):
    picture = QLabel()
    picture.setFixedSize(size, size)
    picture.setStyleSheet("background: transparent;")
    # nothing to load: the power node gets the same drawn bolt as the toolbar
    # button and the box on the map, a missing picture its drawn frame
    drawing = picture_drawing(path)
    if drawing is not None:
        picture.setPixmap(symbol_pixmap(drawing[0], drawing[1], size))
        picture.setAlignment(Qt.AlignCenter)
        return picture
    pixmap = scaled_picture(path, size)
    if not pixmap.isNull():
        picture.setPixmap(pixmap)
        picture.setAlignment(Qt.AlignCenter)
    return picture

_scaled_pictures = {}
def scaled_picture(path, size):
    key = (path, size)
    if key not in _scaled_pictures:
        pixmap = loaded_picture(path)
        if not pixmap.isNull():
            scale = 2   # drawn from twice the size, sharp on a dense screen
            pixmap = pixmap.scaled(size * scale, size * scale, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            pixmap.setDevicePixelRatio(scale)
        _scaled_pictures[key] = pixmap
    return _scaled_pictures[key]

# the same picture as a pixmap, and as an icon for a list or dropdown row -
# the drawn stand-in when there is no image to load
def picture_pixmap(path, size):
    drawing = picture_drawing(path)
    return symbol_pixmap(drawing[0], drawing[1], size) if drawing is not None else loaded_picture(path)

_picture_icons = {}
def picture_icon(path, size):
    key = (path, size)
    if key not in _picture_icons:
        _picture_icons[key] = QIcon(picture_pixmap(path, size))
    return _picture_icons[key]

def info_label(text, color, size=NODE_INFO_TEXT_FONT_SIZE, bold=False, wrap=False):
    label = QLabel(text)
    label.setStyleSheet(f"color: {color}; font-size: {size}px; background: transparent;"
                        + (" font-weight: bold;" if bold else ""))
    label.setWordWrap(wrap)
    return label

# floating card of a node's info, hidden until a node is clicked open.
# panel.set_node(node, values) fills it - the most useful numbers first, what
# goes in and comes out, and every raw field under a More info toggle.
# panel.wanted_height() is the height its content asks for; panel.on_resize,
# set by whoever places it, is called when More info opens or shuts.
def make_node_info_panel(parent):
    panel = QWidget(parent)
    panel.setObjectName("node_info_panel")
    panel.setAttribute(Qt.WA_StyledBackground, True)
    # scoped to the panel itself: an unscoped rule is inherited by every child,
    # which drew the same border again around everything inside
    panel.setStyleSheet(
        "QWidget#node_info_panel {"
        f"  background-color: {DIALOG_BG};"
        f"  border: 1px solid {OUTPUT_FIELD_BORDER};"
        f"  border-radius: {HOVER_BORDER_RADIUS + 2}px;"
        "}"
    )
    panel.setFixedWidth(NODE_INFO_WIDTH)

    layout = QVBoxLayout(panel)
    layout.setContentsMargins(14, 14, 14, 14)
    layout.setSpacing(0)

    # the content is rebuilt for each node inside this one holder
    body = QWidget()
    body.setStyleSheet("background: transparent;")
    body_layout = QVBoxLayout(body)
    body_layout.setContentsMargins(0, 0, PANEL_SCROLLBAR_WIDTH, 0)
    body_layout.setSpacing(10)

    state = {"more": False}

    def clear():
        while body_layout.count():
            entry = body_layout.takeAt(0)
            if entry.widget() is not None:
                entry.widget().hide()   # out of sight now, not only once deleted
                entry.widget().deleteLater()

    def section_title(text):
        title = info_label(text.upper(), PANEL_TITLE_COLOR, NODE_INFO_SMALL_FONT_SIZE, bold=True)
        title.setStyleSheet(title.styleSheet() + f" letter-spacing: {PANEL_TITLE_SPACING}px;")
        return title

    # rows of a quiet name against a value set to the right
    def stats(pairs, value_color=TEXT_STRONG, size=NODE_INFO_TEXT_FONT_SIZE, name_color=TEXT_MUTED):
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(4)
        grid.setColumnStretch(1, 1)
        # a pair may carry a color of its own, for a value that means something
        # by its color (power made against power drawn)
        for row, (name, value, *own_color) in enumerate(pairs):
            grid.addWidget(info_label(name, name_color, size), row, 0, Qt.AlignLeft | Qt.AlignTop)
            value_label = info_label(value, own_color[0] if own_color else value_color, size, wrap=True)
            value_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
            # a long unbroken value (a file path) wraps within the card rather
            # than widening it past its edge
            value_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            grid.addWidget(value_label, row, 1)
        return grid_widget

    # an item going in or out: its picture, its name, its rate
    def flow_rows(title, flows):
        block = QWidget()
        block_layout = QVBoxLayout(block)
        block_layout.setContentsMargins(0, 0, 0, 0)
        block_layout.setSpacing(4)
        block_layout.addWidget(section_title(title))
        for item, rate in flows:
            row = QHBoxLayout()
            row.setSpacing(8)
            row.addWidget(picture_label(item_picture(item), NODE_INFO_FLOW_PICTURE_SIZE))
            row.addWidget(info_label(item.display_name, TEXT_NORMAL), 1)
            row.addWidget(info_label(f"{rate:,.2f} {rate_unit(item)}", TEXT_STRONG))
            block_layout.addLayout(row)
        return block

    def header(node):
        box = QWidget()
        row = QHBoxLayout(box)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        row.addWidget(picture_label(node_picture(node), NODE_INFO_PICTURE_SIZE), 0, Qt.AlignTop)
        column = QVBoxLayout()
        column.setSpacing(4)
        column.addWidget(info_label(node_label(node), DIALOG_TEXT_COLOR, NODE_INFO_TITLE_FONT_SIZE,
                                    bold=True, wrap=True))
        # the kind, in the color the node is drawn with
        color = QColor(node_border_color(node))
        tag = info_label(node_kind(node), color.name(), NODE_INFO_SMALL_FONT_SIZE, bold=True)
        tag.setStyleSheet(tag.styleSheet() +
                          f" background: rgba({color.red()}, {color.green()}, {color.blue()}, {NODE_INFO_TAG_ALPHA});"
                          f" border-radius: {HOVER_BORDER_RADIUS}px; padding: 1px 6px;")
        column.addWidget(tag, 0, Qt.AlignLeft)
        row.addLayout(column, 1)
        return box

    # the button that ticks a node off as built, and un-ticks it: the same
    # thing a double click on the box does, for anyone who would rather press
    # a button than know that. Its ground is the green the box itself takes.
    def done_button(node):
        button = QPushButton()
        button.setCursor(Qt.PointingHandCursor)
        button.setFocusPolicy(Qt.NoFocus)

        def refresh():
            done = panel.is_done(node)
            button.setText(NODE_INFO_BUILT_LABEL if done else NODE_INFO_TO_BUILD_LABEL)
            ground = NODE_DONE_BG.name() if done else OUTPUT_FIELD_BG
            button.setStyleSheet(
                "QPushButton {"
                f"  background: {ground};"
                f"  color: {TEXT_STRONG if done else TEXT_NORMAL};"
                f"  border: 1px solid {NODE_OUTPUT_BORDER_COLOR if done else OUTPUT_FIELD_BORDER};"
                f"  border-radius: {HOVER_BORDER_RADIUS}px;"
                f"  font-size: {NODE_INFO_TEXT_FONT_SIZE}px;"
                "  padding: 6px;"
                "}"
                f"QPushButton:hover {{ border-color: {NODE_OUTPUT_BORDER_COLOR}; }}"
            )

        button.clicked.connect(lambda: panel.on_complete(node))
        refresh()
        return button

    def more_block(node):
        block = QWidget()
        block_layout = QVBoxLayout(block)
        block_layout.setContentsMargins(0, 0, 0, 0)
        block_layout.setSpacing(6)

        toggle = QPushButton()
        toggle.setCursor(Qt.PointingHandCursor)
        toggle.setFocusPolicy(Qt.NoFocus)
        toggle.setStyleSheet(
            "QPushButton {"
            "  background: transparent; border: none; text-align: left;"
            f"  color: {TEXT_ACCENT}; font-size: {NODE_INFO_SMALL_FONT_SIZE}px;"
            f"  padding: 4px 6px; border-radius: {HOVER_BORDER_RADIUS}px;"
            "}"
            f"QPushButton:hover {{ background: {TAB_SYMBOL_HOVER_BG}; color: {TAB_SELECTED_COLOR}; }}"
            f"QPushButton:pressed {{ background: {TAB_SYMBOL_PRESS_BG}; }}"
        )
        fields = stats(node_info_fields(node), TEXT_NORMAL, NODE_INFO_SMALL_FONT_SIZE, TEXT_FAINT)
        fields.setVisible(state["more"])

        def refresh():
            toggle.setText(f"{NODE_INFO_MORE_LABEL}  {'▴' if state['more'] else '▾'}")

        def flip():
            state["more"] = not state["more"]
            refresh()
            fields.setVisible(state["more"])
            if state["more"]:
                fade_in(fields)
            # measured on the next pass: right now the rows that just went away
            # still count toward the layout, and the panel would keep the
            # height it had - looking as though it had not closed at all
            if panel.on_resize is not None:
                QTimer.singleShot(0, panel.on_resize)

        toggle.clicked.connect(flip)
        refresh()
        block_layout.addWidget(toggle, 0, Qt.AlignLeft)
        block_layout.addWidget(fields)
        return block

    showing = [None, None]   # the node on it now, and its numbers

    def set_node(node, values):
        showing[:] = [node, values]
        clear()
        body_layout.addWidget(header(node))
        body_layout.addWidget(make_panel_divider())

        if is_power_node(node):
            # the factory's power in one place: what the generators make, what
            # the machines take, and whether that leaves anything over
            taking = sorted(node.products[0]["to"].items(), key=lambda pair: -pair[1])
            making = sorted(node.ingredients[0]["from"].items(), key=lambda pair: -pair[1])
            spare = node.generated - node.rate
            # The machines whose draw is a range do not all peak at once, but
            # they can: the factory's own draw swings between the sum of their
            # low ends and the sum of their high ones, with every steady
            # machine counted in both. Worth saying, because the totals beside
            # it are averages - build to those and the factory browns out at
            # the top of the swing.
            low = high = 0.0
            swinging = 0
            for machine, watts in taking:
                # read off the machines as they stand, the way the rates
                # beside them are: this panel is only handed its own node's
                # recorded numbers
                ends = power_range_for(machine, getattr(machine, "machine_nb", 0))
                if ends is None:
                    low, high = low + watts, high + watts
                else:
                    low, high = low + ends[0], high + ends[1]
                    swinging += 1
            rows = [("Made", format_power(node.generated), POWER_MADE_COLOR),
                    ("Drawn", format_power(node.rate), POWER_DRAWN_COLOR)]
            if swinging:
                rows.append(("Between", format_power_range(low, high), POWER_DRAWN_COLOR))
            rows += [("Spare" if spare >= 0 else "Short", format_power(abs(spare)),
                      POWER_MADE_COLOR if spare >= 0 else POWER_DRAWN_COLOR),
                     ("Machines", f"{len(taking)} drawing"
                      + (f", {swinging} of them swinging" if swinging else ""))]
            body_layout.addWidget(stats(rows))

            def power_rows(title, entries, color):
                block = QWidget()
                block_layout = QVBoxLayout(block)
                block_layout.setContentsMargins(0, 0, 0, 0)
                block_layout.setSpacing(4)
                block_layout.addWidget(section_title(title))
                for machine, watts in entries:
                    row = QHBoxLayout()
                    row.setSpacing(8)
                    row.addWidget(picture_label(node_picture(machine), NODE_INFO_FLOW_PICTURE_SIZE))
                    row.addWidget(info_label(node_label(machine), TEXT_NORMAL), 1)
                    row.addWidget(info_label(format_power(watts), color))
                    block_layout.addLayout(row)
                return block

            if making:
                body_layout.addWidget(power_rows("In", making, POWER_MADE_COLOR))
            body_layout.addWidget(power_rows("Out", taking, POWER_DRAWN_COLOR))

        elif isinstance(node, Recipe_Node):
            # the numbers of the step being shown, not of the node as it stands now
            machine_nb = values["machine_nb"]
            full = int(machine_nb)
            clock = machine_nb - full
            buildings = full + (1 if clock > 1e-9 else 0)
            built = f"{buildings} building{'s' if buildings != 1 else ''}"
            if clock > 1e-9 and full:
                built += f", last at {clock * 100:.0f}%"
            elif clock > 1e-9:
                built = f"1 building at {clock * 100:.0f}%"
            crafts = 60 / node.duration * machine_nb
            # the recipe this one node runs - any recipe of anything it
            # supplies: picking another rebuilds the tree
            options = recipe_options(supplied_items(node), node.recipe)
            # picking here rebuilds that node's subtree, which a locked graph
            # does not allow: the row still shows what it runs, greyed out
            if len(options) > 1 and panel.on_recipe_pick is not None:
                line = QWidget()
                line_layout = QHBoxLayout(line)
                line_layout.setContentsMargins(0, 0, 0, 0)
                line_layout.setSpacing(OUTPUT_RECIPE_GAP)
                line_layout.addWidget(info_label("Recipe", TEXT_MUTED))
                field, get_recipe = make_recipe_dropdown(
                    node.needed_item, node.recipe, options=options,
                    on_change=lambda: panel.on_recipe_pick(node, get_recipe()))
                field.setToolTip(LOCKED_TOOLTIP if panel_options["locked"]
                                 else "Switch this node's recipe and rebuild the tree")
                field.setEnabled(not panel_options["locked"])
                line.setEnabled(not panel_options["locked"])
                line_layout.addWidget(field, 1)
                body_layout.addWidget(line)
            # a generator's line says what it makes, in green; every other
            # machine's says what it takes, in red
            if is_generator(node):
                made = next((entry["rate"] for entry in node.products if entry["item"] is POWER_ITEM), 0.0)
                power_row = ("Power made", format_power(made), POWER_MADE_COLOR)
            else:
                power_row = ("Power", format_power(node_power(node, values)), POWER_DRAWN_COLOR)
            rows = [("Machine", f"{html.escape(node.machine.display_name)}&nbsp; "
                                f"<b>× {machine_count(machine_nb)}</b>"),
                    ("Buildings", built),
                    power_row]
            # what it swings between, under what it draws on average
            ends = node_power_range(node, values)
            if ends is not None:
                rows.append(("Between", format_power_range(*ends), POWER_DRAWN_COLOR))
            body_layout.addWidget(stats(rows))
            if node.recipe.ingredients:
                body_layout.addWidget(flow_rows("In", [(e["item"], e["amount"] * crafts)
                                                       for e in node.recipe.ingredients]))
            body_layout.addWidget(flow_rows("Out", [(e["item"], e["amount"] * crafts)
                                                    for e in node.recipe.products]))
        else:
            body_layout.addWidget(stats([("Rate", f"{values['rate']:,.2f} {rate_unit(node.item)}")]))

        body_layout.addWidget(make_panel_divider())
        # the power node is the whole factory's tally rather than anything to
        # put up, so it is the one box with nothing to tick off
        if not is_power_node(node) and panel.on_complete is not None:
            body_layout.addWidget(done_button(node))
        body_layout.addWidget(more_block(node))

        # into a panel already showing, Qt shows new widgets only on its next
        # pass - until then they count for nothing, and the height measured for
        # the next node came out as the bare margins. Shown here, they count.
        for index in range(body_layout.count()):
            body_layout.itemAt(index).widget().show()

    def wanted_height():
        # measured from the layout as it stands now: a row just hidden or shown
        # is only taken into account once the layout has been run again, and
        # without this the panel kept the height it had before
        body_layout.activate()
        margins = layout.contentsMargins()
        inner = NODE_INFO_WIDTH - margins.left() - margins.right()
        content = (body_layout.totalHeightForWidth(inner) if body_layout.hasHeightForWidth()
                   else body_layout.totalSizeHint().height())
        return margins.top() + margins.bottom() + content

    panel.set_node = set_node
    # the same node again, for when something outside it changed what its rows
    # should say - the graph being locked, say
    panel.refresh = lambda: set_node(*showing) if showing[0] is not None else None
    panel.wanted_height = wanted_height
    panel.on_resize = None
    panel.on_recipe_pick = None   # (node, recipe), set by whoever can rebuild the tree
    panel.on_complete = None      # (node), the same - ticks it off as built
    panel.is_done = lambda node: False

    # a node with many fields is taller than the view it floats over, so the
    # body scrolls inside whatever height position_info_panel leaves it rather
    # than running off the bottom of the screen
    scroll = QScrollArea()
    scroll.setWidget(body)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
    scroll.setStyleSheet(
        "QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; }"
        "QScrollBar:vertical {"
        "  background: transparent;"
        f"  width: {PANEL_SCROLLBAR_WIDTH}px;"
        "  margin: 0;"
        "}"
        "QScrollBar::handle:vertical {"
        f"  background: {PANEL_SCROLLBAR_COLOR};"
        f"  border-radius: {PANEL_SCROLLBAR_WIDTH // 2}px;"
        "  min-height: 24px;"
        "}"
        "QScrollBar::handle:vertical:hover {"
        f"  background: {PANEL_SCROLLBAR_HOVER_COLOR};"
        "}"
        "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }"
    )

    layout.addWidget(scroll, 1)
    panel.hide()
    return panel

def snap_to_grid(value):
    return round(value / SNAP_STEP) * SNAP_STEP

# the distance between two stacked nodes' centers, rounded up onto the grid so
# packed rows and a parent centered between its children both stay on it
LAYOUT_ROW = math.ceil(NODE_ROW_SPACING / SNAP_STEP) * SNAP_STEP
# extra room where a branch with children of its own meets its neighbor, so
# separate branches read as separate groups. Siblings that are single nodes
# stay at the tight LAYOUT_ROW. Two grid squares, to stay on the grid and to
# keep the paths of lines apart.
LAYOUT_BRANCH_GAP = 2 * SNAP_STEP
# Compact boxes close that gap up to a single square. The row itself cannot
# shrink - a compact box keeps its height, and the two lines of text under it
# need most of the square below - so the room between branches is where a
# compact graph comes in vertically.
LAYOUT_COMPACT_BRANCH_GAP = SNAP_STEP

def layout_branch_gap():
    return LAYOUT_COMPACT_BRANCH_GAP if panel_options["compact"] else LAYOUT_BRANCH_GAP
LAYOUT_SWAP_ROUNDS = 200     # most sibling swaps kept before the search stops improving the order

# ---- tree layout ----
#
# One placement for the finished tree, worked out from nothing but the graph
# itself (layers and links). Outputs sit in layer 0 at x = 0; everything they
# need grows leftward, a layer per column.
#
# The vertical space is a tidy tree:
#   - every node belongs to one parent for the purpose of placement: the first
#     consumer one layer up that reaches it, walking top to bottom. A node
#     several recipes share still has all its lines; it just hangs from one.
#   - a parent's children go top to bottom in its recipe's ingredient order,
#     then reordered to untangle the lines (see layout_tree).
#   - sibling subtrees are pushed apart just far enough that no column of one
#     runs into the same column of the other. So a branch with many children
#     gets exactly the room they take, while a plain chain beside it keeps a
#     single row and a short branch tucks in under a deep one's overhang -
#     room where it is needed, rather than every branch spread out evenly.
#   - each parent sits centered on its first and last child.

def is_byproduct(node):
    return getattr(node, "is_byproduct", False)

# the daughters a node hangs from it, in the order its recipe lists the
# ingredients they supply
# - or, once a placement has been tried, by `priority`: where each wants to be
def ordered_daughters(node, present, priority=None):
    ingredient_order = {entry["item"]: index for index, entry in enumerate(node.ingredients)}

    def rank(daughter):
        supplied = [ingredient_order[p["item"]] for p in daughter.products if p["item"] in ingredient_order]
        if not supplied and daughter.item in ingredient_order:
            supplied = [ingredient_order[daughter.item]]
        return min(supplied, default=len(ingredient_order))

    candidates = [d for d in node.daughter_nodes if d in present and not is_byproduct(d)]
    if priority:
        # one the swaps never placed (newly claimed by this parent) goes last
        return sorted(candidates, key=lambda d: (priority.get(d, len(candidates)), rank(d)))
    return sorted(candidates, key=rank)

# lays subtrees top to bottom as tightly as their columns allow. Each subtree
# is (contour, offsets): contour maps a layer to the (top, bottom) centers it
# fills there, offsets every node's y - both relative to the subtree's own
# root at 0. Returns where each root landed and the combined contour.
def pack_subtrees(subtrees):
    shifts, merged = [], {}
    previous_is_branch = False
    for contour, _ in subtrees:
        is_branch = len(contour) > 1   # reaches past its own column: it has children
        if not merged:
            shift = 0
        else:
            spacing = LAYOUT_ROW + (layout_branch_gap() if is_branch or previous_is_branch else 0)
            shift = max((merged[layer][1] - top + spacing
                         for layer, (top, _) in contour.items() if layer in merged),
                        default=shifts[-1] + spacing)
        shifts.append(shift)
        previous_is_branch = is_branch
        for layer, (top, bottom) in contour.items():
            if layer in merged:
                merged[layer] = (min(merged[layer][0], top + shift), max(merged[layer][1], bottom + shift))
            else:
                merged[layer] = (top + shift, bottom + shift)
    return shifts, merged

# The order siblings go in decides how much the lines between the branches
# cross. The recipe's own ingredient order comes first, then siblings are
# swapped around for as long as it untangles the graph: fewer crossing lines
# first, then shorter lines - which is what pulls things fed by the same
# producer, or feeding the same consumer, next to each other on their paths.
def layout_tree(nodes):
    present = set(nodes)
    links = [(mother, node) for node in nodes for mother in node.mother_nodes
             if mother in present and mother is not node]

    def score():
        return (count_crossings(links), sum(abs(m.coordinate[1] - d.coordinate[1]) for m, d in links))

    def roots_of(children):
        claimed = {kid for kids in children.values() for kid in kids}
        return [node for node in nodes if node not in claimed and node.layer == 0 and not is_byproduct(node)]

    # the recipes' own order first, then: two siblings next to each other
    # swap places, and the swap is kept only when the placement it gives
    # crosses less (or, crossing as much, draws shorter lines). Tried over
    # every pair of neighbors, the outputs included, until no swap helps.
    # A swap can change which consumer a shared node hangs from, so the
    # groups of siblings are read again after every kept one.
    children = place_tree(nodes, None)
    priority = {}
    for group in [roots_of(children)] + list(children.values()):
        for index, node in enumerate(group):
            priority[node] = index
    best = (score(), {node: node.coordinate for node in nodes})

    for _ in range(LAYOUT_SWAP_ROUNDS):
        tick_loading()      # the longest stretch of a load: keep the cog turning
        kept = False
        groups = [roots_of(children)] + [kids for kids in children.values() if len(kids) > 1]
        for group in groups:
            for first, second in zip(group, group[1:]):
                priority[first], priority[second] = priority[second], priority[first]
                trial_children = place_tree(nodes, priority)
                trial = score()
                if trial < best[0]:
                    best = (trial, {node: node.coordinate for node in nodes})
                    children = trial_children
                    for group_after in [roots_of(children)] + list(children.values()):
                        for index, node in enumerate(group_after):
                            priority[node] = index
                    kept = True
                    break
                priority[first], priority[second] = priority[second], priority[first]
            if kept:
                break
        if not kept:
            break

    for node, coordinate in best[1].items():
        node.coordinate = coordinate

# how many pairs of lines cross, each taken as the straight run from the
# consumer's left side to the producer's right side. Two lines meeting at a
# shared node do not count.
def count_crossings(links):
    def segment(mother, daughter):
        mx, my = mother.coordinate
        dx, dy = daughter.coordinate
        return (mx, my + NODE_HEIGHT / 2), (dx + node_width(), dy + NODE_HEIGHT / 2)

    def turn(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    segments = [(m, d, *segment(m, d)) for m, d in links]
    crossings = 0
    for i, (m1, d1, a, b) in enumerate(segments):
        for m2, d2, c, e in segments[i + 1:]:
            if {m1, d1} & {m2, d2}:
                continue
            if turn(a, b, c) * turn(a, b, e) < 0 and turn(c, e, a) * turn(c, e, b) < 0:
                crossings += 1
    return crossings

# one placement of the tree, siblings in the order `priority` wants them
# (None: the recipes' own ingredient order). Returns which node hangs from which.
def place_tree(nodes, priority):
    present = set(nodes)

    # the placement parent of each node, claimed top to bottom
    children = {node: [] for node in nodes}
    claimed = set()
    # Two recipes feeding each other stand in the one column (see set_stacked),
    # so neither is the other's placement parent - and before, the one that
    # had no consumer a column over went unclaimed, and everything it needed
    # with it: the Ficsonium tree fell almost whole to place_in_free_row and
    # came out packed row on row. The pair hangs as one instead: the partner
    # right under the node that reached it, and what either of them needs
    # hanging from the two.
    partner = {}

    def claim(node):
        own = ordered_daughters(node, present, priority)
        mate = next((d for d in own if d.layer == node.layer and d is not node and d not in claimed), None)
        if mate is not None and node not in partner.values():
            claimed.add(mate)
            partner[node] = mate
            own = own + ordered_daughters(mate, present, priority)
        for daughter in own:
            if daughter in claimed or daughter.layer != node.layer + 1:
                continue
            claimed.add(daughter)
            children[node].append(daughter)
        for child in children[node]:
            claim(child)

    roots = [node for node in nodes if node.layer == 0 and not is_byproduct(node)]
    if priority:
        roots.sort(key=lambda root: priority.get(root, len(roots)))
    for root in roots:
        claimed.add(root)
        claim(root)

    def build(node):
        kids = children[node]
        mate = partner.get(node)
        # a pair takes two rows of its column, the partner in the lower one,
        # and the two of them sit centered on what they need together
        above = snap_to_grid(LAYOUT_ROW / 2) if mate is not None else 0
        own = {node: -above}
        if mate is not None:
            own[mate] = LAYOUT_ROW - above
        if not kids:
            return {node.layer: (min(own.values()), max(own.values()))}, own
        subtrees = [build(kid) for kid in kids]
        shifts, merged = pack_subtrees(subtrees)
        middle = snap_to_grid((shifts[0] + shifts[-1]) / 2)
        contour = {layer: (top - middle, bottom - middle) for layer, (top, bottom) in merged.items()}
        contour[node.layer] = (min(own.values()), max(own.values()))
        offsets = dict(own)
        for shift, (_, sub_offsets) in zip(shifts, subtrees):
            for member, y in sub_offsets.items():
                offsets[member] = y + shift - middle
        return contour, offsets

    placed_y = {}
    if roots:
        forest = [build(root) for root in roots]
        shifts, _ = pack_subtrees(forest)
        middle = snap_to_grid((shifts[0] + shifts[-1]) / 2)
        for shift, (_, offsets) in zip(shifts, forest):
            for member, y in offsets.items():
                placed_y[member] = y + shift - middle

    for node, y in placed_y.items():
        node.coordinate = (-node.layer * layer_spacing(), y)

    # whatever the tree walk never reached - a byproduct, which hangs off the
    # recipe that makes it rather than a consumer, or anything a recipe loop
    # cut off - goes level with a neighbor it is linked to, in the nearest row
    # of its own column that is free
    for node in nodes:
        if node in placed_y:
            continue
        neighbors = [n for n in node.daughter_nodes + node.mother_nodes if n in placed_y]
        anchor_y = placed_y[neighbors[0]] if neighbors else 0
        place_in_free_row(node, anchor_y, placed_y)

    return children

# puts `node` in its own column at the row closest to anchor_y that clears
# every node already placed there, trying above and below alternately
def place_in_free_row(node, anchor_y, placed_y):
    column = [y for other, y in placed_y.items() if other.layer == node.layer]
    target = snap_to_grid(anchor_y)
    for distance in range(len(column) + 1):
        for y in ((target,) if distance == 0 else
                  (target + distance * LAYOUT_ROW, target - distance * LAYOUT_ROW)):
            if all(abs(y - other) >= LAYOUT_ROW for other in column):
                placed_y[node] = y
                node.coordinate = (-node.layer * layer_spacing(), y)
                return

# over the top of everything the tree ended up covering, in the middle of it
def place_power_node(steps, final):
    spot = power_layout(final)
    if spot is None:
        return
    for step in steps:
        for node in step["nodes"]:
            if is_power_node(node):
                node.coordinate = (spot[1].x(), spot[1].y())

def pin_kept_nodes(steps, kept, anchor):
    final = [node for node in steps[-1]["nodes"] if not is_power_node(node)]
    laid_out = {node: node.coordinate for node in final}   # where the fresh layout put each

    # a node gone by the end stays where it stood, for the steps before it left
    for node, coordinate in kept.items():
        if node not in final:
            node.coordinate = coordinate

    # every node that was already there keeps exactly where it was, its column
    # included: a build that reaches deeper would otherwise slide half the map
    # over, and a node put somewhere by hand belongs where it was put. Only
    # what is new to this build is placed.
    taken = []
    for node in final:
        if node in kept:
            node.coordinate = kept[node]
            taken.append(node.coordinate)

    # the new ones, each hung level with the nodes it is wired to that are
    # already down - kept or new, whichever is there by then - and then to the
    # nearest free row of its own column. Going by the kept ones alone left a
    # chain of new nodes falling back on where a whole fresh layout would have
    # put them, which is nowhere near the part already on the map, and their
    # lines crossed everything on the way. The first of them takes the
    # replaced node's spot, when there is one.
    placed = dict(kept)
    for node in final:
        if node in kept:
            continue
        x = -node.layer * layer_spacing()
        # the power node hangs over the map with a line into every machine: it
        # is nobody's neighbour for placing purposes, and it was not laid out
        neighbors = [n for n in node.mother_nodes + node.daughter_nodes
                     if n in placed and n in laid_out and not is_byproduct(n)]
        if anchor is not None and not is_byproduct(node):
            x, y = anchor
            anchor = None
        elif neighbors:
            # level with them on average, each read as the fresh layout had
            # it relative to this node
            y = sum(placed[n][1] + laid_out[node][1] - laid_out[n][1] for n in neighbors) / len(neighbors)
        else:
            y = laid_out[node][1]
        node.coordinate = (x, free_row(x, y, taken))
        taken.append(node.coordinate)
        placed[node] = node.coordinate

    untangle_new_nodes(final, kept)

# Two new nodes sharing a column may have landed the wrong way round, their
# lines crossing. Swapping a pair costs nothing - both rows are already theirs -
# so neighbouring pairs are swapped for as long as it untangles the graph.
# Only the new ones move: what was already on the map stays where it was.
def untangle_new_nodes(final, kept):
    present = set(final)
    links = [(mother, node) for node in final for mother in node.mother_nodes
             if mother in present and mother is not node
             and not is_power_node(mother) and not is_power_node(node)]
    columns = {}
    for node in final:
        if node not in kept and not is_power_node(node):
            columns.setdefault(node.coordinate[0], []).append(node)

    best = count_crossings(links)
    for _ in range(LAYOUT_SWAP_ROUNDS):
        if not best:
            return
        swapped = False
        for column in columns.values():
            column.sort(key=lambda node: node.coordinate[1])
            for first, second in zip(column, column[1:]):
                first.coordinate, second.coordinate = second.coordinate, first.coordinate
                trial = count_crossings(links)
                if trial < best:
                    best, swapped = trial, True
                else:
                    first.coordinate, second.coordinate = second.coordinate, first.coordinate
        if not swapped:
            return

# the row closest to `y` in the column at `x` that clears everything in
# `taken` ([(x, y)]), tried above and below in turn
def free_row(x, y, taken):
    column = [spot[1] for spot in taken if spot[0] == x]
    y = snap_to_grid(y)
    for distance in range(len(column) + 1):
        for option in ((y,) if distance == 0 else (y + distance * LAYOUT_ROW, y - distance * LAYOUT_ROW)):
            if all(abs(option - other) >= LAYOUT_ROW for other in column):
                return option
    return y

# places every node of the snapshots Node.get_nodes_from_outputs hands back.
# The finished tree - the last step - is laid out first, and every node that
# shows up in an earlier step only is placed relative to it. So a node keeps
# the same spot in every step it appears in, and walking the steps reads as
# pieces landing in the finished tree's own places.
#
# `kept` ({node: coordinate}), for a tree rebuilt around one node (see
# Node.rebuild_subtree), is where the tree's nodes stood before: every node
# still in its column stays exactly there, and only what is new is laid out -
# as the finished tree would place it, the whole new part moved together onto
# where the node it replaces (`anchor`) stood, then down or up by whole rows
# until it clears what was already there.
def layout_nodes(steps, kept=None, anchor=None):
    if not steps:
        return
    # the power node hangs over the whole map rather than under a consumer, so
    # it is left out of the tree's own layout and placed once it is done
    final = [node for node in steps[-1]["nodes"] if not is_power_node(node)]
    layout_tree(final)
    if kept:
        pin_kept_nodes(steps, kept, anchor)
    place_power_node(steps, final)
    # the power node is placed by hand above the rest, and the sweeps below
    # must leave it where it was put
    placed = set(final) | set(kept or ())
    placed.update(node for step in steps for node in step["nodes"] if is_power_node(node))

    # a node that was merged away goes right under the node it became, half a
    # square of space between the two, so the step that created it reads as
    # the pair about to merge. It only exists for the one step before its own
    # merge, so two of them never share the screen and each takes that spot.
    for step in steps:
        for node in step["nodes"]:
            if node in placed or node.merged_into is None:
                continue
            survivor = node.merged_into
            while survivor.merged_into is not None:   # merged into something merged away
                survivor = survivor.merged_into
            x, y = survivor.coordinate
            node.coordinate = (x, y + NODE_HEIGHT + NODE_MERGING_GAP)
            placed.add(node)

    # anything else gone by the end - a byproduct a later merge replaced - is
    # placed from the links its own steps recorded, beside what it was wired to
    placed_y = {node: node.coordinate[1] for node in steps[-1]["nodes"]}
    for step in steps:
        for node in step["nodes"]:
            if node in placed:
                continue
            linked = [other for mother, daughter, _, _ in step["links"]
                      for other in ((daughter,) if mother is node else (mother,) if daughter is node else ())
                      if other in placed_y]
            anchor_y = placed_y[linked[0]] if linked else 0
            place_in_free_row(node, anchor_y, placed_y)
            placed.add(node)

# one port per item crossing the border, in the recipe's own order - not one
# per connected node, so two mothers buying the same item share one port and an
# ingredient with no producer under it still gets its own
# power is an ingredient like any other to the tree, but it does not arrive on
# a belt: it has its own line into the top of the box (see PowerEdge), so it
# gets no port on the border
def input_items(node):
    return [entry["item"] for entry in node.ingredients if entry["item"] is not POWER_ITEM]

def output_items(node):
    return [entry["item"] for entry in node.products if entry["item"] is not POWER_ITEM]

# how many lines of the selected tier it takes to carry `rate` of `item`: belts
# against the conveyor level for a solid, pipes against the pipe level for a
# liquid or gas. A fluid moves in liters, so a pipe holds far more of it than a
# belt holds items - counted against a belt, 2000 L/min of acid read as 34 lines.
def lines_needed(item, rate):
    if rate <= 0:
        return 0
    if getattr(item, "is_fluid", False):
        capacity = PIPE_CAPACITY[panel_options["pipe_lvl"]]
    else:
        capacity = CONVEYOR_CAPACITY[panel_options["conveyor_lvl"]]
    return max(1, math.ceil(rate / capacity))

# ---- drawing quality at any zoom ----
#
# The graph is drawn at whatever zoom the view is at, and fitting a whole
# factory on screen takes it far below 1:1. Three things fall apart down there,
# each handled here:
#   - pictures: a 512px texture squeezed into a 20px square in one bilinear
#     step reads only a few of its pixels, and comes out grainy and shimmering
#     as the zoom moves. Each picture is kept as a chain of halvings instead,
#     and drawn from the one closest above the size it lands on screen.
#   - text: glyph hinting snaps the outlines to whole pixels at the font's own
#     size, which the view then scales - so it is turned off, and the text
#     scales as the smooth shape it is.
#   - lines and borders: a few scene units wide is well under a pixel zoomed
#     out, and fades to nearly nothing. They are held to a minimum width on
#     screen instead, whatever the zoom.
MIN_SCREEN_LINE_PX = 1.3            # thinnest a line or a border is ever drawn on screen
MIN_LINE_BOUNDS_MARGIN = 24         # scene units a widened line may spill past its own bounds
PICTURE_SMALLEST_LEVEL = 16         # the chain of halvings stops at this size

_picture_levels = {}

# the picture at `path`, full size first, then halved until it is small
def picture_levels(path):
    levels = _picture_levels.get(path)
    if levels is None:
        levels = []
        image = QImage(picture_file(path))
        if not image.isNull():
            image = image.convertToFormat(QImage.Format_ARGB32_Premultiplied)
            levels.append(QPixmap.fromImage(image))
            # each halving a smooth one from the level before: every pixel
            # of the source still counts toward the small ones
            while max(image.width(), image.height()) > PICTURE_SMALLEST_LEVEL:
                image = image.scaled(max(1, image.width() // 2), max(1, image.height() // 2),
                                     Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                levels.append(QPixmap.fromImage(image))
        _picture_levels[path] = levels
    return levels

# how many device pixels one scene unit covers where the painter is drawing
def device_scale(painter):
    transform = painter.worldTransform()
    ratio = painter.device().devicePixelRatioF() if painter.device() is not None else 1.0
    return math.hypot(transform.m11(), transform.m12()) * ratio or 1.0

# the view an item is being painted into, and how much it scales the scene -
# read off the view rather than worked out from the painter, which is the same
# answer for every item of a frame and was being computed hundreds of times
def painting_view(widget):
    return widget.parent() if widget is not None else None

def view_scale(view, painter):
    scale = getattr(view, "draw_scale", 0.0)
    return scale if scale else device_scale(painter)

# a pen that is never thinner on screen than MIN_SCREEN_LINE_PX
def screen_pen(painter, pen, scale=None):
    thinnest = MIN_SCREEN_LINE_PX / (scale or device_scale(painter))
    if pen.style() == Qt.NoPen or pen.widthF() >= thinnest:
        return pen
    wider = QPen(pen)
    wider.setWidthF(thinnest)
    return wider

# Text is what a frame is spent on: laying out and hinting a few hundred labels
# costs several times everything else in the scene together. Two things are done
# about it, and both only ever drop text that could not be read anyway:
#   - below TEXT_MIN_SCREEN_PX a glyph is a smudge of a pixel or two, so the
#     whole label is skipped. Zoomed out far enough, that is every label.
#   - while the view is moving - panned, zoomed, or playing a build - text is
#     skipped too, and drawn again the moment it settles (see GridGraphicsView
#     .moving). What is moving cannot be read either.
TEXT_MIN_SCREEN_PX = 4.5

class SceneText(QGraphicsTextItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pixel_size = self.font().pixelSize()

    # kept as a plain number: read on every paint of every label, and asking
    # the item for its font hands back a whole QFont each time
    def setFont(self, font):
        super().setFont(font)
        self.pixel_size = font.pixelSize()

    def paint(self, painter, option, widget=None):
        view = painting_view(widget)
        if self.pixel_size * view_scale(view, painter) < TEXT_MIN_SCREEN_PX:
            return
        super().paint(painter, option, widget)

# a font for text drawn in the scene: unhinted, so it scales cleanly
def scene_font(font, pixel_size):
    font = QFont(font)
    font.setPixelSize(pixel_size)
    font.setHintingPreference(QFont.PreferNoHinting)
    font.setStyleStrategy(QFont.PreferAntialias)
    return font

# a picture drawn into a `width` x `height` box, from the level of its chain
# closest above the size the box covers on screen
class PictureItem(QGraphicsItem):
    def __init__(self, path, width, height, parent=None):
        super().__init__(parent)
        self.levels = picture_levels(path)
        self.box = QRectF(0, 0, width, height)
        self.setAcceptedMouseButtons(Qt.NoButton)

    def boundingRect(self):
        return self.box

    def paint(self, painter, option, widget=None):
        if not self.levels:
            return
        needed = self.box.width() * view_scale(painting_view(widget), painter)
        chosen = self.levels[0]
        for level in self.levels:
            if level.width() < needed:
                break
            chosen = level
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.drawPixmap(self.box, chosen, QRectF(chosen.rect()))

# ---- power ----
#
# Every machine takes power as much as it takes ore, so the graph draws it:
# one node at the top of the map, in the yellow of the game's own power, a line
# from it down into every recipe that draws from it, and a line up from every
# generator feeding it. It is the only power node there is - what a generator
# makes past what the factory takes is reported there as spare, not carried off
# to a byproduct node of its own.
#
# The lines are drawn faintly: they cross the whole map, and the factory itself
# has to stay readable through them. Clicking the power node brings them all
# up. Each one leaves its machine straight up, and only turns toward the power
# node once it is clear of the topmost box by a block - so the run up out of
# each machine reads as its own line rather than a diagonal across everything.
POWER_COLOR = "#f1c40f"
POWER_LINE_WIDTH = 2.5
POWER_LINE_Z = -2                  # under the boxes and under the supply lines...
POWER_LINE_LIVE_Z = -1.9           # ...and over the other power lines once it is picked out
POWER_LINE_ALPHA = 55              # at rest the line keeps out of the way...
POWER_LINE_LIVE_ALPHA = 225        # ...and comes up when the power node is picked out
POWER_LIVE_WIDEN = 1.6             # thickening with it
POWER_RAIL_GAP = GRID_SQUARE       # the block of clear air above the topmost node
POWER_NODE_GAP = GRID_SQUARE * 2   # from the rail up to the power node's box
POWER_NODE_WIDTH = NODE_WIDTH * 1.4   # wider than a node: it carries a column of its own
POWER_NODE_HEIGHT = NODE_HEIGHT * 0.95   # its name, what is made, and what is drawn
POWER_NODE_FONT_SIZE = 40          # about the node names' own size
POWER_NODE_VALUE_FONT_SIZE = 30
POWER_MADE_LABEL = "▲"        # what the generators send up
POWER_DRAWN_LABEL = "▼"       # what the machines pull down
POWER_MADE_COLOR = NODE_OUTPUT_BORDER_COLOR   # what is produced reads green...
POWER_DRAWN_COLOR = "#e74c3c"                 # ...and what is consumed, red
# which way the power runs, said twice over: a generator's line into the node is
# green and the machines' draw out of it red - the colors the node's own two
# rows already use - and each line meets its boxes through the same triangle an
# ingredient's line does, pointing into the side taking the power and out of
# the side giving it. Every line runs to the one point on the power node.
POWER_TOTAL_SHARE = 0.45           # of the room beside the bolt, kept for the net total
POWER_TOTAL_FONT_SIZE = 52         # the headline number of the box: bigger than either row
POWER_BOLT_SIZE = 96               # the bolt in the power node's box
POWER_PICTURE = "<power>"          # stands in for a picture path: the bolt is drawn, not loaded

CONVEYOR_ARROW_LENGTH = 22   # "old" arrow mode only: one floating arrow per line, not built into the node
CONVEYOR_ARROW_WIDTH = 16
# a node feeding its own output back into itself: the line leaves its right
# side, dips under the box and comes back up into its left side. The dip stays
# inside the gap to the row below, label included, and passes under the
# caption resting beneath the box rather than through it.
CONVEYOR_LOOP_DEPTH = 68    # from the node's bottom edge down to the line
CONVEYOR_LOOP_PULL = 80      # how far past each side the line swings out as it turns
CONVEYOR_LOOP_LEGACY_HEIGHT = 0.75   # "old" mode: where on the sides the loop meets the box, top to bottom

# closed-form point/tangent on a cubic bezier - "old" mode's floating arrow
# needs to know exactly where the curve crosses a node's border, and which
# way it's pointing there, rather than just landing on a fixed slot
def cubic_point(p0, p1, p2, p3, t):
    mt = 1 - t
    x = mt**3 * p0.x() + 3 * mt**2 * t * p1.x() + 3 * mt * t**2 * p2.x() + t**3 * p3.x()
    y = mt**3 * p0.y() + 3 * mt**2 * t * p1.y() + 3 * mt * t**2 * p2.y() + t**3 * p3.y()
    return QPointF(x, y)

def cubic_tangent(p0, p1, p2, p3, t):
    mt = 1 - t
    x = 3 * mt**2 * (p1.x() - p0.x()) + 6 * mt * t * (p2.x() - p1.x()) + 3 * t**2 * (p3.x() - p2.x())
    y = 3 * mt**2 * (p1.y() - p0.y()) + 6 * mt * t * (p2.y() - p1.y()) + 3 * t**2 * (p3.y() - p2.y())
    return QPointF(x, y)

# t=0 sits at the rect's own center (always "inside"); bisection finds where
# the curve first leaves the axis-aligned box around it - whichever side
# (left/right or top/bottom) that turns out to be, so a steep edge that
# should exit through the top or bottom doesn't get measured against the
# side edges instead and land past them, off the node entirely
def cubic_t_leaving_rect(p0, p1, p2, p3, center, half_width, half_height):
    def inside(t):
        point = cubic_point(p0, p1, p2, p3, t)
        return abs(point.x() - center.x()) <= half_width and abs(point.y() - center.y()) <= half_height

    lo, hi = 0.0, 1.0
    for _ in range(24):
        mid = (lo + hi) / 2
        if inside(mid):
            lo = mid
        else:
            hi = mid
    return hi

# a curved connector (a shallow bezier, not a hard elbow) labelled with what
# flows across it. In "old" arrow mode it also carries its own floating
# arrow, positioned fresh in set_endpoints; in "new" mode legacy_arrow is
# False and the node itself draws the fixed arrows instead.
class ConveyorEdge(QGraphicsPathItem):
    def __init__(self, item_name, rate, belts, legacy_arrow, unit="/min"):
        super().__init__()
        # below the nodes, so a belt passing over a box runs behind it instead
        # of being drawn across its icon and text
        self.setZValue(CONVEYOR_Z)
        self.start = QPointF(0, 0)
        self.end = QPointF(0, 0)
        # in slot mode the endpoints are fixed left/right border slots, so the
        # curve must always leave them outward (left of start, right of end).
        # "old" mode's endpoints are plain centers with no side to respect.
        self.fixed_sides = not legacy_arrow
        # the NodeItem at both ends when a node consumes its own output: the
        # line is then drawn as a loop off that box, see set_loop
        self.loop_item = None
        # which way round the box that loop goes: +1 under its bottom, -1 over
        # its top, settled by NodeItem.place_line from where the box supplying
        # the same item stands. Held as a number rather than a flag so a change
        # of side can be eased through the box rather than jumping across it.
        self.loop_side = 1.0
        self.loop_target = None
        self.loop_animation = None
        # two recipes feeding each other stand in the one column - neither is
        # under the other - and a line between them runs straight down the gap
        # from one border to the other rather than out to a side port, see
        # set_stacked
        self.stacked = False
        # its two ends, as (the box, its PortEnd): which border each of them
        # leaves by depends on how the two boxes sit, so moving either one
        # re-places both (see NodeItem.place_line)
        self.stack_ends = []
        # (maker color, taker color) while its node's panel is open, and how
        # far the light has come up along it: 0 plain, 1 fully lit
        self.highlight = None
        self.glow = 0.0
        self.glow_animation = None
        self.last_highlight = (NODE_LINE_COLOR, NODE_LINE_COLOR)   # what it is fading back from

        # a bit thicker per extra belt needed, so a heavier flow visibly
        # reads as a heavier line - capped so it never gets out of hand
        width = min(CONVEYOR_LINE_WIDTH + max(belts - 1, 0) * CONVEYOR_WIDTH_STEP, CONVEYOR_MAX_WIDTH)
        pen = QPen(QColor(NODE_LINE_COLOR), width)
        pen.setCapStyle(Qt.RoundCap)
        self.setPen(pen)

        label_text = f"{item_name}  {rate:.1f} {unit}"
        if belts > 1:
            label_text += f"  ×{belts}"
        # a child of the line, so it inherits its stacking and passes behind a
        # box along with the curve it belongs to
        self.label = SceneText(label_text, self)
        self.label.setDefaultTextColor(QColor(CONVEYOR_LABEL_COLOR))
        self.label.setFont(scene_font(self.label.font(), CONVEYOR_LABEL_FONT_SIZE))
        self.label.setTransformOriginPoint(self.label.boundingRect().center())
        # what it measures at full size, for fit_label to work its size out
        # from arithmetic rather than by laying the text out again
        self.label_size = CONVEYOR_LABEL_FONT_SIZE
        self.label_full = self.label.boundingRect().width()

        # tip at the local origin, pointing along +x - set_endpoints moves
        # and rotates it so the tip lands exactly on the receiving node's border
        self.arrow = None
        if legacy_arrow:
            self.arrow = QGraphicsPolygonItem(QPolygonF([
                QPointF(0, 0),
                QPointF(-CONVEYOR_ARROW_LENGTH, -CONVEYOR_ARROW_WIDTH / 2),
                QPointF(-CONVEYOR_ARROW_LENGTH, CONVEYOR_ARROW_WIDTH / 2),
            ]), self)
            self.arrow.setPen(Qt.NoPen)
            self.arrow.setBrush(QBrush(QColor(NODE_LINE_COLOR)))

    # held to its on-screen minimum width zoomed far out, with room for it
    def boundingRect(self):
        return super().boundingRect().adjusted(-MIN_LINE_BOUNDS_MARGIN, -MIN_LINE_BOUNDS_MARGIN,
                                               MIN_LINE_BOUNDS_MARGIN, MIN_LINE_BOUNDS_MARGIN)

    def paint(self, painter, option, widget=None):
        view = painting_view(widget)
        # a curve costs most of a frame to draw smoothly, and a moving one is
        # not being looked at closely: it is drawn hard-edged until it settles
        if getattr(view, "moving", False):
            painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setPen(screen_pen(painter, self.pen(), view_scale(view, painter)))
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path())

    # A short line cannot hold its own label: two boxes a column apart, or one
    # stacked over the other, leave less room along the line than the item and
    # its rate take to write. The label is shrunk to whatever room there is,
    # down to a size past which it would not be worth reading - below that it
    # keeps that size and runs past its line, which reads better than a row of
    # dots.
    #
    # Worked out from the width it measured at full size rather than by
    # measuring again: text width goes with the font size, and this runs for
    # every edge on every frame of a drag.
    def fit_label(self, room):
        wanted = CONVEYOR_LABEL_FONT_SIZE
        if self.label_full > 0 and room < self.label_full:
            wanted = max(CONVEYOR_LABEL_MIN_FONT_SIZE,
                         CONVEYOR_LABEL_FONT_SIZE * room / self.label_full)
        if abs(wanted - self.label_size) < 0.5:
            return
        self.label_size = wanted
        self.label.setFont(scene_font(self.label.font(), round(wanted)))
        self.label.setTransformOriginPoint(self.label.boundingRect().center())

    # one of the lines into or out of the node whose panel is open: it takes
    # the colors of the two boxes it joins - the one it comes out of at its
    # own end, the one it feeds at the other - and fades from one to the other
    # when they differ. `maker` and `taker` are those two colors.
    def set_highlight(self, on, maker=None, taker=None):
        was = self.highlight
        self.highlight = (maker, taker) if on else None
        # the colors come up rather than snapping on: clicking a box runs the
        # light out along its own lines, and off them again when it is let go.
        # A line already lit for another box changes color outright - it is the
        # same light moving over, not a line lighting up.
        if (was is None) == (self.highlight is None):
            self.glow = 1.0 if on else 0.0
            self.apply_highlight()
            return
        if self.glow_animation is not None:
            self.glow_animation.stop()
            self.glow_animation = None
        owner = self.scene()
        if owner is None:
            self.glow = 1.0 if on else 0.0
            self.apply_highlight()
            return

        def step(value):
            self.glow = value
            self.apply_highlight()

        self.glow_animation = animate_value(owner, self.glow, 1.0 if on else 0.0,
                                            step, CONVEYOR_GLOW_MS)
        self.glow_animation.finished.connect(lambda: setattr(self, "glow_animation", None))

    def apply_highlight(self):
        # up over the other lines while it is picked out, back down after -
        # raised as soon as the light starts coming up, lowered once it is gone
        self.setZValue(CONVEYOR_Z if self.glow <= 0 else CONVEYOR_LIVE_Z)
        pen = self.pen()
        if self.highlight is None and self.glow <= 0:
            pen.setBrush(QBrush(QColor(NODE_LINE_COLOR)))
            self.label.setDefaultTextColor(QColor(CONVEYOR_LABEL_COLOR))
            tip = QColor(NODE_LINE_COLOR)
        else:
            lit = self.highlight if self.highlight is not None else self.last_highlight
            maker, taker = (blend_color(NODE_LINE_COLOR, color, self.glow) for color in lit)
            self.last_highlight = lit
            if maker == taker:
                pen.setBrush(QBrush(QColor(maker)))
            else:
                # `end` is where it leaves its producer, `start` where it
                # arrives at its consumer. Each end holds its own color for a
                # good part of the run and they change over in the middle,
                # rather than blending across the whole line.
                fade = QLinearGradient(self.end, self.start)
                fade.setColorAt(0.0, QColor(maker))
                fade.setColorAt(0.5 - CONVEYOR_FADE_SPAN / 2, QColor(maker))
                fade.setColorAt(0.5 + CONVEYOR_FADE_SPAN / 2, QColor(taker))
                fade.setColorAt(1.0, QColor(taker))
                pen.setBrush(QBrush(fade))
            self.label.setDefaultTextColor(blend_color(CONVEYOR_LABEL_COLOR, lit[0], self.glow))
            tip = QColor(taker)   # it lands on its consumer, in that node's color
        self.setPen(pen)
        # "old" arrow mode's floating arrow is its own item: the pen does not
        # reach it, so it is colored here too
        arrow = getattr(self, "arrow", None)   # made after this can first run
        if arrow is not None:
            arrow.setBrush(QBrush(tip))

    # a shallow S curve between the two points, its label re-centred and
    # rotated to the curve's own tangent at the midpoint.
    #
    # This fires on every pixel of a node drag, once per connected edge, so it
    # deliberately avoids QPainterPath.length()/pointAtPercent()/angleAtPercent():
    # those are accurate but each walk the curve numerically, and doing that
    # on every mouse-move is what made dragging feel laggy. A cubic bezier's
    # midpoint and tangent both have a plain closed-form answer at t=0.5.
    def set_endpoints(self, start, end):
        self.start = start
        self.end = end
        self.apply_highlight()   # a fade runs between the ends: they just moved
        if self.loop_item is not None:
            self.set_loop()
            return
        if self.stacked:
            self.set_stacked()
            return

        inside_start = inside_end = None
        if self.fixed_sides:
            # both ends run on into their boxes rather than stopping at the
            # slot: a line is drawn under the boxes, so the round cap - which
            # would otherwise show as a blunt bulge past the arrow it meets -
            # ends up hidden under the box. That stretch is a straight run to
            # the slot, so the line still leaves its port dead level and only
            # then turns, instead of coming out of the box already on the bend.
            inside_start = QPointF(start.x() + CONVEYOR_NODE_OVERLAP, start.y())
            inside_end = QPointF(end.x() - CONVEYOR_NODE_OVERLAP, end.y())

            # `start` is an input slot on a node's left border and `end` an
            # output slot on another's right border, so the tangent at each
            # end is pinned outward regardless of how the two nodes sit
            # relative to each other. The pull grows with the gap but never
            # drops below the minimum, so vertically stacked nodes still get
            # a line that visibly pops out of the slot instead of one that
            # runs straight up through the middle of the boxes.
            pull = max(abs(end.x() - start.x()) * curve_strength(), curve_min_pull())
            c1 = QPointF(start.x() - pull, start.y())
            c2 = QPointF(end.x() + pull, end.y())
        else:
            dx = (end.x() - start.x()) * curve_strength()
            c1 = QPointF(start.x() + dx, start.y())
            c2 = QPointF(end.x() - dx, end.y())

        path = QPainterPath(inside_start if inside_start is not None else start)
        if inside_start is not None:
            path.lineTo(start)          # the straight run out of the consumer
        path.cubicTo(c1, c2, end)
        if inside_end is not None:
            path.lineTo(inside_end)     # and on into the producer, past its arrow
        self.setPath(path)

        # B(0.5) and B'(0.5) for a cubic bezier, in closed form
        midpoint = QPointF(
            (start.x() + 3 * c1.x() + 3 * c2.x() + end.x()) / 8,
            (start.y() + 3 * c1.y() + 3 * c2.y() + end.y()) / 8,
        )
        tangent_x = end.x() + c2.x() - c1.x() - start.x()
        tangent_y = end.y() + c2.y() - c1.y() - start.y()
        # atan2 in scene space (y grows downward) already matches Qt's own
        # clockwise-positive rotation, so no sign flip is needed here
        angle = math.degrees(math.atan2(tangent_y, tangent_x)) % 360
        if 90 < angle < 270:
            angle -= 180   # would read upside down/mirrored otherwise

        if self.arrow is not None:
            # "old" mode's endpoints are plain node centers, so the arrow
            # follows the curve out to wherever it actually crosses the
            # *start* node's border, pointing back into it (material flows
            # from `end`, the producer, to `start`, the consumer - the
            # opposite of the path's own start-to-end parametrization)
            t_border = cubic_t_leaving_rect(start, c1, c2, end, start, node_width() / 2, NODE_HEIGHT / 2)
            arrow_point = cubic_point(start, c1, c2, end, t_border)
            path_tangent = cubic_tangent(start, c1, c2, end, t_border)
            flow_x, flow_y = -path_tangent.x(), -path_tangent.y()
            if flow_x == 0 and flow_y == 0:
                flow_x, flow_y = start.x() - end.x(), start.y() - end.y()
            self.arrow.setPos(arrow_point)
            self.arrow.setRotation(math.degrees(math.atan2(flow_y, flow_x)))

        # the normal to the tangent, on the side above the curve (screen up
        # when the curve is flat), so the label rests right on the line. Mother
        # to daughter can point either left-to-right or right-to-left depending
        # on which layer is which, and that sign flips which of the tangent's
        # two normals is "up" - so it's forced onto the up side explicitly
        # rather than trusting a single fixed rotation of the tangent.
        # the label lies along the curve at its middle, so what it has to fit
        # in is the run between the two ends
        self.fit_label(math.hypot(end.x() - start.x(), end.y() - start.y()) - CONVEYOR_LABEL_ROOM_MARGIN)

        tangent_len = math.hypot(tangent_x, tangent_y) or 1
        normal_x = tangent_y / tangent_len
        normal_y = -tangent_x / tangent_len
        if normal_y > 0:
            normal_x, normal_y = -normal_x, -normal_y

        bounds = self.label.boundingRect()
        offset = bounds.height() / 2 + CONVEYOR_LABEL_GAP
        anchor = QPointF(midpoint.x() + normal_x * offset, midpoint.y() + normal_y * offset)

        center = bounds.center()
        self.label.setRotation(angle)
        self.label.setPos(anchor - center)

    # two boxes in the one column, one above the other: the line is the plain
    # run down the gap between them, no curve to it - both ends sit on the same
    # x, on the borders that face each other. The label rides beside it, upright
    # rather than turned along the line: a vertical label reads badly, and there
    # is room to the side of a gap that is only a line wide.
    def set_stacked(self):
        path = QPainterPath(self.start)
        path.lineTo(self.end)
        self.setPath(path)

        # upright beside the run, so what it has to fit in is the clear air
        # between this column of boxes and the next
        self.fit_label(layer_spacing() - node_width() - CONVEYOR_LABEL_ROOM_MARGIN)
        bounds = self.label.boundingRect()
        self.label.setRotation(0)
        self.label.setPos(self.start.x() + self.pen().widthF() / 2 + CONVEYOR_LABEL_GAP,
                          (self.start.y() + self.end.y()) / 2 - bounds.height() / 2)
        if self.arrow is not None:
            self.arrow.setPos(self.start)
            self.arrow.setRotation(90 if self.end.y() < self.start.y() else 270)

    # The side its loop runs on, eased when it changes rather than jumping from
    # under the box to over it: the run sweeps through the box on its way, and
    # a line is drawn under the boxes, so it reads as the loop passing behind
    # the box and coming out the other side. The first side it is given is
    # simply taken, there being nothing to move from.
    def set_loop_side(self, side):
        if side == self.loop_target:
            return
        first = self.loop_target is None
        self.loop_target = side
        owner = self.scene()
        if first or owner is None:
            self.loop_side = side
            self.set_loop()
            return
        if self.loop_animation is not None:
            self.loop_animation.stop()

        def step(value):
            self.loop_side = value
            self.set_loop()

        self.loop_animation = animate_value(owner, self.loop_side, side, step, CONVEYOR_LOOP_FLIP_MS)
        self.loop_animation.finished.connect(lambda: setattr(self, "loop_animation", None))

    # A node eating its own output: out of its output port on the right, round
    # the outside of the box, and back into its input port on the left. It goes
    # under the bottom or over the top - `loop_top` - so it can be kept to the
    # side the item is supplied from rather than always hanging below (see
    # NodeItem.loop_border_is_top). Read off the box itself rather than the
    # endpoints, which in "old" mode are both just its center.
    def set_loop(self):
        item = self.loop_item
        left = item.pos().x()
        right = left + item.rect().width()
        middle = item.pos().y() + item.rect().height() / 2
        run_y = middle + self.loop_side * (item.rect().height() / 2 + CONVEYOR_LOOP_DEPTH)
        if self.fixed_sides:
            # backed off the input arrow's base, the same as a normal line
            start = QPointF(self.start.x() - (self.pen().widthF() / 2 + CONVEYOR_ARROW_CLEARANCE), self.start.y())
            end = self.end
        else:
            # low on each side, clear of the lines that meet the box's center
            low = item.pos().y() + item.rect().height() * CONVEYOR_LOOP_LEGACY_HEIGHT
            start, end = QPointF(left, low), QPointF(right, low)

        pull = CONVEYOR_LOOP_PULL
        path = QPainterPath(start)
        path.cubicTo(QPointF(start.x() - pull, start.y()), QPointF(start.x() - pull, run_y),
                     QPointF(start.x(), run_y))
        path.lineTo(end.x(), run_y)
        path.cubicTo(QPointF(end.x() + pull, run_y), QPointF(end.x() + pull, end.y()), end)
        self.setPath(path)

        if self.arrow is not None:
            # flow comes round into the left side, pointing into the box
            self.arrow.setPos(start)
            self.arrow.setRotation(0)

        # level, on the far side of the straight run from the box: under it for
        # a loop below, over it for one above - and no wider than that run
        self.fit_label(abs(end.x() - start.x()) - CONVEYOR_LABEL_ROOM_MARGIN)
        bounds = self.label.boundingRect()
        self.label.setRotation(0)
        gap = self.pen().widthF() / 2 + CONVEYOR_LABEL_GAP
        self.label.setPos((start.x() + end.x()) / 2 - bounds.width() / 2,
                          run_y + gap if self.loop_side > 0 else run_y - bounds.height() - gap)

# a draggable, rounded box. Every edge plugged into it (as either endpoint) is
# one end of a line where it meets a node: the port it lands on, given as a
# slot index of `count`, and the item it carries - which is what decides that
# slot as the boxes move about (see restack_ports). The slot is kept as a float
# so a swap can be eased from the old port to the new one rather than the line
# jumping across the border. `slot` is None in "old" arrow mode, where a line
# runs to the box's plain center and there are no ports at all.
class PortEnd:
    __slots__ = ("edge", "role", "slot", "target", "count", "flow", "slide", "arrow", "stack")

    def __init__(self, edge, role, slot, count, flow=None, arrow=None, stack=None):
        self.edge = edge
        self.role = role      # "start": this node's input port, "end": its output
        self.slot = slot      # where it is drawn now, eased while it changes over
        self.target = slot    # the port it belongs on
        self.count = count
        self.flow = flow
        self.slide = None     # the animation carrying it from the one to the other
        self.arrow = arrow    # the triangle it lands on, which rides along with it
        # (the box on the other end, how far along the border it meets it) for
        # a run between two boxes in the one column - it has no side port at
        # all, and which border it leaves by is read off where they now stand.
        # The box on the other end is this end's own box for a loop, which
        # reads its border off whoever else supplies the same item instead.
        self.stack = stack

# kept in self.lines, so itemChange can slide that endpoint whenever the box
# moves. A press+release that did not turn into a drag counts as a click.
class NodeItem(QGraphicsRectItem):
    def __init__(self, width, height, node, on_click, on_move):
        super().__init__(0, 0, width, height)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.set_locked(panel_options["locked"])
        # (edge, "start", index, count) for an edge arriving at the tip of
        # one of this node's fixed left-border input slots, or (edge, "end",
        # index, count) for an edge leaving from the tip of one of its fixed
        # right-border output slots. index is None in "old" arrow mode,
        # where there are no fixed slots and the edge just runs to the
        # node's plain center instead.
        self.lines = []
        # {"in"|"out": {item: [the node items on the other end]}} - who a port's
        # lines run to, so the ports can be put back in order as those move
        self.port_partners = {"in": {}, "out": {}}
        # the drawn triangles, by the port each started on: a line takes the
        # one it lands on along with it when it is given another port
        self.port_arrows = {"in": [], "out": []}
        self.node = node
        self.on_click = on_click
        self.on_move = on_move
        self.press_pos = None
        self.last_click = 0.0     # when it was last let go of, for the double click below
        self.edge_shift = 0.0     # how far its right edge is from home, mid-resize
        self.right_edge_items = []   # pinned to that edge besides the out ports: a power arrow
        self.on_complete = None   # set by whoever keeps the list of built boxes
        # a node answers the mouse like any clickable: its ground lifts a
        # shade under the mouse - eased in and out, not flicked - and sinks
        # while held, the hand closing on it
        self.setAcceptHoverEvents(True)
        self.hover_level = 0.0
        self.hover_animation = None

    # the box whose info panel is open: a heavier border, to go with its own
    # supply lines coming up out of the rest (see highlight_supply)
    def set_selected(self, on):
        pen = self.pen()
        pen.setWidthF(NODE_SELECTED_BORDER_WIDTH if on else NODE_BORDER_WIDTH)
        self.setPen(pen)
        self.set_glow(on)

    # the light around a box: its own color, coming off it while it is the one
    # picked out. A box the build is making already carries one of these, put
    # there when the scene was drawn; that one is left alone.
    def set_glow(self, on):
        if getattr(self, "focus_glow", False):
            return      # the build's own light on this box stands
        set_node_lit(self, on)

    def ease_hover(self, to):
        if self.hover_animation is not None:
            try:
                self.hover_animation.stop()
            except RuntimeError:
                pass   # went with the scene it ran in, already
            self.hover_animation = None
        owner = self.scene()
        if owner is None:
            self.hover_level = to
            self.update()
            return

        def step(value):
            self.hover_level = value
            self.update()

        self.hover_animation = animate_value(owner, self.hover_level, to, step, NODE_HOVER_MS)
        self.hover_animation.finished.connect(lambda: setattr(self, "hover_animation", None))

    def hoverEnterEvent(self, event):
        self.ease_hover(1.0)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.ease_hover(0.0)
        super().hoverLeaveEvent(event)

    def center(self):
        return self.pos() + self.rect().center()

    def slot_y(self, index, count):
        return self.pos().y() + port_slot_y(index, count, self.rect().height())

    def slot_height(self, count):
        return port_slot_height(count, self.rect().height())

    # base of the index-th (of `count`) input arrow on the left edge - the
    # incoming line stops here and the arrow carries the flow the rest of the
    # way in, rather than the line running under the arrow to its apex
    def entry_point(self, index, count):
        return QPointF(self.pos().x(), self.slot_y(index, count))

    # tip of the index-th (of `count`) output arrow on the right edge,
    # poking out past the border - where an outgoing line actually starts
    def exit_point(self, index, count):
        height = flow_arrow_height(self.slot_height(count))
        return QPointF(self.pos().x() + self.rect().width() + height, self.slot_y(index, count))

    def itemChange(self, change, value):
        # ItemPositionChange arrives with the position the drag is about to
        # take, and whatever is returned here is used instead - so snapping
        # happens before the move, and the edges below then follow the
        # already-snapped position rather than being dragged back afterwards
        # a graph transition glides the box through the positions in between:
        # those are neither snapped nor where the node really is
        animating = getattr(self, "animating", False)
        # only a drag by hand snaps: the layout places nodes itself, some of
        # them on purpose off the grid (a duplicate half a square under its
        # merger), and those must land exactly where they were put
        # (read with getattr: Qt already calls this while __init__ sets the flags)
        dragging = getattr(self, "press_pos", None) is not None
        if change == QGraphicsItem.ItemPositionChange and panel_options["snap"] and dragging and not animating:
            return QPointF(snap_to_grid(value.x()), snap_to_grid(value.y()))
        if change == QGraphicsItem.ItemPositionHasChanged:
            # kept in sync so a manual drag survives a redraw that reuses
            # this same Node (an arrow-mode switch, say) instead of being
            # overwritten by the layout position it started at
            if not animating:
                self.node.coordinate = (self.pos().x(), self.pos().y())
            if dragging:
                # dragged by hand: the graph is moving, and is drawn cheaply
                # until it is let go (see GridGraphicsView.keep_moving)
                for view in self.scene().views() if self.scene() is not None else ():
                    if hasattr(view, "keep_moving"):
                        view.keep_moving()
            for end in self.lines:
                self.place_line(end)
            # the ports are re-sorted only for a box moved by hand: the layout
            # placing a box, and a transition gliding one, both work from an
            # order that was settled when the scene was built
            self.on_move(self if dragging else None)
        return super().itemChange(change, value)

    # one of its line ends put back on the port it sits at now - after a drag,
    # or a step of the slide onto a port it has just been given
    # Which border a loop runs off: the one facing the box that supplies the
    # same item, so the loop sits on the side the material already comes from
    # rather than reaching around the box. Dragging that supplier over or under
    # this box moves the loop with it. With no other supplier - a node feeding
    # itself entirely - it hangs under the bottom, where it always did.
    def loop_border_is_top(self, flow):
        suppliers = [box for box in self.port_partners["in"].get(flow, ()) if box is not self]
        if not suppliers:
            return False
        middle = self.pos().y() + self.rect().height() / 2
        return sum(box.pos().y() + box.rect().height() / 2 for box in suppliers) / len(suppliers) < middle

    def place_line(self, end):
        # a loop's two ends are both this box's own side ports; which way round
        # the box the line itself goes is settled before it is laid
        if end.edge.loop_item is self:
            end.edge.set_loop_side(-1.0 if self.loop_border_is_top(end.flow) else 1.0)
        if end.stack is not None:
            # both ends, not just this box's: dragging one box of a pair
            # changes which border the box that stayed put should leave by
            for box, far in end.edge.stack_ends:
                box.place_stacked_line(far)
            return
        if end.role == "start":
            point = self.center() if end.slot is None else self.entry_point(end.slot, end.count)
            end.edge.set_endpoints(point, end.edge.end)
        else:
            point = self.center() if end.slot is None else self.exit_point(end.slot, end.count)
            end.edge.set_endpoints(end.edge.start, point)
        if end.arrow is not None:
            # an output arrow rides the right edge, which is off its home
            # while the box is changing size (see shift_right_edge)
            along = self.edge_shift if end.role == "end" else 0
            end.arrow.setPos(along, port_slot_y(end.slot, end.count, self.rect().height()))

    # one end of a run between two boxes in the one column. Which border it
    # leaves by is whichever of this box's faces the other: drag the pair past
    # each other and the run turns over to the other two borders, arrows and
    # all. As on a side port, the line starts at the tip of the triangle giving
    # the material and stops at the border where the one taking it begins.
    def place_stacked_line(self, end):
        other, along = end.stack
        under = other.pos().y() > self.pos().y()      # the other box sits below this one
        border_y = self.rect().height() if under else 0
        giving = end.role == "end"                    # this box is the producer
        # the material runs toward the other box: down when it is below, up
        # when it is above - and the triangle points that way on both borders
        upward = not under if giving else under
        reach = border_arrow_reach() if giving else 0
        # worked out for the box's settled width: mid-resize it keeps its
        # place across the box rather than hanging off the edge
        along *= self.rect().width() / node_width()
        point = QPointF(self.pos().x() + along,
                        self.pos().y() + border_y + (reach if under else -reach))
        if end.role == "start":
            end.edge.set_endpoints(point, end.edge.end)
        else:
            end.edge.set_endpoints(end.edge.start, point)
        if end.arrow is not None:
            end.arrow.setPolygon(border_arrow_points(along, border_y, upward))

    # room for the border held to its on-screen minimum zoomed far out
    def boundingRect(self):
        return super().boundingRect().adjusted(-MIN_LINE_BOUNDS_MARGIN, -MIN_LINE_BOUNDS_MARGIN,
                                               MIN_LINE_BOUNDS_MARGIN, MIN_LINE_BOUNDS_MARGIN)

    def paint(self, painter, option, widget=None):
        view = painting_view(widget)
        if getattr(view, "moving", False):
            painter.setRenderHint(QPainter.Antialiasing, False)
        painter.setPen(screen_pen(painter, self.pen(), view_scale(view, painter)))
        ground = node_ground(self.brush().color(), self.hover_level, getattr(self, "lit_level", 0.0))
        if self.press_pos is not None:
            ground = ground.darker(NODE_PRESS_DARKER)
        painter.setBrush(ground)
        painter.drawRoundedRect(self.rect(), NODE_RADIUS, NODE_RADIUS)

    # While a box is between its two sizes, everything pinned to its right
    # edge - the caret, and the output arrows on that border - travels with
    # that edge rather than waiting at the size it will end up. `dx` is how
    # far the edge still is from where it is going.
    def shift_right_edge(self, dx):
        button = getattr(self, "info_button", None)
        if button is not None:
            button.setPos(button.pos().x() + dx - self.edge_shift, button.pos().y())
        for arrow in self.port_arrows["out"] + self.right_edge_items:
            arrow.setPos(arrow.pos().x() + dx - self.edge_shift, arrow.pos().y())
        self.edge_shift = dx

    # held where it stands, or free to be dragged: the cursor says which
    def set_locked(self, locked):
        self.setFlag(QGraphicsItem.ItemIsMovable, not locked)
        self.setCursor(Qt.ArrowCursor if locked else Qt.OpenHandCursor)

    def mousePressEvent(self, event):
        self.press_pos = event.scenePos()
        if not panel_options["locked"]:
            self.setCursor(Qt.ClosedHandCursor)
        self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.press_pos is not None:
            moved = (event.scenePos() - self.press_pos).manhattanLength()
            if moved < NODE_CLICK_DRAG_THRESHOLD:
                # in one-click mode a plain click ticks the box off as built
                # rather than picking it out (see the Tick toggle)
                if panel_options["quick_done"] and self.on_complete is not None:
                    self.on_complete(self.node)
                else:
                    self.on_click(self.node, self)
                self.last_click = time.monotonic()
        self.press_pos = None
        self.set_locked(panel_options["locked"])
        self.update()

    # Double clicking a box ticks it off as built, and again puts it back: the
    # quickest thing to reach for while working down a factory with the map
    # open beside it. Qt sends this in place of the second press, so the gap
    # measured is from the first click being let go of - and a pair further
    # apart than NODE_DOUBLE_CLICK_MS is left to fall through as two clicks,
    # press_pos and all, rather than being taken for a double one.
    def mouseDoubleClickEvent(self, event):
        event.accept()
        if panel_options["quick_done"]:
            return   # the first click ticked it off and the second put it back
        if (time.monotonic() - self.last_click) * 1000 > NODE_DOUBLE_CLICK_MS:
            return
        self.press_pos = None      # that pair was not a drag, and not a click either
        if self.on_complete is not None:
            self.on_complete(self.node)

    # its ground, which says whether it has been built yet
    def set_done(self, done):
        self.setBrush(QBrush(NODE_DONE_BG if done else NODE_BG))
        self.update()

# the caret in a node's top right corner: the one handle that opens and shuts
# that node's info panel. It is a child of the box, so it rides along with a
# drag, and it takes the press itself - a press that reached the box under it
# would start dragging the node instead of working the button.
class NodeInfoButton(QGraphicsItem):
    def __init__(self, side, color, on_click, parent=None):
        super().__init__(parent)
        self.box = QRectF(0, 0, side, side)
        self.color = QColor(color)   # its node's own, worn while the panel is open
        self.on_click = on_click
        self.open = False
        self.angle = 0.0          # 0 points right at what it opens, 180 back at it
        self.turn = None
        self.hovered = False
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("What this node carries")

    def boundingRect(self):
        return self.box

    # the caret swings round to its new heading rather than flipping, so which
    # way it just went reads even when the panel itself fades
    def set_open(self, on):
        if on == self.open:
            return
        self.open = on
        if self.turn is not None:
            try:
                self.turn.stop()
            except RuntimeError:
                pass   # went with the scene it ran in, already
            self.turn = None
        owner = self.scene()
        target = NODE_INFO_CARET_OPEN_ANGLE if on else 0.0
        if owner is None:
            self.angle = target
            self.update()
            return

        def step(value):
            self.angle = value
            self.update()

        self.turn = animate_value(owner, self.angle, target, step, NODE_INFO_CARET_TURN_MS)
        self.turn.finished.connect(lambda: setattr(self, "turn", None))

    def hoverEnterEvent(self, event):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self.hovered = False
        self.update()

    def mousePressEvent(self, event):
        event.accept()   # kept off the box: no drag starts from the button

    def mouseReleaseEvent(self, event):
        event.accept()
        if self.box.contains(event.pos()):   # released off it again: not a click
            self.on_click()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        color = self.color if self.open else QColor(TEXT_STRONG if self.hovered else NODE_CAPTION_COLOR)
        if self.open or self.hovered:
            ground = QColor(color)
            ground.setAlpha(NODE_INFO_BUTTON_GROUND_ALPHA)
            painter.setPen(Qt.NoPen)
            painter.setBrush(ground)
            radius = self.box.width() / 4
            painter.drawRoundedRect(self.box, radius, radius)
        painter.save()
        painter.scale(self.box.width() / SYMBOL_CANVAS, self.box.height() / SYMBOL_CANVAS)
        draw_caret(painter, color, self.angle)
        painter.restore()

# builds a scene of boxes (one per node, draggable) and curved, labelled
# conveyor lines (one per mother/daughter link, following the boxes they
# connect), laid out left to right by layer. Set on a GridGraphicsView with
# view.setScene(...), the view's own grid still shows through underneath. The
# info panel is parented to the view itself so it floats over the graph and
# tracks the open node as the view pans, zooms or resizes.
#
# The tree comes back as a list of snapshots, one per step of its build, and
# the view holds on to them so the step arrows can walk back and forth without
# rebuilding anything. `step` is where it starts: 0, or -1 for the finished tree.
# the border a node is drawn with, which says what kind of node it is
# a machine that makes power rather than drawing it - a generator
def is_generator(node):
    return isinstance(node, Recipe_Node) and any(entry["item"] is POWER_ITEM for entry in node.recipe.products)

def node_border_color(node):
    if is_power_node(node) or is_generator(node):
        return POWER_COLOR
    if node.merged_into is not None:
        return NODE_MERGING_BORDER_COLOR
    if isinstance(node, Output_Node):
        return NODE_BYPRODUCT_BORDER_COLOR if node.is_byproduct else NODE_OUTPUT_BORDER_COLOR
    if isinstance(node, Manual_Node):
        return NODE_MANUAL_BORDER_COLOR   # no machine makes it: a true source
    # extraction: nothing is crafted under it. The power node hangs under every
    # machine there is, so it does not count as something crafted.
    if not [daughter for daughter in node.daughter_nodes if not is_power_node(daughter)]:
        return NODE_INPUT_BORDER_COLOR
    return NODE_BORDER_COLOR

# a build from the outputs as they stand, laid out from scratch: the same
# outputs always come out the same graph, however they were added to the panel
def generate_node_graph(view, output, step=0):
    # an ore's extraction runs in the miner the options pick
    set_miner_mark(panel_options["miners_mark"])
    steps = Node.get_nodes_from_outputs(output, panel_options["recipe_choices"],
                                        panel_options["node_recipe_choices"])
    layout_nodes(steps)
    view.build_steps = steps
    view.build_step = step % len(steps)
    return render_build_step(view)

# the area every node of a build takes up across all its steps - the
# whole finished tree, plus any duplicate that shows before being merged away.
# Confirm fits the camera to this rather than to the first step, which is only
# the outputs, so the view holds still while the steps fill it in. The arrows
# poking out of a box and the line labels between boxes sit inside FIT_MARGIN.
def build_steps_bounds(steps):
    bounds = QRectF()
    for step in steps:
        for node in step["nodes"]:
            if is_power_node(node) and not panel_options["show_power"]:
                continue   # not drawn: it should not pull the camera up either
            x, y = node.coordinate
            bounds = bounds.united(QRectF(x, y, node_width(), NODE_HEIGHT))
    return bounds

# renders whichever step the view is parked on. An empty build still gets a
# scene, so the canvas has something to show before any output is confirmed.
def render_build_step(view):
    steps = getattr(view, "build_steps", None) or [{"nodes": [], "links": [], "values": {}}]
    view.build_step = max(0, min(getattr(view, "build_step", 0), len(steps) - 1))
    return render_node_graph(view, steps[view.build_step])

# builds the scene for one step of a build (search.snapshot): its nodes,
# already laid out, with the links and the numbers as they stood then. Split
# out from generate_node_graph so an arrow-mode switch can redraw with this
# directly: it reuses the same Node objects (their .coordinate kept in sync
# with any dragging via NodeItem.itemChange) instead of rebuilding the tree
# and relaying it out from scratch, which would snap every dragged node back
# to its original spot.
def render_node_graph(view, frame):
    nodes = frame["nodes"]
    legacy_arrows = panel_options["arrow_mode"] == "old"

    # Two recipes feeding each other share a layer, so neither stands under the
    # other: their line runs straight down the gap between them instead of out
    # to a side port (see set_stacked). Worked out before anything is drawn,
    # because an item that arrives that way needs no port on the side border at
    # all - and leaving an empty one there would push the ports that are used
    # off the middle of the box and bunch them up at one end.
    down_column = set()          # (node, "in"/"out", item) carried down the column
    on_the_side = set()          # ...and the same, carried by an ordinary line
    for mother, daughter, flow_item, _ in frame["links"]:
        if flow_item is POWER_ITEM:
            continue
        stacked = (not legacy_arrows and mother is not daughter
                   and mother.layer == daughter.layer)
        marked = down_column if stacked else on_the_side
        marked.add((mother, "in", flow_item))
        marked.add((daughter, "out", flow_item))

    # the items a node keeps a border port for: all of them, less the ones
    # every line of which comes down the column. An ingredient nothing supplies
    # is in no link at all, so it keeps its port, as it always did.
    def port_items(node, side):
        items = input_items(node) if side == "in" else output_items(node)
        return [item for item in items
                if (node, side, item) not in down_column or (node, side, item) in on_the_side]
    # a fresh graph replaces the old one wholesale: the previous generation's
    # info panel and its now-stale view-changed hook would otherwise linger,
    # showing an old node's info over a graph that no longer has that node
    old_panel = getattr(view, "info_panel", None)
    if old_panel is not None:
        old_panel.deleteLater()
    view.view_changed_callbacks.clear()

    scene = QGraphicsScene()
    scene.setSceneRect(-SCENE_EXTENT, -SCENE_EXTENT, SCENE_EXTENT * 2, SCENE_EXTENT * 2)

    info_panel = make_node_info_panel(view)
    view.info_panel = info_panel
    info_panel.is_done = lambda node: node_key(node) in view.completed
    info_panel.on_complete = lambda node: toggle_done(node)
    open_node = [None]     # the node picked out: its border and its lines lit
    info_open = [False]    # whether that node's info panel is standing open
    items_by_node = {}
    # a recipe picked in the panel goes to whoever rebuilds the tree
    if getattr(view, "on_node_recipe", None) is not None:
        info_panel.on_recipe_pick = view.on_node_recipe

    def position_info_panel(item):
        viewport = view.viewport()
        # it grows with its content but never past the view it floats over -
        # what does not fit scrolls inside the panel instead of off screen.
        # The height is measured rather than left to adjustSize: a word wrapped
        # label's size hint is the height of its text unwrapped, which comes
        # up short and left the panel scrolling with room to spare.
        wanted = info_panel.wanted_height()
        room = max(NODE_INFO_MIN_HEIGHT, viewport.height() - 2 * NODE_INFO_MARGIN)
        info_panel.setFixedHeight(min(wanted, room))
        # anchored to the node's own top right corner, not a fixed view corner
        top_right = view.mapFromScene(item.mapToScene(item.rect().topRight()))
        x = top_right.x() + NODE_INFO_GAP
        if x + info_panel.width() > viewport.width():
            top_left = view.mapFromScene(item.mapToScene(item.rect().topLeft()))
            x = top_left.x() - info_panel.width() - NODE_INFO_GAP   # no room right, hang left instead
        # ...and then pulled back inside the view, so a node near an edge does
        # not push its panel half out of sight
        x = max(NODE_INFO_MARGIN, min(x, viewport.width() - info_panel.width() - NODE_INFO_MARGIN))
        y = max(NODE_INFO_MARGIN, min(top_right.y(),
                                      viewport.height() - info_panel.height() - NODE_INFO_MARGIN))
        info_panel.move(x, y)
        info_panel.raise_()

    # re-anchors the open node's panel whenever the view itself moves, so it
    # stays glued to its node instead of drifting off as you pan/zoom
    def reposition_info():
        if info_open[0] and open_node[0] is not None:
            position_info_panel(items_by_node[open_node[0]])

    # the lines into and out of one node, for picking its own supply out of
    # the rest of the map while its panel is open
    def highlight_supply(node, on):
        item = items_by_node.get(node)
        # the power node's own supply is every line running up to it
        if is_power_node(node):
            if item is not None:
                item.set_live(on)
            for line in power_lines:
                line.set_live(on)
            return
        for (mother, daughter), edge in edge_items.items():
            if mother is node or daughter is node:
                edge.set_highlight(on, node_border_color(daughter), node_border_color(mother))
        if isinstance(item, NodeItem):
            item.set_selected(on)
            if getattr(item, "power_line", None) is not None:
                item.power_line.set_live(on)   # what feeds it power counts too

    # the node picked out of the map: a heavier border, its lines lit and
    # raised over the rest. Only ever the one, so the old one is put back first.
    def set_picked(node):
        if open_node[0] is node:
            return
        if open_node[0] is not None:
            highlight_supply(open_node[0], False)
        open_node[0] = node
        if node is not None:
            highlight_supply(node, True)

    # each node's caret shows whether the panel standing open is its own
    def refresh_info_buttons():
        for node, item in items_by_node.items():
            button = getattr(item, "info_button", None)
            if button is not None:
                button.set_open(info_open[0] and node is open_node[0])

    def close_info():
        if not info_open[0]:
            return
        info_open[0] = False
        fade_out(info_panel)
        refresh_info_buttons()

    # a click on the box itself: it picks the node out and nothing more -
    # clicking the picked one again puts it back. The panel is the caret's.
    def pick_node(node, item):
        close_info()
        set_picked(None if open_node[0] is node else node)

    # the caret in a node's corner: its info panel, on or off
    def toggle_info(node, item):
        if info_open[0] and open_node[0] is node:
            close_info()
            return   # the node stays picked out; only its panel goes
        moving_over = info_open[0]
        set_picked(node)
        info_open[0] = True
        info_panel.set_node(node, recorded[node])
        position_info_panel(item)
        refresh_info_buttons()
        if moving_over:
            pulse(info_panel)      # moved over to another node: its new content flashes in
        else:
            fade_in(info_panel)

    view.view_changed_callbacks.append(reposition_info)

    # a light is a fixed size on the graph, and the effect that draws it works
    # in screen pixels: what it is set to changes with every zoom
    def hold_glows():
        for item in list(items_by_node.values()) + [power_item[0]]:
            if item is not None and hasattr(item, "refresh_glow"):
                item.refresh_glow()

    view.view_changed_callbacks.append(hold_glows)
    info_panel.on_resize = reposition_info   # More info opened or shut

    recorded = frame["values"]
    focus = frame.get("focus")

    node_brush = QBrush(NODE_BG)
    power_lines = []
    power_item = [None]

    # The boxes ticked off as built, by node_key rather than by node object:
    # every build makes its nodes again from scratch, and what was put up in
    # the world does not come down because the tree was generated again. Kept
    # on the view, so it outlives the scene and goes to the save file.
    done = getattr(view, "completed", None)
    if done is None:
        done = view.completed = set()

    def toggle_done(node):
        key = node_key(node)
        done.discard(key) if key in done else done.add(key)
        for other, box in items_by_node.items():
            if isinstance(box, NodeItem) and node_key(other) == key:
                box.set_done(key in done)
        if info_open[0] and open_node[0] is node:
            info_panel.set_node(node, recorded[node])   # its button says the other thing now
        schedule_save()

    # a dragged machine takes its power line with it, and the power node rides
    # a block above whatever is now the highest box on the map
    def reflow_power():
        spot = power_layout([n for n in nodes if not is_power_node(n)])
        if power_item[0] is None or spot is None:
            return
        rail, corner = spot
        # While a transition has hold of the power node it is gliding to that
        # same spot itself, and putting it there outright would take it out of
        # the animation the rest of the graph is in the middle of. Its lines
        # are laid from wherever it is at that moment either way, so they stay
        # plugged into it the whole way across.
        if not getattr(power_item[0], "animating", False):
            power_item[0].setPos(corner)
            power_item[0].node.coordinate = (corner.x(), corner.y())
        feed = {side: power_item[0].feed_point(side) for side in (True, False)}
        for machine, line in power_line_of.items():
            box = items_by_node[machine]
            line.set_ends(QPointF(box.pos().x() + power_arrow_x(line.feeding, box.rect().width()),
                                  box.pos().y()), rail,
                          feed[line.feeding])

    def node_moved(moved=None):
        # a transition drops the whole scene while its boxes are still gliding,
        # so a move can arrive after the items behind it are gone
        try:
            if moved is not None:
                restack_ports(moved)
                schedule_save()   # where a box was dragged to is worth keeping
            reposition_info()
            reflow_power()
        except RuntimeError:
            pass

    power_line_of = {}
    for node in nodes:
        # the power node is drawn its own way - a box at the top of the map
        # every machine's line runs up to - but answers a click like any
        # other: its panel opens, and its lines come up with it
        if is_power_node(node):
            if panel_options["show_power"]:
                power_item[0] = PowerNodeItem(node, pick_node, toggle_info)
                scene.addItem(power_item[0])
                items_by_node[node] = power_item[0]
            continue
        item = NodeItem(node_width(), NODE_HEIGHT, node, pick_node, node_moved)
        item.setPos(*node.coordinate)
        # checked first: a duplicate is merged away before anything is built
        # under it, so with no daughters it would otherwise pass for an input
        merging = node.merged_into is not None
        border_color = node_border_color(node)
        focused = node is focus
        item.setPen(QPen(QColor(border_color), NODE_FOCUS_BORDER_WIDTH if focused else NODE_BORDER_WIDTH))
        item.setBrush(QBrush(NODE_DONE_BG) if node_key(node) in done else node_brush)
        item.on_complete = toggle_done
        item.focus_glow = focused   # the build's own light, not to be put out by a pick
        if focused:
            item.lit_level = 1.0    # lit the same way a picked box is
        # nothing flowing through it: faded back so the parts of the graph that
        # actually carry something read first. Opacity covers the icon and text
        # too, they are children of the box. The focused node is never faded:
        # it is the one the step is about.
        if not focused:
            if merging:
                item.setOpacity(NODE_MERGING_OPACITY)
            elif not node_rate(node, recorded[node]):
                item.setOpacity(NODE_IDLE_OPACITY)
        scene.addItem(item)

        # QGraphicsItem, unlike QWidget/QObject, does not keep its children
        # alive through Python's own reference counting: without a Python
        # reference kept somewhere, each child item is garbage collected the
        # moment the loop variable is reassigned, vanishing from the node
        item.texts = []

        # the caret that opens this node's info, in its top right corner: the
        # panel is shut until it is pressed (see toggle_info). A compact box
        # carries a smaller one - it is all the box says, and the panel is the
        # only place the numbers are left to read
        caret = NODE_INFO_COMPACT_BUTTON_SIZE if panel_options["compact"] else NODE_INFO_BUTTON_SIZE
        info_button = NodeInfoButton(caret, border_color,
                                     lambda n=node, i=item: toggle_info(n, i), item)
        info_button.setPos(node_width() - NODE_INFO_BUTTON_MARGIN - caret,
                           NODE_INFO_BUTTON_MARGIN)
        item.info_button = info_button
        item.texts.append(info_button)

        # one filled arrow per input (left edge) and per output (right edge),
        # marking the fixed points where a line always meets this node, in
        # the same color as the node's own outline. Added before the icon and
        # text below, so on the (fairly rare) input side where the arrow's
        # tip reaches under the icon, the icon draws over it rather than the
        # other way around. "old" arrow mode draws no arrows here at all -
        # ConveyorEdge carries its own floating one instead.
        # An arrow is cut at y = 0 and put on its port with setPos rather than
        # drawn at the port outright: the line that lands on it can be given a
        # different port later (see restack_ports), and the arrow then travels
        # with it instead of the line sliding out from under it.
        if not legacy_arrows:
            def add_flow_arrows(border_x, side, count):
                if not count:
                    return
                slot_height = port_slot_height(count)
                for index in range(count):
                    arrow = QGraphicsPolygonItem(flow_arrow_points(border_x, 0, slot_height), item)
                    arrow.setPos(0, port_slot_y(index, count))
                    arrow.setPen(Qt.NoPen)
                    arrow.setBrush(QColor(border_color))
                    item.port_arrows[side].append(arrow)
                    item.texts.append(arrow)

            add_flow_arrows(0, "in", len(port_items(node, "in")))
            add_flow_arrows(node_width(), "out", len(port_items(node, "out")))

        text_x = NODE_ICON_MARGIN
        # a compact box is its picture and nothing else, so the picture takes
        # the whole of it rather than the square beside a column of text
        icon_size = (NODE_HEIGHT - 2 * NODE_ICON_MARGIN if panel_options["compact"]
                     else NODE_ICON_SIZE)

        picture = node_picture(node)
        icon = None
        drawing = picture_drawing(picture)
        if drawing is not None:
            # nothing to load - the power node's bolt, or the frame standing
            # in for a picture the image folder does not carry - drawn
            # straight into the whole icon square instead
            width = height = icon_size
            icon = SymbolItem(drawing[0], drawing[1], icon_size, item)
        else:
            levels = picture_levels(picture)
            if levels:
                # not baked at NODE_ICON_SIZE: a baked picture is stuck at that
                # resolution and goes soft zoomed in. PictureItem draws from the
                # full texture zoomed in and from a smaller halving zoomed out,
                # whichever is closest to the size it lands on screen.
                full = levels[0]
                scale = icon_size / max(full.width(), full.height())
                width, height = full.width() * scale, full.height() * scale
                icon = PictureItem(picture, width, height, item)

        if icon is not None:
            # the icon keeps its original centered spot - the margin that
            # centering already leaves above and below it is exactly the
            # room a small machine-name label needs, without moving anything.
            # A texture that is not square is centered inside the icon box.
            # A compact box centers it on the box itself, there being nothing
            # beside it to make room for.
            icon_left = (node_width() - icon_size) / 2 if panel_options["compact"] else NODE_ICON_MARGIN
            icon_top = (NODE_HEIGHT - icon_size) / 2
            icon.setPos(icon_left + (icon_size - width) / 2,
                        icon_top + (icon_size - height) / 2)
            item.texts.append(icon)
            text_x = NODE_ICON_MARGIN + icon_size + NODE_ICON_MARGIN

        # A compact box carries nothing but its picture, and says the rest
        # underneath it: what it is, and on the line under that what runs it
        # and how many of them - or, for an output, the rate it delivers. Its
        # power is left to the info panel; a map read at this size is about
        # what is being made and with what, and a megawatt figure under every
        # box is a third line of small print that nobody is reading here.
        # The lines are fitted to the gap between one column and the next, so
        # they stay readable at the size the smaller boxes put the whole graph
        # on screen at, without running into the labels of the box beside them.
        if panel_options["compact"]:
            name, caption = node_display_lines(node, recorded[node])
            lines = [(name, NODE_COMPACT_NAME_FONT_SIZE, NODE_TEXT_COLOR)]
            if caption:
                # the machine and its count kept close, as the one thing they
                # are, rather than held apart the way the wider box holds them
                lines.append((caption.replace("  ", " "), NODE_COMPACT_LINE_FONT_SIZE,
                              NODE_CAPTION_COLOR))

            below = NODE_HEIGHT + NODE_CAPTION_GAP
            for words, size, color in lines:
                line = SceneText(item)
                line.setDefaultTextColor(QColor(color))
                line.document().setDocumentMargin(0)
                line.document().setDefaultTextOption(QTextOption(Qt.AlignHCenter))
                line.setPlainText(words)
                if words is not name:
                    bold_machine_count(line)
                fit_one_line(line, layer_spacing() - NODE_MIN_GAP, float("inf"), size)
                line.setTextWidth(layer_spacing() - NODE_MIN_GAP)
                line.setPos((node_width() - line.textWidth()) / 2, below)
                below += line.boundingRect().height() + NODE_COMPACT_LINE_GAP
                item.texts.append(line)

            items_by_node[node] = item
            continue

        # the text column beside the picture is split into areas of its own,
        # so no text can run into another's: the bottom row is kept first for
        # the power a recipe draws, or the rate a final product delivers, and
        # the name gets everything above it
        name, caption = node_display_lines(node, recorded[node])
        column_width = node_width() - text_x - NODE_ICON_MARGIN
        column_top, column_bottom = NODE_ICON_MARGIN, NODE_HEIGHT - NODE_ICON_MARGIN

        footer = swing = None
        power = node_power(node, recorded[node])
        if power is not None:
            # what its machines draw, small and grey, signed so the one number
            # says which way it goes: a generator draws nothing and puts what it
            # makes here instead, with a + on it
            made = (next((entry["rate"] for entry in node.products if entry["item"] is POWER_ITEM), 0.0)
                    if is_generator(node) else None)
            footer = SceneText(("−" + format_power(power)) if made is None
                               else ("+" + format_power(made)), item)
            footer.setDefaultTextColor(QColor(NODE_POWER_COLOR))
            fit_one_line(footer, column_width, column_bottom - column_top, NODE_POWER_FONT_SIZE)
            # a recipe whose draw is a range gets its two ends under that
            # number, smaller and quieter: what stands above is the average of
            # them, which is what the factory's totals are added up from, and
            # the range is what the machines actually swing between
            ends = node_power_range(node, recorded[node])
            if ends is not None and made is None:
                swing = SceneText(format_power_range(*ends), item)
                swing.setDefaultTextColor(QColor(NODE_POWER_RANGE_COLOR))
                fit_one_line(swing, column_width, column_bottom - column_top,
                             NODE_POWER_RANGE_FONT_SIZE)
        elif caption and isinstance(node, (Output_Node, Manual_Node)):
            # a final product, or a source brought in by hand, keeps its rate
            # inside the box - it has no machine for a caption under it
            footer = SceneText(caption, item)
            footer.setDefaultTextColor(QColor(NODE_CAPTION_COLOR))
            fit_one_line(footer, column_width, column_bottom - column_top, NODE_CAPTION_FONT_SIZE)

        name_bottom = column_bottom
        if swing is not None:
            # the range takes the bottom row and the average sits on top of it
            swing_height = swing.boundingRect().height()
            swing.setPos(text_x, column_bottom - swing_height)
            item.texts.append(swing)
            name_bottom = column_bottom - swing_height
        if footer is not None:
            footer_height = footer.boundingRect().height()
            footer.setPos(text_x, name_bottom - footer_height)
            item.texts.append(footer)
            name_bottom = name_bottom - footer_height - NODE_TEXT_AREA_GAP

        # the name - anchored to the top left of its area, wrapping onto more
        # rows when it is long, and as big as fits the area. It stops short of
        # the caret in the corner rather than running under it.
        text = SceneText(name, item)   # a child moves with its node
        text.setDefaultTextColor(QColor(NODE_TEXT_COLOR))
        name_width = (node_width() - NODE_INFO_BUTTON_MARGIN - NODE_INFO_BUTTON_SIZE
                      - NODE_INFO_BUTTON_GAP - text_x)
        fit_node_name(text, name_width, name_bottom - column_top)
        text.setPos(text_x, column_top)
        item.texts.append(text)

        # that rate reads right under the name - its row was kept all the
        # same, so it can only move up into it
        if footer is not None and isinstance(node, (Output_Node, Manual_Node)):
            footer.setPos(text_x, column_top + text.boundingRect().height())

        # a recipe's caption rests just under the box, centered on it: the
        # machine and how many of it
        if caption and not isinstance(node, (Output_Node, Manual_Node)):
            under = SceneText(item)
            under.setDefaultTextColor(QColor(NODE_CAPTION_COLOR))
            under.document().setDocumentMargin(0)
            under.document().setDefaultTextOption(QTextOption(Qt.AlignHCenter))
            under.setPlainText(caption)
            bold_machine_count(under)
            # one line no wider than the box, smaller when a long machine name
            # would wrap it into the gap below
            fit_one_line(under, node_width(), float("inf"), NODE_CAPTION_FONT_SIZE)
            under.setTextWidth(node_width())
            under.setPos(0, NODE_HEIGHT + NODE_CAPTION_GAP)
            item.texts.append(under)

        items_by_node[node] = item

    # "old" mode matches its original behavior exactly: edges run center to
    # center, and the one floating arrow per edge follows the curve out to
    # the receiving node's actual border. "new" mode's fixed input/output
    # slots are a distinct system, unrelated to how "old" ever worked.
    links = frame["links"]

    # the first step of a generator build is the power node by itself: there is
    # no box for it to hang over yet, and power_layout says so
    placing = power_layout(nodes) if nodes else None
    rail_y = placing[0] if placing else 0

    # Which port a line lands on. A node keeps one port per item it takes in
    # or puts out, but which port an item gets is decided by where the node on
    # the other end of that line sits: the highest supplier takes the highest
    # input port, and the highest consumer the highest output port. Handing
    # them out in the recipe's own order instead had lines crossing over each
    # other on the way in - concrete coming down from above into the lower
    # port while the pellets came up from below into the upper one.
    # Which port an item gets is read off where the boxes stand, so it is asked
    # again whenever one of them is dragged (see restack_ports): each box holds
    # on to who its ports run to rather than to the heights they had at build.
    loop_flow = {}   # box -> the item it makes and then eats again, if any
    for mother, daughter, flow_item, _ in links:
        if flow_item is POWER_ITEM or mother not in items_by_node or daughter not in items_by_node:
            continue
        if mother is daughter:
            loop_flow[items_by_node[mother]] = flow_item
        items_by_node[mother].port_partners["in"].setdefault(flow_item, []).append(items_by_node[daughter])
        items_by_node[daughter].port_partners["out"].setdefault(flow_item, []).append(items_by_node[mother])

    def port_order(box, side):
        items = port_items(box.node, side)
        partnered = box.port_partners[side]
        # A port's place is set by the slope its line arrives on rather than by
        # how high the box on the other end sits: two boxes standing side by
        # side on the same row feed a node from the same height, and ordering
        # them by height alone leaves that tie to the recipe, which crosses
        # their lines as often as not. The nearer of the two comes in steeply
        # and the further one shallowly, so the slopes order them the way the
        # lines actually approach - and where the boxes are at different
        # heights, the slope still reads the same order the height did.
        middle = box.pos().y() + box.rect().height() / 2

        def approach(pair):
            index, flow = pair
            # only the boxes whose line actually lands on this side port: one
            # in the same column comes in down the column onto a top or bottom
            # border instead (see set_stacked), and the box itself loops round
            # to a port pinned on its own (below) - counted in, the one
            # overhead reads as a slope near infinite and drags the port to
            # the top whatever the lines really arriving on it are doing
            slopes = [(other.pos().y() + other.rect().height() / 2 - middle)
                      / max(abs(other.pos().x() - box.pos().x()), 1.0)
                      for other in partnered.get(flow, ())
                      if other is not box and other.node.layer != box.node.layer]
            # an item nothing is wired to keeps its own place in the recipe's
            # order, level with the node itself
            return (sum(slopes) / len(slopes) if slopes else 0.0, index)
        order = [flow for _, flow in sorted(enumerate(items), key=approach)]

        # A loop leaves by the port at the very top or the very bottom of the
        # output side and comes back into the matching one on the input side,
        # whichever way round the box it goes. It runs over the box or under
        # it, so a middle port has it cutting back across every line meeting
        # that side above or below it - where the outermost port lets it leave
        # and arrive alongside them, both ends on the same edge of the box.
        looped = loop_flow.get(box)
        if looped in order:
            order.remove(looped)
            order.insert(0 if box.loop_border_is_top(looped) else len(order), looped)
        return order

    # Two recipes that feed each other are one loop, and a loop is given a
    # single layer - so neither of the two stands under the other, and the pair
    # ends up in the one column. A line between them has no side port to run
    # between: the consumer's input is on the left of a box the producer's
    # output is on the right of, so drawn the usual way both lines set off
    # backwards and cross under their own boxes. They are drawn as a straight
    # run down the gap instead, off one border and into the other (see
    # set_stacked), and several runs between the same two boxes are spread
    # across the width so they stand side by side rather than on top of
    # each other. "old" arrow mode keeps out of this: its lines meet a box at
    # the center and have no ports to be wrong about.
    stack_along = {}
    if not legacy_arrows:
        together = {}
        for mother, daughter, flow_item, _ in links:
            if flow_item is POWER_ITEM or mother is daughter:
                continue
            if mother not in items_by_node or daughter not in items_by_node:
                continue
            if mother.layer == daughter.layer:
                together.setdefault(frozenset((mother, daughter)), []).append((mother, daughter, flow_item))
        for runs in together.values():
            for index, link in enumerate(runs):
                stack_along[link] = stack_port_x(index, len(runs))

    # nothing moves while the scene is being built, so each side is worked out
    # the once and every line of it reads the same answer
    settled = {}

    def slot_items(box, side):
        if (box, side) not in settled:
            settled[(box, side)] = port_order(box, side)
        return settled[(box, side)]

    # A box dragged past another changes which of them sits higher, and with it
    # which port their lines belong on. Every box the dragged one is wired to
    # has its ports worked out again, and a line that changed port eases over
    # to the new one: a line jumping the height of a box reads as a different
    # line rather than the same one moving.
    def restack_ports(moved):
        boxes = {moved}
        for side in ("in", "out"):
            for group in moved.port_partners[side].values():
                boxes.update(group)
        for box in boxes:
            # a loop goes round the side its item is supplied from: dragging
            # that supplier over or under the box takes the loop with it
            for end in box.lines:
                if end.edge.loop_item is box:
                    box.place_line(end)
        for box in boxes:
            for side, role in (("in", "start"), ("out", "end")):
                order = None
                for end in box.lines:
                    # "old" arrow mode has no ports: its lines run to the box's
                    # plain center, and there is nothing to sort them into
                    if end.role != role or end.flow is None or end.target is None:
                        continue
                    if order is None:
                        order = port_order(box, side)
                    slot = order.index(end.flow)
                    if slot != end.target:
                        slide_port(box, end, slot)

    # the triangle a line lands on, or None in "old" arrow mode, where none are
    # drawn. Several suppliers of one item share a port, and so share its arrow.
    def port_arrow(box, side, index):
        arrows = box.port_arrows[side]
        return arrows[index] if index is not None and index < len(arrows) else None

    def slide_port(box, end, slot):
        end.target = slot
        if end.slide is not None:
            end.slide.stop()

        def step(value):
            end.slot = value
            box.place_line(end)

        end.slide = animate_value(scene, end.slot, slot, step, PORT_SLIDE_MS)
        end.slide.finished.connect(lambda: setattr(end, "slide", None))

    edge_items = {}
    edge_rates = {}

    # one triangle on a box's horizontal border, where a power line meets it -
    # a child of that box, so it rides along with a drag and is drawn over the
    # box rather than under it, the way an ingredient's arrow is
    # which ports the node needs: with only generators feeding it, or only
    # machines drawing from it, the one it has takes the middle of its edge.
    # Settled before the first line is laid, so every line runs to the right spot.
    if power_item[0] is not None:
        sides = {is_power_node(mother) for mother, node, flow_item, _ in links
                 if flow_item is POWER_ITEM
                 and items_by_node.get(node if is_power_node(mother) else mother) is not None}
        power_item[0].paired_ports = len(sides) > 1

    # `bolt` marks the arrow a power line lands on, told apart from the ones
    # carrying items by the lightning cut out of it
    def add_border_arrow(box, x, border_y, upward, color, bolt=False):
        points = border_arrow_points(x, border_y, upward)
        if bolt:
            arrow = PowerArrowItem(points, color, box)
        else:
            arrow = QGraphicsPolygonItem(points, box)
            arrow.setPen(Qt.NoPen)
            arrow.setBrush(QColor(color))
        box.texts.append(arrow)   # kept alive by the Python side, see item.texts
        return arrow

    for mother, node, flow_item, rate in links:
        # power runs its own way: straight up out of the machine, and only
        # over to the power node once it is clear of every box. A machine
        # drawing power is the mother of the link; a generator feeding the
        # power node is the daughter of one, and its line runs the other way.
        if flow_item is POWER_ITEM:
            feeding = is_power_node(mother)
            machine = items_by_node.get(node if feeding else mother)
            if power_item[0] is None or machine is None:
                continue
            top = QPointF(machine.pos().x() + power_arrow_x(feeding), machine.pos().y())
            line = PowerEdge(top, rail_y, power_item[0].feed_point(feeding), feeding=feeding)
            scene.addItem(line)
            power_lines.append(line)
            power_line_of[node if feeding else mother] = line
            machine.power_line = line
            # the triangle where that line meets the machine, over on the left
            # of its top border: pointing down into a box drawing power, up out
            # of one making it. It wears its line's own color rather than the
            # box's, which is what sets it apart from the arrows carrying items
            # - those take the outline color, and every one of these is the
            # green of power made or the red of power drawn.
            arrow = add_border_arrow(machine, power_arrow_x(feeding), 0, feeding, line.color, bolt=True)
            if power_arrow_x(feeding) > node_width() / 2:
                machine.right_edge_items.append(arrow)   # travels with that edge on a resize
            continue
        # "old" arrow mode can be switched on over a step, and a step's links
        # were recorded against the nodes it held - either way, a link with an
        # end missing from this scene is simply not drawn
        # (power took the branch above; everything below is an item on a belt)
        item = items_by_node.get(node)
        mother_item = items_by_node.get(mother)
        if item is None or mother_item is None:
            continue
        along = stack_along.get((mother, node, flow_item))
        if along is not None:
            # a run down the column between two recipes feeding each other:
            # no ports, the borders that face each other instead. Each end is
            # placed by its own box, which is also what re-reads the borders
            # when the pair is dragged past each other.
            edge = ConveyorEdge(flow_item.display_name, rate, lines_needed(flow_item, rate),
                                legacy_arrows, rate_unit(flow_item))
            edge.stacked = True
            scene.addItem(edge)
            taking = PortEnd(edge, "start", None, None, flow_item,
                             add_border_arrow(mother_item, along, 0, True, node_border_color(mother)),
                             (item, along))
            giving = PortEnd(edge, "end", None, None, flow_item,
                             add_border_arrow(item, along, 0, True, node_border_color(node)),
                             (mother_item, along))
            mother_item.lines.append(taking)
            item.lines.append(giving)
            edge.stack_ends = [(mother_item, taking), (item, giving)]
            mother_item.place_line(taking)
            edge_items[(mother, node)] = edge
            edge_rates[(mother, node)] = rate
            continue
        if legacy_arrows:
            entry_index = entry_count = exit_index = exit_count = None
            start_point, end_point = mother_item.center(), item.center()
        else:
            # the ports are the item's, not the neighbour's: every line
            # carrying this item leaves the producer by the one output port it
            # belongs to, and arrives at the one port the consumer keeps for
            # that ingredient - which port that is comes from slot_items
            entry_items = slot_items(mother_item, "in")
            entry_index = entry_items.index(flow_item)
            entry_count = len(entry_items)
            exit_items = slot_items(item, "out")
            exit_index = exit_items.index(flow_item)
            exit_count = len(exit_items)
            start_point = mother_item.entry_point(entry_index, entry_count)
            end_point = item.exit_point(exit_index, exit_count)
        edge = ConveyorEdge(
            flow_item.display_name, rate,
            lines_needed(flow_item, rate),
            legacy_arrows,
            rate_unit(flow_item),
        )
        scene.addItem(edge)
        if mother is node:
            edge.loop_item = item   # its own output coming back in
            # which way round the box it goes, settled before it is first laid:
            # the ports were handed out on that answer too (see port_order), so
            # leaving it to the first drag would draw the loop the wrong way
            # round from its own ports until the box was moved
            edge.set_loop_side(-1.0 if item.loop_border_is_top(flow_item) else 1.0)
        edge.set_endpoints(start_point, end_point)
        mother_item.lines.append(PortEnd(edge, "start", entry_index, entry_count, flow_item,
                                         port_arrow(mother_item, "in", entry_index)))
        item.lines.append(PortEnd(edge, "end", exit_index, exit_count, flow_item,
                                  port_arrow(item, "out", exit_index)))
        edge_items[(mother, node)] = edge
        edge_rates[(mother, node)] = rate

    # the power node's own pair, side by side under it: the right one pointing
    # up into the box for the power arriving from the generators, the left one
    # down out of it for the power the machines take - so which bundle is which
    # reads off the node itself. Each in its own line's color, green for the
    # power coming in and red for the power going out. Drawn once, however many
    # lines land on them, and only for a side that has any.
    if power_item[0] is not None:
        for upward, color in ((True, POWER_MADE_COLOR), (False, POWER_DRAWN_COLOR)):
            if any(line.feeding is upward for line in power_lines):
                add_border_arrow(power_item[0],
                                 power_port_x(POWER_NODE_WIDTH, upward, power_item[0].paired_ports),
                                 POWER_NODE_HEIGHT, upward, color, bolt=True)

    # what transition_scene compares the next scene against
    scene.node_items = items_by_node
    scene.edge_items = edge_items
    scene.edge_rates = edge_rates
    scene.values = recorded
    scene.focus_node = focus
    # every label of the scene in one list, for the view to take out while it
    # moves (see GridGraphicsView.show_text)
    scene.text_items = [item for item in scene.items() if isinstance(item, SceneText)]
    scene.power_lines = power_lines
    scene.power_item = power_item[0]

    return scene

GRAPH_TRANSITION_MS = 320
GRAPH_APPEAR_FROM = 0.5      # a new node starts this far back toward the node it grows out of
GRAPH_APPEAR_DROP = 30       # a new node with nothing to grow out of settles down from this high
GHOST_Z = -0.5               # a leaving node: under the boxes that stay, over the lines
GHOST_EDGE_Z = -0.9          # a leaving line: over the lines that stay

def lerp_point(a, b, t):
    return QPointF(a.x() + (b.x() - a.x()) * t, a.y() + (b.y() - a.y()) * t)

# swaps the view onto a freshly rendered scene, animating whatever changed
# between the two - both scenes being render_node_graph's, so they carry
# which node and which link every item stands for. Nodes are matched by
# identity, which is what a step build shares between its snapshots:
#   - a node in both glides to its new spot and fades to its new opacity
#   - a new node fades in, sliding out of a node it is linked to that was
#     already there (its consumer first, else what it hangs off, as a
#     byproduct does off its recipe)
#   - a node gone is carried over into the new scene for the length of the
#     animation and fades out - into the node it merged with, if it did
#   - lines come and go the same way, and the highlight's glow fades across
# `crossfade` is for a restyle of the same graph (pictures, arrows): nothing
# moves, the old look is laid over the new one and fades off it.
#
# A transition still running when the next starts - steps played back
# quickly - is jumped to its end first, so nothing is left half faded.
def transition_scene(view, scene, crossfade=False):
    running = getattr(view, "graph_transition", None)
    if running is not None:
        running()
    old = view.scene()
    old_items = getattr(old, "node_items", {})
    old_edges = getattr(old, "edge_items", {})
    new_items = getattr(scene, "node_items", {})
    new_edges = getattr(scene, "edge_items", {})

    tracks = []    # progress (0 to 1) -> None
    finals = []    # once the animation is over
    ghosts = []    # items carried over, kept referenced while they fade

    def late(p):    # lines come in once their boxes are on their way
        return max(0.0, (p - 0.35) / 0.65)

    def early(p):   # and go before their boxes are
        return min(1.0, p / 0.6)

    def carry_over(item, z):
        old.removeItem(item)
        scene.addItem(item)
        item.setZValue(z)
        ghosts.append(item)
        finals.append(lambda: scene.removeItem(item) if item.scene() is scene else None)

    if crossfade:
        leaving = list(old_items.items())
        leaving_edges = list(old_edges.values())
    else:
        leaving = [(node, item) for node, item in old_items.items() if node not in new_items]
        leaving_edges = [edge for key, edge in old_edges.items() if key not in new_edges]

    for node, item in leaving:
        start, opacity = item.pos(), item.opacity()
        into = None if crossfade else new_items.get(getattr(node, "merged_into", None))
        end = into.pos() if into is not None else start
        item.lines = []          # its lines stay behind with the old scene
        item.animating = True
        item.setAcceptedMouseButtons(Qt.NoButton)
        carry_over(item, 0.5 if crossfade else GHOST_Z)
        tracks.append(lambda p, item=item, start=start, end=end, opacity=opacity:
                      (item.setPos(lerp_point(start, end, p)), item.setOpacity(opacity * (1 - p))))

    for edge in leaving_edges:
        opacity = edge.opacity()
        edge.setAcceptedMouseButtons(Qt.NoButton)
        carry_over(edge, GHOST_EDGE_Z)
        tracks.append(lambda p, edge=edge, opacity=opacity: edge.setOpacity(opacity * (1 - early(p))))

    if not crossfade:
        neighbors = {}
        for mother, daughter in new_edges:
            neighbors.setdefault(daughter, []).append(mother)
        for mother, daughter in new_edges:
            neighbors.setdefault(mother, []).append(daughter)

        for node, item in new_items.items():
            end, target = item.pos(), item.opacity()
            before = old_items.get(node)
            # a box that changed size - the detailed/compact switch - grows or
            # shrinks into the new one on the way over, rather than arriving
            # already resized while it is still gliding
            was_wide = before.rect().width() if before is not None else None
            now_wide = item.rect().width()
            resizing = (was_wide is not None and abs(was_wide - now_wide) > 0.5
                        and hasattr(item, "shift_right_edge"))
            if before is not None:
                start, opacity = before.pos(), before.opacity()
            else:
                source = next((new_items[n] for n in neighbors.get(node, []) if n in old_items), None)
                if source is not None:
                    start = lerp_point(source.pos(), end, 1 - GRAPH_APPEAR_FROM)
                else:
                    start = QPointF(end.x(), end.y() - GRAPH_APPEAR_DROP)
                opacity = 0.0
            if start == end and abs(opacity - target) < 1e-6 and not resizing:
                continue
            item.animating = True

            # the size goes first, so the move that follows lays the lines
            # against the box as it now stands; a box that only changes size
            # fires no move, and has its lines laid again by hand
            def resize(item, width, now_wide):
                item.setRect(0, 0, width, item.rect().height())
                item.shift_right_edge(width - now_wide)
                for line in item.lines:
                    item.place_line(line)
                item.on_move(None)   # its power line rides the new width too

            def track(p, item=item, start=start, end=end, opacity=opacity, target=target,
                      was_wide=was_wide, now_wide=now_wide, resizing=resizing):
                if resizing:
                    item.setRect(0, 0, was_wide + (now_wide - was_wide) * p, item.rect().height())
                item.setPos(lerp_point(start, end, p))
                item.setOpacity(opacity + (target - opacity) * p)
                if resizing:
                    resize(item, item.rect().width(), now_wide)

            def final(item=item, end=end, now_wide=now_wide, resizing=resizing):
                if resizing:
                    item.setRect(0, 0, now_wide, item.rect().height())
                item.setPos(end)
                if resizing:
                    resize(item, now_wide, now_wide)
                item.animating = False

            tracks.append(track)
            finals.append(final)

        for key, edge in new_edges.items():
            if key not in old_edges:
                tracks.append(lambda p, edge=edge: edge.setOpacity(late(p)))

        # the light comes up on the newly focused node and goes off the one
        # before, each box's border thickening and thinning along with it
        old_focus = getattr(old, "focus_node", None)
        new_focus = getattr(scene, "focus_node", None)

        def light_and_border(item, strength):
            item.lit_level = strength
            pen = item.pen()
            pen.setWidthF(NODE_BORDER_WIDTH + (NODE_FOCUS_BORDER_WIDTH - NODE_BORDER_WIDTH) * strength)
            item.setPen(pen)
            item.update()

        if new_focus is not old_focus:
            item = new_items.get(new_focus)
            if item is not None:
                tracks.append(lambda p, item=item: light_and_border(item, p))
            item = new_items.get(old_focus)
            if item is not None:
                tracks.append(lambda p, item=item: light_and_border(item, 1 - p))
                finals.append(lambda item=item: light_and_border(item, 0.0))

    # propagation: timed in milliseconds rather than by the transition's own
    # progress, since a long chain runs on after the boxes have settled
    timed = []     # elapsed ms -> None
    total_ms = GRAPH_TRANSITION_MS
    if not crossfade:
        total_ms = max(total_ms, add_propagation(scene, old, leaving, timed, finals, ghosts))

    view.setScene(scene)
    if getattr(view, "moving", False):
        view.show_text(False)   # the new scene's labels, while it is still moving
    if not tracks and not timed:
        view.graph_transition = None
        return

    # the view normally repaints only the bounds of an item that changed, and
    # a glow lies outside its box: a fading glow was left undrawn, or drawn at
    # full strength and then dropped. While things animate the whole view is
    # repainted instead - a few hundred milliseconds, over a small graph.
    update_mode = view.viewportUpdateMode()
    view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

    # driven in milliseconds, linearly: the boxes' tracks take their eased
    # progress out of the first GRAPH_TRANSITION_MS of it, the propagation
    # reads the clock as it is
    easing = QEasingCurve(ANIMATION_CURVE)

    def apply(ms):
        # the graph is moving: drawn cheaply until the step settles
        if hasattr(view, "keep_moving"):
            view.keep_moving()
        p = easing.valueForProgress(min(1.0, ms / GRAPH_TRANSITION_MS))
        for track in tracks:
            track(p)
        for track in timed:
            track(ms)

    apply(0.0)
    done = [False]

    def finish():
        if done[0]:
            return
        done[0] = True
        view.graph_transition = None
        apply(total_ms)
        for final in finals:
            final()
        ghosts.clear()
        view.setViewportUpdateMode(update_mode)
        view.viewport().update()   # what the finals changed, drawn whole too

    def jump_to_end():
        animation.stop()   # deletes it: finished never fires for a stop
        finish()

    # played back steps come faster than a whole transition: it is played
    # faster, to be over by the time the next one starts
    duration = total_ms
    limit = getattr(view, "transition_limit_ms", None)
    if limit:
        duration = max(1, min(duration, limit))
    animation = animate_value(view, 0.0, total_ms, apply, duration)
    animation.setEasingCurve(QEasingCurve.Linear)
    animation.finished.connect(finish)
    view.graph_transition = jump_to_end

PROPAGATION_START_MS = 160   # once the merge has mostly landed
PROPAGATION_HOP_MS = 340     # the crest of the wave running the length of one line
PROPAGATION_RIPPLE_MS = 420  # the ring a node gives off as the wave reaches it
PROPAGATION_RIPPLE_GROWTH = 40
PROPAGATION_WAVE_HALF_LENGTH = 260   # scene units from the crest to either end of the swell
PROPAGATION_WAVE_MAX_HALF = 0.35     # of a line's own length, however short it is
PROPAGATION_WAVE_SWELL = 16         # how much wider than its line the wave is at its crest
PROPAGATION_WAVE_SAMPLES = 28        # short strokes the swell is drawn in
PROPAGATION_COLOR = QColor(TAB_INDICATOR_COLOR).lighter(160)

# a swell rolling along one line: the line drawn over itself, widening and
# brightening toward a crest and easing back to nothing on either side, like a
# wave passing down a rope. `crest` is how far along the path it is, 0 to 1,
# and may sit past either end while the wave rolls in or out - only the part on
# the line is drawn.
class PropagationWave(QGraphicsItem):
    def __init__(self, edge):
        super().__init__()
        self.path = QPainterPath(edge.path())
        self.line_width = edge.pen().widthF()
        self.length = max(self.path.length(), 1.0)
        # in path fractions - held to part of a short line, or its swell would
        # show on the next line before the crest had got there
        self.half = min(PROPAGATION_WAVE_HALF_LENGTH / self.length, PROPAGATION_WAVE_MAX_HALF)
        self.crest = None
        margin = (self.line_width + PROPAGATION_WAVE_SWELL) / 2 + 2
        self.bounds = self.path.boundingRect().adjusted(-margin, -margin, margin, margin)
        self.setAcceptedMouseButtons(Qt.NoButton)

    def boundingRect(self):
        return self.bounds

    def set_crest(self, crest):
        self.crest = crest
        self.update()

    def paint(self, painter, option, widget=None):
        if self.crest is None:
            return
        low = max(0.0, self.crest - self.half)
        high = min(1.0, self.crest + self.half)
        if high <= low:
            return
        painter.setRenderHint(QPainter.Antialiasing)
        step = (high - low) / PROPAGATION_WAVE_SAMPLES
        line, wave = QColor(NODE_LINE_COLOR), PROPAGATION_COLOR
        previous = self.path.pointAtPercent(low)
        for index in range(1, PROPAGATION_WAVE_SAMPLES + 1):
            at = low + step * index
            point = self.path.pointAtPercent(at)
            # a raised cosine: full at the crest, gently down to nothing
            middle = at - step / 2
            swell = (math.cos(math.pi * min(1.0, abs(middle - self.crest) / self.half)) + 1) / 2
            # blended toward the line's own color rather than faded out: the
            # strokes overlap where they meet, and see-through ones would bead
            color = QColor(
                round(line.red() + (wave.red() - line.red()) * swell),
                round(line.green() + (wave.green() - line.green()) * swell),
                round(line.blue() + (wave.blue() - line.blue()) * swell),
            )
            pen = QPen(color, self.line_width + PROPAGATION_WAVE_SWELL * swell)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawLine(previous, point)
            previous = point

def values_differ(before, after):
    if before is None or after is None:
        return before is not after
    return any(not math.isclose(before.get(key, 0), after.get(key, 0), rel_tol=1e-9, abs_tol=1e-9)
               for key in set(before) | set(after))

# a merge resizes more than the node it lands on: solve_rates carries the new
# demand back down the ingredients, and the byproduct step after it carries the
# new surplus forward. This shows that travelling: from the node the merge
# landed on (or the node whose byproducts are being checked), a wave rolls down
# every line whose rate changed - backward along an ingredient, toward what
# makes it, forward along a byproduct, toward what takes it - and each node it
# reaches whose numbers changed gives off a ring. Lines are followed on through
# nodes that did not change themselves when something further along did.
#
# Adds its items to the scene and its tracks to `timed` (elapsed ms), and
# returns how long it runs; 0 when nothing but the merger changed.
def add_propagation(scene, old, leaving, timed, finals, ghosts):
    old_items = getattr(old, "node_items", {})
    new_items = getattr(scene, "node_items", {})
    new_edges = getattr(scene, "edge_items", {})
    old_values = getattr(old, "values", {})
    new_values = getattr(scene, "values", {})
    old_rates = getattr(old, "edge_rates", {})
    new_rates = getattr(scene, "edge_rates", {})

    def node_changed(node):
        return node in old_items and values_differ(old_values.get(node), new_values.get(node))

    def rate_changed(key):
        return key in old_rates and not math.isclose(old_rates[key], new_rates.get(key, 0),
                                                     rel_tol=1e-9, abs_tol=1e-9)

    origins = [node.merged_into for node, _ in leaving if node.merged_into in new_items]
    if not origins:
        focus = getattr(scene, "focus_node", None)
        origins = [focus] if focus in new_items and focus in old_items else []
    if not origins:
        return 0

    # which way each line can be walked from each end
    ways = {}
    for (mother, daughter), edge in new_edges.items():
        if mother is daughter:
            continue
        if is_byproduct(mother):
            ways.setdefault(daughter, []).append(((mother, daughter), mother, True))
        else:
            ways.setdefault(mother, []).append(((mother, daughter), daughter, False))

    depth = {origin: 0 for origin in origins}
    hops = []                        # (key, target, forward, depth of the hop), outward
    queue = list(origins)
    for node in queue:
        for key, target, forward in ways.get(node, []):
            if target in depth:
                continue
            depth[target] = depth[node] + 1
            hops.append((key, target, forward, depth[node]))
            queue.append(target)

    # kept when it leads to a change: walked from the far ends back in
    leads_on = set()
    kept = []
    for key, target, forward, level in reversed(hops):
        if node_changed(target) or rate_changed(key) or target in leads_on:
            kept.append((key, target, forward, level))
            leads_on.add(key[0] if not forward else key[1])
    if not kept:
        return 0

    def carry(item, z):
        item.setZValue(z)
        item.setVisible(False)
        scene.addItem(item)
        ghosts.append(item)
        finals.append(lambda: scene.removeItem(item) if item.scene() is scene else None)

    # a ring from a node as the wave reaches it - and from the node the merge
    # landed on as the wave sets off, the stone dropped in the water
    def add_ripple(box, ripple_ms):
        ripple = QGraphicsPathItem()
        ripple.setPen(QPen(PROPAGATION_COLOR, NODE_FOCUS_BORDER_WIDTH))
        ripple.setAcceptedMouseButtons(Qt.NoButton)
        carry(ripple, 0.5)

        def run_ripple(ms):
            local = (ms - ripple_ms) / PROPAGATION_RIPPLE_MS
            if not 0 < local < 1:
                ripple.setVisible(False)
                return
            grow = PROPAGATION_RIPPLE_GROWTH * (1 - (1 - local) ** 2)
            rect = QRectF(box.pos(), box.rect().size()).adjusted(-grow, -grow, grow, grow)
            path = QPainterPath()
            path.addRoundedRect(rect, NODE_RADIUS + grow, NODE_RADIUS + grow)
            ripple.setPath(path)
            ripple.setOpacity(1 - local)
            ripple.setVisible(True)

        timed.append(run_ripple)
        return ripple_ms + PROPAGATION_RIPPLE_MS

    end_ms = 0
    for origin in origins:
        end_ms = max(end_ms, add_ripple(new_items[origin], PROPAGATION_START_MS - PROPAGATION_HOP_MS / 3))

    for key, target, forward, level in kept:
        edge = new_edges[key]
        start_ms = PROPAGATION_START_MS + level * PROPAGATION_HOP_MS
        wave = PropagationWave(edge)
        carry(wave, GHOST_EDGE_Z + 0.05)   # over its own line, under the boxes

        # the crest runs the line in one hop, so a chain hands the wave on
        # without a gap; its swell rolls in before and out after. The path
        # runs from the consumer to the producer: an ingredient's wave follows
        # it, a byproduct's runs it the other way.
        def run_wave(ms, wave=wave, start_ms=start_ms, forward=forward):
            local = (ms - start_ms) / PROPAGATION_HOP_MS
            if not -wave.half < local < 1 + wave.half:
                wave.setVisible(False)
                return
            wave.set_crest(1 - local if forward else local)
            wave.setVisible(True)

        timed.append(run_wave)
        end_ms = max(end_ms, start_ms + PROPAGATION_HOP_MS * (1 + wave.half))

        box = new_items.get(target)
        if box is not None and node_changed(target):
            end_ms = max(end_ms, add_ripple(box, start_ms + PROPAGATION_HOP_MS))

    return end_ms

FIT_MARGIN = 120   # scene units of breathing room around the fitted content

# the zoom and scene center that show all of rect, as (zoom, center)
def fit_camera(view, rect):
    if rect.isEmpty():
        return view.zoom, QPointF(0, 0)

    rect = rect.adjusted(-FIT_MARGIN, -FIT_MARGIN, FIT_MARGIN, FIT_MARGIN)
    viewport = view.viewport().size()
    if viewport.width() <= 0 or viewport.height() <= 0:
        return view.zoom, rect.center()

    # no floor: whatever the tree's size, all of it has to fit without moving
    # the camera - even a factory big enough to need less than ZOOM_MIN
    target = min(viewport.width() / rect.width(), viewport.height() / rect.height())
    return min(target, ZOOM_MAX), rect.center()

# zooms and centers the view so the whole generated graph is visible, and
# makes that the starting camera the reset button goes back to. Goes through
# apply_zoom (not view.fitInView) so the view's own self.zoom, which
# wheelEvent steps from, stays in sync with the resulting scale.
def fit_view_to_rect(view, rect, animate=False):
    view.start_rect = QRectF(rect)
    if animate:
        view.reset_camera()   # the same glide the reset button takes
        return
    if view.zoom_animation is not None:
        view.zoom_animation.stop()
        view.zoom_animation = None

    zoom, center = fit_camera(view, rect)
    view.apply_zoom(zoom)
    view.zoom_target = zoom
    view.centerOn(center)

# ===================================================== PANEL =======================================================
PANEL_WIDTH = 350
PANEL_BG = "#2a2a2a"
PANEL_SECTIONS = ("Output", "Option")
PANEL_TAB_LABELS = ("Output", "Generator")   # the two lists the section holds
PANEL_TAB_SIDES = ("output", "generator")
PANEL_TAB_ACCENTS = ("blue", "yellow")   # the accent each side puts the app in
TAB_BADGE_SIZE = 18            # the little count in a tab's corner
TAB_BADGE_FONT_SIZE = 10
TAB_BADGE_MARGIN = 3
TAB_BADGE_BG = "#5a5a5a"       # a strip of tabs with no accents of its own
TAB_BADGE_COLOR = TEXT_ON_ACCENT
PANEL_FONT_SIZE = 15        # panel text runs a size above the rest of the app
PANEL_TITLE_COLOR = TEXT_MUTED
PANEL_TITLE_FONT_SIZE = 13
PANEL_TITLE_SPACING = 1
PANEL_DIVIDER_COLOR = "#3a3a3a"
PANEL_OUTPUT_SHARE = 3      # the two halves split the panel in this ratio
PANEL_OPTION_SHARE = 2
PANEL_SECTION_GAP = 16      # extra breathing room around the divider
PANEL_SYMBOL_SIZE = 22      # remove/dropdown buttons, bigger than the app-wide tab symbols
PANEL_SCROLLBAR_WIDTH = 6
PANEL_SCROLLBAR_COLOR = "#4a4a4a"
PANEL_SCROLLBAR_HOVER_COLOR = "#5e5e5e"
ADD_OUTPUT_LABEL = "Add Output"
ADD_GENERATOR_LABEL = "Add Generator"
ADD_OUTPUT_HOVER_BG = "#2f88c4"  # accent, darkened for hover
CONFIRM_LABEL = "Confirm"
# what the panel's own button says, from what pressing it would do: draw the
# first tree, put the outputs just added into the one on the map, or build the
# same outputs over with whatever else was changed
BUILD_LABELS = {"generate": "Generate", "add": "Add", "change": "Change", "regenerate": "Regenerate",
                "clear": "Clear"}
CONFIRM_ICON_SIZE = 16   # the glyph beside the build button's own word
CANCEL_CHANGES_LABEL = "Cancel changes"
CANCEL_CHANGES_TOOLTIP = "Put the outputs and recipes back the way the build read them"
PANEL_BUTTON_GAP = 6     # between the cancel row and the build button under it
CLEAR_OUTPUTS_LABEL = "Clear all"
CONFIRM_BG = TAB_INDICATOR_COLOR
CONFIRM_HOVER_BG = ADD_OUTPUT_HOVER_BG
CONFIRM_BORDER_WIDTH = 1
# by id, not alphabetically: that is the game data's own order, which follows
# progression, so the early-game parts sit at the top where they are looked for.
# An item nothing can make (no recipe, not even an extraction one) has no tree
# to build, so it is left out of the picker entirely.
OUTPUT_ITEMS = sorted((item for item in All_Items.values() if item.recipes),
                      key=lambda item: item.id)
# what the Generator tab offers: every way of making power, in the order the
# data lists them (the generators' own, biggest fuels last)
GENERATOR_RECIPES = list(POWER_ITEM.recipes)
DEFAULT_OUTPUT_VALUE = 1

# The game's own files read again, without closing the planner. The data is
# reloaded in place (search.reload), the tables this file works out from it
# are worked out again, and every project is built once more from what it
# asked for - its items and recipes are objects from the old data, and would
# otherwise be pointing at a game that is no longer there.
def reload_game_data(window):
    global OUTPUT_ITEMS, GENERATOR_RECIPES, MINER_MARK_PICTURES
    standing = {"projects": [saved_project(page) for page in window.project_pages()],
                "current": window.current_project()}

    search.reload()
    OUTPUT_ITEMS = sorted((item for item in All_Items.values() if item.recipes),
                          key=lambda item: item.id)
    GENERATOR_RECIPES = list(POWER_ITEM.recipes)
    MINER_MARK_PICTURES = {mark: All_Machines[f"Build_MinerMk{mark}_C"].picture
                           for mark in MINER_MARK_OPTIONS}
    # a recipe picked by hand is a recipe object of the data that has gone
    panel_options["recipe_choices"] = {}
    panel_options["node_recipe_choices"] = {}

    tabs = window.project_tabs
    for page in window.project_pages():
        index = tabs.indexOf(page)
        if index != -1:
            tabs.removeTab(index)
        page.deleteLater()
    window.restore(standing)
SEARCH_PLACEHOLDER = "Search…"
SEARCH_GAP = 4  # space between the button and the popup search bar
SEARCH_POPUP_MAX_HEIGHT = 1200  # high enough that the screen, not this, is what stops the list
SEARCH_POPUP_MIN_HEIGHT = 180   # the button sits low on a short screen; never squash it past this
SEARCH_POPUP_BOTTOM_MARGIN = 8  # clearance kept under the popup, off the app window's bottom edge
SEARCH_REOPEN_GUARD = 0.4  # seconds: a click on the opener this soon after the popup closed is the one that closed it
SEARCH_HEADING_ROLE = Qt.UserRole + 1   # marks a row as a category heading, not an item
SEARCH_HEADING_SCALE = 0.85             # a stage's own size against the rows under it
SEARCH_ICON_SIZE = 36
OUTPUT_PICTURE_SIZE = 38          # the item's picture left of the rate field in an output row
OUTPUT_PICTURE_GAP = 8
OUTPUT_RECIPE_HEIGHT = 26         # the recipe dropdown right of an output's name
OUTPUT_RECIPE_FONT_SIZE = 13
OUTPUT_RECIPE_ARROW_WIDTH = 22    # the ▾ at the end of the recipe line
OUTPUT_RECIPE_ARROW_FONT_SIZE = 18
OUTPUT_RATE_MAX_DIGITS = 9         # the rate field takes digits only, up to this many
OUTPUT_UNIT_ROOM = 50            # kept free at the rate field's right for its "/ min"
OUTPUT_FLUID_UNIT_ROOM = 16      # and a little more for a fluid's "m³ / min"
OUTPUT_STEP_WIDTH = 28            # each of the ◀ ▶ stepper buttons
OUTPUT_STEP_FONT_SIZE = 18
OUTPUT_RECIPE_GAP = 6             # between the "Recipe" label and that dropdown
OUTPUT_NAME_COLOR = TEXT_STRONG     # an output's name: softened from pure white, still the brightest text of its card
OUTPUT_RECIPE_COLOR = TEXT_NORMAL   # the chosen recipe: quieter than the name, still readable
OUTPUT_CAPTION_COLOR = TEXT_FAINT  # "Recipe", "/min": the small labels of an output card
OUTPUT_CARD_BG = "#252525"        # an output's card, a shade off the panel so each reads as one
OUTPUT_CARD_PADDING = 10
SEARCH_TAKEN_COLOR = TEXT_DISABLED          # an item already picked, greyed out in the list
SEARCH_TAKEN_TOOLTIP = "Already added"
SELECTION_BG = TAB_SYMBOL_HOVER_BG   # a soft highlight instead of a flat blue block
SEARCH_ROW_HOVER_BG = "rgba(255, 255, 255, 0.06)"   # a row of the output list under the mouse: subtler still
OUTPUT_FIELD_BG = "#1e1e1e"
OUTPUT_FIELD_EDITING_BG = "#2b2b2b"  # lighter while the field has focus
LIST_ROW_INSET = 2                   # a dropdown list row set in from the list's edges
OPTION_FIELD_PRESS_BG = "#181818"    # an option field held down, a step darker than at rest
RECIPE_FIELD_BG = "rgba(255, 255, 255, 0.035)"        # an output's recipe dropdown at rest: barely there
RECIPE_FIELD_BORDER = "rgba(255, 255, 255, 0.08)"
RECIPE_FIELD_HOVER_BORDER = "rgba(255, 255, 255, 0.22)"
OUTPUT_FIELD_BORDER = "#444"
MENU_BG = "#252525"
MENU_ITEM_PADDING = "8px 12px"

STEP_AMOUNT = 1
OUTPUT_REMOVE_SIZE = 26
OUTPUT_REMOVE_SYMBOL_SIZE = 16    # the drawn cross inside it
STEP_LEFT_LABEL = "◀"
STEP_RIGHT_LABEL = "▶"

def make_output_icon_button(label, font_size=PANEL_FONT_SIZE, size=PANEL_SYMBOL_SIZE):
    button = QPushButton(label)
    button.setFixedSize(size, size)
    button.setFlat(True)
    button.setCursor(Qt.PointingHandCursor)
    button.setFocusPolicy(Qt.NoFocus)
    button.setStyleSheet(
        "QPushButton {"
        "  border: none;"
        "  background: transparent;"
        f"  color: {TAB_SYMBOL_COLOR};"
        "  font-weight: bold;"
        f"  font-size: {font_size}px;"
        "  padding: 0;"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "}"
        "QPushButton:hover {"
        f"  background: {TAB_SYMBOL_HOVER_BG};"
        f"  color: {TAB_SYMBOL_HOVER_COLOR};"
        "}"
        "QPushButton:pressed {"
        f"  background: {TAB_SYMBOL_PRESS_BG};"
        f"  color: {CLOSE_BUTTON_HOVER_COLOR};"
        "}"
    )
    return button

def make_remove_output_button():
    button = make_output_icon_button("", size=OUTPUT_REMOVE_SIZE)
    set_close_symbol(button, OUTPUT_REMOVE_SYMBOL_SIZE)
    return button

# every button in the app acts when the click is let go, not when it goes down,
# so a press can still be taken back by sliding off before releasing. A
# QComboBox drops its list on the press; this makes `combo` and the `widgets`
# around it (its field, its combo itself) open it on the release instead - and
# only when the release lands on the widget the press did.
def open_list_on_release(combo, *widgets):
    pressed = {"on": None}

    class Opener(QObject):
        def eventFilter(self, watched, event):
            try:
                kind = event.type()
                if kind not in (QEvent.MouseButtonPress, QEvent.MouseButtonDblClick, QEvent.MouseButtonRelease):
                    return False
                if event.button() != Qt.LeftButton:
                    return False
                if kind != QEvent.MouseButtonRelease:
                    pressed["on"] = watched
                    return True   # nothing yet: the combo would drop its list here
                was, pressed["on"] = pressed["on"], None
                if was is watched and watched.rect().contains(event.position().toPoint()):
                    combo.showPopup()
                return True
            except RuntimeError:
                return False   # a widget gone while the app closes

    combo.opener = Opener(combo)   # kept alive by the combo
    for widget in widgets:
        widget.installEventFilter(combo.opener)

# a combo drops its list as wide as the combo itself, which inside a field is
# narrower than the field - its margins and arrow are not the combo's. The list
# is laid out under the whole field instead, edge to edge with it, right as it
# shows (after the combo has placed it where it wants).
def list_under_field(field, combo):
    # Qt's own roll-down of a combo's list (on Windows) sizes the list only
    # once it has rolled out, so the width snapped over at the end. The lists
    # fade in by themselves (track_field_state), so that roll is switched off
    # and the list has the field's width from its very first frame.
    QApplication.setEffectEnabled(Qt.UI_AnimateCombo, False)
    window = combo.view().window()

    def fit():
        try:
            left = field.mapToGlobal(QPoint(0, 0)).x()
            window.setGeometry(left, window.y(), field.width(), window.height())
        except RuntimeError:
            pass   # the field went while the list was opening

    class Fit(QObject):
        def eventFilter(self, watched, event):
            try:
                if event.type() == QEvent.Show:
                    fit()
                    QTimer.singleShot(0, fit)   # once more, after the combo's own placing
                return False
            except RuntimeError:
                return False

    field.list_fit = Fit(field)   # kept alive by the field
    window.installEventFilter(field.list_fit)

# a field holding a dropdown answers the mouse the way every clickable does: its
# "state" property goes "hover" under the mouse, "pressed" while a click is held
# on it or on anything inside it (`parts`), and "open" while its list shows -
# for the field's own stylesheet to draw. Installed after open_list_on_release,
# so it sees each press before that swallows it.
def track_field_state(field, combo, *parts):
    window = combo.view().window()
    field.setProperty("state", "rest")

    def set_state(state):
        if field.property("state") != state:
            field.setProperty("state", state)
            field.style().unpolish(field)
            field.style().polish(field)

    class Tracker(QObject):
        def eventFilter(self, watched, event):
            try:
                kind = event.type()
                if watched is window:
                    if kind == QEvent.Show:
                        set_state("open")
                        fade_window_in(window)   # the list fades in as it drops
                    elif kind == QEvent.Hide:
                        set_state("hover" if field.underMouse() else "rest")
                    return False
                if field.property("state") == "open":
                    return False
                if kind == QEvent.Enter and watched is field:
                    set_state("hover")
                elif kind == QEvent.Leave and watched is field:
                    set_state("rest")
                elif kind in (QEvent.MouseButtonPress, QEvent.MouseButtonDblClick) and event.button() == Qt.LeftButton:
                    set_state("pressed")
                elif kind == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                    set_state("hover" if field.rect().contains(field.mapFromGlobal(event.globalPosition().toPoint()))
                              else "rest")
                return False
            except RuntimeError:
                return False   # a widget gone while the app closes

    field.tracker = Tracker(field)   # kept alive by the field
    for widget in (field, window) + parts:
        widget.installEventFilter(field.tracker)

# the recipe an output is made with, picked among every recipe its item has -
# the item's first, its default, to start with. A borderless combo with a drawn
# arrow, as the option rows below use (a styled QComboBox loses its native
# arrow), but with no field of its own: it reads as a line of the card it sits
# in, and only lights up under the mouse. The recipe names can be long, so it
# takes what the line leaves and elides; the list it drops is as wide as its
# longest name. Returns the field and a function giving the chosen Recipe.
#
# `recipe` is the one to start on (None: the first). field.set_used(recipes)
# greys out the recipes other outputs of the same item already run, so they
# cannot be picked here; `on_change` is called whenever the pick changes.
# `options`, when given, is the list of recipes to choose from instead of the
# item's own - a node supplying several items answers for all of them
def make_recipe_dropdown(item, recipe=None, on_change=None, options=None):
    field = QWidget()
    field.setObjectName("recipe_field")
    field.setFixedHeight(OUTPUT_RECIPE_HEIGHT)
    field.setAttribute(Qt.WA_StyledBackground, True)
    field.setStyleSheet(
        # at rest a very faint ground and border, just enough to read as
        # something to click, stronger under the mouse
        "QWidget#recipe_field {"
        f"  background-color: {RECIPE_FIELD_BG};"
        f"  border: 1px solid {RECIPE_FIELD_BORDER};"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "}"
        # states kept by track_field_state
        "QWidget#recipe_field[state=\"hover\"] {"
        f"  background-color: {TAB_SYMBOL_HOVER_BG};"
        f"  border: 1px solid {RECIPE_FIELD_HOVER_BORDER};"
        "}"
        "QWidget#recipe_field[state=\"pressed\"] {"
        f"  background-color: {TAB_SYMBOL_PRESS_BG};"
        f"  border: 1px solid {RECIPE_FIELD_HOVER_BORDER};"
        "}"
        "QWidget#recipe_field[state=\"open\"] {"
        f"  background-color: {TAB_SYMBOL_HOVER_BG};"
        f"  border: 1px solid {TAB_INDICATOR_COLOR};"
        "}"
    )
    field_layout = QHBoxLayout(field)
    field_layout.setContentsMargins(4, 0, 2, 0)
    field_layout.setSpacing(2)

    combo = ignore_closed_wheel(QComboBox())
    combo.setObjectName("recipe_combo")
    # rows painted from the stylesheet (rounded highlight) rather than as menu rows
    combo.setItemDelegate(QStyledItemDelegate(combo))
    options = list(options if options is not None else item.recipes)
    for option in options:
        combo.addItem(option.display_name, option)
    combo.setCurrentIndex(options.index(recipe) if recipe in options else 0)
    combo.setCursor(Qt.PointingHandCursor)
    combo.setToolTip(combo.currentText())

    def changed(_):
        combo.setToolTip(combo.currentText())
        if on_change is not None:
            on_change()

    combo.currentIndexChanged.connect(changed)
    combo.setStyleSheet(
        "QComboBox {"
        "  background: transparent;"
        f"  color: {OUTPUT_RECIPE_COLOR};"
        "  border: none;"
        f"  font-size: {OUTPUT_RECIPE_FONT_SIZE}px;"
        "  padding: 0;"
        "}"
        "QComboBox::drop-down { width: 0; border: none; }"
        "QComboBox QAbstractItemView {"
        "  outline: 0;"   # no focus frame drawn round the current row
        f"  background-color: {MENU_BG};"
        f"  color: {TEXT_NORMAL};"
        f"  border: 1px solid {OUTPUT_FIELD_BORDER};"
        f"  font-size: {OUTPUT_RECIPE_FONT_SIZE}px;"
        f"  selection-background-color: {SELECTION_BG};"
        f"  selection-color: {TAB_SELECTED_COLOR};"
        "}"
        # rows inset a little so their highlight shows its rounded corners
        "QComboBox QAbstractItemView::item {"
        f"  margin: {LIST_ROW_INSET}px;"
        f"  padding: {MENU_ITEM_PADDING};"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "}"
        "QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:selected {"
        f"  background-color: {SELECTION_BG};"
        f"  color: {TAB_SELECTED_COLOR};"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "}"
        "QComboBox QAbstractItemView::item:pressed {"
        f"  background-color: {TAB_SYMBOL_PRESS_BG};"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "}"
        "QComboBox QAbstractItemView::item:focus {"
        "  border: none; outline: 0;"
        "}"
        "QComboBox QAbstractItemView::item:disabled {"
        f"  color: {SEARCH_TAKEN_COLOR};"
        "}"
    )
    view = combo.view()
    view.setMinimumWidth(view.sizeHintForColumn(0) + 2 * view.frameWidth() + 24)

    # the whole rest of its line, its arrow at the card's right edge; a name
    # too long for that is cut rather than pushing the line past the card
    combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
    combo.setMinimumContentsLength(1)
    combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    arrow = QPushButton("▾")
    arrow.setFixedWidth(OUTPUT_RECIPE_ARROW_WIDTH)
    arrow.setFlat(True)
    arrow.setCursor(Qt.PointingHandCursor)
    arrow.setFocusPolicy(Qt.NoFocus)
    arrow.setStyleSheet(
        "QPushButton {"
        "  border: none;"
        "  background: transparent;"
        f"  color: {OUTPUT_CAPTION_COLOR};"
        f"  font-size: {OUTPUT_RECIPE_ARROW_FONT_SIZE}px;"
        "  padding: 0;"
        "}"
        "QPushButton:hover {"
        f"  color: {TAB_SELECTED_COLOR};"
        "}"
        "QPushButton:pressed {"
        f"  color: {TEXT_NORMAL};"
        "}"
    )
    arrow.clicked.connect(combo.showPopup)

    # a click anywhere on the line drops the list, not only on the name - on
    # the click's release, like every button
    open_list_on_release(combo, field, combo)
    track_field_state(field, combo, combo, arrow)
    field.setCursor(Qt.PointingHandCursor)

    # a recipe another output of this item runs is greyed out and unpickable;
    # the one this output runs itself always stays available
    def set_used(recipes):
        model = combo.model()
        for index in range(combo.count()):
            used = combo.itemData(index) in recipes and index != combo.currentIndex()
            row_item = model.item(index)
            row_item.setEnabled(not used)
            row_item.setToolTip(SEARCH_TAKEN_TOOLTIP if used else "")

    field_layout.addWidget(combo, 1)
    field_layout.addWidget(arrow)
    field.combo = combo
    field.set_used = set_used
    return field, lambda: combo.currentData()

# an output, as a card read top to bottom - what it is, how it is made, how
# much of it: its name with the remove button, the recipe it is made with,
# then its picture beside the rate field and what that rate is counted in.
# `recipe` and `on_recipe_change` go to its recipe dropdown (see
# make_recipe_dropdown); the row's set_used greys that dropdown's used recipes.
def make_output_row(item, recipe=None, on_recipe_change=None, start=None, on_rate_change=None):
    row = QWidget()
    row.setObjectName("output_card")
    row.setAttribute(Qt.WA_StyledBackground, True)
    row.setStyleSheet(
        "QWidget#output_card {"
        f"  background-color: {OUTPUT_CARD_BG};"
        f"  border-radius: {HOVER_BORDER_RADIUS + 2}px;"
        "}"
        # the panel paints its own ground on everything inside it; the card's
        # text and rows show the card's instead, not a band of the panel's
        "QWidget#output_card QLabel, QWidget#output_card QWidget#output_header {"
        "  background: transparent;"
        "}"
    )
    row_layout = QVBoxLayout(row)
    row_layout.setContentsMargins(OUTPUT_CARD_PADDING, OUTPUT_CARD_PADDING,
                                  OUTPUT_CARD_PADDING, OUTPUT_CARD_PADDING)
    row_layout.setSpacing(4)

    header = QWidget()
    header.setObjectName("output_header")
    header_layout = QHBoxLayout(header)
    header_layout.setContentsMargins(0, 0, 0, 0)
    header_layout.setSpacing(4)

    # the item's own picture, left of its rate field. Scaled smoothly from the
    # texture at twice the size and marked as such, so it stays sharp on a high
    # density screen. A generator card carries its building instead, the way its
    # node does: power has no picture of its own, and which generator it is is
    # the whole of what the card says.
    def card_picture(recipe):
        if item is POWER_ITEM and recipe is not None:
            return picture_or_missing(recipe.machine[0].picture)
        return item_picture(item)

    picture = picture_label(card_picture(recipe), OUTPUT_PICTURE_SIZE)

    label = QLabel(item.display_name)
    label.setStyleSheet(f"color: {OUTPUT_NAME_COLOR}; font-size: {PANEL_FONT_SIZE}px; font-weight: bold;")

    remove_button = make_remove_output_button()
    remove_button.setToolTip("Remove this output")

    header_layout.addWidget(label, 1)
    header_layout.addWidget(remove_button)

    # how it is made: a quiet label, then the recipe it can be switched to
    recipe_line = QHBoxLayout()
    recipe_line.setContentsMargins(0, 0, 0, 0)
    recipe_line.setSpacing(OUTPUT_RECIPE_GAP)
    recipe_title = QLabel("Recipe:")
    recipe_title.setStyleSheet(f"color: {OUTPUT_CAPTION_COLOR}; font-size: {OUTPUT_RECIPE_FONT_SIZE}px;")
    # switching a generator card to another fuel switches its building too
    def recipe_picked():
        fresh = picture_label(card_picture(get_recipe()), OUTPUT_PICTURE_SIZE)
        picture.setPixmap(fresh.pixmap())
        picture.setAlignment(Qt.AlignCenter)
        if on_recipe_change is not None:
            on_recipe_change()

    recipe_field, get_recipe = make_recipe_dropdown(item, recipe, recipe_picked)
    row.set_used = recipe_field.set_used
    row.combo = recipe_field.combo
    recipe_line.addWidget(recipe_title)
    recipe_line.addWidget(recipe_field, 1)

    fluid = getattr(item, "is_fluid", False)
    # power is asked for in megawatts, and a generator card starts at what one
    # of that generator makes rather than at a single megawatt
    start = DEFAULT_OUTPUT_VALUE if start is None else start
    field = QLineEdit(str(start))
    field.setFixedHeight(OUTPUT_PICTURE_SIZE)   # level with the picture beside it
    # only digits go in: anything else typed or pasted is simply not taken.
    # Empty stays allowed while typing; commit() puts the last good value back.
    field.setValidator(QRegularExpressionValidator(QRegularExpression(rf"\d{{0,{OUTPUT_RATE_MAX_DIGITS}}}"), field))
    field.setStyleSheet(
        "QLineEdit {"
        f"  background-color: {OUTPUT_FIELD_BG};"
        f"  color: {TAB_SELECTED_COLOR};"
        f"  border: 1px solid {OUTPUT_FIELD_BORDER};"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        f"  font-size: {PANEL_FONT_SIZE}px;"
        # room on the right for the unit written inside the field
        f"  padding: 0 {OUTPUT_UNIT_ROOM + (OUTPUT_FLUID_UNIT_ROOM if fluid else 0)}px 0 10px;"
        "}"
        # while it holds focus the field is being edited: accent border and a
        # lighter background, so it is obvious which value you are typing into
        "QLineEdit:focus {"
        f"  background-color: {OUTPUT_FIELD_EDITING_BG};"
        f"  border: 1px solid {TAB_INDICATOR_COLOR};"
        "}"
        "QLineEdit:hover:!focus {"
        f"  border: 1px solid {TAB_SYMBOL_COLOR};"
        "}"
    )

    # editingFinished fires on Enter and on losing focus, which is exactly when
    # the typed text should be taken. Anything that is not a natural number is
    # thrown away and the last good value comes back.
    value = [start]

    def commit():
        typed = field.text().strip()
        if typed.isdigit():
            value[0] = int(typed)
        field.setText(str(value[0]))
        field.clearFocus()      # Enter ends the edit instead of leaving a caret
        if on_rate_change is not None:
            on_rate_change()    # a rate typed is a change to undo like any other

    field.editingFinished.connect(commit)

    def step(delta):
        value[0] = max(0, value[0] + delta)
        field.setText(str(value[0]))
        if on_rate_change is not None:
            on_rate_change()

    # a stepper of two buttons as tall as the field, square to it
    step_left = make_output_icon_button(STEP_LEFT_LABEL, OUTPUT_STEP_FONT_SIZE, OUTPUT_STEP_WIDTH)
    step_left.setFixedHeight(OUTPUT_PICTURE_SIZE)
    step_left.setToolTip(f"{-STEP_AMOUNT} {rate_unit(item)}")
    step_left.clicked.connect(lambda: step(-STEP_AMOUNT))

    step_right = make_output_icon_button(STEP_RIGHT_LABEL, OUTPUT_STEP_FONT_SIZE, OUTPUT_STEP_WIDTH)
    step_right.setFixedHeight(OUTPUT_PICTURE_SIZE)
    step_right.setToolTip(f"+{STEP_AMOUNT} {rate_unit(item)}")
    step_right.clicked.connect(lambda: step(STEP_AMOUNT))

    # what the number counts - that much of the item made every minute, in
    # cubic meters for a fluid - written inside the field at its right end,
    # and letting clicks through
    unit = QLabel("MW" if item is POWER_ITEM else "m³ / min" if fluid else "/ min")
    unit.setAttribute(Qt.WA_TransparentForMouseEvents)
    unit.setStyleSheet(f"color: {OUTPUT_CAPTION_COLOR}; font-size: {OUTPUT_RECIPE_FONT_SIZE}px;"
                       " background: transparent; border: none;")
    unit_layout = QHBoxLayout(field)
    unit_layout.setContentsMargins(0, 0, 10, 0)
    unit_layout.addStretch(1)
    unit_layout.addWidget(unit)

    value_row = QHBoxLayout()
    value_row.setSpacing(2)
    value_row.addWidget(picture)
    value_row.addSpacing(OUTPUT_PICTURE_GAP - 2)
    value_row.addWidget(field, 1)
    value_row.addSpacing(4)
    value_row.addWidget(step_left)
    value_row.addWidget(step_right)

    row_layout.addWidget(header)
    row_layout.addLayout(recipe_line)
    row_layout.addSpacing(4)
    row_layout.addLayout(value_row)

    return row, remove_button, lambda: value[0], get_recipe

# Qt.Popup makes this its own window: it grabs input, closes on an outside click
# or Escape, and can spill past the panel's edges, exactly like the menu did.
# The list lives inside the popup rather than in a QCompleter, so there is only
# one popup and the two cannot fight over the input grab. `items` is anything
# with .display_name (Item, Machine, Recipe, ...); `picture` says where its
# icon comes from, the entry's own by default. `is_taken`, when given,
# says which of them are already used: those stay listed, so a search still
# finds them, but greyed out and unpickable - popup.refresh_taken() rereads it,
# for the opener to call each time it shows the popup.
# The add list, filed by the stage of the game each item comes in at, and shown
# in the order written here. The space elevator's parts close off each tier,
# in bold - they are what that tier is building toward (SPACE_ELEVATOR_PARTS).
#
# Kept by hand, by display name. An item not listed here still shows, at the
# end under "Other", so a new one in the data never goes missing.
OUTPUT_CATEGORIES = [
    ("Tier 0", [
        "Iron Ore",
        "Iron Ingot",
        "Iron Plate",
        "Iron Rod",
        "Screw",
        "Reinforced Iron Plate",
        "Limestone",
        "Concrete",
        "Copper Ore",
        "Copper Ingot",
        "Wire",
        "Cable",
    ]),
    ("Tier 2", [
        "Copper Sheet",
        "Modular Frame",
        "Rotor",
        "Smart Plating",
    ]),
    ("Tier 3", [
        "Coal",
        "Water",
        "Steel Beam",
        "Steel Ingot",
        "Steel Pipe",
        "Versatile Framework",
    ]),
    ("Tier 4", [
        "Encased Industrial Beam",
        "Motor",
        "Stator",
        "Automated Wiring",
    ]),
    ("Tier 5", [
        "Petroleum Coke",
        "Crude Oil",
        "Heavy Oil Residue",
        "Rubber",
        "Plastic",
        "Polymer Resin",
        "Circuit Board",
    ]),
    ("Tier 6", [
        "Heavy Modular Frame",
        "Computer",
        "Adaptive Control Unit",
        "Modular Engine",
    ]),
    ("Tier 7", [
        "Bauxite",
        "Alclad Aluminium Sheet",
        "Alumina Solution",
        "Aluminium Casing",
        "Aluminium Scrap",
        "Aluminium Ingot",
        "Silica",
        "Caterium Ore",
        "Caterium Ingot",
        "Quickwire",
        "Fabric",
        "Sulfur",
        "Sulfuric Acid",
        "Battery",
        "Raw Quartz",
        "Quartz Crystal",
        "Crystal Oscillator",
        "Radio Control Unit",
        "AI Limiter",
        "High-Speed Connector",
        "Supercomputer",
        "Assembly Director System",
    ]),
    ("Tier 8", [
        "Uranium",
        "Electromagnetic Control Rod",
        "Encased Uranium Cell",
        "Nitrogen Gas",
        "Cooling System",
        "Fused Modular Frame",
        "Heat Sink",
        "Turbo Motor",
        "Copper Powder",
        "Encased Plutonium Cell",
        "Nitric Acid",
        "Non-Fissile Uranium",
        "Plutonium Pellet",
        "Pressure Conversion Cube",
        "Magnetic Field Generator",
        "Nuclear Pasta",
        "Thermal Propulsion Rocket",
    ]),
    ("Tier 9", [
        "SAM",
        "Diamonds",
        "Ficsite Ingot",
        "Ficsite Trigon",
        "Reanimated SAM",
        "SAM Fluctuator",
        "Time Crystal",
        "Dark Matter Crystal",
        "Power Shard",
        "Dark Matter Residue",
        "Excited Photonic Matter",
        "Neural-Quantum Processor",
        "Superposition Oscillator",
        "Singularity Cell",
        "Ficsonium",
        "AI Expansion Server",
        "Ballistic Warp Drive",
        "Biochemical Sculptor",
    ]),
    ("Fuels", [
        "Biomass",
        "Solid Biofuel",
        "Liquid Biofuel",
        "Compacted Coal",
        "Fuel",
        "Turbofuel",
        "Rocket Fuel",
        "Ionized Fuel",
        "Uranium Fuel Rod",
        "Plutonium Fuel Rod",
        "Ficsonium Fuel Rod",
    ]),
    ("Waste", [
        "Uranium Waste",
        "Plutonium Waste",
    ]),
    ("Packaging", [
        "Empty Canister",
        "Empty Fluid Tank",
        "Packaged Liquid Biofuel",
        "Packaged Water",
        "Packaged Oil",
        "Packaged Heavy Oil Residue",
        "Packaged Fuel",
        "Packaged Alumina Solution",
        "Packaged Sulfuric Acid",
        "Packaged Nitrogen Gas",
        "Packaged Nitric Acid",
        "Packaged Turbofuel",
        "Packaged Rocket Fuel",
        "Packaged Ionized Fuel",
    ]),
    ("Equipment & ammo", [
        "Black Powder",
        "Smokeless Powder",
        "Nobelisk",
        "Gas Nobelisk",
        "Pulse Nobelisk",
        "Cluster Nobelisk",
        "Nuke Nobelisk",
        "Iron Rebar",
        "Stun Rebar",
        "Shatter Rebar",
        "Explosive Rebar",
        "Rifle Ammo",
        "Homing Rifle Ammo",
        "Turbo Rifle Ammo",
        "Gas Filter",
        "Iodine-Infused Filter",
    ]),
    ("Alien", [
        "Alien Protein",
        "Alien DNA Capsule",
        "Alien Power Matrix",
    ]),
    ("Alternate recipes only", [
        "Dissolved Silica",
        "Portable Miner",
    ]),
    ("Events", [
        "Blue FICSMAS Ornament",
        "Candy Cane",
        "Copper FICSMAS Ornament",
        "FICSMAS Actual Snow",
        "FICSMAS Bow",
        "FICSMAS Ornament Bundle",
        "FICSMAS Tree Branch",
        "FICSMAS Wonder Star",
        "FICSMAS Wreath",
        "Fancy Fireworks",
        "Iron FICSMAS Ornament",
        "Red FICSMAS Ornament",
        "Snowball",
        "Sparkly Fireworks",
        "Sweet Fireworks",
    ]),
]

# the space elevator's parts, shown in bold - the last of each tier's list
SPACE_ELEVATOR_PARTS = {
    "Smart Plating",
    "Versatile Framework",
    "Automated Wiring",
    "Adaptive Control Unit",
    "Modular Engine",
    "Assembly Director System",
    "Magnetic Field Generator",
    "Nuclear Pasta",
    "Thermal Propulsion Rocket",
    "AI Expansion Server",
    "Ballistic Warp Drive",
    "Biochemical Sculptor",
}

# The items of a list as rows, in the order they are shown: ("group", title)
# and ("item", entry, bold) - a space elevator part being the bold one. A
# category with nothing of this list in it is left out.
def categorized_rows(items):
    by_name = {entry.display_name: entry for entry in items}
    rows, placed = [], set()
    for group, names in OUTPUT_CATEGORIES:
        entries = [by_name[name] for name in names if name in by_name]
        if entries:
            rows.append(("group", group))
            rows += [("item", entry, entry.display_name in SPACE_ELEVATOR_PARTS) for entry in entries]
            placed.update(entries)
    rest = sorted((entry for entry in items if entry not in placed), key=lambda entry: entry.display_name)
    if rest:
        rows += [("group", "Other")] + [("item", entry, False) for entry in rest]
    return rows

def make_search_popup(parent, items, on_pick, is_taken=None, picture=None):
    popup = QWidget(parent, Qt.Popup)
    popup.setAttribute(Qt.WA_StyledBackground, True)
    popup.setStyleSheet(
        f"background-color: {MENU_BG};"
        f"border: 1px solid {OUTPUT_FIELD_BORDER};"
        f"border-radius: {HOVER_BORDER_RADIUS}px;"
    )

    popup_layout = QVBoxLayout(popup)
    popup_layout.setContentsMargins(6, 6, 6, 6)
    popup_layout.setSpacing(6)

    field = QLineEdit()
    field.setPlaceholderText(SEARCH_PLACEHOLDER)
    field.setStyleSheet(
        "QLineEdit {"
        f"  background-color: {OUTPUT_FIELD_BG};"
        f"  color: {TAB_SELECTED_COLOR};"
        f"  border: 1px solid {TAB_INDICATOR_COLOR};"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        f"  font-size: {PANEL_FONT_SIZE}px;"
        "  padding: 8px;"
        "}"
    )

    choices = QListWidget()
    choices.setIconSize(QSize(SEARCH_ICON_SIZE, SEARCH_ICON_SIZE))
    # The output list is filed by stage of the game (see OUTPUT_CATEGORIES):
    # 157 items is more than anyone reads through, and where a thing comes in
    # is how a player already knows it. A heading is a row like any other,
    # minus the flags that let it be picked or landed on; SEARCH_HEADING_ROLE
    # marks it, for the filter below. The generators' list is made of recipes,
    # not items, and is shown as it comes.
    def heading_row(title):
        row = QListWidgetItem(title.upper())
        row.setFlags(Qt.ItemIsEnabled & ~Qt.ItemIsEnabled)   # no flags: shown, never picked
        row.setData(SEARCH_HEADING_ROLE, 1)
        font = row.font()
        font.setBold(True)
        font.setPointSizeF(font.pointSizeF() * SEARCH_HEADING_SCALE)
        row.setFont(font)
        row.setForeground(QColor(TEXT_MUTED))
        return row

    filed = picture is None   # a list of items, rather than the generators' recipes
    rows = categorized_rows(items) if filed else [("item", entry, False) for entry in items]
    for row in rows:
        if row[0] == "group":
            choices.addItem(heading_row(row[1]))
        else:
            entry, bold = row[1], row[2]
            icon = picture(entry) if picture is not None else getattr(entry, "picture", "")
            list_item = QListWidgetItem(picture_icon(icon, SEARCH_ICON_SIZE), entry.display_name)
            list_item.setData(Qt.UserRole, entry)   # so choose() can hand back the real object
            if bold:
                font = list_item.font()
                font.setBold(True)
                list_item.setFont(font)
            choices.addItem(list_item)
    choices.setFrameShape(QListWidget.NoFrame)
    choices.setMaximumHeight(SEARCH_POPUP_MAX_HEIGHT)
    popup.choices = choices   # the opener resizes it to the room below the button
    choices.setStyleSheet(
        "QListWidget {"
        "  outline: 0;"   # no focus frame drawn round the current row
        f"  background-color: {MENU_BG};"
        f"  color: {TEXT_NORMAL};"
        f"  font-size: {PANEL_FONT_SIZE}px;"
        "  border: none;"
        "}"
        "QListWidget::item {"
        f"  padding: {MENU_ITEM_PADDING};"
        "}"
        # a soft neutral highlight instead of a flat blue block, so the icon
        # and text stay readable when an item is hovered/current
        "QListWidget::item:focus {"
        "  border: none; outline: 0;"
        "}"
        "QListWidget::item:hover {"
        f"  background-color: {SEARCH_ROW_HOVER_BG};"
        f"  color: {TAB_SELECTED_COLOR};"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "}"
        "QListWidget::item:pressed {"
        f"  background-color: {TAB_SYMBOL_PRESS_BG};"
        "}"
        "QListWidget::item:selected {"
        f"  background-color: {SEARCH_ROW_HOVER_BG};"
        f"  color: {TAB_SELECTED_COLOR};"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "}"
        # already taken: greyed out, and no hover highlight to invite a click.
        # The icon greys along with it, Qt drawing a disabled item's icon in
        # its disabled mode.
        "QListWidget::item:disabled {"
        f"  color: {SEARCH_TAKEN_COLOR};"
        "  background-color: transparent;"
        "}"
    )

    popup_layout.addWidget(field)
    popup_layout.addWidget(choices)

    def pickable(option):
        return bool(option.flags() & Qt.ItemIsEnabled)

    def is_heading(option):
        return bool(option.data(SEARCH_HEADING_ROLE))

    def refilter(text):
        text = text.strip().lower()
        first_visible = None
        # the items first, on their own names...
        for i in range(choices.count()):
            option = choices.item(i)
            if is_heading(option):
                continue
            hidden = text not in option.text().lower()
            option.setHidden(hidden)
            # a taken top match stays the one Enter points at, and choose()
            # refuses it - rather than Enter quietly adding the next match down
            if not hidden and first_visible is None:
                first_visible = option
        # ...then each heading, shown only while something under it is: up to
        # the next heading as high as itself, so a tier reaches past its own
        # milestones and a milestone stops at the next one
        for i in range(choices.count()):
            option = choices.item(i)
            level = option.data(SEARCH_HEADING_ROLE)
            if not level:
                continue
            shown = False
            for j in range(i + 1, choices.count()):
                below = choices.item(j)
                deeper = below.data(SEARCH_HEADING_ROLE)
                if deeper and deeper <= level:
                    break
                if not deeper and not below.isHidden():
                    shown = True
                    break
            option.setHidden(not shown)
        # NoUpdate keeps the top match "current" (so Enter still picks it)
        # without visually selecting it, no blue highlight before a real click
        choices.setCurrentItem(first_visible, QItemSelectionModel.NoUpdate)

    def refresh_taken():
        for i in range(choices.count()):
            option = choices.item(i)
            if is_heading(option):
                continue
            taken = bool(is_taken and is_taken(option.data(Qt.UserRole)))
            flags = option.flags()
            if taken:
                option.setFlags(flags & ~(Qt.ItemIsEnabled | Qt.ItemIsSelectable))
            else:
                option.setFlags(flags | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            option.setToolTip(SEARCH_TAKEN_TOOLTIP if taken else "")
        refilter(field.text())

    popup.refresh_taken = refresh_taken

    def choose(option):
        if option is None or option.isHidden() or not pickable(option):
            return
        popup.hide()
        # the pick is done with: the row it was does not stay marked for next time
        choices.clearSelection()
        on_pick(option.data(Qt.UserRole))

    field.textChanged.connect(refilter)
    field.returnPressed.connect(lambda: choose(choices.currentItem()))
    choices.itemClicked.connect(choose)
    refilter("")

    # Qt closes a popup on the mouse press that lands outside it, before that
    # click reaches whatever was pressed. When that was the button that opens
    # it, the click would then open it straight back up - so the moment it
    # closed is kept, for the opener to tell that click from a fresh one.
    popup.closed_at = 0.0

    class ClosedStamp(QObject):
        def eventFilter(self, watched, event):
            if event.type() == QEvent.Hide:
                popup.closed_at = time.monotonic()
            return False

    popup.closed_stamp = ClosedStamp(popup)   # kept alive by the popup
    popup.installEventFilter(popup.closed_stamp)

    return popup, field

# one titled half of the side panel. Returns the section and the layout to fill,
# so the caller never has to know about the title row or the scrolling.
# a strip of tabs, one of them always down: the same one the left panel's
# pages use. `on_select` gets the index picked; the first starts selected.
def make_tab_strip(titles, on_select, accents=None):
    strip = QWidget()
    strip.setObjectName("left_tabs")
    strip.setAttribute(Qt.WA_StyledBackground, True)
    strip.setStyleSheet(
        "QWidget#left_tabs {"
        f"  background: {LEFT_PANEL_TAB_BG};"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "}"
    )
    row = QHBoxLayout(strip)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(0)
    tabs = []

    def select(index):
        for position, tab in enumerate(tabs):
            tab.setChecked(position == index)
        on_select(index)

    for index, title in enumerate(titles):
        if index:
            divider = QWidget()
            divider.setAttribute(Qt.WA_StyledBackground, True)
            divider.setFixedSize(1, LEFT_PANEL_TAB_DIVIDER_HEIGHT)
            divider.setStyleSheet(f"background: {LEFT_PANEL_TAB_DIVIDER};")
            row.addWidget(divider, 0, Qt.AlignVCenter)

        # rounded only on the strip's outside
        first, last = index == 0, index == len(titles) - 1
        radius = HOVER_BORDER_RADIUS
        corners = (f"  border-top-left-radius: {radius if first else 0}px;"
                   f"  border-bottom-left-radius: {radius if first else 0}px;"
                   f"  border-top-right-radius: {radius if last else 0}px;"
                   f"  border-bottom-right-radius: {radius if last else 0}px;")

        tab = QPushButton(title)
        tab.setCheckable(True)
        tab.setChecked(index == 0)
        tab.setCursor(Qt.PointingHandCursor)
        tab.setFocusPolicy(Qt.NoFocus)
        tab.setStyleSheet(
            "QPushButton {"
            f"  font-size: {PANEL_FONT_SIZE}px;"
            f"  padding: {LEFT_PANEL_TAB_PADDING}px;"
            "  border: none;"
            f"  border-bottom: {LEFT_PANEL_TAB_INDICATOR}px solid transparent;"
            + corners +
            f"  background: {LEFT_PANEL_TAB_BG};"
            f"  color: {TAB_UNSELECTED_COLOR};"
            "}"
            "QPushButton:hover {"
            f"  color: {TAB_SYMBOL_HOVER_COLOR};"
            f"  background: {LEFT_PANEL_TAB_HOVER_BG};"
            "}"
            "QPushButton:pressed {"
            f"  background: {TAB_SYMBOL_PRESS_BG};"
            "}"
            "QPushButton:checked {"
            f"  background: {LEFT_PANEL_TAB_CHECKED_BG};"
            f"  color: {TAB_SELECTED_COLOR};"
            f"  border-bottom: {LEFT_PANEL_TAB_INDICATOR}px solid {TAB_INDICATOR_COLOR};"
            "  border-bottom-left-radius: 0; border-bottom-right-radius: 0;"
            "  font-weight: bold;"
            "}"
        )
        # a small count in the corner, for how many cards that tab holds. Each
        # wears its own tab's accent whichever tab is down, so the two counts
        # can be told apart at a glance: fixed_accent keeps the app-wide swap
        # off it (see accent_widgets).
        badge = QLabel("0", tab)
        badge.setObjectName("tab_badge")
        badge.setProperty("fixed_accent", True)
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedSize(TAB_BADGE_SIZE, TAB_BADGE_SIZE)
        badge.setStyleSheet(
            "QLabel#tab_badge {"
            f"  background: {ACCENT_SHADES[accents[index]]['base'] if accents else TAB_BADGE_BG};"
            f"  color: {TAB_BADGE_COLOR};"
            f"  border-radius: {TAB_BADGE_SIZE // 2}px;"
            f"  font-size: {TAB_BADGE_FONT_SIZE}px;"
            "  font-weight: bold;"
            "}"
        )
        badge.hide()   # nothing in that list yet: no point in a zero
        tab.badge = badge

        def place_badge(tab=tab, badge=badge):
            badge.move(tab.width() - badge.width() - TAB_BADGE_MARGIN, TAB_BADGE_MARGIN)
            badge.raise_()

        tab.resizeEvent = lambda event, place=place_badge: place()
        tab.clicked.connect(lambda checked=False, position=index: select(position))
        row.addWidget(tab, 1)
        tabs.append(tab)

    # how many each holds, from the caller
    def set_counts(counts):
        for tab, count in zip(tabs, counts):
            tab.badge.setText(str(count))
            tab.badge.setVisible(bool(count))
            tab.badge.move(tab.width() - tab.badge.width() - TAB_BADGE_MARGIN, TAB_BADGE_MARGIN)
            tab.badge.raise_()

    strip.set_counts = set_counts
    return strip, tabs

def make_panel_section(title):
    section = QWidget()
    section_layout = QVBoxLayout(section)
    section_layout.setContentsMargins(0, 0, 0, 0)
    section_layout.setSpacing(8)

    heading = QLabel(title.upper())
    heading.setStyleSheet(
        f"color: {PANEL_TITLE_COLOR};"
        f"font-size: {PANEL_TITLE_FONT_SIZE}px;"
        "font-weight: bold;"
        f"letter-spacing: {PANEL_TITLE_SPACING}px;"
    )
    section_layout.addWidget(heading)

    # what stays put above the scrolling part (section.pinned) - the Add Output
    # button, say, which must not scroll away with the outputs it adds
    pinned = QVBoxLayout()
    pinned.setSpacing(8)
    section_layout.addLayout(pinned)
    section.pinned = pinned

    # the content lives inside a scroll area, so a section that fills up scrolls
    # on its own instead of pushing the other half off the panel
    content = QWidget()
    content_layout = QVBoxLayout(content)
    content_layout.setContentsMargins(0, 0, 0, 0)
    content_layout.setSpacing(8)

    body = QVBoxLayout()         # what the caller fills
    body.setSpacing(8)
    content_layout.addLayout(body)
    content_layout.addStretch()  # keeps the content packed at the top

    scroll = QScrollArea()
    scroll.setWidget(content)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QScrollArea.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setStyleSheet(
        "QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; }"
        "QScrollBar:vertical {"
        "  background: transparent;"
        f"  width: {PANEL_SCROLLBAR_WIDTH}px;"
        "  margin: 0;"
        "}"
        "QScrollBar::handle:vertical {"
        f"  background: {PANEL_SCROLLBAR_COLOR};"
        f"  border-radius: {PANEL_SCROLLBAR_WIDTH // 2}px;"
        "  min-height: 24px;"
        "}"
        "QScrollBar::handle:vertical:hover {"
        f"  background: {PANEL_SCROLLBAR_HOVER_COLOR};"
        "}"
        "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }"
        "QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }"
    )
    section_layout.addWidget(scroll, 1)

    return section, body

def make_panel_divider():
    divider = QWidget()
    divider.setAttribute(Qt.WA_StyledBackground, True)
    divider.setFixedHeight(1)
    divider.setStyleSheet(f"background-color: {PANEL_DIVIDER_COLOR};")
    return divider

# a label beside a dropdown, for a fixed set of choices (miner mark, conveyor
# level, ...). on_change fires with the picked value already converted to int.
FIELD_ROW_WIDTH = 150
FIELD_ROW_HEIGHT = 52
OPTION_ROW_GAP = 12
OPTION_ICON_SIZE = 32
OPTION_STAT_FONT_SIZE = 11

# what one level of each option is worth, shown small under its label
def miner_stat(mark):
    miner = All_Machines[f"Build_MinerMk{mark}_C"]
    per_minute = miner.items_per_cycle / miner.extract_cycle_time * 60
    return f"{per_minute:g} /min on a normal node"

def conveyor_stat(level):
    return f"{CONVEYOR_CAPACITY[level]:g} items/min"

def pipe_stat(level):
    return f"{PIPE_CAPACITY[level]:g} m³/min"

# stat_for turns the picked value into that little line; None leaves it out
def make_option_row(label_text, values, pictures, current, on_change, stat_for=None):
    row = QWidget()
    row_layout = QHBoxLayout(row)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.setSpacing(8)

    label = QLabel(label_text)
    label.setStyleSheet(f"color: {TAB_UNSELECTED_COLOR}; font-size: {PANEL_FONT_SIZE}px;")

    stat = None
    if stat_for is not None:
        stat = QLabel(stat_for(current))
        stat.setStyleSheet(f"color: {TEXT_ACCENT}; font-size: {OPTION_STAT_FONT_SIZE}px;")
        stat.setWordWrap(True)

    # a QComboBox loses its native drop-down arrow the moment its own border
    # or background is styled via QSS, so the arrow is drawn ourselves instead:
    # the combo sits borderless inside a field that looks like the other
    # inputs, with an explicit "v" button as the unmistakable dropdown cue.
    #
    # The whole field is the button: a click anywhere on it drops the list. It
    # answers the mouse like the rate fields do - a lighter border under it,
    # the accent border and a lighter ground while its list is open - through
    # the "state" property the event filter below keeps.
    field = QWidget()
    field.setObjectName("option_field")
    field.setFixedSize(FIELD_ROW_WIDTH, FIELD_ROW_HEIGHT)
    field.setAttribute(Qt.WA_StyledBackground, True)
    field.setCursor(Qt.PointingHandCursor)
    field.setStyleSheet(
        "QWidget#option_field {"
        f"  background-color: {OUTPUT_FIELD_BG};"
        f"  border: 1px solid {OUTPUT_FIELD_BORDER};"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "}"
        # states kept by track_field_state
        "QWidget#option_field[state=\"hover\"] {"
        f"  border: 1px solid {TAB_SYMBOL_COLOR};"
        "}"
        "QWidget#option_field[state=\"pressed\"] {"
        f"  background-color: {OPTION_FIELD_PRESS_BG};"
        f"  border: 1px solid {TAB_SYMBOL_HOVER_COLOR};"
        "}"
        "QWidget#option_field[state=\"open\"] {"
        f"  background-color: {OUTPUT_FIELD_EDITING_BG};"
        f"  border: 1px solid {TAB_INDICATOR_COLOR};"
        "}"
    )
    field_layout = QHBoxLayout(field)
    field_layout.setContentsMargins(8, 4, 6, 4)
    field_layout.setSpacing(6)

    combo = ignore_closed_wheel(QComboBox())
    combo.setItemDelegate(QStyledItemDelegate(combo))   # rounded row highlight, see the recipe dropdown
    combo.setIconSize(QSize(OPTION_ICON_SIZE, OPTION_ICON_SIZE))
    for value in values:
        # the picture drawn as is on the highlighted row too, not tinted blue
        picture = picture_pixmap(pictures[value], OPTION_ICON_SIZE)
        icon = QIcon(picture)
        icon.addPixmap(picture, QIcon.Selected)
        combo.addItem(icon, str(value))
    combo.setCurrentText(str(current))
    combo.setCursor(Qt.PointingHandCursor)
    combo.setStyleSheet(
        "QComboBox {"
        "  background: transparent;"
        f"  color: {TAB_SELECTED_COLOR};"
        "  border: none;"
        f"  font-size: {PANEL_FONT_SIZE}px;"
        "  padding: 4px 0;"
        "}"
        "QComboBox::drop-down { width: 0; border: none; }"
        "QComboBox QAbstractItemView {"
        "  outline: 0;"   # no focus frame drawn round the current row
        f"  background-color: {MENU_BG};"
        f"  color: {TEXT_NORMAL};"
        f"  border: 1px solid {OUTPUT_FIELD_BORDER};"
        f"  selection-background-color: {SELECTION_BG};"
        f"  selection-color: {TAB_SELECTED_COLOR};"
        "}"
        # rows inset a little so their highlight shows its rounded corners
        "QComboBox QAbstractItemView::item {"
        f"  margin: {LIST_ROW_INSET}px;"
        f"  padding: {MENU_ITEM_PADDING};"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "}"
        "QComboBox QAbstractItemView::item:hover, QComboBox QAbstractItemView::item:selected {"
        f"  background-color: {SELECTION_BG};"
        f"  color: {TAB_SELECTED_COLOR};"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "}"
        "QComboBox QAbstractItemView::item:pressed {"
        f"  background-color: {TAB_SYMBOL_PRESS_BG};"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "}"
    )
    def changed(text):
        value = int(text)
        if stat is not None:
            stat.setText(stat_for(value))
        on_change(value)

    combo.currentTextChanged.connect(changed)

    arrow = QPushButton("▾")
    arrow.setFixedWidth(20)
    arrow.setFlat(True)
    arrow.setCursor(Qt.PointingHandCursor)
    arrow.setFocusPolicy(Qt.NoFocus)
    arrow.setStyleSheet(
        "QPushButton {"
        "  border: none;"
        "  background: transparent;"
        f"  color: {TAB_UNSELECTED_COLOR};"
        f"  font-size: {PANEL_FONT_SIZE}px;"
        "}"
        "QPushButton:hover {"
        f"  color: {TAB_SELECTED_COLOR};"
        "}"
        "QPushButton:pressed {"
        f"  color: {TEXT_NORMAL};"
        "}"
    )
    arrow.clicked.connect(combo.showPopup)

    field_layout.addWidget(combo, 1)
    field_layout.addWidget(arrow)

    open_list_on_release(combo, field, combo)   # the click lands on the release
    track_field_state(field, combo, combo, arrow)
    list_under_field(field, combo)
    field.combo = combo

    # the name on top and its stat right under it, both left of the dropdown
    caption = QVBoxLayout()
    caption.setContentsMargins(0, 0, 0, 0)
    caption.setSpacing(2)
    caption.addStretch()
    caption.addWidget(label)
    if stat is not None:
        caption.addWidget(stat)
    caption.addStretch()

    row_layout.addLayout(caption, 1)
    row_layout.addSpacing(OPTION_ROW_GAP)
    row_layout.addWidget(field)

    return row

LEFT_PANEL_PAGES = ("Recipes", "Details")
LEFT_PANEL_TAB_PADDING = 8
LEFT_PANEL_TAB_INDICATOR = 2      # the accent line under the page being shown
LEFT_PANEL_TAB_BG = "#262626"         # a shade darker than the panel behind them
LEFT_PANEL_TAB_HOVER_BG = "#303030"
LEFT_PANEL_TAB_CHECKED_BG = "#232323"
LEFT_PANEL_TAB_DIVIDER = "rgba(255, 255, 255, 0.14)"   # the faint line between two options
LEFT_PANEL_TAB_DIVIDER_HEIGHT = 18

# the panel on the canvas' left: the right one's twin in size and look. A row
# of options at its top - Recipes, Details - flips the page shown under it;
# both pages are empty for now. It takes focus on a click the same way as the
# right one, so a value being typed there still commits when this is clicked.
# `on_recipes_change` fires when a recipe is picked on the Recipes page, whose
# picks wait for the right panel's build button (see make_recipes_page)
def make_left_panel(on_recipes_change=None):
    panel = QWidget()
    panel.setObjectName("left_panel")
    panel.setAttribute(Qt.WA_StyledBackground, True)
    panel.setStyleSheet(f"background-color: {PANEL_BG};")
    panel.setFixedWidth(PANEL_WIDTH)
    panel.setFocusPolicy(Qt.ClickFocus)

    panel_layout = QVBoxLayout(panel)
    panel_layout.setContentsMargins(12, 12, 12, 12)
    panel_layout.setSpacing(12)

    # the options as one strip, no gap between them: a faint white line
    # parts them instead. Only the strip's outer corners are rounded.
    strip = QWidget()
    strip.setObjectName("left_tabs")
    strip.setAttribute(Qt.WA_StyledBackground, True)
    strip.setStyleSheet(
        "QWidget#left_tabs {"
        f"  background: {LEFT_PANEL_TAB_BG};"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "}"
    )
    tabs_row = QHBoxLayout(strip)
    tabs_row.setContentsMargins(0, 0, 0, 0)
    tabs_row.setSpacing(0)
    pages = QStackedWidget()
    tabs = []

    def select(index):
        for i, tab in enumerate(tabs):
            tab.setChecked(i == index)
        if pages.currentIndex() != index:
            pages.setCurrentIndex(index)
            fade_in(pages.currentWidget())

    for index, title in enumerate(LEFT_PANEL_PAGES):
        if index:
            divider = QWidget()
            divider.setAttribute(Qt.WA_StyledBackground, True)
            divider.setFixedSize(1, LEFT_PANEL_TAB_DIVIDER_HEIGHT)
            divider.setStyleSheet(f"background: {LEFT_PANEL_TAB_DIVIDER};")
            tabs_row.addWidget(divider, 0, Qt.AlignVCenter)

        # rounded only on the strip's outside
        first, last = index == 0, index == len(LEFT_PANEL_PAGES) - 1
        radius = HOVER_BORDER_RADIUS
        corners = (f"  border-top-left-radius: {radius if first else 0}px;"
                   f"  border-bottom-left-radius: {radius if first else 0}px;"
                   f"  border-top-right-radius: {radius if last else 0}px;"
                   f"  border-bottom-right-radius: {radius if last else 0}px;")

        tab = QPushButton(title)
        tab.setCheckable(True)
        tab.setCursor(Qt.PointingHandCursor)
        tab.setFocusPolicy(Qt.NoFocus)
        tab.setStyleSheet(
            "QPushButton {"
            f"  font-size: {PANEL_FONT_SIZE}px;"
            f"  padding: {LEFT_PANEL_TAB_PADDING}px;"
            "  border: none;"
            f"  border-bottom: {LEFT_PANEL_TAB_INDICATOR}px solid transparent;"
            + corners +
            f"  background: {LEFT_PANEL_TAB_BG};"
            f"  color: {TAB_UNSELECTED_COLOR};"
            "}"
            "QPushButton:hover {"
            f"  color: {TAB_SYMBOL_HOVER_COLOR};"
            f"  background: {LEFT_PANEL_TAB_HOVER_BG};"
            "}"
            "QPushButton:pressed {"
            f"  background: {TAB_SYMBOL_PRESS_BG};"
            "}"
            "QPushButton:checked {"
            f"  background: {LEFT_PANEL_TAB_CHECKED_BG};"
            f"  color: {TAB_SELECTED_COLOR};"
            f"  border-bottom: {LEFT_PANEL_TAB_INDICATOR}px solid {TAB_INDICATOR_COLOR};"
            "  border-bottom-left-radius: 0; border-bottom-right-radius: 0;"
            "  font-weight: bold;"
            "}"
        )
        tab.clicked.connect(lambda checked=False, i=index: select(i))
        tabs_row.addWidget(tab, 1)
        tabs.append(tab)

        page = make_details_page() if title == "Details" else make_recipes_page(on_recipes_change)
        page.setObjectName(f"left_page_{title.lower()}")
        pages.addWidget(page)

    # held at the width they have when the panel is open, so collapsing it
    # slides them out of sight rather than squeezing them: a shrinking button
    # re-centres and clips its own label, which reads as the text squirming
    margins = panel_layout.contentsMargins()
    content_width = PANEL_WIDTH - margins.left() - margins.right()
    strip.setFixedWidth(content_width)
    pages.setFixedWidth(content_width)

    panel_layout.addWidget(strip)
    panel_layout.addWidget(pages, 1)
    select(0)

    panel.tabs = tabs
    panel.pages = pages
    # a confirmed build refreshes both pages at once
    def show_report(nodes):
        for index in range(pages.count()):
            pages.widget(index).show_report(nodes)

    panel.show_report = show_report
    panel.recipes = pages.widget(LEFT_PANEL_PAGES.index("Recipes"))
    return panel

REPORT_ICON_SIZE = OPTION_ICON_SIZE   # the same pictures as the right panel's options
REPORT_ROW_SPACING = 4
REPORT_ACCENT_WIDTH = 4   # the node-colored bar at a recipe row's left edge, as thick as a node's border
REPORT_EMPTY_TEXT = "Confirm a build to see what its machines cost to put up."
RECIPES_EMPTY_TEXT = "Confirm a build to see every recipe it runs."

# one line of the report: a picture, a name, and a count set against the right -
# and, when `detail` is given, a small line of it under the name. `name` may be
# a widget, set in the name's place. `accent`, a color, is shown as a thin bar
# down the row's left edge - the border color of the node it stands for.
def make_report_row(picture_path, name, count_text, detail=None, accent=None):
    row = QWidget()
    row.setObjectName("report_row")
    row.setAttribute(Qt.WA_StyledBackground, True)
    row.setStyleSheet("QWidget#report_row { background: transparent; }")
    row_layout = QHBoxLayout(row)
    row_layout.setContentsMargins(0, 2, 4, 2)
    row_layout.setSpacing(OUTPUT_PICTURE_GAP)
    if accent is not None:
        bar = QWidget()
        bar.setObjectName("report_accent")
        bar.setAttribute(Qt.WA_StyledBackground, True)
        bar.setFixedWidth(REPORT_ACCENT_WIDTH)
        bar.setStyleSheet(f"QWidget#report_accent {{ background: {accent}; border-radius: {REPORT_ACCENT_WIDTH // 2}px; }}")
        row_layout.addWidget(bar)

    picture = picture_label(picture_path, REPORT_ICON_SIZE)

    if isinstance(name, QWidget):
        label = name
    else:
        label = QLabel(name)
        # the right panel's option label and option value, to the letter
        label.setStyleSheet(f"color: {TAB_UNSELECTED_COLOR}; font-size: {PANEL_FONT_SIZE}px; background: transparent;")
    name_column = QVBoxLayout()
    name_column.setContentsMargins(0, 0, 0, 0)
    name_column.setSpacing(1)
    name_column.addWidget(label)
    if detail:
        # small, like the stat under an option's label, but quiet
        detail_label = QLabel(detail)
        detail_label.setWordWrap(True)
        detail_label.setStyleSheet(f"color: {TEXT_FAINT}; font-size: {OPTION_STAT_FONT_SIZE}px; background: transparent;")
        name_column.addWidget(detail_label)
    count = QLabel(count_text)
    count.setStyleSheet(f"color: {TAB_SELECTED_COLOR}; font-size: {PANEL_FONT_SIZE}px; background: transparent;")
    count.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    row_layout.addWidget(picture, 0, Qt.AlignVCenter)
    row_layout.addLayout(name_column, 1)
    row_layout.addWidget(count)
    return row

# the recipes a node can be switched to: every recipe of every item it
# supplies, the one it runs first among them, each listed once
def recipe_options(items, running=None):
    options = [running] if running is not None else []
    for item in items:
        for recipe in item.recipes:
            if recipe not in options:
                options.append(recipe)
    return options

def format_count(amount):
    return f"{amount:,.0f}" if float(amount).is_integer() else f"{amount:,.2f}"

# the Recipes page: every recipe the last confirmed build runs, read the way
# the tree reads - from the outputs down to what is extracted. Each shows the
# picture of the item it is run for, a dropdown of that item's recipes set on
# the one it runs, how many machines run it, and under that what goes in and
# what comes out. page.show_report(nodes) fills it from a finished build's
# nodes; before any build it says what it is waiting for.
#
# Picking a recipe changes nothing by itself: the picks wait for the build
# button in the right panel, which says "Change" while any is waiting.
# page.changes() hands them over - {Item: Recipe} for every node making that
# item, {output index: Recipe} for the outputs themselves, and
# {old Recipe: new Recipe} for the rows switched - and page.waiting() says
# whether a row was touched at all. `on_change` fires whenever one is.
def make_recipes_page(on_change=None):
    page = QWidget()
    page_layout = QVBoxLayout(page)
    page_layout.setContentsMargins(0, 0, 0, 0)
    page_layout.setSpacing(0)

    empty = QLabel(RECIPES_EMPTY_TEXT)
    empty.setWordWrap(True)
    empty.setStyleSheet(f"color: {TEXT_FAINT}; font-size: {PANEL_FONT_SIZE}px;")
    page_layout.addWidget(empty)

    section, body = make_panel_section("Recipes")
    page_layout.addWidget(section, 1)

    # one per row: {"item", "items", "recipe", "fed", "inside", "get_recipe", "field"}
    rows = []

    def flow(entries):
        return ", ".join(f"{format_count(entry['amount'])}{amount_unit(entry['item'])} {entry['item'].display_name}"
                         for entry in entries)

    # an item made for several outputs runs a different recipe for each: every
    # such row greys out what the other outputs of its item run
    def refresh_used():
        for row in rows:
            if row["fed"]:
                row["field"].set_used([other["get_recipe"]() for other in rows
                                       if other is not row and other["fed"] and other["item"] is row["item"]])

    def picked():
        refresh_used()
        if on_change is not None:
            on_change()

    def waiting():
        return any(row["get_recipe"]() is not row["recipe"] for row in rows)

    def changes():
        item_choices, output_choices, replaced = {}, {}, {}
        for row in rows:
            recipe = row["get_recipe"]()
            if recipe is row["recipe"]:
                # left as it was: it says nothing, and must not undo a pick
                # made for one of its items on an earlier confirm
                continue
            replaced[row["recipe"]] = recipe
            # an output is its item, and its card the recipe this row was
            # running: that is the card the pick belongs to
            for item in row["fed"]:
                output_choices[(item, row["recipe"])] = recipe
            if row["inside"] or not row["fed"]:
                # the pick stands for every item of the row's that the recipe
                # makes; anything else it supplied is left to that item's own
                made = [entry["item"] for entry in recipe.products]
                for item in row["items"]:
                    if item in made:
                        item_choices[item] = recipe
        return item_choices, output_choices, replaced

    def show_report(nodes):
        entries = recipes_report(nodes)
        rows.clear()
        while body.count():
            item = body.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        empty.setVisible(not entries)
        section.setVisible(bool(entries))
        if not entries:
            return

        line = QLabel(f"{len(entries)} recipes, "
                      f"{sum(1 for entry in entries if entry[0].is_alternate)} alternate")
        line.setStyleSheet(f"color: {TEXT_ACCENT}; font-size: {OPTION_STAT_FONT_SIZE}px;")
        body.addWidget(line)
        for recipe, machine, machine_nb, _, item, fed, inside, node, items in entries:
            detail = (f"{machine.display_name}:  {flow(recipe.ingredients)}  \u2192  {flow(recipe.products)}"
                      if recipe.ingredients else f"{machine.display_name}:  \u2192  {flow(recipe.products)}")
            field, get_recipe = make_recipe_dropdown(item, recipe, on_change=picked,
                                                     options=recipe_options(items, recipe))
            rows.append({"item": item, "items": items, "recipe": recipe, "fed": fed, "inside": inside,
                         "get_recipe": get_recipe, "field": field})
            body.addWidget(make_report_row(item_picture(item), field, f"\u00d7 {machine_count(machine_nb)}", detail,
                                           accent=node_border_color(node)))
        refresh_used()
        body.setSpacing(REPORT_ROW_SPACING + 2)
        fade_in(page)

    # every row back to the recipe it was showing when the tree was built,
    # for the panel's Cancel
    def discard():
        for row in rows:
            combo = row["field"].combo
            for index in range(combo.count()):
                if combo.itemData(index) is row["recipe"]:
                    combo.setCurrentIndex(index)
                    break
        refresh_used()

    show_report([])
    page.show_report = show_report
    page.waiting = waiting
    page.changes = changes
    page.discard = discard
    return page

# the Details page: what the last confirmed build takes to put up. The machines
# first - how many buildings of each - then, added up over all of them, every
# part those buildings cost. page.show_report(nodes) fills it from a finished
# build's nodes; before any build it says what it is waiting for.
def make_details_page():
    page = QWidget()
    page_layout = QVBoxLayout(page)
    page_layout.setContentsMargins(0, 0, 0, 0)
    page_layout.setSpacing(0)

    empty = QLabel(REPORT_EMPTY_TEXT)
    empty.setWordWrap(True)
    empty.setStyleSheet(f"color: {TEXT_FAINT}; font-size: {PANEL_FONT_SIZE}px;")
    page_layout.addWidget(empty)

    # parted the way the right panel parts its sections: a gap, the divider
    # bar, a gap
    machines_section, machines_body = make_panel_section("Machines")
    materials_section, materials_body = make_panel_section("Build materials")
    divider = QWidget()
    divider_layout = QVBoxLayout(divider)
    divider_layout.setContentsMargins(0, PANEL_SECTION_GAP, 0, PANEL_SECTION_GAP)
    divider_layout.addWidget(make_panel_divider())
    page_layout.addWidget(machines_section, 2)
    page_layout.addWidget(divider)
    page_layout.addWidget(materials_section, 3)

    def clear(layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()

    def summary(text):
        line = QLabel(text)
        line.setStyleSheet(f"color: {TEXT_ACCENT}; font-size: {OPTION_STAT_FONT_SIZE}px;")
        return line

    def show_report(nodes):
        machines, materials = construction_report(nodes)
        clear(machines_body)
        clear(materials_body)
        empty.setVisible(not machines)
        machines_section.setVisible(bool(machines))
        divider.setVisible(bool(machines))
        materials_section.setVisible(bool(machines))
        if not machines:
            return

        buildings = sum(machines.values())
        machines_body.addWidget(summary(f"{format_count(buildings)} buildings, {len(machines)} kinds"))
        for machine, count in machines.items():
            machines_body.addWidget(make_report_row(machine.picture, machine.display_name, f"× {format_count(count)}"))

        materials_body.addWidget(summary(f"{len(materials)} different parts"))
        for item, amount in materials.items():
            materials_body.addWidget(make_report_row(item_picture(item), item.display_name, format_count(amount)))

        for body in (machines_body, materials_body):
            body.setSpacing(REPORT_ROW_SPACING)
        fade_in(page)

    show_report([])
    page.show_report = show_report
    return page

PANEL_COLLAPSE_WIDTH = 18         # the little tab sticking out of a panel's inner edge
PANEL_COLLAPSE_HEIGHT = 44
PANEL_COLLAPSE_TOP = 12           # how far down the canvas' edge it sits
PANEL_COLLAPSE_MS = 200
DEFAULT_LEFT_PANEL_OPEN = False   # the left panel starts collapsed, its tab showing

# a small arrow tab sticking out of a panel's inner edge, near the top, over
# the canvas. A click slides the panel shut - its width down to nothing, the
# canvas growing into the room - and the tab stays at the canvas' edge with its
# arrow turned round, to slide it open again. `side` is where the panel is,
# "left" or "right"; `canvas` is the widget between the panels, whose edge the
# tab rides. It is the container's child, never in a layout, so it floats over
# the canvas and follows that edge whenever the canvas moves or resizes.
# `open` is how the panel starts out.
def add_panel_collapse(container, panel, canvas, side, open=True):
    button = QPushButton(container)
    button.setObjectName(f"collapse_{side}")
    button.setFixedSize(PANEL_COLLAPSE_WIDTH, PANEL_COLLAPSE_HEIGHT)
    button.setCursor(Qt.PointingHandCursor)
    button.setFocusPolicy(Qt.NoFocus)
    button.setIconSize(QSize(STEP_BAR_ICON_SIZE, STEP_BAR_ICON_SIZE))
    # rounded on the side that sticks out, square where it meets the panel
    outer = "right" if side == "left" else "left"
    button.setStyleSheet(
        "QPushButton {"
        f"  background: {PANEL_BG};"
        "  border: none;"
        f"  border-top-{outer}-radius: {HOVER_BORDER_RADIUS + 2}px;"
        f"  border-bottom-{outer}-radius: {HOVER_BORDER_RADIUS + 2}px;"
        "  padding: 0;"
        "}"
        "QPushButton:hover {"
        f"  background: {FULLSCREEN_BUTTON_HOVER_BG};"
        "}"
        "QPushButton:pressed {"
        f"  background: {TAB_SYMBOL_PRESS_BG};"
        "}"
    )

    state = {"open": open, "animation": None, "hovered": False}
    if not open:
        panel.setFixedWidth(0)
    icons = {symbol: (step_bar_icon(symbol, TAB_UNSELECTED_COLOR), step_bar_icon(symbol, TAB_SELECTED_COLOR))
             for symbol in ("previous", "next")}

    # the arrow points the way the panel will move: back into its side to
    # collapse it, out of it to open it
    def refresh():
        closing_way = "previous" if side == "left" else "next"
        opening_way = "next" if side == "left" else "previous"
        symbol = closing_way if state["open"] else opening_way
        button.setIcon(icons[symbol][1 if state["hovered"] else 0])
        button.setToolTip("Collapse the panel" if state["open"] else "Expand the panel")

    def reposition():
        corner = canvas.mapTo(container, QPoint(0, 0))
        x = corner.x() if side == "left" else corner.x() + canvas.width() - button.width()
        button.move(x, corner.y() + PANEL_COLLAPSE_TOP)
        button.raise_()

    def toggle():
        state["open"] = not state["open"]
        if state["animation"] is not None:
            state["animation"].stop()   # reversed half way: go back from where it got to
        state["animation"] = animate_value(button, panel.width(), PANEL_WIDTH if state["open"] else 0,
                                           lambda width: panel.setFixedWidth(round(width)),
                                           PANEL_COLLAPSE_MS)
        state["animation"].finished.connect(lambda: state.update(animation=None))
        refresh()

    button.clicked.connect(toggle)

    class Watcher(QObject):
        def eventFilter(self, watched, event):
            if watched is button and event.type() in (QEvent.Enter, QEvent.Leave):
                state["hovered"] = event.type() == QEvent.Enter
                refresh()
            elif watched is not button and event.type() in (QEvent.Resize, QEvent.Move, QEvent.Show):
                reposition()
            return False

    button.watcher = Watcher(button)   # kept alive by the button
    button.installEventFilter(button.watcher)
    canvas.installEventFilter(button.watcher)
    container.installEventFilter(button.watcher)
    button.is_open = lambda: state["open"]
    refresh()
    reposition()
    return button

# the outlined accent button at the bottom of a panel that builds the tree
def make_confirm_button(label=CONFIRM_LABEL, name="confirm"):
    button = QPushButton(label)
    button.setObjectName(name)
    button.setCursor(Qt.PointingHandCursor)
    button.setStyleSheet(
        "QPushButton {"
        "  background-color: transparent;"
        f"  color: {CONFIRM_BG};"
        "  font-weight: bold;"
        f"  border: {CONFIRM_BORDER_WIDTH}px solid {CONFIRM_BG};"
        f"  font-size: {PANEL_FONT_SIZE}px;"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "  padding: 12px;"
        "}"
        "QPushButton:hover {"
        f"  background-color: {CONFIRM_HOVER_BG};"
        f"  color: {TEXT_ON_ACCENT};"
        "}"
        "QPushButton:pressed {"
        f"  background-color: {ACCENT_PRESS_BG};"
        f"  border-color: {ACCENT_PRESS_BG};"
        f"  color: {TEXT_ON_ACCENT};"
        "}"
    )
    return button

def make_side_panel(on_confirm):
    panel = QWidget()
    panel.setAttribute(Qt.WA_StyledBackground, True)
    panel.setStyleSheet(f"background-color: {PANEL_BG};")
    panel.setFixedWidth(PANEL_WIDTH)
    # a plain QWidget refuses focus, so a click on the panel background would
    # leave the caret in a value field and never commit it. Let the panel take
    # the click, which pulls focus out of the field and fires editingFinished.
    panel.setFocusPolicy(Qt.ClickFocus)

    panel_layout = QVBoxLayout(panel)
    panel_layout.setContentsMargins(12, 12, 12, 12)
    panel_layout.setSpacing(12)

    add_button = QPushButton(ADD_OUTPUT_LABEL)
    add_button.setCursor(Qt.PointingHandCursor)
    add_button.setStyleSheet(
        "QPushButton {"
        f"  background-color: {TAB_INDICATOR_COLOR};"
        f"  color: {TEXT_ON_ACCENT};"
        "  font-weight: bold;"
        "  border: none;"
        f"  font-size: {PANEL_FONT_SIZE}px;"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "  padding: 12px;"
        "}"
        "QPushButton::menu-indicator {"
        "  image: none;"
        "  width: 0px;"
        "}"
        "QPushButton:hover {"
        f"  background-color: {ADD_OUTPUT_HOVER_BG};"
        "}"
        "QPushButton:pressed {"
        f"  background-color: {ACCENT_PRESS_BG};"
        "}"
    )

    # The section holds two lists, one per tab: the things to make, and the
    # generators to power them with. A generator is an output like any other -
    # power, made by one generator's recipe - so both lists are output cards
    # and the build reads them together.
    pages = {}
    for side in ("output", "generator"):
        page = QWidget()
        page.setStyleSheet("background: transparent;")
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(10)
        pages[side] = page
    outputs_layout = pages["output"].layout()
    generators_layout = pages["generator"].layout()
    pages["generator"].hide()
    current = ["output"]

    # each entry is {"item", "get_rate", "get_recipe", "row", "side"}; this is the live
    # source of truth confirm() reads from, not just what the layout happens to show
    added_outputs = []

    # an item can be an output several times, each with a recipe of its own:
    # never the same item made the same way twice
    def used_recipes(item):
        return [entry["get_recipe"]() for entry in added_outputs if entry["item"] is item]

    # every card of the item greys out, in its dropdown, what the others run
    def refresh_used(item):
        for entry in added_outputs:
            if entry["item"] is item:
                others = [other["get_recipe"]() for other in added_outputs
                          if other["item"] is item and other is not entry]
                entry["row"].set_used(others)

    def remove_output(entry):
        def drop():
            entry["row"].parentWidget().layout().removeWidget(entry["row"])
            entry["row"].deleteLater()
        added_outputs.remove(entry)
        refresh_used(entry["item"])
        refresh_confirm()
        # rolls up out of the list, the cards under it easing up into its place
        roll_up(entry["row"], drop)

    # one card, on whichever list it belongs to
    def add_card(item, recipe, side, start=None):
        row, remove_button, get_rate, get_recipe = make_output_row(
            item, recipe, start=start, on_rate_change=refresh_confirm,
            # a recipe picked on a card is a change to build again, and one to
            # be able to cancel, as much as a card added or a rate typed
            on_recipe_change=lambda: (refresh_used(item), refresh_confirm()))
        entry = {"item": item, "get_rate": get_rate, "get_recipe": get_recipe, "row": row, "side": side}
        added_outputs.append(entry)
        remove_button.clicked.connect(lambda: remove_output(entry))
        (outputs_layout if side == "output" else generators_layout).addWidget(row)
        paint_accent(row)   # made after a switch: it takes the accent as it stands
        row.setEnabled(not panel_options["locked"])
        refresh_used(item)
        refresh_confirm()
        unroll(row)   # the card unrolls into the list rather than popping in

    def add_output(item):
        # a second of the same item starts on the first recipe not taken yet -
        # the one picked for the item on the Recipes page, if that is free
        used = used_recipes(item)
        free = [recipe for recipe in item.recipes if recipe not in used]
        if not free:
            return   # every recipe runs already; the list greys such an item out
        picked = panel_options["recipe_choices"].get(item)
        add_card(item, picked if picked in free else free[0], "output")

    # a generator is picked by its recipe - burn coal, burn fuel - and lands as
    # a card asking for so many megawatts made that way
    def add_generator(recipe):
        if recipe in used_recipes(POWER_ITEM):
            return
        one = recipe.products[0]["amount"] / recipe.duration * 60   # what one of them makes
        add_card(POWER_ITEM, recipe, "generator", start=round(one))

    # an item is greyed out in the list only once every one of its recipes
    # is some output's already. Power is not in the list: its recipes are the
    # generators, and they have a tab of their own.
    search_popup, search_field = make_search_popup(
        panel, [item for item in OUTPUT_ITEMS if item is not POWER_ITEM], add_output,
        is_taken=lambda item: len(set(used_recipes(item))) >= len(item.recipes))
    generator_popup, generator_field = make_search_popup(
        panel, GENERATOR_RECIPES, add_generator,
        is_taken=lambda recipe: recipe in used_recipes(POWER_ITEM),
        picture=lambda recipe: picture_or_missing(recipe.machine[0].picture))

    def toggle_search():
        search_popup, search_field = (popups[current[0]])
        if search_popup.isVisible():
            search_popup.hide()
            return
        # the press on this very button is what just closed it - leave it shut
        if time.monotonic() - search_popup.closed_at < SEARCH_REOPEN_GUARD:
            return
        search_popup.setFixedWidth(add_button.width())
        # a Qt.Popup is its own window, so it is placed in screen coordinates
        top_left = add_button.mapToGlobal(QPoint(0, add_button.height() + SEARCH_GAP))

        # the popup is a window of its own, so it is free to hang past the panel
        # and take the whole height of the app - but not past the app's own
        # bottom edge, where it would read as a stray floating window. The
        # screen is checked too, for an app window dragged partly off it.
        chrome = (search_popup.layout().contentsMargins().top()
                  + search_popup.layout().contentsMargins().bottom()
                  + search_popup.layout().spacing()
                  + search_field.sizeHint().height())
        window = add_button.window()
        bottom = min(window.mapToGlobal(QPoint(0, window.height())).y(),
                     add_button.screen().availableGeometry().bottom())
        room = bottom - top_left.y() - SEARCH_POPUP_BOTTOM_MARGIN - chrome

        # a fixed height, not just a ceiling: a QListWidget asks for a small
        # default size no matter how many rows it holds, so raising its maximum
        # alone left adjustSize shrinking the popup back to about three rows
        choices = search_popup.choices
        rows = choices.count()
        content = choices.sizeHintForRow(0) * rows + 2 * choices.frameWidth()
        choices.setFixedHeight(max(SEARCH_POPUP_MIN_HEIGHT,
                                   min(SEARCH_POPUP_MAX_HEIGHT, room, content)))
        search_popup.adjustSize()
        search_popup.move(top_left)
        search_field.clear()
        search_popup.choices.clearSelection()   # opens clean, no row still marked
        search_popup.refresh_taken()   # the outputs may have changed since it last showed
        # a top level window fades through its own opacity, not a graphics effect
        search_popup.setWindowOpacity(0.0)
        search_popup.show()
        opacity = QPropertyAnimation(search_popup, b"windowOpacity", search_popup)
        opacity.setDuration(ANIMATION_MS)
        opacity.setStartValue(0.0)
        opacity.setEndValue(1.0)
        run(opacity)
        search_field.setFocus()

    popups = {"output": (search_popup, search_field),
              "generator": (generator_popup, generator_field)}
    add_button.clicked.connect(toggle_search)

    confirm_button = make_confirm_button(BUILD_LABELS["generate"], "build_confirm")
    # above it, and quieter than it: the way back to the panel as the last
    # build read it, greyed out while there is nothing to put back
    cancel_button = QPushButton(CANCEL_CHANGES_LABEL)
    cancel_button.setObjectName("build_cancel")
    cancel_button.setCursor(Qt.PointingHandCursor)
    cancel_button.setFocusPolicy(Qt.NoFocus)
    cancel_button.setIconSize(QSize(CONFIRM_ICON_SIZE, CONFIRM_ICON_SIZE))
    cancel_button.setStyleSheet(
        "QPushButton {"
        "  background-color: transparent;"
        f"  color: {TEXT_MUTED};"
        f"  border: 1px solid {OUTPUT_FIELD_BORDER};"
        f"  font-size: {OUTPUT_RECIPE_FONT_SIZE}px;"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "  padding: 7px;"
        "}"
        f"QPushButton:hover {{ color: {TEXT_STRONG}; border-color: {TAB_SYMBOL_COLOR}; }}"
        f"QPushButton:pressed {{ background-color: {TAB_SYMBOL_PRESS_BG}; }}"
        f"QPushButton:disabled {{ color: {TEXT_FAINT}; border-color: {PANEL_DIVIDER_COLOR}; }}"
    )

    # every output card at once, for starting a list over
    clear_button = QPushButton(CLEAR_OUTPUTS_LABEL)
    clear_button.setObjectName("clear_outputs")
    clear_button.setCursor(Qt.PointingHandCursor)
    clear_button.setToolTip("Remove every output")
    clear_button.setStyleSheet(
        "QPushButton {"
        "  background-color: transparent;"
        f"  color: {TEXT_MUTED};"
        f"  border: 1px solid {OUTPUT_FIELD_BORDER};"
        f"  font-size: {OUTPUT_RECIPE_FONT_SIZE}px;"
        f"  border-radius: {HOVER_BORDER_RADIUS}px;"
        "  padding: 6px 10px;"
        "}"
        "QPushButton:hover {"
        f"  color: {TAB_SELECTED_COLOR};"
        f"  background-color: {TAB_SYMBOL_HOVER_BG};"
        f"  border: 1px solid {TAB_SYMBOL_COLOR};"
        "}"
        "QPushButton:pressed {"
        f"  background-color: {TAB_SYMBOL_PRESS_BG};"
        "}"
        "QPushButton:disabled {"
        f"  color: {TEXT_DISABLED};"
        f"  border: 1px solid {OUTPUT_FIELD_BORDER};"
        "}"
    )

    def clear_outputs():
        for entry in list(added_outputs):
            if entry["side"] == current[0]:
                remove_output(entry)

    clear_button.clicked.connect(clear_outputs)

    # the two tabs. Switching them turns the app's accent with them - blue for
    # what to make, the power yellow for what powers it - so it is plain which
    # half of the plan is in front of you.
    def show_side(side):
        current[0] = side
        for name, page in pages.items():
            page.setVisible(name == side)
        add_button.setText(ADD_OUTPUT_LABEL if side == "output" else ADD_GENERATOR_LABEL)
        clear_button.setToolTip("Remove every output" if side == "output" else "Remove every generator")
        for popup, _ in popups.values():
            popup.hide()
        set_accent("blue" if side == "output" else "yellow", panel.window())
        refresh_confirm()
        fade_in(pages[side])

    tab_strip, side_tabs = make_tab_strip(PANEL_TAB_LABELS, lambda index: show_side(PANEL_TAB_SIDES[index]),
                                          accents=PANEL_TAB_ACCENTS)

    # top half : everything about the outputs
    output_section, output_body = make_panel_section(PANEL_SECTIONS[0])
    output_section.pinned.addWidget(tab_strip)   # the two lists, above the button that fills them
    output_section.pinned.addWidget(add_button)  # stays at the top while the outputs scroll
    output_section.pinned.addWidget(clear_button)
    output_body.addWidget(pages["output"])
    output_body.addWidget(pages["generator"])

    # bottom half : miner mark and conveyor level, feeding straight into panel_options
    option_section, option_body = make_panel_section(PANEL_SECTIONS[1])

    def set_miners_mark(value):
        panel_options["miners_mark"] = value
        schedule_save()

    def set_conveyor_lvl(value):
        panel_options["conveyor_lvl"] = value
        schedule_save()

    def set_pipe_lvl(value):
        panel_options["pipe_lvl"] = value
        schedule_save()

    option_body.addWidget(make_option_row(
        "Miner Mark", MINER_MARK_OPTIONS, MINER_MARK_PICTURES,
        panel_options["miners_mark"], set_miners_mark, miner_stat
    ))
    option_body.addWidget(make_option_row(
        "Conveyor Level", CONVEYOR_LVL_OPTIONS, CONVEYOR_LVL_PICTURES,
        panel_options["conveyor_lvl"], set_conveyor_lvl, conveyor_stat
    ))
    option_body.addWidget(make_option_row(
        "Pipe Level", PIPE_LVL_OPTIONS, PIPE_LVL_PICTURES,
        panel_options["pipe_lvl"], set_pipe_lvl, pipe_stat
    ))

    panel_layout.addWidget(output_section, PANEL_OUTPUT_SHARE)
    panel_layout.addSpacing(PANEL_SECTION_GAP)
    panel_layout.addWidget(make_panel_divider())
    panel_layout.addSpacing(PANEL_SECTION_GAP)
    panel_layout.addWidget(option_section, PANEL_OPTION_SHARE)
    panel_layout.addWidget(cancel_button)
    panel_layout.addSpacing(PANEL_BUTTON_GAP)
    panel_layout.addWidget(confirm_button)
    clear_button.setEnabled(bool(added_outputs))

    # the cards as the last confirm read them, in the order of its outputs
    confirmed = []
    # and what those cards said, so Cancel can put them back exactly: the same
    # items on the same lists, at the rates and recipes the build was made
    # from. Read as plain names and numbers rather than as the card widgets,
    # which are thrown away and made again by the undo itself.
    baseline = []

    def card_config(entry):
        recipe = entry["get_recipe"]()
        return {"item": entry["item"].full_name, "rate": entry["get_rate"](),
                "recipe": recipe.full_name if recipe else None, "side": entry["side"]}

    def current_config():
        return [card_config(entry) for entry in added_outputs]

    # anything the build would read differently than it did last time - a card
    # added or taken off, a rate typed, a recipe picked here or on the Recipes
    # page. Nothing to cancel while this is false, and the button says so.
    def config_changed():
        return bool(confirmed) and (current_config() != baseline or panel.recipes_waiting())

    def cancel_changes():
        if not config_changed():
            return
        for entry in list(added_outputs):
            entry["row"].setParent(None)   # taken off outright: several at once
            entry["row"].deleteLater()
        added_outputs.clear()
        restore_cards(baseline)
        panel.discard_recipes()
        refresh_confirm()

    # Nothing built yet, outputs added since the last build, recipes picked on
    # the Recipes page, or the same outputs to build again - the button says
    # which, and the build reads it back to know what it is doing.
    #
    # A card taken away since the last build makes it a fresh Generate rather
    # than an Add, however many were put in its place: what comes out is not
    # the last factory with more on top of it, it is another factory. Removing
    # the only output and asking for something else is the plain case - that
    # cannot read "Add" - and removing one of several is the same in kind.
    # With every card gone and a factory still on the map, the button has
    # nothing to build: it says Clear, and pressing it takes the map away.
    def build_state():
        if not confirmed:
            return "generate"
        if not added_outputs:
            return "clear"   # every output taken off: what it builds is nothing
        # read off what the cards say rather than which card widgets they are:
        # Cancel throws the rows away and makes them again, and those are the
        # same outputs however new the widgets holding them
        now = current_config()
        if now == baseline:
            return "change" if panel.recipes_waiting() else "regenerate"
        if all(card in now for card in baseline):
            return "add"     # everything the build had, and more on top of it
        return "generate"

    def refresh_confirm():
        state = build_state()
        label = BUILD_LABELS[state]
        if confirm_button.text() != label:
            confirm_button.setText(label)
            pulse(confirm_button)   # it changed under the mouse: a flash says so
        # in the accent as it stands: the button's own colors are swapped with
        # it by the stylesheet, and a drawn glyph has to be made again
        confirm_button.setIcon(symbol_icon(BUILD_SYMBOLS[state], accent_shade()))
        confirm_button.setIconSize(QSize(CONFIRM_ICON_SIZE, CONFIRM_ICON_SIZE))
        # nothing changed since the build, nothing to cancel
        undoable = config_changed() and not panel_options["locked"]
        cancel_button.setEnabled(undoable)
        cancel_button.setIcon(symbol_icon(draw_build_cancel, TEXT_MUTED if undoable else TEXT_FAINT))
        cancel_button.setToolTip(CANCEL_CHANGES_TOOLTIP if undoable else "")
        here = [entry for entry in added_outputs if entry["side"] == current[0]]
        clear_button.setEnabled(bool(here))
        tab_strip.set_counts([sum(1 for entry in added_outputs if entry["side"] == side)
                              for side in PANEL_TAB_SIDES])

    # a locked graph cannot be built again, so the button that would do it is
    # greyed out along with the lists that feed it - what is on the map stays
    # exactly as it is until the lock comes off
    def set_locked(locked):
        confirm_button.setEnabled(not locked)
        cancel_button.setEnabled(not locked and config_changed())
        confirm_button.setToolTip(LOCKED_TOOLTIP if locked else "")
        add_button.setEnabled(not locked)
        clear_button.setEnabled(not locked and bool(
            [entry for entry in added_outputs if entry["side"] == current[0]]))
        for entry in added_outputs:
            entry["row"].setEnabled(not locked)

    refresh_confirm()   # the button starts with its own word and glyph on it
    set_locked(panel_options["locked"])
    panel.set_locked = set_locked
    panel.refresh_confirm = refresh_confirm
    panel.cards = lambda: list(added_outputs)   # what is asked for, for the save file

    # the cards of a saved project, put back on the lists they were on. Their
    # own recipes are restored with them, rather than the default the picker
    # would hand out, so a project comes back running what it was running.
    def restore_cards(saved):
        for card in saved:
            item = All_Items.get(card.get("item"))
            recipe = All_Recipes.get(card.get("recipe"))
            if item is None:
                continue
            add_card(item, recipe if recipe in item.recipes else None,
                     card.get("side", "output"), start=card.get("rate"))

    panel.restore_cards = restore_cards
    panel.recipes_waiting = lambda: False   # the canvas hands the real one over
    panel.before_build = lambda: None       # and what to take in before a build
    panel.discard_recipes = lambda: None    # ...and how to put its picks back

    def confirm():
        # panel_options["output"] is what generate_node_graph actually reads;
        # without this it would keep confirming whatever it started with
        state = build_state()
        # recipes picked on the Recipes page first: one of them may switch an
        # output's card, and the cards are read just below
        panel.before_build()
        confirmed[:] = added_outputs
        baseline[:] = current_config()   # what Cancel puts the panel back to
        panel_options["output"] = [
            {"item": entry["item"], "rate": entry["get_rate"](), "recipe": entry["get_recipe"]()}
            for entry in added_outputs
        ]
        on_confirm(state)
        refresh_confirm()

    cancel_button.clicked.connect(cancel_changes)
    confirm_button.clicked.connect(confirm)

    # switching the recipe an output was made with: the card of that item
    # running `was` follows, so map and panel never disagree. A card removed
    # since the last build is left alone.
    def set_output_recipe(item, was, recipe):
        entry = next((e for e in confirmed if e in added_outputs
                      and e["item"] is item and e["get_recipe"]() is was), None)
        if entry is not None and recipe in item.recipes:
            entry["row"].combo.setCurrentIndex(item.recipes.index(recipe))

    panel.set_output_recipe = set_output_recipe
    return panel, confirm

# ===================================================== CANVAS ======================================================
def make_canvas():
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    graphics_view = make_graphics_view()
    # the view's home in the canvas: full screen lifts it out of here and
    # puts it back
    content_stack = QStackedWidget()
    content_stack.addWidget(graphics_view)

    fullscreen = FullscreenToggle(graphics_view, content_stack)

    step_bar = [None]   # built further down, once redraw_graph exists to feed it
    side = [None, None]   # the right panel and its confirm, made further down

    # the recipes picked on the Recipes page, taken in just before a build:
    # kept for every later build, and the outputs' cards switched to theirs. A
    # recipe switched there for every node that ran it also replaces it where
    # one node had picked it for itself.
    def take_recipe_picks():
        if not left_panel.recipes.waiting():
            return
        item_choices, output_choices, replaced = left_panel.recipes.changes()
        panel_options["recipe_choices"].update(item_choices)
        picks = panel_options["node_recipe_choices"]
        for key, recipe in picks.items():
            picks[key] = replaced.get(recipe, recipe)
        for (item, was), recipe in output_choices.items():
            side[0].set_output_recipe(item, was, recipe)

    # a recipe picked in one node's info panel: kept for that node alone - the
    # item made for the machines it feeds - or, on an output's own node, set on
    # that output's card. Then only that node's subtree is taken out and grown
    # again, the rest of the tree left where and as it is.
    def pick_node_recipe(node, recipe):
        while node.merged_into is not None:
            node = node.merged_into
        built = graphics_view.build_steps[-1]["nodes"]
        outputs = [n for n in built if isinstance(n, Output_Node) and not n.is_byproduct]
        made = [entry["item"] for entry in recipe.products]
        for mother in node.mother_nodes:
            # only what the new recipe makes follows it here; anything else the
            # node supplied is made again by its own item's recipe
            taken = next((entry["item"] for entry in node.products if mother in entry["to"]), node.needed_item)
            if taken not in made:
                continue
            if mother in outputs:
                side[0].set_output_recipe(taken, node.recipe, recipe)
                for output in panel_options["output"]:
                    if output["item"] is taken and output.get("recipe") is node.recipe:
                        output["recipe"] = recipe
                        break
            elif isinstance(mother, Recipe_Node):
                panel_options["node_recipe_choices"][(taken, mother.recipe)] = recipe
        # rebuilt once the dropdown's own list has closed
        QTimer.singleShot(0, lambda: rebuild_node(node, recipe))

    def rebuild_node(node, recipe):
        built = graphics_view.build_steps[-1]["nodes"]
        if node not in built:
            return
        kept = {n: n.coordinate for n in built}
        anchor = node.coordinate
        set_miner_mark(panel_options["miners_mark"])
        steps, _ = Node.rebuild_subtree(built, node, recipe, panel_options["recipe_choices"],
                                        panel_options["node_recipe_choices"])
        layout_nodes(steps, kept, anchor)
        reveal = panel_options["build_reveal"]
        graphics_view.build_steps = steps
        graphics_view.build_step = len(steps) - 1 if reveal == "skip" else 0
        # the camera stays put: the tree around the change has not moved
        transition_scene(graphics_view, render_build_step(graphics_view))
        left_panel.show_report(steps[-1]["nodes"])
        if step_bar[0] is not None:
            step_bar[0].refresh()
            if reveal == "play":
                step_bar[0].play_from_start()

    graphics_view.on_node_recipe = pick_node_recipe

    # its pages report on every confirmed build; a recipe picked there waits
    # for the build button, which says "Change" meanwhile
    left_panel = make_left_panel(lambda: side[0] and side[0].refresh_confirm())

    # builds the tree and shows it the way the Build toggle says: parked on its
    # first step, played through from there, or skipped straight to the end.
    # The steps stay walkable with the arrows whichever it was.
    def confirm(state="generate"):
        reveal = panel_options["build_reveal"]
        # Every build off this button lays the whole tree out afresh, whatever
        # brought it here. Adding an output used to keep the last build's spots
        # and place only what was new, but a tree grown that way is not the one
        # the layout would have drawn: the new branch takes whatever room is
        # left instead of its own, and the graph ends up with several times the
        # crossings of the same outputs generated from scratch - so the same
        # outputs read differently depending on whether they were added one at
        # a time or built in one go. Picking a recipe on a node still moves
        # nothing but its own subtree (see rebuild_node): that is a change to
        # one part of a tree, not a new tree.
        scene = generate_node_graph(graphics_view, panel_options["output"],
                                    step=-1 if reveal == "skip" else 0)
        transition_scene(graphics_view, scene)
        fit_view_to_rect(graphics_view, build_steps_bounds(graphics_view.build_steps), animate=True)
        left_panel.show_report(graphics_view.build_steps[-1]["nodes"])   # what the finished factory costs
        if step_bar[0] is not None:
            step_bar[0].refresh()
            if reveal == "play":
                step_bar[0].play_from_start()
        schedule_save()

    # panel's own confirm syncs panel_options["output"] from the output rows
    # before calling confirm()
    panel, side_confirm = make_side_panel(confirm)
    side[:] = [panel, side_confirm]
    panel.recipes_waiting = left_panel.recipes.waiting   # what the button reads to say "Change"
    panel.discard_recipes = left_panel.recipes.discard   # ...and what Cancel puts back
    panel.before_build = take_recipe_picks               # and takes in as it builds

    # an arrow-mode switch only needs the existing graph redrawn in the new
    # style - reusing the same Node objects (and so every dragged position)
    # rather than rebuilding with a confirm, which would relayout from
    # scratch and snap dragged nodes back to their original spot. The view
    # itself must not budge either: the scroll offset is put back as it was.
    #
    # Restored from the scroll bars rather than by centering on the scene point
    # that was in the middle: that point comes back rounded to a whole pixel,
    # and centering on it rounds again, so every switch nudged the view a pixel
    # or so further along and a few flips visibly walked the graph off center.
    # Both scenes carry the same scene rect, so the raw values mean the same
    # thing in either and can simply be handed back.
    def redraw_graph():
        if not getattr(graphics_view, "build_steps", None):
            return   # nothing built yet: the next confirm draws in the new style
        horizontal = graphics_view.horizontalScrollBar()
        vertical = graphics_view.verticalScrollBar()
        offset_x, offset_y = horizontal.value(), vertical.value()
        # a step keeps its own record of the graph, so it is redrawn through
        # the step rather than from the nodes as they stand now
        transition_scene(graphics_view, render_build_step(graphics_view), crossfade=True)
        horizontal.setValue(offset_x)
        vertical.setValue(offset_y)
        graphics_view.notify_view_changed()

    def flip(key, first, second):
        panel_options[key] = second if panel_options[key] == first else first
        schedule_save()

    def toggle_power():
        # the power node and its lines are part of the scene, so a redraw -
        # off takes them away, on brings them back
        panel_options["show_power"] = not panel_options["show_power"]
        schedule_save()
        redraw_graph()
        # the camera stays where it is, but what Reset fits changes with it: the
        # power node hangs well above the rest of the map, and the frame either
        # takes it in or stops at the top of the factory (see build_steps_bounds)
        steps = getattr(graphics_view, "build_steps", None)
        if steps:
            graphics_view.start_rect = QRectF(build_steps_bounds(steps))

    def toggle_build():
        # start, play, skip, and round again. Nothing is rebuilt: it only
        # decides how the next confirm shows its tree
        order = BUILD_REVEAL_ORDER
        panel_options["build_reveal"] = order[(order.index(panel_options["build_reveal"]) + 1) % len(order)]
        schedule_save()

    def toggle_pictures():
        # pictures are baked into the scene's items, so a redraw
        flip("picture_mode", "machine", "item")
        redraw_graph()

    def toggle_snap():
        # nothing to redraw: it only decides where the next dragged node lands
        panel_options["snap"] = not panel_options["snap"]
        schedule_save()

    def toggle_arrows():
        flip("arrow_mode", "new", "old")
        redraw_graph()

    # Holding the graph as it stands: nothing that would move a box or build
    # the tree again answers while it is on. The boxes stop being draggable,
    # and everything that would rebuild them - the build button, the output
    # lists, a node's own recipe picker - greys out. What the lock leaves alone
    # is everything that only looks: the camera, the steps, the toggles, and
    # ticking a box off as built, which is about the factory in the world
    # rather than the graph on the map.
    def toggle_lock():
        panel_options["locked"] = not panel_options["locked"]
        for box in graphics_view.scene().node_items.values() if graphics_view.scene() else ():
            if isinstance(box, NodeItem):
                box.set_locked(panel_options["locked"])
        compact_button.setEnabled(not panel_options["locked"])
        if side[0] is not None:
            side[0].set_locked(panel_options["locked"])
            if getattr(graphics_view, "info_panel", None) is not None:
                graphics_view.info_panel.refresh()   # its recipe row greys with it
        schedule_save()

    # Compact boxes: half as wide, their picture and nothing else, with the
    # layers closing up behind them. The whole graph is laid out again at the
    # new size and glides into place, so it can be switched over with a build
    # already on the map - which makes it a change to the graph, and one a
    # locked graph does not take.
    def toggle_compact():
        spacing_before = layer_spacing()
        panel_options["compact"] = not panel_options["compact"]
        steps = getattr(graphics_view, "build_steps", None)
        if steps:
            # the camera is left exactly where it was: the boxes glide to their
            # new places under it (transition_scene matches them by node, and
            # every line follows the box it is plugged into), which reads as the
            # graph closing up. Refitting the view at the same time turned that
            # into a jump - the map moving under a camera that was moving too.
            #
            # Unless it was framing the whole graph, as Reset leaves it. Then it
            # keeps framing it: it glides to the new graph's own framing over
            # the same time and with the same easing as the boxes, so the two
            # arrive together and the graph never slides out of its frame.
            framed = graphics_view.at_start_camera()   # read before anything moves
            horizontal = graphics_view.horizontalScrollBar()
            vertical = graphics_view.verticalScrollBar()
            offset_x, offset_y = horizontal.value(), vertical.value()
            # not laid out again: every box keeps its row and whatever it was
            # dragged off its spot by, and only closes up or opens out with
            # its column. The power node is placed over the map on its own.
            shift = spacing_before - layer_spacing()
            moved = set()
            for step in steps:
                for node in step["nodes"]:
                    if is_power_node(node) or id(node) in moved:
                        continue
                    moved.add(id(node))
                    x, y = node.coordinate
                    node.coordinate = (x + node.layer * shift, y)
            # started first, so the new scene is built with the bend the lines
            # still have rather than the one they are going to
            ease_line_curves(graphics_view, GRAPH_TRANSITION_MS)
            transition_scene(graphics_view, render_build_step(graphics_view))
            horizontal.setValue(offset_x)
            vertical.setValue(offset_y)
            # the camera has not moved, but what it would go back to has: the
            # graph is half the size it was, and Reset fits the graph as it
            # now stands rather than the frame the old one was built into
            graphics_view.start_rect = QRectF(build_steps_bounds(steps))
            if framed:
                graphics_view.reset_camera(GRAPH_TRANSITION_MS)
            graphics_view.notify_view_changed()
        schedule_save()

    # one click to tick a box off as built instead of two, for working down a
    # factory a box at a time: the click that would pick the node out marks it
    def toggle_quick_done():
        panel_options["quick_done"] = not panel_options["quick_done"]
        schedule_save()

    # top to bottom, with full screen at the foot of the bar, in the corner
    # where it has always been
    toolbar = add_view_toolbar(graphics_view)
    compact_button = toolbar.add_toggle(
        lambda: f"size_{'compact' if panel_options['compact'] else 'detail'}",
        lambda: NODE_SIZE_LABELS[panel_options["compact"]],
        toggle_compact, active_for=lambda: panel_options["compact"])
    toolbar.add_toggle(lambda: f"lock_{'on' if panel_options['locked'] else 'off'}",
                       lambda: LOCK_MODE_LABELS[panel_options["locked"]],
                       toggle_lock, active_for=lambda: panel_options["locked"])
    toolbar.add_toggle(lambda: "done_tick",
                       lambda: QUICK_DONE_LABELS[panel_options["quick_done"]],
                       toggle_quick_done, active_for=lambda: panel_options["quick_done"])
    toolbar.add_toggle(lambda: "power",
                       lambda: POWER_MODE_LABELS[panel_options["show_power"]],
                       toggle_power, active_for=lambda: panel_options["show_power"])
    toolbar.add_toggle(lambda: f"build_{panel_options['build_reveal']}",
                       lambda: BUILD_REVEAL_LABELS[panel_options["build_reveal"]], toggle_build)
    toolbar.add_toggle(lambda: f"pictures_{panel_options['picture_mode']}",
                       lambda: PICTURE_MODE_LABELS[panel_options["picture_mode"]], toggle_pictures)
    toolbar.add_toggle(lambda: "snap",
                       lambda: SNAP_MODE_LABELS[panel_options["snap"]],
                       toggle_snap, active_for=lambda: panel_options["snap"])
    toolbar.add_toggle(lambda: f"arrows_{panel_options['arrow_mode']}",
                       lambda: ARROW_MODE_LABELS[panel_options["arrow_mode"]], toggle_arrows)
    # not a toggle but the same kind of button: back to the starting camera
    toolbar.add_toggle(lambda: "camera", lambda: CAMERA_RESET_LABEL, graphics_view.reset_camera)
    fullscreen_button = toolbar.add_toggle(
        lambda: "fullscreen_exit" if fullscreen.is_on() else "fullscreen_enter",
        lambda: FULLSCREEN_MODE_LABELS[fullscreen.is_on()],
        fullscreen.toggle, active_for=fullscreen.is_on)
    fullscreen.on_change = fullscreen_button.refresh   # Escape leaves full screen too

    # the same scroll-preserving redraw the pills use, pointed at whichever
    # step the arrows just moved to
    def show_step():
        horizontal = graphics_view.horizontalScrollBar()
        vertical = graphics_view.verticalScrollBar()
        offset_x, offset_y = horizontal.value(), vertical.value()
        transition_scene(graphics_view, render_build_step(graphics_view))
        horizontal.setValue(offset_x)
        vertical.setValue(offset_y)
        graphics_view.notify_view_changed()

    step_bar[0] = add_build_step_bar(graphics_view, show_step)

    layout.addWidget(left_panel)
    layout.addWidget(content_stack, 1)
    layout.addWidget(panel)

    # an arrow tab on each panel's inner edge, to slide it shut and open again
    add_panel_collapse(container, left_panel, content_stack, "left", open=DEFAULT_LEFT_PANEL_OPEN)
    add_panel_collapse(container, panel, content_stack, "right")

    # the left panel sliding moves the canvas' left edge, and the view keeps
    # the map pinned to its own left edge - so the map would slide along with
    # it. The view is scrolled by as much as the edge moved instead, and the
    # map holds still on screen while the canvas grows or shrinks around it.
    # (The right panel only moves the right edge, which the map is not pinned to.)
    class HoldMapStill(QObject):
        def eventFilter(self, watched, event):
            if event.type() == QEvent.Move and graphics_view.parent() is content_stack:
                moved = event.pos().x() - event.oldPos().x()
                if moved:
                    horizontal = graphics_view.horizontalScrollBar()
                    horizontal.setValue(horizontal.value() + moved)
                    graphics_view.notify_view_changed()
            return False

    content_stack.hold_map = HoldMapStill(content_stack)   # kept alive by the stack
    content_stack.installEventFilter(content_stack.hold_map)

    # what the save file reads off a project, and what a restored one is put
    # back through (see saved_project / MainWindow.restore)
    container.view = graphics_view
    container.panel = panel
    # the panel's own confirm, not the canvas': it reads the cards into
    # panel_options["output"] first, which is what the build actually goes on
    container.build = side_confirm
    return container


# A page being put together hangs its cog here. The work that takes the time
# - laying a tree out, above all - calls tick_loading() as it goes, and the
# cog takes a step and redraws itself on the spot: nothing else can, because
# the work holds the event loop until it is done.
loading_tick = [None]

def tick_loading():
    turn = loading_tick[0]
    if turn is not None:
        turn()

LOADING_SPIN_MS = 1600      # one full turn of the cog while a project loads
LOADING_SPIN_STEP_MS = 30   # ...and how often it is redrawn on the way round
LOADING_TEXT_GAP = 28
LOADING_TEXT_SIZE = 48      # big enough to read from across the room


# A project's tab page. Until it is first opened it holds only the project as
# the save file had it, and shows the home cog while it is being built.
# The loading screen, laid over the page while it is being put together. A
# sheet of its own rather than the page painting it: the canvas under it has
# to be up and at its real size the whole time, or the camera it restores is
# fitted to a window that is not there yet and the graph comes up zoomed out.
class LoadingCover(QWidget):
    def __init__(self, page):
        super().__init__(page)
        self.spin = 0.0
        self.setGeometry(page.rect())
        self.show()
        self.raise_()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(HOME_BG))
        radius = min(self.width(), self.height()) * HOME_COG_SIZE / 2
        center = QRectF(self.rect()).center()
        paint_home_cog(painter, center, radius, self.spin)
        font = QFont(painter.font())
        font.setPixelSize(LOADING_TEXT_SIZE)
        painter.setFont(font)
        painter.setPen(QColor(TEXT_NORMAL))
        line = QFontMetrics(font).height()
        painter.drawText(QRectF(0, center.y() + radius + LOADING_TEXT_GAP, self.width(), line),
                         Qt.AlignCenter, "Loading")
        painter.end()


class ProjectPage(QWidget):
    def __init__(self, name, saved=None):
        super().__init__()
        self.project_name = name
        self.saved = saved
        # the color of its tab, and of the band under the row while it is open
        self.tab_color = (saved or {}).get("color") or TAB_DEFAULT_COLOR
        self.canvas = None
        self.cover = None       # the loading screen, while there is one
        self.wanted_camera = None   # where a saved project was being looked at
        self.load_queued = False
        # the cog turns while the page is loading, so a build that takes a
        # moment reads as working rather than as stopped
        self.spin = 0.0
        self.last_tick = 0.0
        self.spinner = QTimer(self)
        self.spinner.setInterval(LOADING_SPIN_STEP_MS)
        self.spinner.timeout.connect(self.turn_cog)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

    def loaded(self):
        return self.canvas is not None

    # ...and whether it is still being put together, under its loading screen
    def loading(self):
        return self.cover is not None

    def turn_cog(self):
        self.spin = (self.spin + 360 * LOADING_SPIN_STEP_MS / LOADING_SPIN_MS) % 360
        self.draw_cog()

    # whichever is showing the cog: the page itself before the canvas is up,
    # the sheet over it afterwards
    def draw_cog(self, at_once=False):
        showing = self.cover if self.cover is not None else self
        if self.cover is not None:
            self.cover.spin = self.spin
            self.cover.setGeometry(self.rect())
        showing.repaint() if at_once else showing.update()

    # the same step, but taken from inside work that is holding the event
    # loop: it is drawn on the spot rather than left to the next paint, and
    # only as often as the timer would have done it anyway
    def tick_cog(self):
        now = time.monotonic() * 1000
        if now - self.last_tick < LOADING_SPIN_STEP_MS:
            return
        self.last_tick = now
        self.spin = (self.spin + 360 * LOADING_SPIN_STEP_MS / LOADING_SPIN_MS) % 360
        self.draw_cog(at_once=True)

    @property
    def view(self):
        return self.canvas.view

    @property
    def panel(self):
        return self.canvas.panel

    def build(self):
        self.canvas.build()

    # the cog is painted first, and the build waits a tick after it: built
    # straight away, the window would sit frozen on the page it came from
    def paintEvent(self, event):
        if self.loaded() and not self.loading():
            self.spinner.stop()
            return
        if not self.spinner.isActive():
            self.spinner.start()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(HOME_BG))
        radius = min(self.width(), self.height()) * HOME_COG_SIZE / 2
        center = QRectF(self.rect()).center()
        paint_home_cog(painter, center, radius, self.spin)
        font = QFont(painter.font())
        font.setPixelSize(LOADING_TEXT_SIZE)
        painter.setFont(font)
        painter.setPen(QColor(TEXT_NORMAL))
        line = QFontMetrics(font).height()
        painter.drawText(QRectF(0, center.y() + radius + LOADING_TEXT_GAP, self.width(), line),
                         Qt.AlignCenter, "Loading")
        painter.end()
        if not self.load_queued:
            self.load_queued = True
            QTimer.singleShot(0, self.load)

    # The work is done a piece at a time, each piece handed back to Qt before
    # the next: run in one go it holds the event loop for as long as it takes,
    # and the cog sits frozen on a page that is meant to say it is working.
    # The canvas is up and sized from the first piece, with the loading
    # screen over it until the last.
    def load(self):
        if self.loaded():
            return
        project = self.saved
        self.saved = None
        pieces = [self.lay_out_canvas]
        if project:
            pieces += [lambda: self.put_back_cards(project),
                       lambda: self.put_back_build(project),
                       self.put_back_camera]
        pieces.append(self.show_canvas)
        self.work_through(pieces)

    def work_through(self, pieces):
        if not pieces:
            return
        loading_tick[0] = self.tick_cog
        wait = 1
        try:
            wait = pieces[0]() or 1
        except RuntimeError:
            return      # the tab was closed while it was loading
        finally:
            loading_tick[0] = None
        # a nothing of a delay, but enough of one that the cog's own timer
        # gets its turn between the pieces - unless the piece asks to be
        # waited on, the way a build waits for its own camera to settle
        QTimer.singleShot(max(wait, 1), lambda: self.work_through(pieces[1:]))

    def lay_out_canvas(self):
        self.canvas = make_canvas()
        self.layout().addWidget(self.canvas)
        self.layout().activate()
        self.canvas.show()
        self.cover = LoadingCover(self)

    def put_back_cards(self, project):
        self.panel.restore_cards(project.get("outputs", []))
        # set before the build: the boxes come up already ticked off
        self.view.completed = set(project.get("built_nodes") or ())

    def put_back_build(self, project):
        if not project.get("built"):
            return 1
        self.rebuild_saved(project)
        # the scene it just raised fits itself to the whole graph over the
        # next moment; where the project was really left is put back once
        # that is done, and all of it under the loading screen, so the graph
        # is never seen at a framing nobody asked for
        return RECENTER_MS + GRAPH_TRANSITION_MS

    def show_canvas(self):
        self.spinner.stop()
        if self.cover is not None:
            self.cover.deleteLater()
            self.cover = None
        self.update()

    def put_back_camera(self):
        camera, self.wanted_camera = self.wanted_camera, None
        if not camera or not self.loaded():
            return
        # the zoom first: it changes what the scrollbars run over, so setting
        # them before it would leave them somewhere else once it was applied
        # (a camera saved before zoom was kept has two numbers, not three)
        if len(camera) > 2 and camera[2]:
            self.view.apply_zoom(camera[2])
            self.view.zoom_target = self.view.zoom
        self.view.horizontalScrollBar().setValue(camera[0])
        self.view.verticalScrollBar().setValue(camera[1])

    # its cards on the panel, its build run again from them, and then every
    # box it had dragged moved back to where it was left. The build is put
    # back finished, whatever the Build toggle says: watching a project play
    # itself in again is not what opening it is for.
    def restore(self, project):
        self.put_back_cards(project)
        if project.get("built"):
            self.rebuild_saved(project)

    # the build itself, run again and put back where it was left
    def rebuild_saved(self, project):
        reveal = panel_options["build_reveal"]
        panel_options["build_reveal"] = "skip"
        try:
            self.build()
        finally:
            panel_options["build_reveal"] = reveal
        steps = getattr(self.view, "build_steps", None)
        if not steps:
            return
        apply_positions(steps[-1]["nodes"], project.get("positions") or {})
        self.view.build_step = project.get("step", 0) % len(steps)
        transition_scene(self.view, render_build_step(self.view), crossfade=True)
        # where it was left is put back last of all: the scene coming up runs
        # a camera of its own (transition_scene fits the new graph), and that
        # would land after this and leave the project framed rather than
        # where it was being looked at
        self.wanted_camera = project.get("camera")




# ==================================================== MAIN WINDOW ==================================================
DEFAULT_WINDOW_SIZE = (1200, 800)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Satisfactory-Planner")
        # the options are read before anything is built: every panel and every
        # graph is drawn from them
        saved = read_appdata()
        load_options(saved.get("options", {}))
        self.resize(*(saved.get("window") or DEFAULT_WINDOW_SIZE))

        central = QWidget()

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 1)
        layout.setSpacing(0)

        self.project_tabs = make_project_tabs()
        self.full_screen = self.project_tabs.full_screen

        layout.addWidget(self.project_tabs, 1)
        QShortcut(QKeySequence(Qt.Key_F11), self, activated=self.full_screen.toggle_full_screen)
        
        self.setCentralWidget(central)
        self.last_project = None
        self.project_tabs.currentChanged.connect(self.remember_project)
        # once the window is up: a tab picked while the bar is still at its
        # first tiny width scrolls the row along, and it stays scrolled
        QTimer.singleShot(0, lambda: self.restore(saved))

    # where the game was said to be, for the home page to open on it again
    def game_path(self):
        home = getattr(self.project_tabs, "home_page", None)
        field = getattr(home, "path_field", None)
        return field.text().strip() if field is not None else ""

    # every project page, in tab order (the trailing "+" is not one)
    def project_pages(self):
        tabs = self.project_tabs
        return [tabs.widget(index) for index in range(tabs.count())
                if tabs.tabText(index) != PLUS_TAB_LABEL and tabs.widget(index) is not tabs.home_page]

    def remember_project(self, index):
        page = self.project_tabs.widget(index)
        if page in self.project_pages():
            self.last_project = page

    # the project open last, even when home was showing at the end: the app
    # reopens on it
    def current_project(self):
        pages = self.project_pages()
        return pages.index(self.last_project) if self.last_project in pages else 0

    # every project of the save file gets its tab back, but only the one open
    # last is built: the others wait until their tab is opened
    def restore(self, saved):
        for project in saved.get("projects") or []:
            self.project_tabs.add_project_tab(rename=False, name=project.get("name"), saved=project, select=False)
        pages = self.project_pages()
        if pages:
            # by page rather than by index: home stands before the projects
            page = pages[min(saved.get("current", 0), len(pages) - 1)]
            self.project_tabs.setCurrentIndex(self.project_tabs.indexOf(page))
            self.last_project = page

    def closeEvent(self, event):
        save_appdata(self)
        super().closeEvent(event)

    # call from anywhere to change the bottom line
    def set_status(self, text):
        self.status.setText(text)


# ===================================================== ENTRY POINT =================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    apply_app_font(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
