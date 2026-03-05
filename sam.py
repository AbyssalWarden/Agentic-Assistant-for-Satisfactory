import sys
import os
import json
import requests
import math
import random
import numpy as np
import scipy
from scipy import ndimage
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QTextEdit, QLineEdit, QPushButton, QHBoxLayout, QLabel,
                            QMenu, QMenuBar, QStatusBar, QToolBar, QSizePolicy,
                            QDialog, QComboBox, QSpinBox, QDoubleSpinBox, QGridLayout,
                            QScrollArea, QFrame, QFileDialog, QMessageBox, QInputDialog,
                            QColorDialog, QGroupBox, QDialogButtonBox, QProgressBar)
from PyQt6.QtCore import Qt, QSize, QTimer, QPoint, QRect, QPointF
from PyQt6.QtGui import (
    QFont, QIcon, QLinearGradient, QColor, QPalette, QImage,
    QPixmap, QAction, QPainter, QPen, QBrush, QDrag, QPolygonF,
    QCursor, QRadialGradient, QConicalGradient, QFontDatabase,
    QPainterPath
)
from chat_history import ChatHistory
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Ensure the 'layout' directory exists
LAYOUT_DIR = "layout"
if not os.path.exists(LAYOUT_DIR):
    os.makedirs(LAYOUT_DIR)

class SatisfactoryGuide(QMainWindow):
    def __init__(self):
        super().__init__()
        self.chat_history = ChatHistory(agent_name="sam")
        self.conversation_context = []
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.type_next_word)
        self.current_message = ""
        self.words_to_type = []
        self.current_word_index = 0
        self.sound_effects_enabled = True
        
        # Default custom theme settings
        self.custom_bg_color = QColor(35, 36, 58) # Deep Dark Grey (matches existing dark theme somewhat)
        self.custom_text_color = QColor(0, 255, 255) # Cyan
        self.custom_accent_color = QColor(255, 0, 255) # Magenta
        self.custom_gradient_type = "Linear"

        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Satisfactory Guide")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(400, 600)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Add Status Bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.setStyleSheet("QStatusBar { background-color: #2a2a2a; color: #00FFFF; font-size: 10px; }")
        
        # Create top section with info and logo
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        
        # Add info panel in top left
        info_panel = QLabel()
        info_panel.setStyleSheet("""
            QLabel {
                background-color: rgba(42, 42, 42, 0.9);
                color: #00FFFF;
                border: 2px solid #FF00FF;
                border-radius: 8px;
                padding: 8px;
                font-family: 'Arial', sans-serif;
                min-width: 130px;
                max-width: 130px;
                font-size: 11px;
            }
        """)
        info_text = """
        <b>SAM</b><br>
        <i>FICSIT Technical Support</i><br>
        <br>
        Your guide to efficient<br>
        factory building and<br>
        resource management.<br>
        <br>
        <i>"Efficiency First!"</i>
        """
        info_panel.setText(info_text)
        info_panel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        top_layout.addWidget(info_panel)
        
        # Add logo in top right
        logo_label = QLabel()
        try:
            logo_pixmap = QPixmap("satisfactory/Satisfactory_Early_Access_edited.jpg")
            if not logo_pixmap.isNull():
                logo_pixmap = logo_pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(logo_pixmap)
            else:
                print("Failed to load logo image")
        except Exception as e:
            print(f"Error loading logo: {str(e)}")
            
        logo_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        logo_label.setStyleSheet("""
            QLabel {
                background: transparent;
                padding: 5px;
                min-width: 150px;
                max-width: 150px;
                min-height: 150px;
                max-height: 150px;
                qproperty-alignment: AlignCenter;
            }
        """)
        top_layout.addWidget(logo_label)
        
        # Add stretch to center the logo
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        
        self.create_menu_bar()
        
        # Chat display area with metallic frame
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding) # Use QSizePolicy
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00FFFF;
                border: 3px solid;
                border-image: linear-gradient(45deg, #FFFF00, #FF00FF, #FFFF00) 1;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Arial', sans-serif;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.chat_display, 1)
        
        # Input area with metallic frame
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        self.input_field = QLineEdit()
        self.input_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed) # Use QSizePolicy
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 3px solid;
                border-image: linear-gradient(45deg, #FFFF00, #FF00FF, #FFFF00) 1;
                border-radius: 8px;
                padding: 8px;
                font-size: 11px;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        
        send_button = QPushButton("Send")
        send_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #00FFFF,
                    stop: 0.5 #00CCCC,
                    stop: 1 #00FFFF
                );
                color: #000000;
                border: 2px solid #FF00FF;
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #33FFFF,
                    stop: 0.5 #00FFFF,
                    stop: 1 #33FFFF
                );
                border: 2px solid #FF33FF;
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #00CCCC,
                    stop: 0.5 #009999,
                    stop: 1 #00CCCC
                );
            }
        """)
        send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(send_button)
        layout.addLayout(input_layout)
        
        # Set the background with enhanced gradient
        central_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #FF00FF,
                    stop: 0.5 #00FFFF,
                    stop: 1 #FF00FF
                );
                border: 2px solid #00008B;
                border-radius: 15px;
                margin: 10px;
            }
        """)
        
        # Set the window background color to match the border
        self.setStyleSheet("""
            QMainWindow {
                background-color: #00008B;
            }
        """)
        
        # Add initial greeting
        initial_greeting = "Welcome, Pioneer! I'm SAM, your FICSIT Technical Support AI. How can I help you optimize your factory today?"
        self.start_typing_animation(initial_greeting)
        # Only add to context once
        self.conversation_context = [{"role": "assistant", "content": initial_greeting}]
        
    def start_typing_animation(self, message: str):
        """Start the typing animation for a message."""
        self.words_to_type = message.split()
        self.current_word_index = 0
        self.current_message = ""
        self.typing_timer.start(100)  # Type a word every 100ms
        
    def type_next_word(self):
        """Type the next word in the animation."""
        if self.current_word_index < len(self.words_to_type):
            if self.current_message:
                self.current_message += " "
            self.current_message += self.words_to_type[self.current_word_index]
            # Clear the last message and add the new one
            self.chat_display.clear()
            self.chat_display.append(f"<p style='color: #00FFFF;'><b>SAM:</b> {self.current_message}</p>")
            self.current_word_index += 1
            # Auto-scroll to bottom
            self.chat_display.verticalScrollBar().setValue(
                self.chat_display.verticalScrollBar().maximum()
            )
        else:
            self.typing_timer.stop()
            # Add the final message to chat history
            self.chat_display.append("")  # Add a blank line after the message
            # Auto-scroll to bottom
            self.chat_display.verticalScrollBar().setValue(
                self.chat_display.verticalScrollBar().maximum()
            )
        
    def send_message(self):
        """Handle sending and receiving messages."""
        user_message = self.input_field.text().strip()
        if not user_message:
            return
            
        self.add_user_message(user_message)
        self.input_field.clear()
        
        # Add user message to context
        self.conversation_context.append({"role": "user", "content": user_message})
        
        # Generate bot response
        bot_response = self.generate_response(user_message)
        self.start_typing_animation(bot_response)
        
        # Add bot response to context
        self.conversation_context.append({"role": "assistant", "content": bot_response})
        
        # Save to history
        self.chat_history.add_message(user_message, bot_response)
        
    def generate_response(self, user_message: str) -> str:
        try:
            system_message = (
                "You are SAM, a FICSIT Technical Support AI assistant for the game Satisfactory. "
                "You provide helpful, technical advice about factory building, resource management, "
                "and game mechanics. Keep responses concise and focused on Satisfactory gameplay. "
                "Use technical terms and maintain a professional, helpful tone. "
                "Address the user as 'Pioneer'. Limit responses to 1-2 sentences."
            )

            messages = [
                {"role": "system", "content": system_message}
            ] + self.conversation_context[-4:]

            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "llama3.1:8b",
                    "messages": messages,
                    "stream": False
                },
                timeout=30
            )

            if response.status_code == 200:
                content = response.json()["message"]["content"]
                max_word_count = 52
                shortened = ' '.join(content.split()[:max_word_count])
                return shortened
            else:
                print(f"API Error: {response.status_code} - {response.text}")
                return "Pioneer, I'm experiencing some technical difficulties. Please try again."
                
        except requests.exceptions.Timeout:
            print("Request timed out")
            return "Pioneer, the system is taking longer than expected to respond. Please try again."
        except requests.exceptions.ConnectionError:
            print("Connection error")
            return "Pioneer, I'm unable to connect to the FICSIT network. Please check your connection."
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "Pioneer, I've encountered an unexpected error. Please try again."

    def add_user_message(self, message: str):
        """Add a user message to the chat display."""
        self.chat_display.append(f"<p style='color: #ffffff;'><b>You:</b> {message}</p>")
        # Auto-scroll to bottom
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )
        
    def mousePressEvent(self, event):
        """Handle window dragging."""
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """Handle window dragging."""
        delta = event.globalPosition().toPoint() - self.oldPos
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()

    def create_menu_bar(self):
        """Create the menu bar with various options."""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #2a2a2a;
                color: #00FFFF;
                font-size: 11px;
            }
            QMenuBar::item:selected {
                background-color: #FF00FF;
            }
            QMenu {
                background-color: #2a2a2a;
                color: #00FFFF;
                border: 1px solid #FF00FF;
                font-size: 11px;
            }
            QMenu::item:selected {
                background-color: #FF00FF;
            }
        """
        )
        
        # File menu
        file_menu = menubar.addMenu("File")
        new_chat_action = QAction("New Chat", self)
        new_chat_action.triggered.connect(self.clear_chat)
        file_menu.addAction(new_chat_action)
        save_chat_action = QAction("Save Chat", self)
        save_chat_action.triggered.connect(self.save_chat)
        file_menu.addAction(save_chat_action)
        load_chat_action = QAction("Load Chat", self)
        load_chat_action.triggered.connect(self.load_chat)
        file_menu.addAction(load_chat_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        calculator_action = QAction("Production Calculator", self)
        calculator_action.triggered.connect(self.show_calculator)
        tools_menu.addAction(calculator_action)
        quick_ref_action = QAction("Quick Reference", self)
        quick_ref_action.triggered.connect(self.show_quick_reference)
        tools_menu.addAction(quick_ref_action)
        power_grid_action = QAction("Power Grid Simulator", self)
        power_grid_action.triggered.connect(self.show_power_grid_simulator)
        tools_menu.addAction(power_grid_action)
        # New tools
        layout_planner_action = QAction("Factory Layout Planner", self)
        layout_planner_action.triggered.connect(self.show_factory_layout_planner)
        tools_menu.addAction(layout_planner_action)
        prod_chain_action = QAction("Production Chain Visualizer", self)
        prod_chain_action.triggered.connect(self.show_production_chain_visualizer)
        tools_menu.addAction(prod_chain_action)
        route_optimizer_action = QAction("Train/Truck Route Optimizer", self)
        route_optimizer_action.triggered.connect(self.show_route_optimizer)
        tools_menu.addAction(route_optimizer_action)
        storage_calc_action = QAction("Inventory/Storage Calculator", self)
        storage_calc_action.triggered.connect(self.show_storage_calculator)
        tools_menu.addAction(storage_calc_action)
        perf_monitor_action = QAction("Performance Monitor", self)
        perf_monitor_action.triggered.connect(self.show_performance_monitor)
        tools_menu.addAction(perf_monitor_action)
        
        # Settings menu
        settings_menu = menubar.addMenu("Settings")
        theme_menu = settings_menu.addMenu("Theme")
        dark_theme_action = QAction("Dark Theme", self)
        dark_theme_action.triggered.connect(lambda: self.change_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        light_theme_action = QAction("Light Theme", self)
        light_theme_action.triggered.connect(lambda: self.change_theme("light"))
        theme_menu.addAction(light_theme_action)
        # New settings
        custom_theme_action = QAction("Custom Theme...", self)
        custom_theme_action.triggered.connect(self.show_custom_theme_dialog)
        settings_menu.addAction(custom_theme_action)
        font_size_action = QAction("Font Size/Style...", self)
        font_size_action.triggered.connect(self.show_font_settings_dialog)
        settings_menu.addAction(font_size_action)
        compact_ui_action = QAction("Compact/Expanded UI", self)
        compact_ui_action.triggered.connect(self.toggle_compact_ui)
        settings_menu.addAction(compact_ui_action)
        sound_effects_action = QAction("Sound Effects", self)
        sound_effects_action.triggered.connect(self.toggle_sound_effects)
        settings_menu.addAction(sound_effects_action)
        startup_tool_action = QAction("Startup Tool...", self)
        startup_tool_action.triggered.connect(self.show_startup_tool_dialog)
        settings_menu.addAction(startup_tool_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        tips_action = QAction("Random Tips", self)
        tips_action.triggered.connect(self.show_random_tip)
        help_menu.addAction(tips_action)
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def clear_chat(self):
        """Clear the chat history and display."""
        self.chat_display.clear()
        self.conversation_context = []
        self.chat_history.clear_history()
        self.start_typing_animation("Chat cleared. How can I help you today, Pioneer?") # Keeping typing animation for chat

    def save_chat(self):
        """Save the current chat to a file."""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Chat",
            f"satisfactory_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )
        
        if file_name:
            try:
                # Get chat history
                chat_data = {
                    "timestamp": datetime.now().isoformat(),
                    "messages": self.chat_history.get_all_messages()
                }
                
                # Save to file
                with open(file_name, 'w') as f:
                    json.dump(chat_data, f, indent=2)
                
                self.statusBar.showMessage("Chat history saved successfully, Pioneer!", 3000)
            except Exception as e:
                self.statusBar.showMessage(f"Failed to save chat: {str(e)}", 5000)
    
    def load_chat(self):
        """Load a chat from a file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Load Chat",
            "",
            "JSON Files (*.json)"
        )
        
        if file_name:
            try:
                # Load from file
                with open(file_name, 'r') as f:
                    chat_data = json.load(f)
                
                # Clear current chat
                self.chat_display.clear()
                self.conversation_context = []
                
                # Load messages
                for message in chat_data["messages"]:
                    self.add_user_message(message["user"])
                    self.chat_display.append(f"<p style='color: #00FFFF;'><b>SAM:</b> {message['assistant']}</p>")
                    self.conversation_context.append({"role": "user", "content": message["user"]})
                    self.conversation_context.append({"role": "assistant", "content": message["assistant"]})
                
                self.statusBar.showMessage("Chat history loaded successfully, Pioneer!", 3000)
            except Exception as e:
                self.statusBar.showMessage(f"Failed to load chat: {str(e)}", 5000)
    
    def show_calculator(self):
        """Show the production calculator window."""
        calculator = ProductionCalculator(self)
        calculator.exec()
        
    def show_quick_reference(self):
        """Show the quick reference window."""
        quick_ref = QuickReference(self)
        quick_ref.exec()
    
    def change_theme(self, theme):
        """Change the application theme."""
        if theme == "dark":
            self.set_dark_theme()
        else:
            self.set_light_theme()
    
    def set_dark_theme(self):
        """Set the dark theme."""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #23243a,
                    stop: 0.5 #2a2a2a,
                    stop: 1 #00FFFF
                );
            }
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #23243a,
                    stop: 0.5 #2a2a2a,
                    stop: 1 #00FFFF
                );
                color: #00FFFF;
            }
            QTextEdit {
                background-color: #1a1a1a;
                color: #00FFFF;
                border: 3px solid;
                border-image: linear-gradient(45deg, #FFFF00, #FF00FF, #FFFF00) 1;
                border-radius: 8px;
                padding: 10px;
                font-size: 11px;
            }
            QLineEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 3px solid;
                border-image: linear-gradient(45deg, #FFFF00, #FF00FF, #FFFF00) 1;
                border-radius: 8px;
                padding: 8px;
                font-size: 11px;
            }
            QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #00FFFF,
                    stop: 0.5 #00CCCC,
                    stop: 1 #00FFFF
                );
                color: #000000;
                border: 2px solid #FF00FF;
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #33FFFF,
                    stop: 0.5 #00FFFF,
                    stop: 1 #33FFFF
                );
                border: 2px solid #FF33FF;
            }
            QMenuBar {
                background-color: #2a2a2a;
                color: #00FFFF;
                font-size: 11px;
            }
            QMenuBar::item:selected {
                background-color: #FF00FF;
            }
            QMenu {
                background-color: #2a2a2a;
                color: #00FFFF;
                border: 1px solid #FF00FF;
                font-size: 11px;
            }
            QMenu::item:selected {
                background-color: #FF00FF;
            }
            QStatusBar {
                background-color: #2a2a2a; /* Match menu bar */
                color: #00FFFF;
            }
        """)
    
    def set_light_theme(self):
        """Set the light theme."""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #fffbe6,
                    stop: 0.5 #ffffff,
                    stop: 1 #FFD700
                );
            }
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #fffbe6,
                    stop: 0.5 #ffffff,
                    stop: 1 #FFD700
                );
                color: #000000;
            }
            QTextEdit {
                background-color: #1a1a1a;
                color: #00FFFF;
                border: 3px solid;
                border-image: linear-gradient(45deg, #FFD700, #FFA500, #FFD700) 1;
                border-radius: 8px;
                padding: 10px;
                font-size: 11px;
            }
            QLineEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 3px solid;
                border-image: linear-gradient(45deg, #FFD700, #FFA500, #FFD700) 1;
                border-radius: 8px;
                padding: 8px;
                font-size: 11px;
            }
            QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #FFD700,
                    stop: 0.5 #FFA500,
                    stop: 1 #FFD700
                );
                color: #000000;
                border: 2px solid #FFA500;
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #FFE44D,
                    stop: 0.5 #FFD700,
                    stop: 1 #FFE44D
                );
                border: 2px solid #FFB700;
            }
            QMenuBar {
                background-color: #ffffff;
                color: #000000;
                font-size: 11px;
            }
            QMenuBar::item:selected {
                background-color: #FFD700;
            }
            QMenu {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #FFA500;
                font-size: 11px;
            }
            QMenu::item:selected {
                background-color: #FFD700;
            }
            QStatusBar {
                background-color: #ffffff; /* Match menu bar */
                color: #000000;
            }
        """)
        
        # Update text colors in chat display
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00FFFF;
                border: 3px solid;
                border-image: linear-gradient(45deg, #FFD700, #FFA500, #FFD700) 1;
                border-radius: 8px;
                padding: 10px;
                font-size: 11px;
            }
        """)

    def show_random_tip(self):
        """Show a random Satisfactory tip."""
        tips = [
            "Use foundations to create a flat building surface.",
            "Power poles can be connected to machines automatically.",
            "Use the 'Z' key to toggle between build modes.",
            "Conveyor belts can be stacked using conveyor lifts.",
            "Use the 'R' key to rotate buildings while placing them.",
            "Hold Ctrl while placing to snap to grid.",
            "Build vertically to save space.",
            "Use wall mounts for power connections.",
            "Create a central storage area for resources.",
            "Use the map to plan your factory layout.",
            "Upgrade your HUB early to unlock more buildings and recipes.",
            "Use lookout towers to scout your surroundings.",
            "Automate biomass production for early-game power.",
            "Use splitters and mergers to balance conveyor belt loads.",
            "Stack conveyor belts to save space and reduce clutter.",
            "Use smart and programmable splitters for advanced logistics.",
            "Build on cliffs to maximize vertical space.",
            "Use hypertubes for fast travel across your factory.",
            "Place beacons to mark important locations.",
            "Use the object scanner to find resources and slugs.",
            "Upgrade miners and smelters to increase efficiency.",
            "Use foundations to align machinery perfectly.",
            "Keep a supply of healing items for exploring dangerous areas.",
            "Automate the production of reinforced iron plates and rotors early.",
            "Use the chainsaw to clear large areas of foliage quickly.",
            "Build walkways and ladders for easy access to tall structures.",
            "Use the MAM to research new technologies and upgrades.",
            "Plan your factory layout before expanding.",
            "Use the awesome sink to get rid of excess items and earn coupons.",
            "Build multiple power grids for redundancy.",
            "Use color gun to organize and color-code your factory.",
            "Upgrade belts and lifts as soon as possible to avoid bottlenecks.",
            "Use the map to set custom markers and plan routes.",
            "Keep an eye on power consumption to avoid blackouts.",
            "Use the hover pack for easy building and exploration.",
            "Automate the production of modular frames and computers for late-game needs.",
            "Explore caves and hidden areas for hard drives and slugs.",
            "Use the tractor and truck for early-game resource transport.",
            "Build refineries near oil nodes to minimize transport distance.",
            "Use the zipline for quick movement along power lines.",
            "Keep your inventory organized for efficient building.",
            "Use the radar tower to reveal more of the map.",
            "Upgrade your equipment regularly for better survivability.",
            "Use the Nobelisk detonator to clear boulders and access new areas.",
            "Build factories in modules for easier expansion and upgrades.",
            "Use the train system for large-scale resource transport.",
            "Experiment with alternate recipes for more efficient production.",
            "Keep a supply of fuel and coal for vehicles and generators.",
            "Use the jetpack for vertical construction and exploration.",
            "Always have a backup save before making major changes."
        ]
        import random
        tip = random.choice(tips)
        self.start_typing_animation(f"Tip: {tip}")

    def show_about(self):
        """Show the about dialog."""
        about_text = """
        <h2>SAM - FICSIT Technical Support</h2>
        <p>Version 1.0</p>
        <p>A Satisfactory-themed AI assistant to help you optimize your factory building experience.</p>
        <br>
        <p><b>Features:</b></p>
        <ul>
            <li>AI-powered technical support</li>
            <li>Production calculator</li>
            <li>Quick reference guide</li>
            <li>Chat history management</li>
            <li>Dark and light themes</li>
        </ul>
        <br>
        <p><i>"Efficiency First!"</i></p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("About SAM")
        msg.setText(about_text)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #2a2a2a;
                color: #00FFFF;
            }
            QLabel {
                color: #00FFFF;
                min-width: 400px;
                font-size: 11px;
            }
            QPushButton {
                background-color: #FF00FF;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #FF33FF;
            }
        """)
        msg.exec()

    def show_power_grid_simulator(self):
        """Show the power grid simulator window."""
        simulator = PowerGridSimulator(self)
        simulator.exec()

    # Tool stubs
    def show_factory_layout_planner(self):
        dlg = FactoryLayoutPlanner(self)
        dlg.exec()
    def show_production_chain_visualizer(self):
        dlg = ProductionChainVisualizer(self)
        dlg.exec()
    def show_route_optimizer(self):
        dlg = RouteOptimizer(self)
        dlg.exec()
    def show_storage_calculator(self):
        dlg = StorageCalculator(self)
        dlg.exec()
    def show_performance_monitor(self):
        dlg = PerformanceMonitor(self)
        dlg.exec()
    # Settings stubs
    def show_custom_theme_dialog(self):
        """Show a dialog for custom theme settings."""
        dlg = CustomThemeDialog(self)
        dlg.exec()
    def show_font_settings_dialog(self):
        """Show a dialog for font size and style settings."""
        dlg = FontSettingsDialog(self)
        dlg.exec()
    def toggle_compact_ui(self):
        """Toggle between compact and expanded UI modes."""
        if self.width() == 400 and self.height() == 600:
            # Currently compact, expand it
            self.setFixedSize(600, 800)
        else:
            # Currently expanded, make it compact
            self.setFixedSize(400, 600)
        self.statusBar.showMessage("UI size toggled.", 3000)
    def toggle_sound_effects(self):
        """Toggle sound effects on or off."""
        self.sound_effects_enabled = not self.sound_effects_enabled
        status = "enabled" if self.sound_effects_enabled else "disabled"
        self.statusBar.showMessage(f"UI sound effects are now {status}.", 3000)
    def show_startup_tool_dialog(self):
        """Show a dialog for selecting the startup tool."""
        dlg = StartupToolDialog(self)
        dlg.exec()

    def set_custom_theme(self, bg_color: QColor, text_color: QColor, accent_color: QColor, gradient_type: str):
        """Set a custom theme based on provided colors and gradient type."""
        self.custom_bg_color = bg_color
        self.custom_text_color = text_color
        self.custom_accent_color = accent_color
        self.custom_gradient_type = gradient_type

        # Determine gradient stops based on type
        gradient_stops_bg = f"stop: 0 {bg_color.name()}, stop: 0.5 {bg_color.darker(150).name()}, stop: 1 {accent_color.name()}"
        gradient_stops_accent = f"stop: 0 {accent_color.name()}, stop: 0.5 {accent_color.darker(150).name()}, stop: 1 {accent_color.name()}"

        if gradient_type == "Linear":
            gradient_str_bg = f"qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, {gradient_stops_bg})"
            gradient_str_accent = f"qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, {gradient_stops_accent})"
        elif gradient_type == "Radial":
            gradient_str_bg = f"qradialgradient(cx: 0.5, cy: 0.5, radius: 0.7, {gradient_stops_bg})"
            gradient_str_accent = f"qradialgradient(cx: 0.5, cy: 0.5, radius: 0.7, {gradient_stops_accent})"
        elif gradient_type == "Conical":
            gradient_str_bg = f"qconicalgradient(cx: 0.5, cy: 0.5, angle: 90, {gradient_stops_bg})"
            gradient_str_accent = f"qconicalgradient(cx: 0.5, cy: 0.5, angle: 90, {gradient_stops_accent})"
        else:
            # Default to solid color if unknown gradient type
            gradient_str_bg = bg_color.name()
            gradient_str_accent = accent_color.name()

        self.setStyleSheet(f"""
            QMainWindow {{
                background: {gradient_str_bg};
            }}
            QWidget {{
                background: {gradient_str_bg};
                color: {text_color.name()};
            }}
            QTextEdit {{
                background-color: #1a1a1a;
                color: {text_color.name()};
                border: 3px solid;
                border-image: linear-gradient(45deg, {accent_color.name()}, {accent_color.darker(150).name()}, {accent_color.name()}) 1;
                border-radius: 8px;
                padding: 10px;
                font-size: 11px;
            }}
            QLineEdit {{
                background-color: #1a1a1a;
                color: {text_color.name()};
                border: 3px solid;
                border-image: linear-gradient(45deg, {accent_color.name()}, {accent_color.darker(150).name()}, {accent_color.name()}) 1;
                border-radius: 8px;
                padding: 8px;
                font-size: 11px;
            }}
            QPushButton {{
                background: {gradient_str_accent};
                color: {bg_color.name()}; /* Button text color contrast to accent */
                border: 2px solid {accent_color.darker(150).name()};
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {accent_color.lighter(150).name()};
                border: 2px solid {accent_color.name()};
            }}
            QMenuBar {{
                background-color: {bg_color.darker(150).name()};
                color: {text_color.name()};
                font-size: 11px;
            }}
            QMenuBar::item:selected {{
                background-color: {accent_color.name()};
            }}
            QMenu {{
                background-color: {bg_color.darker(150).name()};
                color: {text_color.name()};
                border: 1px solid {accent_color.name()};
                font-size: 11px;
            }}
            QMenu::item:selected {{
                background-color: {accent_color.name()};
            }}
            QComboBox, QSpinBox, QDoubleSpinBox {{
                background-color: {bg_color.darker(120).name()};
                color: {text_color.name()};
                border: 1px solid {accent_color.name()};
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {bg_color.darker(120).name()};
                color: {text_color.name()};
                selection-background-color: {accent_color.name()};
                selection-color: {text_color.name()};
            }}
            QMessageBox {{
                background-color: {bg_color.name()};
                color: {text_color.name()};
            }}
            QMessageBox QLabel {{
                color: {text_color.name()};
            }}
            QStatusBar {{
                background-color: {bg_color.darker(120).name()};
                color: {text_color.name()};
            }}
        """
        )

        # Update specific widget stylesheets that might be overridden
        self.chat_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: #1a1a1a;
                color: {text_color.name()};
                border: 3px solid;
                border-image: linear-gradient(45deg, {accent_color.name()}, {accent_color.darker(150).name()}, {accent_color.name()}) 1;
                border-radius: 8px;
                padding: 10px;
                font-size: 11px;
            }}
        """
        )

        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: #1a1a1a;
                color: {text_color.name()};
                border: 3px solid;
                border-image: linear-gradient(45deg, {accent_color.name()}, {accent_color.darker(150).name()}, {accent_color.name()}) 1;
                border-radius: 8px;
                padding: 8px;
                font-size: 11px;
            }}
        """
        )

        # Update info panel as well
        info_panel = self.centralWidget().findChild(QLabel)
        if info_panel:
            info_panel.setStyleSheet(f"""
                QLabel {{
                    background-color: {bg_color.darker(120).name()};
                    color: {text_color.name()};
                    border: 2px solid {accent_color.name()};
                    border-radius: 8px;
                    padding: 8px;
                    font-family: 'Arial', sans-serif;
                    min-width: 130px;
                    max-width: 130px;
                    font-size: 11px;
                }}
            """
            )

    def set_application_font(self, font_family: str, font_size: int):
        """Set the application-wide font and apply to relevant widgets."""
        new_font = QFont(font_family, font_size)
        QApplication.instance().setFont(new_font)

        # Apply font to chat display and input field explicitly, as stylesheets might override
        self.chat_display.setFont(new_font)
        self.input_field.setFont(new_font)

        # Update info panel font
        info_panel = self.centralWidget().findChild(QLabel)
        if info_panel:
            info_panel.setFont(new_font)

    def export_layout(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Layout", os.path.join(LAYOUT_DIR, "factory_layout.json"), "JSON Files (*.json)"
        )
        if file_name:
            try:
                serializable_blocks = []
                for block_data in self.grid.blocks:
                    comp_type, x, y, color, *extra = block_data
                    serializable_color = {"r": color.red(), "g": color.green(), "b": color.blue()}

                    if comp_type == "conveyor":
                        p1, p2 = extra[0]
                        serializable_p1 = {"x": p1.x(), "y": p1.y()}
                        serializable_p2 = {"x": p2.x(), "y": p2.y()}
                        serializable_block = [comp_type, x, y, serializable_color, (serializable_p1, serializable_p2)]
                    elif comp_type == "storage" or comp_type == "miner":
                        # If orientation exists, it's the first element in extra
                        orientation = extra[0] if extra else "H" # Default to H for old saves
                        serializable_block = [comp_type, x, y, serializable_color, orientation]
                    elif comp_type == "text":
                        text_content = extra[0]
                        serializable_block = [comp_type, x, y, serializable_color, text_content]
                    else:
                        serializable_block = [comp_type, x, y, serializable_color]
                    serializable_blocks.append(serializable_block)

                with open(file_name, 'w') as f:
                    json.dump(serializable_blocks, f, indent=2)
                self.statusBar.showMessage("Factory layout saved successfully!", 3000)
            except Exception as e:
                self.statusBar.showMessage(f"Failed to save layout: {e}", 5000)

    def import_layout(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Load Layout", LAYOUT_DIR, "JSON Files (*.json)"
        )
        if file_name:
            try:
                # Load from file
                with open(file_name, 'r') as f:
                    chat_data = json.load(f)
                
                # Clear current chat
                self.chat_display.clear()
                self.conversation_context = []
                
                # Load messages
                for message in chat_data["messages"]:
                    self.add_user_message(message["user"])
                    self.chat_display.append(f"<p style='color: #00FFFF;'><b>SAM:</b> {message['assistant']}</p>")
                    self.conversation_context.append({"role": "user", "content": message["user"]})
                    self.conversation_context.append({"role": "assistant", "content": message["assistant"]})
                
                self.statusBar.showMessage("Chat history loaded successfully, Pioneer!", 3000)
            except Exception as e:
                self.statusBar.showMessage(f"Failed to load chat: {str(e)}", 5000)
    
    def set_conveyor_arrow_style(self, index):
        arrow_styles = ["None", ">", "<", "^", "v"]
        selected_style = arrow_styles[index]
        self.grid.set_arrow_style(selected_style)

    def zoom_out(self):
        self.grid.zoom_level /= 1.1
        self.grid.zoom_level = max(0.1, self.grid.zoom_level)
        self.grid.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_H:
            if self.current_mode == "add_storage":
                self.current_storage_orientation = "H"
                self.grid.set_mode("add_storage", "H")
                QMessageBox.information(self, "Orientation", "Storage set to Horizontal")
            elif self.current_mode == "add_miner":
                self.current_miner_orientation = "H"
                self.grid.set_mode("add_miner", "H")
                QMessageBox.information(self, "Orientation", "Miner set to Horizontal")
        elif event.key() == Qt.Key.Key_V:
            if self.current_mode == "add_storage":
                self.current_storage_orientation = "V"
                self.grid.set_mode("add_storage", "V")
                QMessageBox.information(self, "Orientation", "Storage set to Vertical")
            elif self.current_mode == "add_miner":
                self.current_miner_orientation = "V"
                self.grid.set_mode("add_miner", "V")
                QMessageBox.information(self, "Orientation", "Miner set to Vertical")

    def mousePressEvent(self, event):
        """Handle window dragging."""
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """Handle window dragging."""
        delta = event.globalPosition().toPoint() - self.oldPos
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()

    def create_menu_bar(self):
        """Create the menu bar with various options."""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #2a2a2a;
                color: #00FFFF;
                font-size: 11px;
            }
            QMenuBar::item:selected {
                background-color: #FF00FF;
            }
            QMenu {
                background-color: #2a2a2a;
                color: #00FFFF;
                border: 1px solid #FF00FF;
                font-size: 11px;
            }
            QMenu::item:selected {
                background-color: #FF00FF;
            }
        """
        )
        
        # File menu
        file_menu = menubar.addMenu("File")
        new_chat_action = QAction("New Chat", self)
        new_chat_action.triggered.connect(self.clear_chat)
        file_menu.addAction(new_chat_action)
        save_chat_action = QAction("Save Chat", self)
        save_chat_action.triggered.connect(self.save_chat)
        file_menu.addAction(save_chat_action)
        load_chat_action = QAction("Load Chat", self)
        load_chat_action.triggered.connect(self.load_chat)
        file_menu.addAction(load_chat_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        calculator_action = QAction("Production Calculator", self)
        calculator_action.triggered.connect(self.show_calculator)
        tools_menu.addAction(calculator_action)
        quick_ref_action = QAction("Quick Reference", self)
        quick_ref_action.triggered.connect(self.show_quick_reference)
        tools_menu.addAction(quick_ref_action)
        power_grid_action = QAction("Power Grid Simulator", self)
        power_grid_action.triggered.connect(self.show_power_grid_simulator)
        tools_menu.addAction(power_grid_action)
        # New tools
        layout_planner_action = QAction("Factory Layout Planner", self)
        layout_planner_action.triggered.connect(self.show_factory_layout_planner)
        tools_menu.addAction(layout_planner_action)
        prod_chain_action = QAction("Production Chain Visualizer", self)
        prod_chain_action.triggered.connect(self.show_production_chain_visualizer)
        tools_menu.addAction(prod_chain_action)
        route_optimizer_action = QAction("Train/Truck Route Optimizer", self)
        route_optimizer_action.triggered.connect(self.show_route_optimizer)
        tools_menu.addAction(route_optimizer_action)
        storage_calc_action = QAction("Inventory/Storage Calculator", self)
        storage_calc_action.triggered.connect(self.show_storage_calculator)
        tools_menu.addAction(storage_calc_action)
        perf_monitor_action = QAction("Performance Monitor", self)
        perf_monitor_action.triggered.connect(self.show_performance_monitor)
        tools_menu.addAction(perf_monitor_action)
        
        # Settings menu
        settings_menu = menubar.addMenu("Settings")
        theme_menu = settings_menu.addMenu("Theme")
        dark_theme_action = QAction("Dark Theme", self)
        dark_theme_action.triggered.connect(lambda: self.change_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        light_theme_action = QAction("Light Theme", self)
        light_theme_action.triggered.connect(lambda: self.change_theme("light"))
        theme_menu.addAction(light_theme_action)
        # New settings
        custom_theme_action = QAction("Custom Theme...", self)
        custom_theme_action.triggered.connect(self.show_custom_theme_dialog)
        settings_menu.addAction(custom_theme_action)
        font_size_action = QAction("Font Size/Style...", self)
        font_size_action.triggered.connect(self.show_font_settings_dialog)
        settings_menu.addAction(font_size_action)
        compact_ui_action = QAction("Compact/Expanded UI", self)
        compact_ui_action.triggered.connect(self.toggle_compact_ui)
        settings_menu.addAction(compact_ui_action)
        sound_effects_action = QAction("Sound Effects", self)
        sound_effects_action.triggered.connect(self.toggle_sound_effects)
        settings_menu.addAction(sound_effects_action)
        startup_tool_action = QAction("Startup Tool...", self)
        startup_tool_action.triggered.connect(self.show_startup_tool_dialog)
        settings_menu.addAction(startup_tool_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        tips_action = QAction("Random Tips", self)
        tips_action.triggered.connect(self.show_random_tip)
        help_menu.addAction(tips_action)
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def clear_chat(self):
        """Clear the chat history and display."""
        self.chat_display.clear()
        self.conversation_context = []
        self.chat_history.clear_history()
        self.start_typing_animation("Chat cleared. How can I help you today, Pioneer?") # Keeping typing animation for chat

    def save_chat(self):
        """Save the current chat to a file."""
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Save Chat",
            f"satisfactory_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )
        
        if file_name:
            try:
                # Get chat history
                chat_data = {
                    "timestamp": datetime.now().isoformat(),
                    "messages": self.chat_history.get_all_messages()
                }
                
                # Save to file
                with open(file_name, 'w') as f:
                    json.dump(chat_data, f, indent=2)
                
                self.statusBar.showMessage("Chat history saved successfully, Pioneer!", 3000)
            except Exception as e:
                self.statusBar.showMessage(f"Failed to save chat: {str(e)}", 5000)
    
    def load_chat(self):
        """Load a chat from a file."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Load Chat",
            "",
            "JSON Files (*.json)"
        )
        
        if file_name:
            try:
                # Load from file
                with open(file_name, 'r') as f:
                    chat_data = json.load(f)
                
                # Clear current chat
                self.chat_display.clear()
                self.conversation_context = []
                
                # Load messages
                for message in chat_data["messages"]:
                    self.add_user_message(message["user"])
                    self.chat_display.append(f"<p style='color: #00FFFF;'><b>SAM:</b> {message['assistant']}</p>")
                    self.conversation_context.append({"role": "user", "content": message["user"]})
                    self.conversation_context.append({"role": "assistant", "content": message["assistant"]})
                
                self.statusBar.showMessage("Chat history loaded successfully, Pioneer!", 3000)
            except Exception as e:
                self.statusBar.showMessage(f"Failed to load chat: {str(e)}", 5000)
    
    def show_calculator(self):
        """Show the production calculator window."""
        calculator = ProductionCalculator(self)
        calculator.exec()
        
    def show_quick_reference(self):
        """Show the quick reference window."""
        quick_ref = QuickReference(self)
        quick_ref.exec()
    
    def change_theme(self, theme):
        """Change the application theme."""
        if theme == "dark":
            self.set_dark_theme()
        else:
            self.set_light_theme()
    
    def set_dark_theme(self):
        """Set the dark theme."""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #23243a,
                    stop: 0.5 #2a2a2a,
                    stop: 1 #00FFFF
                );
            }
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #23243a,
                    stop: 0.5 #2a2a2a,
                    stop: 1 #00FFFF
                );
                color: #00FFFF;
            }
            QTextEdit {
                background-color: #1a1a1a;
                color: #00FFFF;
                border: 3px solid;
                border-image: linear-gradient(45deg, #FFFF00, #FF00FF, #FFFF00) 1;
                border-radius: 8px;
                padding: 10px;
                font-size: 11px;
            }
            QLineEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 3px solid;
                border-image: linear-gradient(45deg, #FFFF00, #FF00FF, #FFFF00) 1;
                border-radius: 8px;
                padding: 8px;
                font-size: 11px;
            }
            QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #00FFFF,
                    stop: 0.5 #00CCCC,
                    stop: 1 #00FFFF
                );
                color: #000000;
                border: 2px solid #FF00FF;
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #33FFFF,
                    stop: 0.5 #00FFFF,
                    stop: 1 #33FFFF
                );
                border: 2px solid #FF33FF;
            }
            QMenuBar {
                background-color: #2a2a2a;
                color: #00FFFF;
                font-size: 11px;
            }
            QMenuBar::item:selected {
                background-color: #FF00FF;
            }
            QMenu {
                background-color: #2a2a2a;
                color: #00FFFF;
                border: 1px solid #FF00FF;
                font-size: 11px;
            }
            QMenu::item:selected {
                background-color: #FF00FF;
            }
            QStatusBar {
                background-color: #2a2a2a; /* Match menu bar */
                color: #00FFFF;
            }
        """)
    
    def set_light_theme(self):
        """Set the light theme."""
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #fffbe6,
                    stop: 0.5 #ffffff,
                    stop: 1 #FFD700
                );
            }
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #fffbe6,
                    stop: 0.5 #ffffff,
                    stop: 1 #FFD700
                );
                color: #000000;
            }
            QTextEdit {
                background-color: #1a1a1a;
                color: #00FFFF;
                border: 3px solid;
                border-image: linear-gradient(45deg, #FFD700, #FFA500, #FFD700) 1;
                border-radius: 8px;
                padding: 10px;
                font-size: 11px;
            }
            QLineEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 3px solid;
                border-image: linear-gradient(45deg, #FFD700, #FFA500, #FFD700) 1;
                border-radius: 8px;
                padding: 8px;
                font-size: 11px;
            }
            QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #FFD700,
                    stop: 0.5 #FFA500,
                    stop: 1 #FFD700
                );
                color: #000000;
                border: 2px solid #FFA500;
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #FFE44D,
                    stop: 0.5 #FFD700,
                    stop: 1 #FFE44D
                );
                border: 2px solid #FFB700;
            }
            QMenuBar {
                background-color: #ffffff;
                color: #000000;
                font-size: 11px;
            }
            QMenuBar::item:selected {
                background-color: #FFD700;
            }
            QMenu {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #FFA500;
                font-size: 11px;
            }
            QMenu::item:selected {
                background-color: #FFD700;
            }
            QStatusBar {
                background-color: #ffffff; /* Match menu bar */
                color: #000000;
            }
        """)
        
        # Update text colors in chat display
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00FFFF;
                border: 3px solid;
                border-image: linear-gradient(45deg, #FFD700, #FFA500, #FFD700) 1;
                border-radius: 8px;
                padding: 10px;
                font-size: 11px;
            }
        """)

    def show_random_tip(self):
        """Show a random Satisfactory tip."""
        tips = [
            "Use foundations to create a flat building surface.",
            "Power poles can be connected to machines automatically.",
            "Use the 'Z' key to toggle between build modes.",
            "Conveyor belts can be stacked using conveyor lifts.",
            "Use the 'R' key to rotate buildings while placing them.",
            "Hold Ctrl while placing to snap to grid.",
            "Build vertically to save space.",
            "Use wall mounts for power connections.",
            "Create a central storage area for resources.",
            "Use the map to plan your factory layout.",
            "Upgrade your HUB early to unlock more buildings and recipes.",
            "Use lookout towers to scout your surroundings.",
            "Automate biomass production for early-game power.",
            "Use splitters and mergers to balance conveyor belt loads.",
            "Stack conveyor belts to save space and reduce clutter.",
            "Use smart and programmable splitters for advanced logistics.",
            "Build on cliffs to maximize vertical space.",
            "Use hypertubes for fast travel across your factory.",
            "Place beacons to mark important locations.",
            "Use the object scanner to find resources and slugs.",
            "Upgrade miners and smelters to increase efficiency.",
            "Use foundations to align machinery perfectly.",
            "Keep a supply of healing items for exploring dangerous areas.",
            "Automate the production of reinforced iron plates and rotors early.",
            "Use the chainsaw to clear large areas of foliage quickly.",
            "Build walkways and ladders for easy access to tall structures.",
            "Use the MAM to research new technologies and upgrades.",
            "Plan your factory layout before expanding.",
            "Use the awesome sink to get rid of excess items and earn coupons.",
            "Build multiple power grids for redundancy.",
            "Use color gun to organize and color-code your factory.",
            "Upgrade belts and lifts as soon as possible to avoid bottlenecks.",
            "Use the map to set custom markers and plan routes.",
            "Keep an eye on power consumption to avoid blackouts.",
            "Use the hover pack for easy building and exploration.",
            "Automate the production of modular frames and computers for late-game needs.",
            "Explore caves and hidden areas for hard drives and slugs.",
            "Use the tractor and truck for early-game resource transport.",
            "Build refineries near oil nodes to minimize transport distance.",
            "Use the zipline for quick movement along power lines.",
            "Keep your inventory organized for efficient building.",
            "Use the radar tower to reveal more of the map.",
            "Upgrade your equipment regularly for better survivability.",
            "Use the Nobelisk detonator to clear boulders and access new areas.",
            "Build factories in modules for easier expansion and upgrades.",
            "Use the train system for large-scale resource transport.",
            "Experiment with alternate recipes for more efficient production.",
            "Keep a supply of fuel and coal for vehicles and generators.",
            "Use the jetpack for vertical construction and exploration.",
            "Always have a backup save before making major changes."
        ]
        import random
        tip = random.choice(tips)
        self.start_typing_animation(f"Tip: {tip}")

    def show_about(self):
        """Show the about dialog."""
        about_text = """
        <h2>SAM - FICSIT Technical Support</h2>
        <p>Version 1.0</p>
        <p>A Satisfactory-themed AI assistant to help you optimize your factory building experience.</p>
        <br>
        <p><b>Features:</b></p>
        <ul>
            <li>AI-powered technical support</li>
            <li>Production calculator</li>
            <li>Quick reference guide</li>
            <li>Chat history management</li>
            <li>Dark and light themes</li>
        </ul>
        <br>
        <p><i>"Efficiency First!"</i></p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("About SAM")
        msg.setText(about_text)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #2a2a2a;
                color: #00FFFF;
            }
            QLabel {
                color: #00FFFF;
                min-width: 400px;
                font-size: 11px;
            }
            QPushButton {
                background-color: #FF00FF;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #FF33FF;
            }
        """)
        msg.exec()

    def show_power_grid_simulator(self):
        """Show the power grid simulator window."""
        simulator = PowerGridSimulator(self)
        simulator.exec()

    # Tool stubs
    def show_factory_layout_planner(self):
        dlg = FactoryLayoutPlanner(self)
        dlg.exec()
    def show_production_chain_visualizer(self):
        dlg = ProductionChainVisualizer(self)
        dlg.exec()
    def show_route_optimizer(self):
        dlg = RouteOptimizer(self)
        dlg.exec()
    def show_storage_calculator(self):
        dlg = StorageCalculator(self)
        dlg.exec()
    def show_performance_monitor(self):
        dlg = PerformanceMonitor(self)
        dlg.exec()
    # Settings stubs
    def show_custom_theme_dialog(self):
        """Show a dialog for custom theme settings."""
        dlg = CustomThemeDialog(self)
        dlg.exec()
    def show_font_settings_dialog(self):
        """Show a dialog for font size and style settings."""
        dlg = FontSettingsDialog(self)
        dlg.exec()
    def toggle_compact_ui(self):
        """Toggle between compact and expanded UI modes."""
        if self.width() == 400 and self.height() == 600:
            # Currently compact, expand it
            self.setFixedSize(600, 800)
        else:
            # Currently expanded, make it compact
            self.setFixedSize(400, 600)
        self.statusBar.showMessage("UI size toggled.", 3000)
    def toggle_sound_effects(self):
        """Toggle sound effects on or off."""
        self.sound_effects_enabled = not self.sound_effects_enabled
        status = "enabled" if self.sound_effects_enabled else "disabled"
        self.statusBar.showMessage(f"UI sound effects are now {status}.", 3000)
    def show_startup_tool_dialog(self):
        """Show a dialog for selecting the startup tool."""
        dlg = StartupToolDialog(self)
        dlg.exec()

    def set_custom_theme(self, bg_color: QColor, text_color: QColor, accent_color: QColor, gradient_type: str):
        """Set a custom theme based on provided colors and gradient type."""
        self.custom_bg_color = bg_color
        self.custom_text_color = text_color
        self.custom_accent_color = accent_color
        self.custom_gradient_type = gradient_type

        # Determine gradient stops based on type
        gradient_stops_bg = f"stop: 0 {bg_color.name()}, stop: 0.5 {bg_color.darker(150).name()}, stop: 1 {accent_color.name()}"
        gradient_stops_accent = f"stop: 0 {accent_color.name()}, stop: 0.5 {accent_color.darker(150).name()}, stop: 1 {accent_color.name()}"

        if gradient_type == "Linear":
            gradient_str_bg = f"qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, {gradient_stops_bg})"
            gradient_str_accent = f"qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, {gradient_stops_accent})"
        elif gradient_type == "Radial":
            gradient_str_bg = f"qradialgradient(cx: 0.5, cy: 0.5, radius: 0.7, {gradient_stops_bg})"
            gradient_str_accent = f"qradialgradient(cx: 0.5, cy: 0.5, radius: 0.7, {gradient_stops_accent})"
        elif gradient_type == "Conical":
            gradient_str_bg = f"qconicalgradient(cx: 0.5, cy: 0.5, angle: 90, {gradient_stops_bg})"
            gradient_str_accent = f"qconicalgradient(cx: 0.5, cy: 0.5, angle: 90, {gradient_stops_accent})"
        else:
            # Default to solid color if unknown gradient type
            gradient_str_bg = bg_color.name()
            gradient_str_accent = accent_color.name()

        self.setStyleSheet(f"""
            QMainWindow {{
                background: {gradient_str_bg};
            }}
            QWidget {{
                background: {gradient_str_bg};
                color: {text_color.name()};
            }}
            QTextEdit {{
                background-color: #1a1a1a;
                color: {text_color.name()};
                border: 3px solid;
                border-image: linear-gradient(45deg, {accent_color.name()}, {accent_color.darker(150).name()}, {accent_color.name()}) 1;
                border-radius: 8px;
                padding: 10px;
                font-size: 11px;
            }}
            QLineEdit {{
                background-color: #1a1a1a;
                color: {text_color.name()};
                border: 3px solid;
                border-image: linear-gradient(45deg, {accent_color.name()}, {accent_color.darker(150).name()}, {accent_color.name()}) 1;
                border-radius: 8px;
                padding: 8px;
                font-size: 11px;
            }}
            QPushButton {{
                background: {gradient_str_accent};
                color: {bg_color.name()}; /* Button text color contrast to accent */
                border: 2px solid {accent_color.darker(150).name()};
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {accent_color.lighter(150).name()};
                border: 2px solid {accent_color.name()};
            }}
            QMenuBar {{
                background-color: {bg_color.darker(150).name()};
                color: {text_color.name()};
                font-size: 11px;
            }}
            QMenuBar::item:selected {{
                background-color: {accent_color.name()};
            }}
            QMenu {{
                background-color: {bg_color.darker(150).name()};
                color: {text_color.name()};
                border: 1px solid {accent_color.name()};
                font-size: 11px;
            }}
            QMenu::item:selected {{
                background-color: {accent_color.name()};
            }}
            QComboBox, QSpinBox, QDoubleSpinBox {{
                background-color: {bg_color.darker(120).name()};
                color: {text_color.name()};
                border: 1px solid {accent_color.name()};
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {bg_color.darker(120).name()};
                color: {text_color.name()};
                selection-background-color: {accent_color.name()};
                selection-color: {text_color.name()};
            }}
            QMessageBox {{
                background-color: {bg_color.name()};
                color: {text_color.name()};
            }}
            QMessageBox QLabel {{
                color: {text_color.name()};
            }}
            QStatusBar {{
                background-color: {bg_color.darker(120).name()};
                color: {text_color.name()};
            }}
        """
        )

        # Update specific widget stylesheets that might be overridden
        self.chat_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: #1a1a1a;
                color: {text_color.name()};
                border: 3px solid;
                border-image: linear-gradient(45deg, {accent_color.name()}, {accent_color.darker(150).name()}, {accent_color.name()}) 1;
                border-radius: 8px;
                padding: 10px;
                font-size: 11px;
            }}
        """
        )

        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: #1a1a1a;
                color: {text_color.name()};
                border: 3px solid;
                border-image: linear-gradient(45deg, {accent_color.name()}, {accent_color.darker(150).name()}, {accent_color.name()}) 1;
                border-radius: 8px;
                padding: 8px;
                font-size: 11px;
            }}
        """
        )

        # Update info panel as well
        info_panel = self.centralWidget().findChild(QLabel)
        if info_panel:
            info_panel.setStyleSheet(f"""
                QLabel {{
                    background-color: {bg_color.darker(120).name()};
                    color: {text_color.name()};
                    border: 2px solid {accent_color.name()};
                    border-radius: 8px;
                    padding: 8px;
                    font-family: 'Arial', sans-serif;
                    min-width: 130px;
                    max-width: 130px;
                    font-size: 11px;
                }}
            """
            )

    def set_application_font(self, font_family: str, font_size: int):
        """Set the application-wide font and apply to relevant widgets."""
        new_font = QFont(font_family, font_size)
        QApplication.instance().setFont(new_font)

        # Apply font to chat display and input field explicitly, as stylesheets might override
        self.chat_display.setFont(new_font)
        self.input_field.setFont(new_font)

        # Update info panel font
        info_panel = self.centralWidget().findChild(QLabel)
        if info_panel:
            info_panel.setFont(new_font)

    def export_layout(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Layout", os.path.join(LAYOUT_DIR, "factory_layout.json"), "JSON Files (*.json)"
        )
        if file_name:
            try:
                serializable_blocks = []
                for block_data in self.grid.blocks:
                    comp_type, x, y, color, *extra = block_data
                    serializable_color = {"r": color.red(), "g": color.green(), "b": color.blue()}

                    if comp_type == "conveyor":
                        p1, p2 = extra[0]
                        serializable_p1 = {"x": p1.x(), "y": p1.y()}
                        serializable_p2 = {"x": p2.x(), "y": p2.y()}
                        serializable_block = [comp_type, x, y, serializable_color, (serializable_p1, serializable_p2)]
                    elif comp_type == "storage" or comp_type == "miner":
                        # If orientation exists, it's the first element in extra
                        orientation = extra[0] if extra else "H" # Default to H for old saves
                        serializable_block = [comp_type, x, y, serializable_color, orientation]
                    elif comp_type == "text":
                        text_content = extra[0]
                        serializable_block = [comp_type, x, y, serializable_color, text_content]
                    else:
                        serializable_block = [comp_type, x, y, serializable_color]
                    serializable_blocks.append(serializable_block)

                with open(file_name, 'w') as f:
                    json.dump(serializable_blocks, f, indent=2)
                self.statusBar.showMessage("Factory layout saved successfully!", 3000)
            except Exception as e:
                self.statusBar.showMessage(f"Failed to save layout: {e}", 5000)

    def import_layout(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Load Layout", LAYOUT_DIR, "JSON Files (*.json)"
        )
        if file_name:
            try:
                # Load from file
                with open(file_name, 'r') as f:
                    chat_data = json.load(f)
                
                # Clear current chat
                self.chat_display.clear()
                self.conversation_context = []
                
                # Load messages
                for message in chat_data["messages"]:
                    self.add_user_message(message["user"])
                    self.chat_display.append(f"<p style='color: #00FFFF;'><b>SAM:</b> {message['assistant']}</p>")
                    self.conversation_context.append({"role": "user", "content": message["user"]})
                    self.conversation_context.append({"role": "assistant", "content": message["assistant"]})
                
                self.statusBar.showMessage("Chat history loaded successfully, Pioneer!", 3000)
            except Exception as e:
                self.statusBar.showMessage(f"Failed to load chat: {str(e)}", 5000)
    
    def set_conveyor_arrow_style(self, index):
        arrow_styles = ["None", ">", "<", "^", "v"]
        selected_style = arrow_styles[index]
        self.grid.set_arrow_style(selected_style)

    def zoom_out(self):
        self.grid.zoom_level /= 1.1
        self.grid.zoom_level = max(0.1, self.grid.zoom_level)
        self.grid.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_H:
            if self.current_mode == "add_storage":
                self.current_storage_orientation = "H"
                self.grid.set_mode("add_storage", "H")
                QMessageBox.information(self, "Orientation", "Storage set to Horizontal")
            elif self.current_mode == "add_miner":
                self.current_miner_orientation = "H"
                self.grid.set_mode("add_miner", "H")
                QMessageBox.information(self, "Orientation", "Miner set to Horizontal")
        elif event.key() == Qt.Key.Key_V:
            if self.current_mode == "add_storage":
                self.current_storage_orientation = "V"
                self.grid.set_mode("add_storage", "V")
                QMessageBox.information(self, "Orientation", "Storage set to Vertical")
            elif self.current_mode == "add_miner":
                self.current_miner_orientation = "V"
                self.grid.set_mode("add_miner", "V")
                QMessageBox.information(self, "Orientation", "Miner set to Vertical")


class ProductionCalculator(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Production Calculator")
        self.setFixedSize(400, 500)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setStyleSheet("""
            QDialog {
                background-color: #2a2a2a;
                color: #00FFFF;
            }
            QLabel {
                color: #00FFFF;
                font-size: 13px;
                font-weight: bold;
            }
            QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #232323;
                color: #FFFFFF;
                border: 1px solid #FF00FF;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #232323;
                color: #FFFFFF;
                selection-background-color: #FF00FF;
                selection-color: #FFFFFF;
            }
            QPushButton {
                background-color: #FF00FF;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #FF33FF;
            }
        """)
        layout = QVBoxLayout(self)
        # Recipe selection
        recipe_label = QLabel("Select Recipe:")
        self.recipe_combo = QComboBox()
        self.recipe_combo.addItems([
            "Iron Plate",
            "Iron Rod",
            "Screw",
            "Reinforced Iron Plate",
            "Modular Frame",
            "Steel Beam",
            "Steel Pipe",
            "Encased Industrial Beam",
            "Heavy Modular Frame"
        ])
        # Input rate
        input_label = QLabel("Desired Output Rate (per minute):")
        self.input_rate = QDoubleSpinBox()
        self.input_rate.setRange(0, 1000)
        self.input_rate.setValue(60)
        self.input_rate.setSuffix(" /min")
        # Calculate button
        calculate_btn = QPushButton("Calculate")
        calculate_btn.clicked.connect(self.calculate)
        # Results display
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        layout.addWidget(recipe_label)
        layout.addWidget(self.recipe_combo)
        layout.addWidget(input_label)
        layout.addWidget(self.input_rate)
        layout.addWidget(calculate_btn)
        layout.addWidget(self.results_display)
    def calculate(self):
        recipe = self.recipe_combo.currentText()
        target_rate = self.input_rate.value()
        # Recipe data (simplified for example)
        recipes = {
            "Iron Plate": {"input": {"Iron Ore": 30}, "output": 20, "time": 6},
            "Iron Rod": {"input": {"Iron Ore": 15}, "output": 15, "time": 4},
            "Screw": {"input": {"Iron Rod": 10}, "output": 40, "time": 6},
            "Reinforced Iron Plate": {"input": {"Iron Plate": 30, "Screw": 60}, "output": 5, "time": 12},
            "Modular Frame": {"input": {"Reinforced Iron Plate": 3, "Iron Rod": 12}, "output": 2, "time": 15},
            "Steel Beam": {"input": {"Steel Ingot": 60}, "output": 15, "time": 4},
            "Steel Pipe": {"input": {"Steel Ingot": 30}, "output": 20, "time": 6},
            "Encased Industrial Beam": {"input": {"Steel Beam": 24, "Concrete": 30}, "output": 6, "time": 10},
            "Heavy Modular Frame": {"input": {"Modular Frame": 10, "Steel Pipe": 30, "Encased Industrial Beam": 10, "Screw": 200}, "output": 2, "time": 30}
        }
        if recipe in recipes:
            recipe_data = recipes[recipe]
            machines_needed = target_rate / (recipe_data["output"] * (60 / recipe_data["time"]))
            machines_needed = round(machines_needed, 2)
            # Calculate input requirements
            input_requirements = {}
            for item, amount in recipe_data["input"].items():
                input_requirements[item] = amount * machines_needed * (60 / recipe_data["time"])
            # Display results
            result_text = f"Recipe: {recipe}\n"
            result_text += f"Target Output: {target_rate} /min\n"
            result_text += f"Machines Needed: {machines_needed}\n\n"
            result_text += "Input Requirements:\n"
            for item, amount in input_requirements.items():
                result_text += f"{item}: {amount:.2f} /min\n"
            self.results_display.setText(result_text)

class QuickReference(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Reference")
        self.setFixedSize(600, 800)
        self.setStyleSheet("""
            QDialog {
                background-color: #2a2a2a;
                color: #00FFFF;
            }
            QLabel {
                color: #00FFFF;
            }
            QScrollArea {
                border: none;
            }
            QFrame {
                background-color: #3a3a3a;
                border: 1px solid #FF00FF;
                border-radius: 5px;
                margin: 5px;
            }
        """)
        layout = QVBoxLayout(self)
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        # Add sections
        self.add_tier_section(scroll_layout)
        self.add_keybinds_section(scroll_layout)
        self.add_tips_section(scroll_layout)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
    def add_tier_section(self, layout):
        frame = QFrame()
        frame_layout = QVBoxLayout(frame)
        title = QLabel("Tier Progression")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        frame_layout.addWidget(title)
        tiers = [
            ("Tier 0", "Basic building and crafting"),
            ("Tier 1", "Basic automation, Iron production"),
            ("Tier 2", "Advanced automation, Steel production"),
            ("Tier 3", "Coal power, Advanced steel production"),
            ("Tier 4", "Oil processing, Computers"),
            ("Tier 5", "Advanced oil processing, Heavy modular frames"),
            ("Tier 6", "Nuclear power, Turbo motors"),
            ("Tier 7", "Quantum computers, Assembly director systems"),
            ("Tier 8", "Nuclear pasta, Thermal propulsion rockets")
        ]
        for tier, desc in tiers:
            tier_label = QLabel(f"{tier}: {desc}")
            frame_layout.addWidget(tier_label)
        layout.addWidget(frame)
    def add_keybinds_section(self, layout):
        frame = QFrame()
        frame_layout = QVBoxLayout(frame)
        title = QLabel("Keybinds")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        frame_layout.addWidget(title)
        keybinds = [
            ("WASD", "Move"),
            ("Space", "Jump"),
            ("Shift", "Sprint"),
            ("Ctrl", "Crouch"),
            ("E", "Interact"),
            ("Q", "Drop item"),
            ("R", "Rotate building"),
            ("Z", "Toggle build mode"),
            ("X", "Dismantle"),
            ("F", "Flashlight"),
            ("Tab", "Inventory"),
            ("M", "Map"),
            ("P", "Photo mode")
        ]
        for key, action in keybinds:
            keybind_label = QLabel(f"{key}: {action}")
            frame_layout.addWidget(keybind_label)
        layout.addWidget(frame)
    def add_tips_section(self, layout):
        frame = QFrame()
        frame_layout = QVBoxLayout(frame)
        title = QLabel("Building Tips")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        frame_layout.addWidget(title)
        tips = [
            "Use foundations to create a flat building surface",
            "Power poles can be connected to machines automatically",
            "Conveyor belts can be stacked using conveyor lifts",
            "Use the 'R' key to rotate buildings while placing them",
            "Hold Ctrl while placing to snap to grid",
            "Use the 'Z' key to toggle between build modes",
            "Build vertically to save space",
            "Use wall mounts for power connections",
            "Create a central storage area for resources",
            "Use the map to plan your factory layout"
        ]
        for tip in tips:
            tip_label = QLabel(f"• {tip}")
            frame_layout.addWidget(tip_label)
        layout.addWidget(frame)

class PowerGridCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.power_sources = []  # List of (color, label)
        self.machines = []       # List of (color, label)
        self.warning = False
        self.setMinimumSize(400, 400)
    def set_data(self, power_sources, machines, warning):
        self.power_sources = power_sources
        self.machines = machines
        self.warning = warning
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        margin = 40
        box_size = 32
        spacing = 20
        # Draw faint grid
        grid_spacing = 40
        painter.setPen(QPen(QColor(60, 60, 80, 80), 1))
        for x in range(margin, w - margin, grid_spacing):
            painter.drawLine(x, margin, x, h - margin)
        for y in range(margin, h - margin, grid_spacing):
            painter.drawLine(margin, y, w - margin, y)
        # Draw a box around the grid area
        painter.setPen(QPen(QColor(0, 200, 255), 3))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(margin, margin, w - 2 * margin, h - 2 * margin)
        # Draw power source (left, vertically centered)
        if self.power_sources:
            src_color, src_label = self.power_sources[0]
            src_x = margin
            src_y = h // 2 - box_size // 2
            painter.setPen(QPen(Qt.GlobalColor.black, 3))
            painter.setBrush(QBrush(src_color))
            painter.drawRect(src_x, src_y, box_size, box_size)
        # Draw machines (right, stacked vertically)
        machine_boxes = []
        if self.machines:
            total_m = len(self.machines)
            total_height = total_m * box_size + (total_m - 1) * spacing
            start_y = h // 2 - total_height // 2
            for i, (m_color, m_label) in enumerate(self.machines):
                mx = w - margin - box_size
                my = start_y + i * (box_size + spacing)
                painter.setPen(QPen(Qt.GlobalColor.black, 3))
                painter.setBrush(QBrush(m_color))
                painter.drawRect(mx, my, box_size, box_size)
                machine_boxes.append((mx, my))
        # Draw lines
        if self.power_sources and machine_boxes:
            # Horizontal bus line
            src_center_y = h // 2
            bus_start_x = margin + box_size
            bus_end_x = w - margin - box_size
            pen_color = Qt.GlobalColor.red if self.warning else QColor(0, 170, 255)
            painter.setPen(QPen(pen_color, 4))
            painter.drawLine(bus_start_x, src_center_y, bus_end_x, src_center_y)
            # Vertical lines to each machine
            for mx, my in machine_boxes:
                painter.drawLine(mx, src_center_y, mx, my + box_size // 2)

class PowerGridSimulator(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Power Grid Simulator")
        self.setMinimumSize(800, 600)
        
        # Initialize data
        self.power_sources = []
        self.machines = []
        
        # Create main layout
        layout = QVBoxLayout()
        
        # Create controls
        controls_layout = QHBoxLayout()
        
        # Power sources controls
        power_sources_group = QGroupBox("Power Sources")
        power_sources_layout = QVBoxLayout()
        
        self.power_sources_combo = QComboBox()
        self.power_sources_combo.addItems([
            "Biomass Burner",
            "Coal Generator",
            "Fuel Generator",
            "Geothermal Generator",
            "Nuclear Power Plant"
        ])
        power_sources_layout.addWidget(self.power_sources_combo)
        
        self.power_sources_count = QSpinBox()
        self.power_sources_count.setRange(1, 100)
        self.power_sources_count.setValue(1)
        power_sources_layout.addWidget(self.power_sources_count)
        
        add_power_btn = QPushButton("Add Power Source")
        add_power_btn.clicked.connect(self.add_power_source)
        power_sources_layout.addWidget(add_power_btn)
        
        power_sources_group.setLayout(power_sources_layout)
        controls_layout.addWidget(power_sources_group)
        
        # Machines controls
        machines_group = QGroupBox("Machines")
        machines_layout = QVBoxLayout()
        
        self.machines_combo = QComboBox()
        self.machines_combo.addItems([
            "Miner",
            "Constructor",
            "Assembler",
            "Manufacturer",
            "Blender",
            "Refinery",
            "Packager",
            "Smelter",
            "Foundry",
            "Particle Accelerator",
            "Awesome Sink",
            "Freight Platform",
            "Truck Station",
            "Train Station",
            "Electric Locomotive",
            "Radar Tower",
            "Power Pole",
            "Power Line",
            "Power Switch",
            "Power Storage",
            "Conveyor Belt",
            "Conveyor Lift",
            "Pipeline",
            "Buffer",
            "Railway Track",
            "Space Elevator",
            "HUB",
            "Workbench",
            "MAM",
            "AWESOME Shop"
        ])
        machines_layout.addWidget(self.machines_combo)
        
        self.machines_count = QSpinBox()
        self.machines_count.setRange(1, 100)
        self.machines_count.setValue(1)
        machines_layout.addWidget(self.machines_count)
        
        add_machine_btn = QPushButton("Add Machine")
        add_machine_btn.clicked.connect(self.add_machine)
        machines_layout.addWidget(add_machine_btn)
        
        machines_group.setLayout(machines_layout)
        controls_layout.addWidget(machines_group)
        
        layout.addLayout(controls_layout)
        
        # Create grid canvas
        self.grid_canvas = PowerGridCanvas()
        layout.addWidget(self.grid_canvas)
        
        # Create results display
        self.results_label = QLabel()
        layout.addWidget(self.results_label)
        
        # Create reset button
        reset_btn = QPushButton("Reset Grid")
        reset_btn.clicked.connect(self.reset_grid)
        layout.addWidget(reset_btn)
        
        self.setLayout(layout)
        self.update_results()

    def add_power_source(self):
        source = self.power_sources_combo.currentText()
        count = self.power_sources_count.value()
        color = self.get_power_source_color(source)
        for _ in range(count):
            self.power_sources.append((color, source))
        self.update_grid()
        self.update_results()

    def add_machine(self):
        machine = self.machines_combo.currentText()
        count = self.machines_count.value()
        color = self.get_machine_color(machine)
        for _ in range(count):
            self.machines.append((color, machine))
        self.update_grid()
        self.update_results()

    def get_power_source_color(self, source):
        """Get the color for a power source."""
        colors = {
            "Biomass Burner": QColor(139, 69, 19),  # Brown
            "Coal Generator": QColor(128, 128, 128),  # Gray
            "Fuel Generator": QColor(255, 165, 0),  # Orange
            "Geothermal Generator": QColor(0, 255, 0),  # Green
            "Nuclear Power Plant": QColor(0, 0, 255)  # Blue
        }
        return colors.get(source, QColor(128, 128, 128))  # Default gray

    def get_machine_color(self, machine):
        """Get the color for a machine."""
        colors = {
            "Miner": QColor(192, 192, 192),  # Silver
            "Constructor": QColor(255, 255, 0),  # Yellow
            "Assembler": QColor(70, 130, 180),  # Metallic Blue
            "Manufacturer": QColor(255, 0, 0),  # Red
            "Blender": QColor(128, 0, 128),  # Purple
            "Refinery": QColor(0, 255, 255),  # Cyan
            "Packager": QColor(0, 255, 0),  # Green
            "Smelter": QColor(255, 140, 0),  # Dark Orange
            "Foundry": QColor(165, 42, 42),  # Brown
            "Particle Accelerator": QColor(255, 0, 255),  # Magenta
            "Awesome Sink": QColor(128, 128, 128),  # Gray
            "Freight Platform": QColor(0, 128, 128),  # Teal
            "Truck Station": QColor(0, 128, 128),  # Teal
            "Train Station": QColor(0, 128, 128),  # Teal
            "Electric Locomotive": QColor(0, 128, 128),  # Teal
            "Radar Tower": QColor(255, 255, 255),  # White
            "Power Pole": QColor(192, 192, 192),  # Silver
            "Power Line": QColor(192, 192, 192),  # Silver
            "Power Switch": QColor(192, 192, 192),  # Silver
            "Power Storage": QColor(192, 192, 192),  # Silver
            "Conveyor Belt": QColor(192, 192, 192),  # Silver
            "Conveyor Lift": QColor(192, 192, 192),  # Silver
            "Pipeline": QColor(192, 192, 192),  # Silver
            "Buffer": QColor(192, 192, 192),  # Silver
            "Railway Track": QColor(192, 192, 192),  # Silver
            "Space Elevator": QColor(255, 255, 255),  # White
            "HUB": QColor(255, 255, 255),  # White
            "Workbench": QColor(192, 192, 192),  # Silver
            "MAM": QColor(192, 192, 192),  # Silver
            "AWESOME Shop": QColor(192, 192, 192)  # Silver
        }
        return colors.get(machine, QColor(128, 128, 128))  # Default gray

    def reset_grid(self):
        self.power_sources = []
        self.machines = []
        self.update_results()
        self.update_grid()
    def update_grid(self):
        # Only show one power source visually (as in the diagram)
        src = self.power_sources[0] if self.power_sources else None
        machines = self.machines
        # Calculate warning
        total_power_production = sum(self.get_power_source_value(src[1]) for src in self.power_sources)
        total_power_consumption = sum(self.get_machine_value(m[1]) for m in self.machines)
        warning = total_power_consumption > total_power_production
        self.grid_canvas.set_data([src] if src else [], machines, warning)
    def get_power_source_value(self, source):
        """Get the power output value for a given source."""
        values = {
            "Biomass Burner": 30,  # 30 MW
            "Coal Generator": 75,  # 75 MW
            "Fuel Generator": 150,  # 150 MW
            "Geothermal Generator": 400,  # Average of 200-600 MW
            "Nuclear Power Plant": 2500  # 2500 MW
        }
        return values.get(source, 0)
    def get_machine_value(self, machine):
        """Get the power consumption value for a given machine."""
        values = {
            # Production Machines
            "Miner": 30,  # Added Miner with correct power consumption
            "Constructor": 4,
            "Assembler": 15,
            "Manufacturer": 55,
            "Blender": 75,
            "Refinery": 30,
            "Packager": 10,
            "Smelter": 4,
            "Foundry": 16,
            "Particle Accelerator": 500,
            "Awesome Sink": 30,
            
            # Logistics
            "Freight Platform": 25,
            "Truck Station": 25,
            "Train Station": 25,
            "Electric Locomotive": 25,
            
            # Special Buildings
            "Radar Tower": 30,
            
            # Power Infrastructure (0 MW)
            "Power Pole": 0,
            "Power Line": 0,
            "Power Switch": 0,
            "Power Storage": 0,
            
            # Logistics (0 MW)
            "Conveyor Belt": 0,
            "Conveyor Lift": 0,
            "Pipeline": 0,
            "Buffer": 0,
            "Railway Track": 0,
            
            # Special Buildings (0 MW)
            "Space Elevator": 0,
            "HUB": 0,
            "Workbench": 0,
            "MAM": 0,
            "AWESOME Shop": 0
        }
        return values.get(machine, 0)
    def update_results(self):
        total_power_production = sum(self.get_power_source_value(src[1]) for src in self.power_sources)
        total_power_consumption = sum(self.get_machine_value(m[1]) for m in self.machines)
        result_text = f"Total Power Production: {total_power_production} MW\n"
        result_text += f"Total Power Consumption: {total_power_consumption} MW\n"
        result_text += f"Net Power: {total_power_production - total_power_consumption} MW\n"
        if total_power_consumption > total_power_production:
            result_text += "Warning: Power consumption exceeds production!"
        self.results_label.setText(result_text)

class FactoryLayoutPlanner(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Factory Layout Planner")
        self.setFixedSize(800, 700)
        
        # Set dark theme
        self.setStyleSheet("""
    QDialog {
        background-color: #2b2b2b;
        color: #ffffff;
    }
    QPushButton {
        background-color: #FF00FF;
        color: #ffffff;
        border: 1px solid #FF00FF;
        padding: 5px;
        border-radius: 3px;
    }
    QPushButton:hover {
        background-color: #FF33FF;
    }
    QPushButton:pressed {
        background-color: #CC00CC;
    }
    QComboBox {
        background-color: #3b3b3b;
        color: #ffffff;
        border: 1px solid #555555;
        padding: 5px;
        border-radius: 3px;
    }
    QComboBox::drop-down {
        color: black;
        border: none;
    }
    QComboBox::down-arrow {
        image: none;
        border: none;
    }
    QComboBox QAbstractItemView {
        background-color: #2b2b2b;
        color: #ffffff;
        selection-background-color: #444444;
    }
    QLabel {
        color: #ffffff;
    }
    QSpinBox {
        background-color: #3b3b3b;
        color: #ffffff;
        border: 1px solid #555555;
        padding: 5px;
        border-radius: 3px;
    }
""")


        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Component selector
        self.component_selector = QComboBox()
        self.component_selector.addItem("Select Tool")
        self.component_selector.addItem("Constructor")
        self.component_selector.addItem("Assembler")
        self.component_selector.addItem("Conveyor")
        self.component_selector.addItem("Splitter")
        self.component_selector.addItem("Merger")
        self.component_selector.addItem("H Storage")
        self.component_selector.addItem("V Storage")
        self.component_selector.addItem("Smelter")
        self.component_selector.addItem("H Miner")
        self.component_selector.addItem("V Miner")
        self.component_selector.currentIndexChanged.connect(self.select_component_mode)
        
        # Grid controls
        grid_controls = QHBoxLayout()
        
        # Grid visibility toggle
        self.grid_visible_btn = QPushButton("Hide Grid")
        self.grid_visible_btn.setCheckable(True)
        self.grid_visible_btn.setChecked(True)
        self.grid_visible_btn.toggled.connect(self.toggle_grid_visibility)
        
        # Snap to grid toggle
        self.snap_to_grid_btn = QPushButton("Snap to Grid")
        self.snap_to_grid_btn.setCheckable(True)
        self.snap_to_grid_btn.setChecked(True)
        self.snap_to_grid_btn.toggled.connect(self.toggle_snap_to_grid)
        
        # Zoom controls
        zoom_in_btn = QPushButton("+")
        zoom_out_btn = QPushButton("-")
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_out_btn.clicked.connect(self.zoom_out)

        # Add all controls to toolbar
        grid_controls.addWidget(self.grid_visible_btn)
        grid_controls.addWidget(self.snap_to_grid_btn)
        grid_controls.addWidget(zoom_in_btn)
        grid_controls.addWidget(zoom_out_btn)
        
        toolbar.addWidget(self.component_selector)
        toolbar.addLayout(grid_controls)
        toolbar.addStretch()
        
        # Add existing buttons (Clear Grid)
        clear_btn = QPushButton("Clear Grid")
        clear_btn.clicked.connect(self.clear_grid)
        toolbar.addWidget(clear_btn)

        # Add Optimize button (green)
        optimize_btn = QPushButton("Optimize")
        optimize_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        optimize_btn.clicked.connect(self.optimize_layout)
        toolbar.addWidget(optimize_btn)

        # Continous convayor icon
        self.continuous_conveyor_btn = QPushButton("Continuous Conveyor: OFF")
        self.continuous_conveyor_btn.setCheckable(True)
        self.continuous_conveyor_btn.toggled.connect(self.toggle_continuous_conveyor)
        toolbar.addWidget(self.continuous_conveyor_btn)
        
        # Create a vertical layout for the bottom-right buttons
        bottom_right_layout = QVBoxLayout()
        bottom_right_layout.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight)
        bottom_right_layout.setSpacing(5)

        # Undo button with icon
        undo_btn = QPushButton('U')
        undo_btn.setIcon(QIcon('icons/undo.png')) # Assumed path
        undo_btn.setIconSize(QSize(32, 32)) # Adjust size as needed
        undo_btn.setFixedSize(40, 40) # Ensure button is square
        undo_btn.clicked.connect(self.undo)
        bottom_right_layout.addWidget(undo_btn)
        
        # Redo button with icon
        redo_btn = QPushButton('R')
        redo_btn.setIcon(QIcon('icons/redo.png')) # Assumed path
        redo_btn.setIconSize(QSize(32, 32)) # Adjust size as needed
        redo_btn.setFixedSize(40, 40) # Ensure button is square
        redo_btn.clicked.connect(self.redo)
        bottom_right_layout.addWidget(redo_btn)

        # Export button with icon
        export_btn = QPushButton('EX')
        export_btn.setIcon(QIcon('icons/export.png')) # Assumed path
        export_btn.setIconSize(QSize(32, 32)) # Adjust size as needed
        export_btn.setFixedSize(40, 40) # Ensure button is square
        export_btn.clicked.connect(self.export_layout)
        bottom_right_layout.addWidget(export_btn)

        # Import button with icon
        import_btn = QPushButton('IM')
        import_btn.setIcon(QIcon('icons/import.png')) # Assumed path
        import_btn.setIconSize(QSize(32, 32)) # Adjust size as needed
        import_btn.setFixedSize(40, 40) # Ensure button is square
        import_btn.clicked.connect(self.import_layout)
        bottom_right_layout.addWidget(import_btn)
        
        layout.addLayout(toolbar)
        
        # Initialize self.grid here
        self.grid = LayoutGridWidget()
        
        # Main content area (grid and the new button layout)
        main_content_layout = QHBoxLayout()
        main_content_layout.addWidget(self.grid, 1) # Grid takes most space
        main_content_layout.addLayout(bottom_right_layout) # Add the new button layout
        
        layout.addLayout(main_content_layout)

    def undo(self):
        self.grid.undo()

    def redo(self):
        self.grid.redo()

    def toggle_grid_visibility(self, show):
        self.grid.toggle_grid(show)
        self.grid_visible_btn.setText("Show Grid" if not show else "Hide Grid")

    def toggle_snap_to_grid(self, snap):
        self.grid.toggle_snap_to_grid(snap)

    def zoom_in(self):
        self.grid.zoom_level *= 1.1
        self.grid.zoom_level = min(5.0, self.grid.zoom_level)
        self.grid.update()

    def zoom_out(self):
        self.grid.zoom_level /= 1.1
        self.grid.zoom_level = max(0.1, self.grid.zoom_level)
        self.grid.update()

    def toggle_continuous_conveyor(self, checked):
        self.grid.set_continuous_conveyor_enabled(checked)
        if checked:
            self.continuous_conveyor_btn.setText("Continuous Conveyor: ON")
        else:
            self.continuous_conveyor_btn.setText("Continuous Conveyor: OFF")

    def clear_grid(self):
        reply = QMessageBox.question(self, 'Clear Grid', 
                                   'Are you sure you want to clear the entire grid?',
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.grid.clear_grid()

    def select_component_mode(self, index):
        selected_text = self.component_selector.currentText()
        mode_to_set = "select"
        orientation = None

        if selected_text == "Select Tool":
            mode_to_set = "select"
        elif selected_text == "Constructor":
            mode_to_set = "add_constructor"
        elif selected_text == "Assembler":
            mode_to_set = "add_assembler"
        elif selected_text == "Conveyor":
            mode_to_set = "conveyor"
        elif selected_text == "Splitter":
            mode_to_set = "add_splitter"
        elif selected_text == "Merger":
            mode_to_set = "add_merger"
        elif selected_text == "H Storage":
            mode_to_set = "add_storage"
            orientation = "H"
            self.grid.current_storage_orientation = "H"
        elif selected_text == "V Storage":
            mode_to_set = "add_storage"
            orientation = "V"
            self.grid.current_storage_orientation = "V"
        elif selected_text == "Smelter":
            mode_to_set = "add_Smelter"
        elif selected_text == "H Miner":
            mode_to_set = "add_miner"
            orientation = "H"
            self.grid.current_miner_orientation = "H"
        elif selected_text == "V Miner":
            mode_to_set = "add_miner"
            orientation = "V"
            self.grid.current_miner_orientation = "V"

        self.grid.set_mode(mode_to_set, orientation)
        self.grid.setFocus() # Set focus back to the grid after selecting a tool

    def export_layout(self):
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Layout", os.path.join(LAYOUT_DIR, "factory_layout.json"), "JSON Files (*.json)"
        )
        if file_name:
            try:
                serializable_blocks = []
                for block_data in self.grid.blocks:
                    comp_type, x, y, color, *extra = block_data
                    serializable_color = {"r": color.red(), "g": color.green(), "b": color.blue()}

                    if comp_type == "conveyor":
                        p1, p2 = extra[0]
                        serializable_p1 = {"x": p1.x(), "y": p1.y()}
                        serializable_p2 = {"x": p2.x(), "y": p2.y()}
                        serializable_block = [comp_type, x, y, serializable_color, (serializable_p1, serializable_p2)]
                    elif comp_type == "storage" or comp_type == "miner":
                        # If orientation exists, it's the first element in extra
                        orientation = extra[0] if extra else "H" # Default to H for old saves
                        serializable_block = [comp_type, x, y, serializable_color, orientation]
                    elif comp_type == "text":
                        text_content = extra[0]
                        serializable_block = [comp_type, x, y, serializable_color, text_content]
                    else:
                        serializable_block = [comp_type, x, y, serializable_color]
                    serializable_blocks.append(serializable_block)

                with open(file_name, 'w') as f:
                    json.dump(serializable_blocks, f, indent=2)
                QMessageBox.information(self, "Layout Exported", "Factory layout saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save layout: {e}")

    def import_layout(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Load Layout", LAYOUT_DIR, "JSON Files (*.json)"
        )
        if file_name:
            try:
                with open(file_name, 'r') as f:
                    data = json.load(f)
                
                loaded_blocks = []
                for block_data in data:
                    comp_type, x, y, color_dict, *extra_data = block_data
                    color = QColor(color_dict["r"], color_dict["g"], color_dict["b"])

                    if comp_type == "conveyor":
                        p1_dict, p2_dict = extra_data[0]
                        p1 = QPoint(p1_dict["x"], p1_dict["y"])
                        p2 = QPoint(p2_dict["x"], p2_dict["y"])
                        loaded_block = [comp_type, x, y, color, (p1, p2)]
                    elif comp_type == "storage" or comp_type == "miner":
                        orientation = extra_data[0] if extra_data else "H" # Default to H for old saves
                        loaded_block = [comp_type, x, y, color, orientation]
                    elif comp_type == "text":
                        text_content = extra_data[0]
                        loaded_block = [comp_type, x, y, color, text_content]
                    else:
                        loaded_block = [comp_type, x, y, color]
                    loaded_blocks.append(loaded_block)

                self.grid.blocks = loaded_blocks
                self.grid.update()
                QMessageBox.information(self, "Layout Imported", "Factory layout loaded successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load layout: {e}")

    def set_conveyor_arrow_style(self, index):
        arrow_styles = ["None", ">", "<", "^", "v"]
        selected_style = arrow_styles[index]
        self.grid.set_arrow_style(selected_style)

    def optimize_layout(self):
        QMessageBox.information(self, "Optimize Layout", "Optimization feature coming soon!")

class LayoutGridWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 600)
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.blocks = []
        self.grid_size = 40
        self.zoom_level = 1.0
        self.show_grid = True
        self.snap_to_grid = True
        self.current_mode = "select"
        self._dragging = None
        self._drag_offset = QPoint()
        self.conveyor_start_point = None
        self.current_storage_orientation = "H"
        self.current_miner_orientation = "H"
        self.arrow_style = ">"  # Set arrow style to the first option by default
        self.undo_stack = []
        self.redo_stack = []
        self._save_state()
        self.continuous_conveyor_enabled = True
        self.component_properties = {
            "Constructor": {"name": "Constructor", "input_rate": 30, "output_rate": 30, "power_usage": 4},
            "Assembler": {"name": "Assembler", "input_rate": 60, "output_rate": 60, "power_usage": 15}, # Added Assembler properties
            "Smelter": {"name": "Smelter", "input_rate": 30, "output_rate": 30, "power_usage": 4},
            "splitter": {"name": "Splitter", "input_rate": 780, "output_rate": 780, "power_usage": 0},
            "merger": {"name": "Merger", "input_rate": 780, "output_rate": 780, "power_usage": 0},
            "storage": {"name": "Storage Container", "capacity": 48, "power_usage": 0},
            "miner": {"name": "Miner Mk.1", "output_rate": 60, "power_usage": 5}
        }
        self.setMouseTracking(True)
        self.mouse_pos = QPoint() # Store current mouse position for dashed line

    def wheelEvent(self, event):
        # Handle zoom with mouse wheel
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_level *= 1.1
            else:
                self.zoom_level /= 1.1
            self.zoom_level = max(0.1, min(5.0, self.zoom_level))
            self.update()

    def set_grid_size(self, size):
        self.grid_size = size
        self.update()

    def toggle_grid(self, show):
        self.show_grid = show
        self.update()

    def toggle_snap_to_grid(self, snap):
        self.snap_to_grid = snap

    def set_continuous_conveyor_enabled(self, enabled):
        self.continuous_conveyor_enabled = enabled

    def set_arrow_style(self, style):
        self.arrow_style = style
        self.update() # Trigger repaint to show/hide arrows

    def _save_state(self):
        # Deep copy to ensure independent state
        current_state = {
            "blocks": [list(block) for block in self.blocks],
            "conveyor_start_point": self.conveyor_start_point
        }
        self.undo_stack.append(current_state)
        self.redo_stack.clear() # Clear redo stack on new action

    def undo(self):
        if len(self.undo_stack) > 1: # Always keep at least the initial state
            last_state = self.undo_stack.pop()
            self.redo_stack.append(last_state)
            previous_state = self.undo_stack[-1]
            self._load_state(previous_state)
            self.update()

    def redo(self):
        if self.redo_stack:
            next_state = self.redo_stack.pop()
            self.undo_stack.append(next_state)
            self._load_state(next_state)
            self.update()

    def _load_state(self, state):
        self.blocks = [list(block) for block in state["blocks"]]
        self.conveyor_start_point = state["conveyor_start_point"]

    def clear_grid(self):
        self._save_state() # Save state before clearing
        self.blocks = []
        self.conveyor_start_point = None
        self.current_mode = "select"
        self.update()

    def set_mode(self, mode, orientation=None):
        self.current_mode = mode
        self.conveyor_start_point = None  # Reset for new mode
        if mode == "conveyor":
            QMessageBox.information(self, "Conveyor Tool", "Click to start conveyor, click again to end. Right-click to cancel.")
        
        if orientation: # Update orientation if provided
            if "storage" in mode: # Check if the mode is related to storage
                self.current_storage_orientation = orientation
            elif "miner" in mode: # Check if the mode is related to miner
                self.current_miner_orientation = orientation
    
    def add_machine_block(self):
        pass # No longer directly used, components are added via mouse click now

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Apply zoom transformation
        painter.scale(self.zoom_level, self.zoom_level)
        
        w = int(self.width() / self.zoom_level)
        h = int(self.height() / self.zoom_level)
        
        # Draw grid if enabled
        if self.show_grid:
            painter.setPen(QPen(QColor(60, 60, 80, 80), 1))
            for x in range(0, w, self.grid_size):
                painter.drawLine(int(x), 0, int(x), h)
            for y in range(0, h, self.grid_size):
                painter.drawLine(0, int(y), w, int(y))
        
        # Draw the dashed line preview for conveyors
        if self.current_mode == "conveyor" and self.conveyor_start_point and self.mouse_pos:
            painter.setPen(QPen(Qt.GlobalColor.cyan, 2, Qt.PenStyle.DashLine))
            painter.drawLine(self.conveyor_start_point, self.mouse_pos)

        # Draw blocks
        for block in self.blocks:
            comp_type, x, y, color, *extra = block
            width = self.grid_size
            height = self.grid_size
            
            # Set dimensions for storage and miner based on orientation
            if comp_type == "storage" or comp_type == "miner":
                orientation = extra[0] if extra else "H"
                if orientation == "H":
                    width = self.grid_size * 2  # Two grid boxes side by side
                    height = self.grid_size
                else:  # V
                    width = self.grid_size
                    height = self.grid_size * 2  # Two grid boxes stacked
            elif comp_type == "text":
                text_content = extra[0]
                # Estimate text width for hit testing
                # This is a simple approximation; a more accurate way would be to use QFontMetrics
                block_width = self.grid_size * len(text_content) // 2
                block_height = self.grid_size # Text height is typically one grid unit

            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.setBrush(QBrush(color))
            
            if comp_type == "splitter":
                # Draw hexagon for splitter
                hex_points = [
                    QPoint(int(x + width/2), int(y)),
                    QPoint(int(x + width), int(y + height/4)),
                    QPoint(int(x + width), int(y + 3*height/4)),
                    QPoint(int(x + width/2), int(y + height)),
                    QPoint(int(x), int(y + 3*height/4)),
                    QPoint(int(x), int(y + height/4))
                ]
                hex_points_f = [QPointF(p) for p in hex_points]
                painter.drawPolygon(QPolygonF(hex_points_f))
            elif comp_type == "merger":
                # Draw diamond for merger
                diamond_points = [
                    QPoint(int(x + width/2), int(y)),
                    QPoint(int(x + width), int(y + height/2)),
                    QPoint(int(x + width/2), int(y + height)),
                    QPoint(int(x), int(y + height/2))
                ]
                diamond_points_f = [QPointF(p) for p in diamond_points]
                painter.drawPolygon(QPolygonF(diamond_points_f))
            elif comp_type == "conveyor":
                # Conveyors are lines, not blocks. Ensure no fill.
                painter.setBrush(Qt.BrushStyle.NoBrush) # Ensure no fill for conveyors

                # Draw conveyor as a line (cyan and thicker)
                p1, p2 = extra[0]
                painter.setPen(QPen(Qt.GlobalColor.cyan, 4))  # Thicker cyan color for conveyors
                painter.drawLine(int(p1.x()), int(p1.y()), int(p2.x()), int(p2.y()))
                
                if self.arrow_style == ">": # Assuming ">" means show arrows
                    # Draw red arrow in the middle, pointing in the direction of the conveyor
                    mid_x = (p1.x() + p2.x()) / 2
                    mid_y = (p1.y() + p2.y()) / 2
                    
                    # Calculate angle of the conveyor line
                    angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
                    
                    painter.save()
                    painter.translate(mid_x, mid_y)
                    painter.rotate(math.degrees(angle))
                    
                    # Draw a triangular arrow head (larger for visibility, points right when angle is 0)
                    # Adjusted coordinates to ensure proper pointing after rotation
                    arrow_head = QPolygonF([
                        QPointF(0, 0),       # Tip of the arrow (at the new origin)
                        QPointF(-18, -9),    # Bottom-left point (relative to tip)
                        QPointF(-18, 9)      # Top-left point (relative to tip)
                    ])
                    
                    painter.setPen(QPen(Qt.GlobalColor.red, 1)) # Arrow outline
                    painter.setBrush(QBrush(Qt.GlobalColor.red)) # Arrow fill
                    painter.drawPolygon(arrow_head)
                    
                    painter.restore()
            else:
                # Draw rectangle for other components (machine, storage, miner, text)
                painter.drawRect(x, y, width, height)
            
            # Draw component label (only for non-conveyor types)
            if comp_type != "conveyor":
                painter.setPen(QPen(Qt.GlobalColor.white)) # Text color
                label = ""
                if comp_type == "storage":
                    label = "Storage"
                elif comp_type == "miner":
                    label = "Miner"
                elif comp_type == "Smelter": 
                    label = "Smelter" # Set label to "Smelter"
                else:
                    label = self.component_properties.get(comp_type, {}).get("name", comp_type.title())
                
                # Set smaller font size for labels
                font = painter.font()
                font.setPointSize(8) # You can adjust this value as needed
                painter.setFont(font)
                
                painter.drawText(QRect(x, y, width, height), Qt.AlignmentFlag.AlignCenter, label)

        # Draw a cyan box around the visible area of the grid
        painter.setPen(QPen(QColor(0, 255, 255), 3)) # Cyan color, 3 pixels thick
        painter.setBrush(Qt.BrushStyle.NoBrush) # No fill
        painter.drawRect(0, 0, w, h) # Draw around the entire widget area adjusted for zoom

    def mouseMoveEvent(self, event):
        # Store the current mouse position (for dashed line drawing in paintEvent)
        self.mouse_pos = event.position().toPoint()
        
        # Dragging logic
        if hasattr(self, '_dragging') and self._dragging is not None:
            pos = event.position().toPoint() - self._drag_offset
            # Snap to grid if enabled
            if self.snap_to_grid:
                gx = round(pos.x() / self.grid_size) * self.grid_size
                gy = round(pos.y() / self.grid_size) * self.grid_size
            else:
                gx = pos.x()
                gy = pos.y()
            self.blocks[self._dragging][1] = gx
            self.blocks[self._dragging][2] = gy
            self.update()
        elif self.current_mode == "conveyor" and self.conveyor_start_point:
            # Just update and let paintEvent draw the dashed line
            self.update()
        else:
            # Tooltip logic
            pos = event.position().toPoint()
            gx = round(pos.x() / self.grid_size) * self.grid_size
            gy = round(pos.y() / self.grid_size) * self.grid_size
            for block in self.blocks:
                comp_type, x, y, color, *extra = block
                # Use actual width/height for hit testing based on type
                block_width = self.grid_size
                block_height = self.grid_size
                if comp_type == "storage" or comp_type == "miner":
                    block_height = self.grid_size * 2
                
                rect = QRect(x, y, block_width, block_height)
                if rect.contains(pos):
                    props = self.component_properties.get(comp_type, {})
                    tooltip = f"{props.get('name', comp_type.title())}\n"
                    if 'input_rate' in props:
                        tooltip += f"Input: {props['input_rate']} items/min\n"
                    if 'output_rate' in props:
                        tooltip += f"Output: {props['output_rate']} items/min\n"
                    if 'power_usage' in props:
                        tooltip += f"Power: {props['power_usage']} MW\n"
                    if 'capacity' in props:
                        tooltip += f"Capacity: {props['capacity']} slots"
                    self.setToolTip(tooltip)
                    return
            self.setToolTip("")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            # If in an "add" mode, try to add a new component
            if self.current_mode.startswith("add_"):
                self._save_state() # Save state before modification
                gx = round(pos.x() / self.grid_size) * self.grid_size
                gy = round(pos.y() / self.grid_size) * self.grid_size
                if self.current_mode == "add_constructor":
                    self.blocks.append(["Constructor", gx, gy, QColor(148, 0, 211)])  # Bright Purple for machine
                elif self.current_mode == "add_assembler":
                    self.blocks.append(["Assembler", gx, gy, QColor(70, 130, 180)]) # Metallic Blue for assembler
                elif self.current_mode == "add_storage":
                    orientation = self.current_storage_orientation
                    if orientation == "H":
                        # For horizontal, use a single 2x1 block (side by side)
                        self.blocks.append(["storage", gx, gy, QColor(0, 70, 0), "H"])
                    else:  # V
                        # For vertical, use a single 1x2 block (stacked)
                        self.blocks.append(["storage", gx, gy, QColor(0, 70, 0), "V"])
                elif self.current_mode == "add_miner":
                    orientation = self.current_miner_orientation
                    if orientation == "H":
                        # For horizontal, use a single 2x1 block (side by side)
                        self.blocks.append(["miner", gx, gy, QColor(70, 130, 180), "H"])
                    else:  # V
                        # For vertical, use a single 1x2 block (stacked)
                        self.blocks.append(["miner", gx, gy, QColor(70, 130, 180), "V"])
                elif self.current_mode == "add_splitter":
                    self.blocks.append(["splitter", gx, gy, QColor(50, 205, 50)]) # Lime Green for splitter
                elif self.current_mode == "add_merger":
                    self.blocks.append(["merger", gx, gy, QColor(0, 0, 255)]) # Blue for merger
                elif self.current_mode == "add_Smelter":
                    self.blocks.append(["Smelter", gx, gy, QColor(255, 0, 0)])  # Pure Red for furnace
                self.update()
                return  # Stop processing to avoid falling into dragging logic
            elif self.current_mode == "conveyor":
                if not self.conveyor_start_point:
                    self.conveyor_start_point = pos
                else:
                    self._save_state() # Save state before modification
                    self.blocks.append(["conveyor", 0, 0, QColor(0, 255, 255), (self.conveyor_start_point, pos)])  # Bright Cyan for conveyor
                    
                    if self.continuous_conveyor_enabled:
                        self.conveyor_start_point = pos  # Set end point as new start point for continuous drawing
                    else:
                        self.conveyor_start_point = None

                    self.update()
                return  # Stop processing
            elif self.current_mode == "add_text":
                text_input, ok = QInputDialog.getText(self, "Enter Text", "Enter text for the label:")
                if ok and text_input:
                    self._save_state() # Save state before modification
                    gx = round(pos.x() / self.grid_size) * self.grid_size
                    gy = round(pos.y() / self.grid_size) * self.grid_size
                    self.blocks.append(["text", gx, gy, QColor(255, 255, 255), text_input]) # White text
                    self.update()
                return # Stop processing to avoid falling into dragging logic
            # If not adding, check for dragging existing blocks
            else:  # self.current_mode == "select"
                for i, block_data in enumerate(self.blocks):
                    comp_type, x, y, color, *extra = block_data
                    block_width = self.grid_size
                    block_height = self.grid_size
                    
                    orientation = None
                    if extra and len(extra) > 0 and isinstance(extra[0], str) and (extra[0] == "H" or extra[0] == "V"):
                        orientation = extra[0]

                    if comp_type == "storage" or comp_type == "miner":
                        # Default to H if orientation not explicitly saved (for old saves)
                        if orientation is None: 
                            orientation = "H"

                        if orientation == "H":
                            block_width = self.grid_size * 2
                            block_height = self.grid_size
                        else:
                            block_width = self.grid_size
                            block_height = self.grid_size * 2
                    elif comp_type == "text":
                        text_content = extra[0]
                        # Estimate text width for hit testing
                        # This is a simple approximation; a more accurate way would be to use QFontMetrics
                        block_width = self.grid_size * len(text_content) // 2
                        block_height = self.grid_size # Text height is typically one grid unit

                    rect = QRect(x, y, block_width, block_height)
                    if rect.contains(pos):
                        self._save_state() # Save state before modification
                        self._dragging = i
                        self._drag_offset = pos - QPoint(x, y)
                        return
        elif event.button() == Qt.MouseButton.RightButton:
            # Cancel current action and revert to select mode
            self.conveyor_start_point = None
            self.current_mode = "select"
            self.update()

    def mouseReleaseEvent(self, event):
        if self._dragging is not None:
            self._save_state() # Save state after drag operation is complete
        self._dragging = None

    def delete_component(self, index):
        """Delete a component from the grid."""
        self._save_state()
        self.blocks.pop(index)
        self.update()

    def rotate_component(self, index):
        """Rotate a component (flip H/V orientation for storage and miner)."""
        self._save_state()
        block = self.blocks[index]
        comp_type, x, y, color, *extra = block
        
        if comp_type in ["storage", "miner"]:
            current_orientation = extra[0] if extra else "H"
            new_orientation = "V" if current_orientation == "H" else "H"
            self.blocks[index] = [comp_type, x, y, color, new_orientation]
            self.update()

    def show_component_properties(self, index):
        """Show and edit component properties."""
        block = self.blocks[index]
        comp_type, x, y, color, *extra = block
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"{comp_type.title()} Properties")
        layout = QVBoxLayout(dialog)
        
        # Add color picker
        color_label = QLabel("Color:")
        color_button = QPushButton()
        color_button.setStyleSheet(f"background-color: rgb({color.red()}, {color.green()}, {color.blue()})")
        
        def pick_color():
            new_color = QColorDialog.getColor(color, self, "Pick Color")
            if new_color.isValid():
                color_button.setStyleSheet(f"background-color: rgb({new_color.red()}, {new_color.green()}, {new_color.blue()})")
                self._save_state()
                self.blocks[index] = [comp_type, x, y, new_color, *extra]
                self.update()
        
        color_button.clicked.connect(pick_color)
        
        # Add orientation selector for storage and miner
        orientation_widget = None
        if comp_type in ["storage", "miner"]:
            orientation_label = QLabel("Orientation:")
            orientation_combo = QComboBox()
            orientation_combo.addItems(["Horizontal", "Vertical"])
            current_orientation = extra[0] if extra else "H"
            orientation_combo.setCurrentText("Horizontal" if current_orientation == "H" else "Vertical")
            
            def change_orientation(text):
                new_orientation = "H" if text == "Horizontal" else "V"
                self._save_state()
                self.blocks[index] = [comp_type, x, y, color, new_orientation]
                self.update()
            
            orientation_combo.currentTextChanged.connect(change_orientation)
            orientation_widget = QWidget()
            orientation_layout = QHBoxLayout(orientation_widget)
            orientation_layout.addWidget(orientation_label)
            orientation_layout.addWidget(orientation_combo)
        
        # Add buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        # Add widgets to layout
        layout.addWidget(color_label)
        layout.addWidget(color_button)
        if orientation_widget:
            layout.addWidget(orientation_widget)
        layout.addWidget(buttons)
        
        dialog.exec()

    def copy_component(self, index):
        """Copy a component to the clipboard."""
        self.copied_component = self.blocks[index].copy()

    def paste_component(self, x, y):
        """Paste a copied component at the specified location."""
        if hasattr(self, 'copied_component'):
            self._save_state()
            new_component = self.copied_component.copy()
            new_component[1] = x  # Update x coordinate
            new_component[2] = y  # Update y coordinate
            self.blocks.append(new_component)
            self.update()

class ProductionChainVisualizer(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Production Chain Visualizer")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #23243a;
                color: #00FFFF;
            }
            QComboBox, QLineEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #FF00FF;
                border-radius: 5px;
                padding: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a1a;
                color: #ffffff;
                selection-background-color: #FF00FF;
            }
            QScrollArea {
                background-color: #23243a;
                border: 1px solid #FF00FF;
            }
            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 15px;
                margin: 0px;
            }
            QScrollBar:horizontal {
                background-color: #1a1a1a;
                height: 15px;
                margin: 0px;
            }
            QScrollBar::handle {
                background-color: #FF00FF;
                min-height: 20px;
                min-width: 20px;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                background-color: #1a1a1a;
            }
        """)
        layout = QVBoxLayout(self)
        
        # Create search and dropdown section
        search_layout = QHBoxLayout()
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search items...")
        self.search_box.textChanged.connect(self._filter_dropdown)
        search_layout.addWidget(self.search_box)
        
        # Dropdown for items
        self.item_dropdown = QComboBox()
        self.item_dropdown.addItem("Select a product...")
        self.item_dropdown.addItems([
            # Basic Resources
            "Iron Ore", "Copper Ore", "Limestone", "Coal", "Caterium Ore",
            "Sulfur", "Bauxite", "Uranium", "Raw Quartz", "Nitrogen Gas",
            "Crude Oil", "Water",
            
            # Basic Smelting
            "Iron Ingot", "Copper Ingot", "Steel Ingot", "Caterium Ingot",
            "Aluminum Ingot",
            
            # Basic Construction
            "Iron Plate", "Iron Rod", "Screw", "Reinforced Iron Plate",
            "Copper Sheet", "Wire", "Cable", "Concrete",
            
            # Advanced Construction
            "Steel Beam", "Steel Pipe", "Encased Industrial Beam",
            "Heavy Modular Frame", "Modular Frame",
            
            # Electronics
            "Circuit Board", "AI Limiter", "High-Speed Connector",
            "Computer", "Supercomputer", "Quickwire",
            
            # Power Generation
            "Nuclear Fuel Rod", "Turbofuel", "Fuel",
            
            # Space Elevator Parts
            "Smart Plating", "Versatile Framework", "Automated Wiring",
            "Modular Engine", "Adaptive Control Unit",
            
            # Nuclear
            "Encased Uranium Cell", "Electromagnetic Control Rod",
            
            # Aluminum Production
            "Aluminum Scrap", "Silica",
            
            # Advanced Materials
            "Plastic", "Rubber", "Quartz Crystal", "Crystal Oscillator",
            
            # Motors and Rotors
            "Rotor", "Stator", "Motor",
            
            # Other
            "Compacted Coal", "Sulfuric Acid"
        ])
        self.item_dropdown.currentIndexChanged.connect(self._on_dropdown_selection)
        search_layout.addWidget(self.item_dropdown)
        
        # Add search section to main layout
        layout.addLayout(search_layout)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create canvas with larger size
        self.canvas = ProductionChainCanvas()
        self.canvas.setMinimumSize(2000, 2000)  # Set a large minimum size to accommodate chains
        
        # Add canvas to scroll area
        scroll_area.setWidget(self.canvas)
        
        # Add scroll area to main layout
        layout.addWidget(scroll_area)
        
        # Add arrow style dropdown
        arrow_layout = QHBoxLayout()
        arrow_layout.addWidget(QLabel("Arrow Style:"))
        self.arrow_style = QComboBox()
        self.arrow_style.addItems(["None", "Simple", "Filled", "Double"])
        self.arrow_style.currentIndexChanged.connect(self.set_chain_arrow_style)
        arrow_layout.addWidget(self.arrow_style)
        arrow_layout.addStretch()
        layout.addLayout(arrow_layout)
        
        # Add visualize button
        visualize_btn = QPushButton("Visualize Chain")
        visualize_btn.clicked.connect(self.visualize_chain)
        layout.addWidget(visualize_btn)
        
        self.setLayout(layout)

    def _on_dropdown_selection(self, index):
        if index > 0:  # Avoid "Select a product..." item
            selected_item = self.item_dropdown.currentText()
            self.search_box.setText(selected_item)
            self.visualize_chain()
            # Reset dropdown to show all items
            self._filter_dropdown("")
            # Restore the dropdown items
            self.item_dropdown.clear()
            self.item_dropdown.addItem("Select a product...")
            self.item_dropdown.addItems([
                # Basic Resources
                "Iron Ore", "Copper Ore", "Limestone", "Coal", "Caterium Ore",
                "Sulfur", "Bauxite", "Uranium", "Raw Quartz", "Nitrogen Gas",
                "Crude Oil", "Water",
                
                # Basic Smelting
                "Iron Ingot", "Copper Ingot", "Steel Ingot", "Caterium Ingot",
                "Aluminum Ingot",
                
                # Basic Construction
                "Iron Plate", "Iron Rod", "Screw", "Reinforced Iron Plate",
                "Copper Sheet", "Wire", "Cable", "Concrete",
                
                # Advanced Construction
                "Steel Beam", "Steel Pipe", "Encased Industrial Beam",
                "Heavy Modular Frame", "Modular Frame",
                
                # Electronics
                "Circuit Board", "AI Limiter", "High-Speed Connector",
                "Computer", "Supercomputer", "Quickwire",
                
                # Power Generation
                "Nuclear Fuel Rod", "Turbofuel", "Fuel",
                
                # Space Elevator Parts
                "Smart Plating", "Versatile Framework", "Automated Wiring",
                "Modular Engine", "Adaptive Control Unit",
                
                # Nuclear
                "Encased Uranium Cell", "Electromagnetic Control Rod",
                
                # Aluminum Production
                "Aluminum Scrap", "Silica",
                
                # Advanced Materials
                "Plastic", "Rubber", "Quartz Crystal", "Crystal Oscillator",
                
                # Motors and Rotors
                "Rotor", "Stator", "Motor",
                
                # Other
                "Compacted Coal", "Sulfuric Acid"
            ])

    def _filter_dropdown(self, text):
        self.item_dropdown.blockSignals(True)
        
        # Store current selection
        current_text = self.item_dropdown.currentText()
        
        self.item_dropdown.clear()
        self.item_dropdown.addItem("Select a product...")
        
        # Get all items from the dropdown
        all_items = []
        for i in range(1, self.item_dropdown.count()):  # Skip the first "Select a product..." item
            all_items.append(self.item_dropdown.itemText(i))
        
        # Filter items based on search text
        filtered_items = [item for item in all_items if text.lower() in item.lower()]
        self.item_dropdown.addItems(filtered_items)
        
        # Restore selection if it's still in the filtered list
        if current_text in filtered_items:
            idx = self.item_dropdown.findText(current_text)
            if idx != -1:
                self.item_dropdown.setCurrentIndex(idx)
        else:
            self.item_dropdown.setCurrentIndex(0)
        
        self.item_dropdown.blockSignals(False)

    def visualize_chain(self):
        item = self.search_box.text().strip()
        if not item or item == "Select a product...":
            self.canvas.set_chain_data([], [])  # Clear canvas
            return

        # Generate data for visualization
        components, connections = self._build_visualization_data(item)
        self.canvas.set_chain_data(components, connections)

    def _build_visualization_data(self, target_item, target_quantity=1, x_start=None, y_start=None, x_spacing=200, y_spacing=150):
        # Calculate center of the grid
        if x_start is None:
            x_start = self.width() // 2
        if y_start is None:
            y_start = self.height() // 2

        components = []
        connections = []
        processed_items = set()

        # Define recipes
        RECIPES = {
            # Basic Resources
            "Iron Ore": {"output": 1, "inputs": {}},
            "Copper Ore": {"output": 1, "inputs": {}},
            "Limestone": {"output": 1, "inputs": {}},
            "Coal": {"output": 1, "inputs": {}},
            "Caterium Ore": {"output": 1, "inputs": {}},
            "Sulfur": {"output": 1, "inputs": {}},
            "Bauxite": {"output": 1, "inputs": {}},
            "Uranium": {"output": 1, "inputs": {}},
            "Raw Quartz": {"output": 1, "inputs": {}},
            "Nitrogen Gas": {"output": 1, "inputs": {}},
            "Crude Oil": {"output": 1, "inputs": {}},
            "Water": {"output": 1, "inputs": {}},
            
            # Basic Smelting
            "Iron Ingot": {"output": 1, "inputs": {"Iron Ore": 1}},
            "Copper Ingot": {"output": 1, "inputs": {"Copper Ore": 1}},
            "Steel Ingot": {"output": 1, "inputs": {"Iron Ore": 1, "Coal": 1}},
            "Caterium Ingot": {"output": 1, "inputs": {"Caterium Ore": 1}},
            "Aluminum Ingot": {"output": 1, "inputs": {"Aluminum Scrap": 2, "Silica": 2}},
            
            # Basic Construction
            "Iron Plate": {"output": 1, "inputs": {"Iron Ingot": 3}},
            "Iron Rod": {"output": 1, "inputs": {"Iron Ingot": 1}},
            "Screw": {"output": 4, "inputs": {"Iron Rod": 1}},
            "Reinforced Iron Plate": {"output": 1, "inputs": {"Iron Plate": 6, "Screw": 12}},
            "Copper Sheet": {"output": 1, "inputs": {"Copper Ingot": 2}},
            "Wire": {"output": 2, "inputs": {"Copper Ingot": 1}},
            "Cable": {"output": 1, "inputs": {"Wire": 2}},
            "Concrete": {"output": 1, "inputs": {"Limestone": 3}},
            
            # Advanced Construction
            "Steel Beam": {"output": 1, "inputs": {"Steel Ingot": 4}},
            "Steel Pipe": {"output": 2, "inputs": {"Steel Ingot": 3}},
            "Encased Industrial Beam": {"output": 1, "inputs": {"Steel Beam": 4, "Concrete": 5}},
            "Heavy Modular Frame": {"output": 1, "inputs": {
                "Modular Frame": 8,
                "Steel Pipe": 10,
                "Encased Industrial Beam": 2,
                "Screw": 36
            }},
            "Modular Frame": {"output": 1, "inputs": {
                "Reinforced Iron Plate": 3,
                "Iron Rod": 12
            }},
            
            # Electronics
            "Circuit Board": {"output": 1, "inputs": {"Copper Sheet": 2, "Plastic": 4}},
            "AI Limiter": {"output": 1, "inputs": {"Copper Sheet": 5, "Quickwire": 20}},
            "High-Speed Connector": {"output": 1, "inputs": {
                "Quickwire": 56,
                "Cable": 10,
                "Circuit Board": 3
            }},
            "Computer": {"output": 1, "inputs": {
                "Circuit Board": 25,
                "Cable": 22,
                "Plastic": 45,
                "Screw": 130
            }},
            "Supercomputer": {"output": 1, "inputs": {
                "Computer": 2,
                "AI Limiter": 2,
                "High-Speed Connector": 3,
                "Plastic": 28
            }},
            "Quickwire": {"output": 5, "inputs": {"Caterium Ingot": 1}},
            
            # Power Generation
            "Nuclear Fuel Rod": {"output": 1, "inputs": {
                "Encased Uranium Cell": 50,
                "Encased Industrial Beam": 1,
                "Electromagnetic Control Rod": 2
            }},
            "Turbofuel": {"output": 1, "inputs": {
                "Fuel": 2,
                "Compacted Coal": 2,
                "Sulfur": 2
            }},
            "Fuel": {"output": 1, "inputs": {"Crude Oil": 3}},
            
            # Space Elevator Parts
            "Smart Plating": {"output": 1, "inputs": {
                "Reinforced Iron Plate": 2,
                "Rotor": 2
            }},
            "Versatile Framework": {"output": 1, "inputs": {
                "Modular Frame": 2,
                "Steel Beam": 12
            }},
            "Automated Wiring": {"output": 1, "inputs": {
                "Stator": 2,
                "Cable": 20
            }},
            "Modular Engine": {"output": 1, "inputs": {
                "Motor": 2,
                "Rubber": 15,
                "Smart Plating": 2
            }},
            "Adaptive Control Unit": {"output": 1, "inputs": {
                "Automated Wiring": 15,
                "Circuit Board": 2,
                "Heavy Modular Frame": 2,
                "Computer": 1
            }},
            
            # Nuclear
            "Encased Uranium Cell": {"output": 1, "inputs": {
                "Uranium": 50,
                "Concrete": 3,
                "Sulfuric Acid": 8
            }},
            "Electromagnetic Control Rod": {"output": 1, "inputs": {
                "Stator": 3,
                "AI Limiter": 2
            }},
            
            # Aluminum Production
            "Aluminum Scrap": {"output": 2, "inputs": {
                "Bauxite": 3,
                "Coal": 3
            }},
            "Silica": {"output": 1, "inputs": {"Raw Quartz": 3}},
            
            # Advanced Materials
            "Plastic": {"output": 1, "inputs": {"Crude Oil": 3}},
            "Rubber": {"output": 1, "inputs": {"Crude Oil": 3}},
            "Quartz Crystal": {"output": 1, "inputs": {"Raw Quartz": 3}},
            "Crystal Oscillator": {"output": 1, "inputs": {
                "Quartz Crystal": 18,
                "Cable": 14,
                "Reinforced Iron Plate": 2
            }},
            
            # Motors and Rotors
            "Rotor": {"output": 1, "inputs": {"Iron Rod": 5, "Screw": 25}},
            "Stator": {"output": 1, "inputs": {"Steel Pipe": 3, "Wire": 8}},
            "Motor": {"output": 1, "inputs": {"Rotor": 2, "Stator": 2}},
            
            # Other
            "Compacted Coal": {"output": 1, "inputs": {"Coal": 5, "Sulfur": 5}},
            "Sulfuric Acid": {"output": 1, "inputs": {"Sulfur": 5, "Water": 5}}
        }

        component_colors = {
            # Basic Resources - Bright natural colors
            "Iron Ore": QColor(180, 180, 180),  # Bright gray
            "Copper Ore": QColor(255, 140, 0),  # Bright copper
            "Limestone": QColor(255, 255, 255),  # White
            "Coal": QColor(60, 60, 60),  # Dark gray
            "Caterium Ore": QColor(255, 215, 0),  # Bright gold
            "Sulfur": QColor(255, 255, 0),  # Bright yellow
            "Bauxite": QColor(255, 69, 0),  # Bright red-orange
            "Uranium": QColor(0, 255, 0),  # Bright green
            "Raw Quartz": QColor(173, 216, 230),  # Light blue
            "Nitrogen Gas": QColor(135, 206, 235),  # Sky blue
            "Crude Oil": QColor(40, 40, 40),  # Dark gray
            "Water": QColor(0, 191, 255),  # Deep sky blue
            
            # Basic Smelting - Bright metallic colors
            "Iron Ingot": QColor(220, 220, 220),  # Bright steel
            "Copper Ingot": QColor(255, 140, 0),  # Bright copper
            "Steel Ingot": QColor(192, 192, 192),  # Bright silver
            "Caterium Ingot": QColor(255, 215, 0),  # Bright gold
            "Aluminum Ingot": QColor(255, 255, 255),  # Bright silver
            
            # Basic Construction - Bright industrial colors
            "Iron Plate": QColor(200, 200, 200),  # Bright gray
            "Iron Rod": QColor(180, 180, 180),  # Medium gray
            "Screw": QColor(160, 160, 160),  # Light gray
            "Reinforced Iron Plate": QColor(220, 220, 220),  # Bright steel
            "Copper Sheet": QColor(255, 140, 0),  # Bright copper
            "Wire": QColor(255, 140, 0),  # Bright copper
            "Cable": QColor(255, 140, 0),  # Bright copper
            "Concrete": QColor(240, 240, 240),  # Bright gray
            
            # Advanced Construction - Bright industrial colors
            "Steel Beam": QColor(192, 192, 192),  # Bright silver
            "Steel Pipe": QColor(220, 220, 220),  # Bright steel
            "Encased Industrial Beam": QColor(200, 200, 200),  # Bright gray
            "Heavy Modular Frame": QColor(180, 180, 180),  # Medium gray
            "Modular Frame": QColor(200, 200, 200),  # Bright gray
            
            # Electronics - Bright modern colors
            "Circuit Board": QColor(0, 255, 0),  # Bright green
            "AI Limiter": QColor(50, 255, 50),  # Light green
            "High-Speed Connector": QColor(100, 255, 100),  # Very light green
            "Computer": QColor(150, 255, 150),  # Pale green
            "Supercomputer": QColor(200, 255, 200),  # Very pale green
            "Quickwire": QColor(255, 215, 0),  # Bright gold
            
            # Power Generation - Bright energy colors
            "Nuclear Fuel Rod": QColor(0, 255, 0),  # Bright green
            "Turbofuel": QColor(255, 165, 0),  # Bright orange
            "Fuel": QColor(255, 140, 0),  # Bright orange-red
            
            # Space Elevator Parts - Bright space colors
            "Smart Plating": QColor(255, 0, 0),  # Bright red
            "Versatile Framework": QColor(255, 50, 50),  # Light red
            "Automated Wiring": QColor(255, 100, 100),  # Very light red
            "Modular Engine": QColor(255, 150, 150),  # Pale red
            "Adaptive Control Unit": QColor(255, 200, 200),  # Very pale red
            
            # Nuclear - Bright radioactive colors
            "Encased Uranium Cell": QColor(0, 255, 0),  # Bright green
            "Electromagnetic Control Rod": QColor(50, 255, 50),  # Light green
            
            # Aluminum Production - Bright metallic colors
            "Aluminum Scrap": QColor(255, 255, 255),  # Bright silver
            "Silica": QColor(240, 240, 240),  # Bright gray
            
            # Advanced Materials - Bright synthetic colors
            "Plastic": QColor(255, 255, 255),  # White
            "Rubber": QColor(60, 60, 60),  # Dark gray
            "Quartz Crystal": QColor(173, 216, 230),  # Light blue
            "Crystal Oscillator": QColor(135, 206, 235),  # Sky blue
            
            # Motors and Rotors - Bright mechanical colors
            "Rotor": QColor(192, 192, 192),  # Bright silver
            "Stator": QColor(220, 220, 220),  # Bright steel
            "Motor": QColor(200, 200, 200),  # Bright gray
            
            # Other - Bright miscellaneous colors
            "Compacted Coal": QColor(80, 80, 80),  # Medium gray
            "Sulfuric Acid": QColor(255, 255, 0)  # Bright yellow
        }

        def get_recipe(item):
            # Return recipe for the given item
            return RECIPES.get(item, {"output": 1, "inputs": {}})

        def add_to_chain(item, quantity, x, y, level):
            if item in processed_items:
                return
            
            processed_items.add(item)
            recipe = get_recipe(item)
            
            # Add component
            components.append({
                "id": item,
                "x": x,
                "y": y,
                "quantity": quantity,
                "output": recipe["output"],
                "color": component_colors.get(item, QColor(200, 200, 200))  # Default gray if no color defined
            })
            
            # Add connections for inputs
            input_y = y + y_spacing
            for i, (input_item, input_quantity) in enumerate(recipe["inputs"].items()):
                input_x = x - (len(recipe["inputs"]) - 1) * x_spacing // 2 + i * x_spacing
                connections.append({
                    "from": input_item,
                    "to": item,
                    "quantity": input_quantity * quantity / recipe["output"]
                })
                add_to_chain(input_item, input_quantity * quantity / recipe["output"], input_x, input_y, level + 1)

        # Start building the chain
        add_to_chain(target_item, target_quantity, x_start, y_start, 0)
        
        return components, connections

    def _add_to_chain_recursive(self, item, quantity, current_x, current_y, level, components, connections, processed_items, component_colors, x_spacing, y_spacing):
        # Avoid redundant processing if an item at this level is already handled
        if item in processed_items:
            return

        processed_items.add(item)
        recipe = self.get_recipe(item)

        # Add component
        components.append({
            "id": item,
            "x": current_x,
            "y": current_y,
            "quantity": quantity,
            "output": recipe["output"]
        })

        # Add connections for inputs
        input_y = current_y + y_spacing
        for i, (input_item, input_quantity) in enumerate(recipe["inputs"].items()):
            input_x = current_x - (len(recipe["inputs"]) - 1) * x_spacing // 2 + i * x_spacing
            connections.append({
                "from": input_item,
                "to": item,
                "quantity": input_quantity * quantity / recipe["output"]
            })
            self._add_to_chain_recursive(
                input_item,
                input_quantity * quantity / recipe["output"],
                input_x,
                input_y,
                level + 1,
                components,
                connections,
                processed_items,
                component_colors,
                x_spacing,
                y_spacing
            )

    def set_chain_arrow_style(self, index):
        arrow_styles = ["None", "Simple", "Filled", "Double"]
        selected_style = arrow_styles[index]
        self.canvas.set_arrow_style(selected_style)

class ProductionChainCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.components = []
        self.connections = []
        self.arrow_style = "None"
        self.component_properties = {}  # Initialize empty dictionary
        self.setMinimumSize(2000, 2000)  # Large canvas for complex chains
        
    def set_chain_data(self, components, connections):
        self.components = components
        self.connections = connections
        self.update()
        
    def set_arrow_style(self, style):
        self.arrow_style = style
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Define grid for visualization area
        grid_size = 40
        w, h = self.width(), self.height()

        # Draw black grid
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        for x in range(0, w, grid_size):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, grid_size):
            painter.drawLine(0, y, w, y)
        
        # Draw connections first (so they appear behind components)
        for conn in self.connections:
            # Find the source and target components
            source_comp = next((c for c in self.components if c["id"] == conn["from"]), None)
            target_comp = next((c for c in self.components if c["id"] == conn["to"]), None)
            
            if source_comp and target_comp:
                # Calculate connection points
                source_x = source_comp["x"]
                source_y = source_comp["y"]
                target_x = target_comp["x"]
                target_y = target_comp["y"]
                
                # Draw the connection line
                painter.setPen(QPen(QColor(0, 191, 255), 2))  # Bright blue color
                
                if self.arrow_style == "Curved":
                    # Draw curved line
                    path = QPainterPath()
                    path.moveTo(source_x, source_y)
                    ctrl_x = (source_x + target_x) / 2
                    ctrl_y = source_y - 50
                    path.quadTo(ctrl_x, ctrl_y, target_x, target_y)
                    painter.drawPath(path)
                else:
                    # Draw straight line
                    painter.drawLine(source_x, source_y, target_x, target_y)
                
                # Draw arrow if style is not None
                if self.arrow_style != "None":
                    # Calculate arrow position and angle
                    start = QPoint(source_x, source_y)
                    end = QPoint(target_x, target_y)
                    
                    # Calculate the angle of the line
                    angle = math.atan2(end.y() - start.y(), end.x() - start.x())
                    
                    # Draw arrow based on style
                    if self.arrow_style == "Simple":
                        painter.setPen(QPen(QColor(0, 191, 255), 2))  # Bright blue
                        painter.setFont(QFont("Arial", 12))
                        painter.translate(end)
                        painter.rotate(math.degrees(angle))
                        painter.drawText(0, 0, ">")
                        painter.rotate(-math.degrees(angle))
                        painter.translate(-end)
                    elif self.arrow_style == "Filled":
                        painter.setPen(QPen(QColor(0, 191, 255), 2))  # Bright blue
                        painter.setBrush(QBrush(QColor(0, 191, 255)))  # Bright blue
                        painter.translate(end)
                        painter.rotate(math.degrees(angle))
                        painter.drawPolygon(QPolygonF([
                            QPointF(0, 0),
                            QPointF(-15, -7),
                            QPointF(-15, 7)
                        ]))
                        painter.rotate(-math.degrees(angle))
                        painter.translate(-end)
                    elif self.arrow_style == "Double":
                        painter.setPen(QPen(QColor(0, 191, 255), 2))  # Bright blue
                        painter.setFont(QFont("Arial", 12))
                        painter.translate(end)
                        painter.rotate(math.degrees(angle))
                        painter.drawText(0, 0, ">>")
                        painter.rotate(-math.degrees(angle))
                        painter.translate(-end)
                
                # Draw quantity label
                mid_x = int((source_x + target_x) / 2)
                mid_y = int((source_y + target_y) / 2)
                painter.setPen(QPen(Qt.GlobalColor.black))
                painter.drawText(mid_x, mid_y, f"{conn['quantity']:.1f}")
        
        # Draw components
        for comp in self.components:
            x, y = int(comp["x"]), int(comp["y"])
            width = 100
            height = 60
            
            # Draw component box with its color
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            color = comp.get("color", QColor(200, 200, 200))  # Default gray if no color defined
            painter.setBrush(QBrush(color))
            painter.drawRect(x - width//2, y - height//2, width, height)
            
            # Draw component name and quantity
            painter.setPen(QPen(Qt.GlobalColor.black))
            label = comp["id"].title()  # Use the component ID directly
            painter.drawText(x - width//2 + 5, y - height//2 + 20, label)
            painter.drawText(x - width//2 + 5, y - height//2 + 40, f"x{comp['quantity']:.1f}")

class RouteOptimizer(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Route Optimizer")
        self.setMinimumSize(1200, 900)
        
        # Initialize Perlin noise permutation table
        self.p = np.arange(256, dtype=int)
        np.random.shuffle(self.p)
        self.p = np.stack([self.p, self.p]).flatten()
        
        # Define terrain types with height ranges and colors
        self.terrain_types = {
            "deep_water": {"color": "#000080", "cost": 5, "height": 0},
            "water": {"color": "#0000FF", "cost": 4, "height": 1},
            "shoreline": {"color": "#90EE90", "cost": 3, "height": 2}, # Light Green for slight elevation
            "low_hills": {"color": "#008000", "cost": 2, "height": 3},   # Green for greater elevation
            "medium_hills": {"color": "#006400", "cost": 2, "height": 4},  # Dark Green for even greater elevation
            "high_hills": {"color": "#FFA500", "cost": 3, "height": 5},    # Orange for high elevation
            "mountain": {"color": "#FF0000", "cost": 4, "height": 6},   # Red for mountain
            "high_mountains": {"color": "#800080", "cost": 5, "height": 7},   # Purple for high mountains
            "temple_core": {"color": "#FFFFFF", "cost": 10, "height": 8},   # White for temple core
            "temple_wall": {"color": "#000000", "cost": 8, "height": 9}   # Black for temple wall
        }
        
        # Grid settings
        self.grid_size = 100  # Start with smaller grid for faster loading
        self.cell_size = 3  # Initial cell size
        self.min_cell_size = 1
        self.max_cell_size = 20
        self.zoom_level = 1.0
        
        # Terrain data
        self.terrain_grid = np.zeros((self.grid_size, self.grid_size), dtype=int)
        self.route_path = []
        self.start_point = None
        self.end_point = None
        
        # Initialize terrain generation attributes
        self._terrain_seed = 0
        self._terrain_offset_x = 0
        self._terrain_offset_y = 0
        
        # Create main layout
        layout = QVBoxLayout()
        
        # Add controls
        controls_layout = QHBoxLayout()
        
        # Left side controls
        left_controls = QVBoxLayout()
        
        # Terrain type control
        terrain_layout = QVBoxLayout()
        terrain_label = QLabel("Terrain Type:")
        self.terrain_type_combo = QComboBox()
        self.terrain_type_combo.addItems([
            "Plains",
            "Hills", 
            "Mountains",
            "Islands",
            "Steep Cliffs",
            "Spiral Land"
        ])
        self.terrain_type_combo.setCurrentText("Plains")
        terrain_layout.addWidget(terrain_label)
        terrain_layout.addWidget(self.terrain_type_combo)
        left_controls.addLayout(terrain_layout)
        
        # Grid size control for faster generation
        grid_size_layout = QVBoxLayout()
        grid_size_label = QLabel("Grid Size:")
        self.grid_size_combo = QComboBox()
        self.grid_size_combo.addItems(["100x100 (Fast)", "250x250 (Medium)", "500x500 (Slow)", "1000x1000 (Very Slow)"])
        self.grid_size_combo.setCurrentText("100x100 (Fast)")
        grid_size_layout.addWidget(grid_size_label)
        grid_size_layout.addWidget(self.grid_size_combo)
        left_controls.addLayout(grid_size_layout)
        
        # Zoom controls
        zoom_layout = QVBoxLayout()
        zoom_label = QLabel("Zoom:")
        zoom_buttons_layout = QHBoxLayout()
        
        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.zoom_reset_btn = QPushButton("Reset Zoom")
        self.zoom_reset_btn.clicked.connect(self.reset_zoom)
        
        zoom_buttons_layout.addWidget(self.zoom_in_btn)
        zoom_buttons_layout.addWidget(self.zoom_out_btn)
        zoom_buttons_layout.addWidget(self.zoom_reset_btn)
        
        zoom_layout.addWidget(zoom_label)
        zoom_layout.addLayout(zoom_buttons_layout)
        left_controls.addLayout(zoom_layout)
        
        # Buttons
        button_layout = QVBoxLayout()
        self.optimize_button = QPushButton("Optimize Route")
        self.optimize_button.clicked.connect(self.optimize_route)
        self.regenerate_button = QPushButton("Generate New Terrain")
        self.regenerate_button.clicked.connect(self.generate_terrain)
        self.clear_route_btn = QPushButton("Clear Route")
        self.clear_route_btn.clicked.connect(self.clear_route)
        button_layout.addWidget(self.optimize_button)
        button_layout.addWidget(self.regenerate_button)
        button_layout.addWidget(self.clear_route_btn)
        left_controls.addLayout(button_layout)
        
        controls_layout.addLayout(left_controls)
        
        # Right side - Start and End location inputs
        right_controls = QVBoxLayout()
        
        # Start location input
        start_label = QLabel("Start Location:")
        start_label.setStyleSheet("font-weight: bold;")
        right_controls.addWidget(start_label)
        
        start_input_layout = QHBoxLayout()
        start_input_layout.addWidget(QLabel("Col (A):"))
        self.start_col_num = QLineEdit()
        self.start_col_num.setPlaceholderText("1-100")
        self.start_col_num.setFixedWidth(70)
        start_input_layout.addWidget(self.start_col_num)
        right_controls.addLayout(start_input_layout)
        
        start_input_layout2 = QHBoxLayout()
        start_input_layout2.addWidget(QLabel("Row (B):"))
        self.start_row_num = QLineEdit()
        self.start_row_num.setPlaceholderText("1-100")
        self.start_row_num.setFixedWidth(70)
        start_input_layout2.addWidget(self.start_row_num)
        right_controls.addLayout(start_input_layout2)
        
        # Add some spacing
        right_controls.addSpacing(10)
        
        # End location input
        end_label = QLabel("End Location:")
        end_label.setStyleSheet("font-weight: bold;")
        right_controls.addWidget(end_label)
        
        end_input_layout = QHBoxLayout()
        end_input_layout.addWidget(QLabel("Col (A):"))
        self.end_col_num = QLineEdit()
        self.end_col_num.setPlaceholderText("1-100")
        self.end_col_num.setFixedWidth(70)
        end_input_layout.addWidget(self.end_col_num)
        right_controls.addLayout(end_input_layout)
        
        end_input_layout2 = QHBoxLayout()
        end_input_layout2.addWidget(QLabel("Row (B):"))
        self.end_row_num = QLineEdit()
        self.end_row_num.setPlaceholderText("1-100")
        self.end_row_num.setFixedWidth(70)
        end_input_layout2.addWidget(self.end_row_num)
        right_controls.addLayout(end_input_layout2)
        
        controls_layout.addLayout(right_controls)
        
        # Add legend
        legend_layout = QVBoxLayout()
        legend_label = QLabel("Terrain Legend:")
        legend_label.setStyleSheet("font-weight: bold;")
        legend_layout.addWidget(legend_label)
        
        # Create legend items
        legend_items = [
            ("Deep Water", "#000080", "Cost: 5"),
            ("Water", "#0000FF", "Cost: 4"),
            ("Shoreline", "#90EE90", "Cost: 3"),
            ("Low Hills", "#008000", "Cost: 2"),
            ("Medium Hills", "#006400", "Cost: 2"),
            ("High Hills", "#FFA500", "Cost: 3"),
            ("Mountain", "#FF0000", "Cost: 4"),
            ("High Mountains", "#800080", "Cost: 5")
        ]
        
        for name, color, cost in legend_items:
            item_layout = QHBoxLayout()
            color_box = QLabel()
            color_box.setFixedSize(20, 20)
            color_box.setStyleSheet(f"background-color: {color}; border: 1px solid #333;")
            item_layout.addWidget(color_box)
            item_layout.addWidget(QLabel(f"{name} ({cost})"))
            item_layout.addStretch()
            legend_layout.addLayout(item_layout)
        
        controls_layout.addLayout(legend_layout)
        
        layout.addLayout(controls_layout)
        
        # Create scrollable grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        
        # Create custom grid widget
        self.grid_widget = RouteGridWidget(self)
        scroll.setWidget(self.grid_widget)
        layout.addWidget(scroll)
        
        # Add route details area
        self.route_details = QTextEdit()
        self.route_details.setReadOnly(True)
        self.route_details.setMaximumHeight(100)
        layout.addWidget(self.route_details)
        
        # Add status bar
        self.status_bar = QLabel()
        self.status_bar.setStyleSheet("background-color: #3b3b3b; color: white; padding: 5px; border-top: 1px solid #555;")
        layout.addWidget(self.status_bar)
        
        # Add progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
                background-color: #3b3b3b;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #0d47a1;
                border-radius: 2px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        
        # Generate initial terrain
        self.generate_terrain()
        
        # Set dark theme
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: white;
            }
            QLabel {
                color: white;
            }
            QLineEdit {
                background-color: #3b3b3b;
                color: white;
                border: 1px solid #555;
                padding: 5px;
            }
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QTextEdit {
                background-color: #3b3b3b;
                color: white;
                border: 1px solid #555;
            }
            QScrollBar:vertical {
                background-color: #2b2b2b;
                width: 15px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #555;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #2b2b2b;
                height: 15px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background-color: #555;
                min-width: 20px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
    
    def zoom_in(self):
        if self.cell_size < self.max_cell_size:
            self.cell_size = min(self.cell_size + 1, self.max_cell_size)
            self.zoom_level = self.cell_size / 3.0
            self.grid_widget.update()
            self.grid_widget.setMinimumSize(self.grid_size * self.cell_size, self.grid_size * self.cell_size)
    
    def zoom_out(self):
        if self.cell_size > self.min_cell_size:
            self.cell_size = max(self.cell_size - 1, self.min_cell_size)
            self.zoom_level = self.cell_size / 3.0
            self.grid_widget.update()
            self.grid_widget.setMinimumSize(self.grid_size * self.cell_size, self.grid_size * self.cell_size)
    
    def reset_zoom(self):
        self.cell_size = 3
        self.zoom_level = 1.0
        self.grid_widget.update()
        self.grid_widget.setMinimumSize(self.grid_size * self.cell_size, self.grid_size * self.cell_size)

    def _fade(self, t):
        return t * t * t * (t * (t * 6 - 15) + 10)

    def _lerp(self, a, b, x):
        return a + x * (b - a)

    def _grad(self, hash, x, y):
        h = hash & 7
        u = y if h < 4 else x
        v = x if h < 4 else y
        return (-u if h & 1 else u, -v if h & 2 else v)

    def _dot(self, a, b):
        return a[0] * b[0] + a[1] * b[1]

    def perlin_noise(self, x, y, seed=0):
        # Implementation of Perlin noise
        np.random.seed(seed)
        
        xi = int(x) & 255  # Wrap around at 255
        yi = int(y) & 255  # Wrap around at 255
        xf = x - int(x)
        yf = y - int(y)
        
        u = self._fade(xf)
        v = self._fade(yf)
        
        # Get gradient vectors
        n00 = self._grad(self.p[self.p[xi] + yi], xf, yf)
        n01 = self._grad(self.p[self.p[xi] + yi + 1], xf, yf - 1)
        n10 = self._grad(self.p[self.p[xi + 1] + yi], xf - 1, yf)
        n11 = self._grad(self.p[self.p[xi + 1] + yi + 1], xf - 1, yf - 1)
        
        # Calculate dot products
        x1 = self._lerp(self._dot(n00, (xf, yf)), self._dot(n10, (xf - 1, yf)), u)
        x2 = self._lerp(self._dot(n01, (xf, yf - 1)), self._dot(n11, (xf - 1, yf - 1)), u)
        
        return self._lerp(x1, x2, v)

    def generate_terrain(self):
        # Get selected grid size
        grid_size_text = self.grid_size_combo.currentText()
        if "100x100" in grid_size_text:
            current_grid_size = 100
        elif "250x250" in grid_size_text:
            current_grid_size = 250
        elif "500x500" in grid_size_text:
            current_grid_size = 500
        else:
            current_grid_size = 1000
        
        # Update grid size if different
        if current_grid_size != self.grid_size:
            self.grid_size = current_grid_size
            self.terrain_grid = np.zeros((self.grid_size, self.grid_size), dtype=int)
            self.grid_widget.setMinimumSize(self.grid_size * self.cell_size, self.grid_size * self.cell_size)
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(self.grid_size)
        self.progress_bar.setValue(0)
        self.status_bar.setText(f"Generating {self.grid_size}x{self.grid_size} terrain...")
        
        # Get terrain type from dropdown
        terrain_type = self.terrain_type_combo.currentText()
        
        # Create height map based on terrain type
        height_map = np.zeros((self.grid_size, self.grid_size))
        
        if terrain_type == "Plains":
            height_map = self._generate_plains()
        elif terrain_type == "Hills":
            height_map = self._generate_hills()
        elif terrain_type == "Mountains":
            height_map = self._generate_mountains()
        elif terrain_type == "Islands":
            height_map = self._generate_islands()
        elif terrain_type == "Steep Cliffs":
            height_map = self._generate_steep_cliffs()
        elif terrain_type == "Spiral Land":
            height_map = self._generate_spiral_land()
        
        self.status_bar.setText("Finalizing terrain...")
        
        # Convert heights to terrain types and store in terrain grid
        for row in range(self.grid_size):
            for col in range(self.grid_size):
                height = int(height_map[row, col])
                # Map height to terrain type with new terrain types
                if height == 0:
                    terrain_height = 0  # deep_water
                elif height == 1:
                    terrain_height = 1  # water
                elif height == 2:
                    terrain_height = 2  # shoreline
                elif height == 3:
                    terrain_height = 3  # low_hills
                elif height == 4:
                    terrain_height = 4  # medium_hills
                elif height == 5:
                    terrain_height = 5  # high_hills
                elif height == 6:
                    terrain_height = 6  # mountain
                elif height == 7:
                    terrain_height = 7  # high_mountains
                elif height == 8:
                    terrain_height = 8  # temple_core (white)
                elif height == 9:
                    terrain_height = 9  # temple_wall (black)
                else:
                    terrain_height = 7  # high_mountains
                
                self.terrain_grid[row, col] = terrain_height
        
        # Hide progress bar and update the grid widget
        self.progress_bar.setVisible(False)
        self.grid_widget.update()
        self.status_bar.setText(f"{self.grid_size}x{self.grid_size} {terrain_type} terrain ready!")
    
    def _generate_plains(self):
        """Generate topographic plains with varied elevation including higher areas and lakes"""
        height_map = np.zeros((self.grid_size, self.grid_size))
        
        # Create falloff mask for natural terrain boundaries
        falloff_mask = self._create_falloff_mask()
        
        # Create natural lake masks using noise for irregular shapes
        lake_mask = np.zeros((self.grid_size, self.grid_size))
        
        # Add several small lakes with irregular shapes
        num_small_lakes = random.randint(3, 6)
        for lake_id in range(num_small_lakes):
            center_x = random.randint(10, self.grid_size - 10)
            center_y = random.randint(10, self.grid_size - 10)
            base_radius = random.randint(3, 5)
            
            for i in range(max(0, center_x - base_radius - 2), min(self.grid_size, center_x + base_radius + 2)):
                for j in range(max(0, center_y - base_radius - 2), min(self.grid_size, center_y + base_radius + 2)):
                    dist = np.sqrt((i - center_x)**2 + (j - center_y)**2)
                    if dist <= base_radius + 2:
                        # Use noise to create irregular lake shape
                        noise_val = self.perlin_noise(i * 0.1 + lake_id * 100, j * 0.1 + lake_id * 100)
                        irregular_radius = base_radius + noise_val * 2
                        
                        if dist <= irregular_radius:
                            # Create natural lake edge with noise variation
                            edge_factor = 1.0 - (dist / irregular_radius)
                            edge_factor += noise_val * 0.3  # Add noise to edge
                            edge_factor = max(0, min(1, edge_factor))  # Clamp to 0-1
                            lake_mask[i, j] = max(lake_mask[i, j], edge_factor * 0.8)
        
        # Add 1-2 medium lakes with more complex irregular shapes
        num_medium_lakes = random.randint(1, 2)
        for lake_id in range(num_medium_lakes):
            center_x = random.randint(15, self.grid_size - 15)
            center_y = random.randint(15, self.grid_size - 15)
            base_radius = random.randint(6, 10)
            
            for i in range(max(0, center_x - base_radius - 3), min(self.grid_size, center_x + base_radius + 3)):
                for j in range(max(0, center_y - base_radius - 3), min(self.grid_size, center_y + base_radius + 3)):
                    dist = np.sqrt((i - center_x)**2 + (j - center_y)**2)
                    if dist <= base_radius + 3:
                        # Use multiple noise layers for more complex shape
                        noise1 = self.perlin_noise(i * 0.08 + lake_id * 200, j * 0.08 + lake_id * 200)
                        noise2 = self.perlin_noise(i * 0.15 + lake_id * 300, j * 0.15 + lake_id * 300)
                        irregular_radius = base_radius + noise1 * 3 + noise2 * 1.5
                        
                        if dist <= irregular_radius:
                            # Create natural lake edge with complex variation
                            edge_factor = 1.0 - (dist / irregular_radius)
                            edge_factor += (noise1 + noise2) * 0.2  # Add noise to edge
                            edge_factor = max(0, min(1, edge_factor))  # Clamp to 0-1
                            lake_mask[i, j] = max(lake_mask[i, j], edge_factor * 0.9)
        
        # Randomize thresholds a bit for variety
        deep_water_thresh = 0.08 + random.uniform(-0.01, 0.01)
        water_thresh = 0.18 + random.uniform(-0.02, 0.02)
        shore_thresh = 0.28 + random.uniform(-0.02, 0.02)
        low_hill_thresh = 0.45 + random.uniform(-0.03, 0.03)
        med_hill_thresh = 0.65 + random.uniform(-0.03, 0.03)
        high_hill_thresh = 0.8 + random.uniform(-0.03, 0.03)
        # Everything above high_hill_thresh is mountains
        
        # Create temple structures
        temple_mask = np.zeros((self.grid_size, self.grid_size), dtype=int)  # 0=none, 1=wall, 2=core
        
        # Add sparse black temple walls (very rare)
        num_temple_walls = random.randint(1, 3)  # Very few walls
        for _ in range(num_temple_walls):
            wall_x = random.randint(5, self.grid_size - 5)
            wall_y = random.randint(5, self.grid_size - 5)
            temple_mask[wall_x, wall_y] = 1  # Black temple wall
        
        # Add very rare white temple cores (only 0-1 per map)
        if random.random() < 0.3:  # 30% chance of having a temple core
            # Find suitable location (deep water or high hills)
            suitable_locations = []
            for i in range(self.grid_size):
                for j in range(self.grid_size):
                    # Check if this would be deep water or high hills/mountains
                    freq1 = 0.008 * (1000 / self.grid_size)
                    freq2 = 0.03 * (1000 / self.grid_size)
                    n1 = self._perlin(i, j, freq1, 0) if hasattr(self, '_perlin') else self.perlin_noise(i * freq1, j * freq1)
                    n2 = self._perlin(i, j, freq2, 1) if hasattr(self, '_perlin') else self.perlin_noise(i * freq2, j * freq2)
                    noise = 0.7 * n1 + 0.3 * n2
                    normalized_noise = (noise + 1) / 2
                    
                    # Check if this would be deep water (very low) or high hills/mountains (very high)
                    if normalized_noise < deep_water_thresh or normalized_noise > high_hill_thresh:
                        suitable_locations.append((i, j))
            
            if suitable_locations:
                # Place temple core
                core_x, core_y = random.choice(suitable_locations)
                temple_mask[core_x, core_y] = 2  # White temple core
                
                # Surround with black temple walls (3x3 pattern)
                for di in range(-1, 2):
                    for dj in range(-1, 2):
                        ni, nj = core_x + di, core_y + dj
                        if (0 <= ni < self.grid_size and 0 <= nj < self.grid_size and 
                            temple_mask[ni, nj] == 0):  # Don't overwrite core
                            temple_mask[ni, nj] = 1  # Black temple wall
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                # Fractal noise: combine low and high frequency
                freq1 = 0.008 * (1000 / self.grid_size)
                freq2 = 0.03 * (1000 / self.grid_size)
                n1 = self._perlin(i, j, freq1, 0) if hasattr(self, '_perlin') else self.perlin_noise(i * freq1, j * freq1)
                n2 = self._perlin(i, j, freq2, 1) if hasattr(self, '_perlin') else self.perlin_noise(i * freq2, j * freq2)
                noise = 0.7 * n1 + 0.3 * n2
                normalized_noise = (noise + 1) / 2
                # Check for temple structures first (temples override everything)
                temple_type = temple_mask[i, j]
                if temple_type == 2:  # White temple core
                    height_map[i, j] = 8  # Special value for white temple core
                elif temple_type == 1:  # Black temple wall
                    height_map[i, j] = 9  # Special value for black temple wall
                else:
                    # Apply lake mask to lower elevation in lake areas
                    lake_factor = lake_mask[i, j]
                    if lake_factor > 0:
                        # In lake areas, force water or deep water based on lake depth
                        if lake_factor > 0.7:
                            height_map[i, j] = 0  # Deep water in center of lakes
                        else:
                            height_map[i, j] = 1  # Water in lake edges
                    else:
                        # Apply falloff mask to create natural terrain boundaries
                        falloff_value = falloff_mask[i, j]
                        # Blend noise with falloff mask
                        blended_noise = normalized_noise * falloff_value
                        
                        # Normal terrain generation with falloff influence
                        if blended_noise < deep_water_thresh:
                            height_map[i, j] = 0  # Deep water
                        elif blended_noise < water_thresh:
                            height_map[i, j] = 1  # Water
                        elif blended_noise < shore_thresh:
                            height_map[i, j] = 2  # Shoreline
                        elif blended_noise < low_hill_thresh:
                            height_map[i, j] = 3  # Low hills
                        elif blended_noise < med_hill_thresh:
                            height_map[i, j] = 4  # Medium hills
                        elif blended_noise < high_hill_thresh:
                            height_map[i, j] = 5  # High hills
                        else:
                            height_map[i, j] = 6  # Mountains
            self.progress_bar.setValue(i + 1)
            QApplication.processEvents()
        return self._smooth_terrain(height_map)

    def _perlin(self, i, j, freq, seed_offset=0):
        # Helper for consistent perlin noise with seed/offset
        return self.perlin_noise(
            i * freq + self._terrain_offset_x,
            j * freq + self._terrain_offset_y,
            seed=self._terrain_seed + seed_offset
        )

    def _create_falloff_mask(self):
        """Create a falloff mask for natural terrain boundaries"""
        falloff_mask = np.zeros((self.grid_size, self.grid_size))
        
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                # Calculate distance from center (0-1)
                x = i / self.grid_size * 2 - 1
                y = j / self.grid_size * 2 - 1
                
                # Calculate distance from center
                distance = np.sqrt(x * x + y * y)
                
                # Create smooth falloff using sigmoid function
                # This creates a gradual transition from center to edges
                falloff = 1.0 / (1.0 + np.exp((distance - 0.7) * 8))
                
                # Add some noise to make the falloff more natural
                noise_val = self.perlin_noise(i * 0.02, j * 0.02) * 0.1
                falloff += noise_val
                
                # Clamp to 0-1 range
                falloff = max(0, min(1, falloff))
                
                falloff_mask[i, j] = falloff
        
        return falloff_mask
    
    def _smooth_terrain(self, height_map):
        """Apply gentle smoothing to create natural terrain transitions"""
        smoothed = height_map.copy()
        kernel_size = 3
        
        for i in range(kernel_size//2, self.grid_size - kernel_size//2):
            for j in range(kernel_size//2, self.grid_size - kernel_size//2):
                # Calculate weighted average of surrounding cells
                total = 0
                weight_sum = 0
                
                for di in range(-kernel_size//2, kernel_size//2 + 1):
                    for dj in range(-kernel_size//2, kernel_size//2 + 1):
                        ni, nj = i + di, j + dj
                        if 0 <= ni < self.grid_size and 0 <= nj < self.grid_size:
                            # Center cell has higher weight
                            weight = 1.0 if di == 0 and dj == 0 else 0.5
                            total += height_map[ni, nj] * weight
                            weight_sum += weight
                
                if weight_sum > 0:
                    avg = total / weight_sum
                    # Preserve topographic features with gentle rounding
                    if avg < 1.3:
                        smoothed[i, j] = 1  # Water
                    elif avg < 2.3:
                        smoothed[i, j] = 2  # Shoreline
                    elif avg < 3.3:
                        smoothed[i, j] = 3  # Low hills
                    elif avg < 4.3:
                        smoothed[i, j] = 4  # Medium hills
                    elif avg < 5.3:
                        smoothed[i, j] = 5  # High hills
                    elif avg < 6.3:
                        smoothed[i, j] = 6  # Mountain
                    else:
                        smoothed[i, j] = 7  # High mountains
        
        return smoothed
    
    def _generate_hills(self):
        """Generate a regular topographic map with gradual elevation changes"""
        height_map = np.zeros((self.grid_size, self.grid_size))
        
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                # Create natural topographic terrain with multiple octaves
                noise = 0
                amplitude = 1.0
                frequency = 0.02 * (1000 / self.grid_size)
                
                for octave in range(4):
                    noise += self.perlin_noise(i * frequency, j * frequency) * amplitude
                    amplitude *= 0.6
                    frequency *= 1.8
                
                # Normalize noise to 0-1 range for consistent elevation mapping
                normalized_noise = (noise + 1) / 2
                
                # Create hills terrain with all types except deep water and high mountains
                # This creates a natural progression from water to mountains
                if normalized_noise < 0.08:
                    height_map[i, j] = 1  # Water (not deep water)
                elif normalized_noise < 0.18:
                    height_map[i, j] = 2  # Shoreline
                elif normalized_noise < 0.32:
                    height_map[i, j] = 3  # Low hills
                elif normalized_noise < 0.52:
                    height_map[i, j] = 4  # Medium hills
                elif normalized_noise < 0.72:
                    height_map[i, j] = 5  # High hills
                else:
                    height_map[i, j] = 6  # Mountains (not high mountains)
            
            self.progress_bar.setValue(i + 1)
            QApplication.processEvents()
        
        return self._smooth_terrain(height_map)
    
    def _generate_mountains(self):
        """Generate mountains with gradual rise, steep peaks, valleys, and varied slopes."""
        height_map = np.zeros((self.grid_size, self.grid_size))
        center_x, center_y = self.grid_size // 2, self.grid_size // 2
        max_dist = np.sqrt(center_x**2 + center_y**2)
        
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                # Large-scale gradient: radial rise from one side (e.g., left or bottom)
                grad = (i / self.grid_size) * 0.7 + (j / self.grid_size) * 0.3
                # Or radial: grad = np.sqrt((i-center_x)**2 + (j-center_y)**2) / max_dist
                # Multi-octave Perlin noise for local variation
                noise = 0
                amplitude = 1.0
                frequency = 0.02 * (1000 / self.grid_size)
                for octave in range(4):
                    noise += self.perlin_noise(i * frequency, j * frequency) * amplitude
                    amplitude *= 0.5
                    frequency *= 2.0
                # High-frequency noise for sharp peaks/valleys
                peak_noise = self.perlin_noise(i * 0.12, j * 0.12)
                # Blend gradient and noise
                base = 0.5 * grad + 0.5 * ((noise + 1) / 2)
                # Add sharp peaks/valleys
                base += 0.18 * peak_noise
                # Clamp to 0-1
                base = max(0, min(1, base))
                # Map to terrain heights
                if base < 0.07:
                    height_map[i, j] = 1  # Water (valleys)
                elif base < 0.16:
                    height_map[i, j] = 2  # Shoreline
                elif base < 0.28:
                    height_map[i, j] = 3  # Low hills (foothills)
                elif base < 0.45:
                    height_map[i, j] = 4  # Medium hills
                elif base < 0.65:
                    height_map[i, j] = 5  # High hills
                elif base < 0.85:
                    height_map[i, j] = 6  # Mountains
                else:
                    height_map[i, j] = 7  # High mountains (peaks)
            self.progress_bar.setValue(i + 1)
            QApplication.processEvents()
        return self._smooth_terrain(height_map)
    
    def _generate_islands(self):
        """Generate natural island terrain with smooth coastlines"""
        height_map = np.zeros((self.grid_size, self.grid_size))
        center_x, center_y = self.grid_size // 2, self.grid_size // 2
        max_dist = np.sqrt(center_x**2 + center_y**2)
        
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                # Distance from center
                dist = np.sqrt((i - center_x)**2 + (j - center_y)**2)
                normalized_dist = dist / max_dist
                
                # Add natural variation with multiple octaves
                noise = 0
                amplitude = 1.0
                frequency = 0.02
                
                for octave in range(3):
                    noise += self.perlin_noise(i * frequency, j * frequency) * amplitude
                    amplitude *= 0.5
                    frequency *= 2.0
                
                # Islands: natural land formation with smooth transitions
                if normalized_dist < 0.25 + noise * 0.1:
                    # Main island - mostly low hills with some medium hills
                    if noise > 0.2:
                        height_map[i, j] = 4  # Medium hills
                    else:
                        height_map[i, j] = 3  # Low hills
                elif normalized_dist < 0.35 + noise * 0.1:
                    # Shoreline transition
                    height_map[i, j] = 2  # Shoreline
                else:
                    # Water
                    height_map[i, j] = 1  # Water
            
            self.progress_bar.setValue(i + 1)
            QApplication.processEvents()
        
        return self._smooth_terrain(height_map)
    
    def _generate_steep_cliffs(self):
        """Generate two parallel steep cliffs with waviness, small random gaps, and slanted, variable-thickness land bridges that always connect both sides."""
        height_map = np.zeros((self.grid_size, self.grid_size))
        
        # Parameters for cliffs
        cliff_width = max(4, self.grid_size // 15)  # Width of each cliff
        gap_width = max(3, self.grid_size // 20)    # Width of the main gap between cliffs
        gap_spacing = max(10, self.grid_size // 8)  # Minimum rows between main gaps
        gap_length = max(3, self.grid_size // 25)   # How many rows the main gap spans
        
        # Waviness parameters
        waviness_amplitude = max(2, self.grid_size // 40)
        waviness_freq = 0.08 * (100 / self.grid_size)
        
        # Position cliffs symmetrically
        left_cliff_base = self.grid_size // 4
        right_cliff_base = self.grid_size - self.grid_size // 4 - cliff_width
        gap_col_base = left_cliff_base + cliff_width + (right_cliff_base - (left_cliff_base + cliff_width) - gap_width) // 2
        
        # Precompute main gap rows
        gap_rows = set()
        row = gap_spacing // 2
        while row < self.grid_size - gap_spacing:
            if np.random.rand() < 0.7:  # 70% chance to place a main gap at this interval
                for k in range(gap_length):
                    if row + k < self.grid_size:
                        gap_rows.add(row + k)
            row += gap_spacing + np.random.randint(-gap_spacing//3, gap_spacing//2)

        # Land bridge parameters
        num_bridges = max(2, self.grid_size // 30)
        possible_rows = list(range(self.grid_size // 8, self.grid_size - self.grid_size // 8))
        bridge_rows = sorted(np.random.choice(possible_rows, size=num_bridges, replace=False)) if possible_rows else []
        bridge_min_width = 2
        bridge_max_width = max(4, self.grid_size // 12)
        bridge_slant_range = max(6, self.grid_size // 10)
        bridge_length = max(self.grid_size // 6, 8)

        # For each bridge, precompute its slant, thickness profile, and row span
        bridges = []
        for bridge_row in bridge_rows:
            # Random slant direction: -1 (left), 1 (right)
            slant_dir = np.random.choice([-1, 1])
            # Start and end columns for the bridge (from left cliff to right cliff)
            wave_offset = int(waviness_amplitude * np.sin(bridge_row * waviness_freq + 2 * np.cos(bridge_row * waviness_freq * 0.7)))
            left_cliff_start = left_cliff_base + wave_offset
            right_cliff_start = right_cliff_base + wave_offset
            bridge_start_col = left_cliff_start + cliff_width - 2
            bridge_end_col = right_cliff_start
            # The bridge will span several rows (slanted)
            start_row = max(0, bridge_row - bridge_length // 2)
            end_row = min(self.grid_size - 1, bridge_row + bridge_length // 2)
            # Random slant offset
            slant_offset = np.random.randint(-bridge_slant_range, bridge_slant_range)
            # Precompute center and width for each row
            bridge_profile = []
            for idx, i in enumerate(range(start_row, end_row + 1)):
                t = idx / max(1, end_row - start_row)
                # Center moves from start_col to end_col, plus slant
                center = int((1 - t) * bridge_start_col + t * bridge_end_col + slant_dir * slant_offset * np.sin(t * np.pi))
                # Thickness varies sinusoidally/randomly
                thickness = int(bridge_min_width + (bridge_max_width - bridge_min_width) * (0.5 + 0.5 * np.sin(t * np.pi + np.random.uniform(-0.5, 0.5))))
                bridge_profile.append((i, center, thickness))
            bridges.append(bridge_profile)

        # For fast lookup: for each row, which bridge (if any) and its center/thickness
        bridge_row_map = {}
        for profile in bridges:
            for i, center, thickness in profile:
                bridge_row_map[i] = (center, thickness)

        for i in range(self.grid_size):
            # Add waviness to cliff positions
            wave_offset = int(waviness_amplitude * np.sin(i * waviness_freq + 2 * np.cos(i * waviness_freq * 0.7)))
            left_cliff_start = left_cliff_base + wave_offset
            right_cliff_start = right_cliff_base + wave_offset
            gap_col_start = gap_col_base + wave_offset

            # If this is a bridge row, get bridge center/thickness
            bridge_info = bridge_row_map.get(i, None)
            if bridge_info:
                bridge_center, bridge_width = bridge_info
                bridge_j_start = bridge_center - bridge_width // 2
                bridge_j_end = bridge_center + bridge_width // 2
                # Openings in cliffs should match the bridge
                left_opening_start = left_cliff_start + cliff_width - 2
                right_opening_start = right_cliff_start
                left_opening_width = max(2, bridge_width // 2)
                right_opening_width = max(2, bridge_width // 2)
            else:
                bridge_j_start = bridge_j_end = -1
                left_opening_start = right_opening_start = -1
                left_opening_width = right_opening_width = 0

            for j in range(self.grid_size):
                left_edge_gap = (j == left_cliff_start or j == left_cliff_start + cliff_width - 1) and np.random.rand() < 0.08
                right_edge_gap = (j == right_cliff_start or j == right_cliff_start + cliff_width - 1) and np.random.rand() < 0.08
                left_cliff_hole = left_cliff_start <= j < left_cliff_start + cliff_width and np.random.rand() < 0.04
                right_cliff_hole = right_cliff_start <= j < right_cliff_start + cliff_width and np.random.rand() < 0.04

                # Left slope
                if j < left_cliff_start:
                    slope = (j / max(1, left_cliff_start))
                    height_map[i, j] = 2 + 3 * slope
                # Left cliff
                elif left_cliff_start <= j < left_cliff_start + cliff_width:
                    if bridge_info and left_opening_start <= j < left_opening_start + left_opening_width and bridge_j_start <= j <= bridge_j_end:
                        height_map[i, j] = 3 if np.random.rand() < 0.7 else 2
                    elif left_edge_gap or left_cliff_hole:
                        height_map[i, j] = 1 + 0.5 * np.random.rand()
                    else:
                        rel = (j - left_cliff_start) / max(1, cliff_width-1)
                        height_map[i, j] = 5 + 2 * rel
                # Main gap between cliffs
                elif gap_col_start <= j < gap_col_start + gap_width:
                    if i in gap_rows:
                        height_map[i, j] = 2
                    elif bridge_info and bridge_j_start <= j <= bridge_j_end:
                        height_map[i, j] = 3 if np.random.rand() < 0.7 else 2
                    else:
                        height_map[i, j] = 1
                # Right cliff
                elif right_cliff_start <= j < right_cliff_start + cliff_width:
                    if bridge_info and right_opening_start <= j < right_opening_start + right_opening_width and bridge_j_start <= j <= bridge_j_end:
                        height_map[i, j] = 3 if np.random.rand() < 0.7 else 2
                    elif right_edge_gap or right_cliff_hole:
                        height_map[i, j] = 1 + 0.5 * np.random.rand()
                    else:
                        rel = 1 - (j - right_cliff_start) / max(1, cliff_width-1)
                        height_map[i, j] = 5 + 2 * rel
                # Right slope
                elif j >= right_cliff_start + cliff_width:
                    slope = (self.grid_size - 1 - j) / max(1, self.grid_size - (right_cliff_start + cliff_width))
                    height_map[i, j] = 2 + 3 * slope
                else:
                    if bridge_info and bridge_j_start <= j <= bridge_j_end:
                        height_map[i, j] = 3 if np.random.rand() < 0.7 else 2
                    else:
                        height_map[i, j] = 1 + 0.5 * np.random.rand()
            self.progress_bar.setValue(i + 1)
            QApplication.processEvents()
        
        return self._smooth_terrain(height_map)
    
    def _generate_spiral_land(self):
        """Generate natural spiral land pattern with smooth transitions"""
        height_map = np.zeros((self.grid_size, self.grid_size))
        center_x, center_y = self.grid_size // 2, self.grid_size // 2
        
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                # Distance from center
                dist = np.sqrt((i - center_x)**2 + (j - center_y)**2)
                max_dist = np.sqrt(center_x**2 + center_y**2)
                normalized_dist = dist / max_dist
                
                # Angle from center
                angle = np.arctan2(j - center_y, i - center_x)
                
                # Create natural spiral pattern
                spiral = np.sin(angle * 2 + dist * 0.05) * 0.15
                
                # Add natural variation
                noise = 0
                amplitude = 1.0
                frequency = 0.015
                
                for octave in range(2):
                    noise += self.perlin_noise(i * frequency, j * frequency) * amplitude
                    amplitude *= 0.5
                    frequency *= 2.0
                
                # Natural spiral land formation
                if normalized_dist > 0.85 + spiral + noise * 0.1:
                    # Border land - mostly low hills
                    height_map[i, j] = 3  # Low hills
                elif normalized_dist < 0.08 + noise * 0.05:
                    # Center island - medium hills
                    height_map[i, j] = 4  # Medium hills
                elif normalized_dist < 0.15 + spiral + noise * 0.1:
                    # Shoreline around center
                    height_map[i, j] = 2  # Shoreline
                else:
                    # Water in middle
                    height_map[i, j] = 1  # Water
            
            self.progress_bar.setValue(i + 1)
            QApplication.processEvents()
        
        return self._smooth_terrain(height_map)
    
    def keyPressEvent(self, event):
        # Keyboard shortcuts for zooming
        if event.key() == Qt.Key.Key_Plus and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.zoom_in()
        elif event.key() == Qt.Key.Key_Minus and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.zoom_out()
        elif event.key() == Qt.Key.Key_0 and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.reset_zoom()
        else:
            super().keyPressEvent(event)

    def optimize_route(self):
        # Get start and end coordinates
        start_col_str = self.start_col_num.text().strip()
        start_row_str = self.start_row_num.text().strip()
        end_col_str = self.end_col_num.text().strip()
        end_row_str = self.end_row_num.text().strip()
        
        # Validate coordinates
        if not (start_col_str and start_row_str and end_col_str and end_row_str):
            self.route_details.setText("Please enter all coordinates for start and end locations.")
            return
        
        try:
            # Convert coordinates to grid positions
            start_col = int(start_col_str) - 1  # Convert to 0-indexed column
            start_row = int(start_row_str) - 1  # Convert to 0-indexed row
            end_col = int(end_col_str) - 1
            end_row = int(end_row_str) - 1
            
            # Validate grid positions
            if not (0 <= start_row < self.grid_size and 0 <= start_col < self.grid_size and
                   0 <= end_row < self.grid_size and 0 <= end_col < self.grid_size):
                self.route_details.setText(f"Invalid coordinates. Use 1-{self.grid_size} for both column and row numbers.")
                return
            
            # Clear previous route
            self.clear_route()
            
            # Set start and end points
            self.start_point = (start_row, start_col)
            self.end_point = (end_row, end_col)
            
            # Simple pathfinding implementation (straight line for now)
            # TODO: Implement A* pathfinding algorithm that takes terrain costs into account
            self.route_path = self._find_path(start_row, start_col, end_row, end_col)
            
            # Update the grid widget
            self.grid_widget.update()
            
            # Update route details
            if self.route_path:
                total_cost = self._calculate_route_cost(self.route_path)
                self.route_details.setText(
                    f"Route from (Col A{start_col + 1}, Row B{start_row + 1}) "
                    f"to (Col A{end_col + 1}, Row B{end_row + 1})\n"
                    f"Path length: {len(self.route_path)} cells\n"
                    f"Total cost: {total_cost:.2f}\n"
                    f"(Simple pathfinding - A* algorithm to be implemented)"
                )
            else:
                self.route_details.setText("No valid path found between the specified points.")
            
        except (ValueError, IndexError):
            self.route_details.setText(f"Invalid coordinate format. Use 1-{self.grid_size} for both column and row numbers.")
    
    def _find_path(self, start_row, start_col, end_row, end_col):
        """A* pathfinding that avoids water, mountains, and high_mountains, and prevents direct water<->high_hills transitions."""
        import heapq
        grid = self.terrain_grid
        get_type = self.grid_widget._get_terrain_type
        terrain_types = self.terrain_types
        n = self.grid_size

        forbidden_types = {"water", "mountain", "high_mountains"}
        blue = "water"
        yellow = "high_hills"

        def heuristic(r, c):
            return abs(r - end_row) + abs(c - end_col)

        def is_valid_move(r1, c1, r2, c2):
            if not (0 <= r2 < n and 0 <= c2 < n):
                return False
            t1 = get_type(grid[r1, c1])
            t2 = get_type(grid[r2, c2])
            if t2 in forbidden_types:
                return False
            if (t1 == blue and t2 == yellow) or (t1 == yellow and t2 == blue):
                return False
            return True

        open_set = []
        heapq.heappush(open_set, (0 + heuristic(start_row, start_col), 0, (start_row, start_col), None))
        came_from = {}
        g_score = {(start_row, start_col): 0}
        closed_set = set()

        while open_set:
            _, cost, (r, c), prev = heapq.heappop(open_set)
            if (r, c) in closed_set:
                continue
            came_from[(r, c)] = prev
            if (r, c) == (end_row, end_col):
                path = []
                node = (r, c)
                while node is not None:
                    path.append(node)
                    node = came_from[node]
                return path[::-1]
            closed_set.add((r, c))
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r + dr, c + dc
                if is_valid_move(r, c, nr, nc) and (nr, nc) not in closed_set:
                    t2 = get_type(grid[nr, nc])
                    move_cost = terrain_types[t2]["cost"]
                    new_g = cost + move_cost
                    if (nr, nc) not in g_score or new_g < g_score[(nr, nc)]:
                        g_score[(nr, nc)] = new_g
                        heapq.heappush(open_set, (new_g + heuristic(nr, nc), new_g, (nr, nc), (r, c)))
        return []
    
    def _calculate_route_cost(self, path):
        """Calculate the total cost of the route based on terrain"""
        total_cost = 0
        for row, col in path:
            height = self.terrain_grid[row, col]
            terrain_type = self.grid_widget._get_terrain_type(height)
            total_cost += self.terrain_types[terrain_type]["cost"]
        return total_cost

    def clear_route(self):
        # Reset route data
        self.route_path = []
        self.start_point = None
        self.end_point = None
        self.grid_widget.update()


class RouteGridWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setMinimumSize(parent.grid_size * parent.cell_size, parent.grid_size * parent.cell_size)
        self.setMouseTracking(True)  # Enable mouse tracking for coordinate display
        
    def wheelEvent(self, event):
        # Handle zoom with mouse wheel
        if event.angleDelta().y() > 0:
            self.parent.zoom_in()
        else:
            self.parent.zoom_out()
    
    def mouseMoveEvent(self, event):
        # Show coordinates in status bar
        col = int(event.position().x() // self.parent.cell_size)
        row = int(event.position().y() // self.parent.cell_size)
        
        if 0 <= row < self.parent.grid_size and 0 <= col < self.parent.grid_size:
            height = self.parent.terrain_grid[row, col]
            terrain_type = self._get_terrain_type(height)
            terrain_cost = self.parent.terrain_types[terrain_type]["cost"]
            
            self.parent.status_bar.setText(
                f"Position: A{col + 1}, B{row + 1} | "
                f"Terrain: {terrain_type} | "
                f"Height: {height} | "
                f"Cost: {terrain_cost} | "
                f"Zoom: {self.parent.zoom_level:.1f}x | "
                f"Click to set coordinates"
            )
        else:
            self.parent.status_bar.setText(f"Zoom: {self.parent.zoom_level:.1f}x")
    
    def mousePressEvent(self, event):
        # Set coordinates on click
        col = int(event.position().x() // self.parent.cell_size)
        row = int(event.position().y() // self.parent.cell_size)
        
        if 0 <= row < self.parent.grid_size and 0 <= col < self.parent.grid_size:
            if event.button() == Qt.MouseButton.LeftButton:
                # Set start point
                self.parent.start_col_num.setText(str(col + 1))
                self.parent.start_row_num.setText(str(row + 1))
            elif event.button() == Qt.MouseButton.RightButton:
                # Set end point
                self.parent.end_col_num.setText(str(col + 1))
                self.parent.end_row_num.setText(str(row + 1))
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get visible area for performance optimization
        visible_rect = event.rect()
        start_col = max(0, int(visible_rect.x() // self.parent.cell_size))
        end_col = min(self.parent.grid_size, int((visible_rect.x() + visible_rect.width()) // self.parent.cell_size + 1))
        start_row = max(0, int(visible_rect.y() // self.parent.cell_size))
        end_row = min(self.parent.grid_size, int((visible_rect.y() + visible_rect.height()) // self.parent.cell_size + 1))
        
        # Draw terrain grid (only visible cells for performance)
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                x = col * self.parent.cell_size
                y = row * self.parent.cell_size
                
                # Get terrain type for this cell
                height = self.parent.terrain_grid[row, col]
                terrain_type = self._get_terrain_type(height)
                color = self.parent.terrain_types[terrain_type]["color"]
                
                # Draw cell
                painter.fillRect(x, y, self.parent.cell_size, self.parent.cell_size, QColor(color))
                
                # Draw border if cell size is large enough
                if self.parent.cell_size > 2:
                    painter.setPen(QPen(QColor("#333"), 1))
                    painter.drawRect(x, y, self.parent.cell_size, self.parent.cell_size)
        
        # Draw route path
        if self.parent.route_path:
            painter.setPen(QPen(QColor("#FFFF00"), max(2, self.parent.cell_size // 3)))
            for i in range(len(self.parent.route_path) - 1):
                start = self.parent.route_path[i]
                end = self.parent.route_path[i + 1]
                x1 = start[1] * self.parent.cell_size + self.parent.cell_size // 2
                y1 = start[0] * self.parent.cell_size + self.parent.cell_size // 2
                x2 = end[1] * self.parent.cell_size + self.parent.cell_size // 2
                y2 = end[0] * self.parent.cell_size + self.parent.cell_size // 2
                painter.drawLine(x1, y1, x2, y2)
        
        # Draw start and end points
        if self.parent.start_point:
            row, col = self.parent.start_point
            x = col * self.parent.cell_size
            y = row * self.parent.cell_size
            painter.fillRect(x, y, self.parent.cell_size, self.parent.cell_size, QColor("#4CAF50"))
            painter.setPen(QPen(QColor("#45a049"), 2))
            painter.drawRect(x, y, self.parent.cell_size, self.parent.cell_size)
        
        if self.parent.end_point:
            row, col = self.parent.end_point
            x = col * self.parent.cell_size
            y = row * self.parent.cell_size
            painter.fillRect(x, y, self.parent.cell_size, self.parent.cell_size, QColor("#f44336"))
            painter.setPen(QPen(QColor("#da190b"), 2))
            painter.drawRect(x, y, self.parent.cell_size, self.parent.cell_size)
    
    def _get_terrain_type(self, height):
        if height == 0:
            return "deep_water"
        elif height == 1:
            return "water"
        elif height == 2:
            return "shoreline"
        elif height == 3:
            return "low_hills"
        elif height == 4:
            return "medium_hills"
        elif height == 5:
            return "high_hills"
        elif height == 6:
            return "mountain"
        elif height == 7:
            return "high_mountains"
        elif height == 8:
            return "temple_core"
        elif height == 9:
            return "temple_wall"
        else:
            return "high_mountains"


class StorageCalculator(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inventory/Storage Calculator")
        self.setFixedSize(700, 500)
        self.setStyleSheet("""
            QDialog {
                background-color: #23243a;
                color: #00FFFF;
            }
        """)
        layout = QVBoxLayout(self)
        # Input area
        input_layout = QHBoxLayout()
        self.rate_input = QLineEdit()
        self.rate_input.setPlaceholderText("Production rate (items/min)")
        self.time_input = QLineEdit()
        self.time_input.setPlaceholderText("Time (minutes)")
        calc_btn = QPushButton("Calculate Storage")
        calc_btn.clicked.connect(self.calculate_storage)
        input_layout.addWidget(self.rate_input)
        input_layout.addWidget(self.time_input)
        input_layout.addWidget(calc_btn)
        layout.addLayout(input_layout)
        # Placeholder for results
        self.result_area = QLabel("Storage calculation results will appear here.")
        self.result_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_area.setStyleSheet("background-color: #1a1a1a; color: #00FFFF; border: 1px solid #FF00FF; font-size: 18px;")
        layout.addWidget(self.result_area, 1)
    def calculate_storage(self):
        try:
            rate = float(self.rate_input.text())
            time = float(self.time_input.text())
            total_items = rate * time
            containers = int((total_items + 2700 - 1) // 2700)  # 2700 is a standard container size
            self.result_area.setText(f"Total items: {total_items:.0f}\nRecommended containers: {containers}\n(Feature coming soon)")
        except Exception:
            self.result_area.setText("Please enter valid numbers for rate and time.")

class PerformanceMonitor(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Performance Monitor")
        self.setFixedSize(600, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #23243a;
                color: #00FFFF;
            }
        """)
        layout = QVBoxLayout(self)
        # Placeholder for performance stats
        self.stats_area = QLabel("Performance stats (FPS, CPU, GPU) will appear here.\n(Feature coming soon)")
        self.stats_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stats_area.setStyleSheet("background-color: #1a1a1a; color: #00FFFF; border: 1px solid #FF00FF; font-size: 18px;")
        layout.addWidget(self.stats_area, 1)

class CustomThemeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent # Store reference to parent (SatisfactoryGuide)
        self.setWindowTitle("Custom Theme Settings")
        self.setFixedSize(400, 350) # Increased size to accommodate new controls
        self.setStyleSheet("""
            QDialog {
                background-color: #2a2a2a;
                color: #00FFFF;
            }
            QLabel {
                color: #00FFFF;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #FF00FF;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #FF33FF;
            }
            QLineEdit { /* For color display */
                background-color: #232323;
                color: #FFFFFF;
                border: 1px solid #FF00FF;
                border-radius: 3px;
                padding: 4px;
            }
            QComboBox {
                background-color: #232323;
                color: #FFFFFF;
                border: 1px solid #FF00FF;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #232323;
                color: #FFFFFF;
                selection-background-color: #FF00FF;
                selection-color: #FFFFFF;
            }
        """)
        layout = QVBoxLayout(self)

        # Current color values (initialize with parent's current custom theme settings)
        self.bg_color = self.parent_app.custom_bg_color
        self.text_color = self.parent_app.custom_text_color
        self.accent_color = self.parent_app.custom_accent_color
        self.gradient_type = self.parent_app.custom_gradient_type

        # Background Color
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("Background Color:"))
        self.bg_color_display = QLineEdit(self.bg_color.name()) # Display current color hex
        self.bg_color_display.setReadOnly(True)
        self.bg_color_display.setStyleSheet(f"background-color: {self.bg_color.name()};")
        bg_btn = QPushButton("Pick...")
        bg_btn.clicked.connect(self._pick_bg_color)
        bg_layout.addWidget(self.bg_color_display)
        bg_layout.addWidget(bg_btn)
        layout.addLayout(bg_layout)

        # Text Color
        text_layout = QHBoxLayout()
        text_layout.addWidget(QLabel("Text Color:"))
        self.text_color_display = QLineEdit(self.text_color.name())
        self.text_color_display.setReadOnly(True)
        self.text_color_display.setStyleSheet(f"background-color: {self.text_color.name()};")
        text_btn = QPushButton("Pick...")
        text_btn.clicked.connect(self._pick_text_color)
        text_layout.addWidget(self.text_color_display)
        text_layout.addWidget(text_btn)
        layout.addLayout(text_layout)

        # Accent Color
        accent_layout = QHBoxLayout()
        accent_layout.addWidget(QLabel("Accent Color:"))
        self.accent_color_display = QLineEdit(self.accent_color.name())
        self.accent_color_display.setReadOnly(True)
        self.accent_color_display.setStyleSheet(f"background-color: {self.accent_color.name()};")
        accent_btn = QPushButton("Pick...")
        accent_btn.clicked.connect(self._pick_accent_color)
        accent_layout.addWidget(self.accent_color_display)
        accent_layout.addWidget(accent_btn)
        layout.addLayout(accent_layout)

        # Gradient Type
        gradient_layout = QHBoxLayout()
        gradient_layout.addWidget(QLabel("Gradient Type:"))
        self.gradient_combo = QComboBox()
        self.gradient_combo.addItems(["Linear", "Radial", "Conical"])
        self.gradient_combo.setCurrentText(self.gradient_type) # Set current selected gradient type
        self.gradient_combo.currentIndexChanged.connect(self._update_gradient_type)
        gradient_layout.addWidget(self.gradient_combo)
        layout.addLayout(gradient_layout)

        layout.addStretch() # Push buttons to bottom

        # Apply and Reset buttons
        button_layout = QHBoxLayout()

        apply_btn = QPushButton("Apply Custom Theme")
        apply_btn.clicked.connect(self.apply_custom_theme)
        button_layout.addWidget(apply_btn)

        reset_btn = QPushButton("Reset to Default")
        reset_btn.clicked.connect(self._reset_theme_to_default)
        button_layout.addWidget(reset_btn)

        layout.addLayout(button_layout)

    def _pick_bg_color(self):
        color = QColorDialog.getColor(self.bg_color, self, "Select Background Color")
        if color.isValid():
            self.bg_color = color
            self.bg_color_display.setText(color.name())
            self.bg_color_display.setStyleSheet(f"background-color: {color.name()};")

    def _pick_text_color(self):
        color = QColorDialog.getColor(self.text_color, self, "Select Text Color")
        if color.isValid():
            self.text_color = color
            self.text_color_display.setText(color.name())
            self.text_color_display.setStyleSheet(f"background-color: {color.name()};")

    def _pick_accent_color(self):
        color = QColorDialog.getColor(self.accent_color, self, "Select Accent Color")
        if color.isValid():
            self.accent_color = color
            self.accent_color_display.setText(color.name())
            self.accent_color_display.setStyleSheet(f"background-color: {color.name()};")

    def _update_gradient_type(self, index):
        self.gradient_type = self.gradient_combo.currentText()

    def apply_custom_theme(self):
        if self.parent_app:
            self.parent_app.set_custom_theme(
                self.bg_color,
                self.text_color,
                self.accent_color,
                self.gradient_type
            )
        QMessageBox.information(self, "Custom Theme", "Custom theme applied!")

    def _reset_theme_to_default(self):
        # Reset colors and gradient type to initial defaults from parent_app
        self.bg_color = QColor(35, 36, 58) # Matches SatisfactoryGuide initial default
        self.text_color = QColor(0, 255, 255) # Matches SatisfactoryGuide initial default
        self.accent_color = QColor(255, 0, 255) # Matches SatisfactoryGuide initial default
        self.gradient_type = "Linear" # Matches SatisfactoryGuide initial default

        # Update UI elements to reflect default values
        self.bg_color_display.setText(self.bg_color.name())
        self.bg_color_display.setStyleSheet(f"background-color: {self.bg_color.name()};")

        self.text_color_display.setText(self.text_color.name())
        self.text_color_display.setStyleSheet(f"background-color: {self.text_color.name()};")

        self.accent_color_display.setText(self.accent_color.name())
        self.accent_color_display.setStyleSheet(f"background-color: {self.accent_color.name()};")

        self.gradient_combo.setCurrentText(self.gradient_type)

        # Apply the reset theme
        self.apply_custom_theme()
        QMessageBox.information(self, "Custom Theme", "Theme reset to default!")

class FontSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = parent # Store reference to parent
        self.setWindowTitle("Font Size/Style Settings")
        self.setFixedSize(400, 250)
        self.setStyleSheet("""
            QDialog {
                background-color: #2a2a2a;
                color: #00FFFF;
            }
            QLabel {
                color: #00FFFF;
                font-size: 13px;
                font-weight: bold;
            }
            QSpinBox, QComboBox {
                background-color: #232323;
                color: #FFFFFF;
                border: 1px solid #FF00FF;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #232323;
                color: #FFFFFF;
                selection-background-color: #FF00FF;
                selection-color: #FFFFFF;
            }
            QPushButton {
                background-color: #FF00FF;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #FF33FF;
            }
        """)
        layout = QVBoxLayout(self)
        # Font size
        font_size_layout = QHBoxLayout()
        font_size_label = QLabel("Font Size:")
        self.font_size_spinbox = QSpinBox()
        self.font_size_spinbox.setRange(8, 24)
        # Initialize with current font size from parent_app
        if self.parent_app and QApplication.instance():
            self.font_size_spinbox.setValue(QApplication.instance().font().pointSize())
        else:
            self.font_size_spinbox.setValue(11) # Default if parent_app not available

        font_size_layout.addWidget(font_size_label)
        font_size_layout.addWidget(self.font_size_spinbox)
        layout.addLayout(font_size_layout)
        # Font style
        font_style_layout = QHBoxLayout()
        font_style_label = QLabel("Font Style:")
        self.font_style_combo = QComboBox()
        self.font_style_combo.addItems(QFontDatabase.families()) # Get all available font families
        # Initialize with current font family from parent_app
        if self.parent_app and QApplication.instance():
            self.font_style_combo.setCurrentText(QApplication.instance().font().family())
        else:
            self.font_style_combo.setCurrentText("Arial") # Default if parent_app not available
        
        font_style_layout.addWidget(font_style_label)
        font_style_layout.addWidget(self.font_style_combo)
        layout.addLayout(font_style_layout)
        # Apply button
        apply_btn = QPushButton("Apply Font Settings")
        apply_btn.clicked.connect(self.apply_font_settings)
        layout.addWidget(apply_btn)

    def apply_font_settings(self):
        selected_size = self.font_size_spinbox.value()
        selected_family = self.font_style_combo.currentText()
        if self.parent_app:
            self.parent_app.set_application_font(selected_family, selected_size)
        QMessageBox.information(self, "Font Settings", f"Font set to {selected_family}, Size: {selected_size}.")

class StartupToolDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Startup Tool Settings")
        self.setFixedSize(400, 200)
        self.setStyleSheet("""
            QDialog {
                background-color: #2a2a2a;
                color:rgb(0, 221, 255);
            }
            QLabel {
                color: #00FFFF;
                font-size: 13px;
                font-weight: bold;
            }
            QComboBox {
                background-color: #232323;
                color: #FFFFFF;
                border: 1px solid #FF00FF;
                border-radius: 5px;
                padding: 5px;
                font-size: 12px;
            }
            QComboBox QAbstractItemView {
                background-color: #232323;
                color: #FFFFFF;
                selection-background-color: #FF00FF;
                selection-color: #FFFFFF;
            }
            QPushButton {
                background-color: #FF00FF;
                color: #FFFFFF;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #FF33FF;
            }
        """)
        layout = QVBoxLayout(self)
        # Select tool
        tool_select_layout = QHBoxLayout()
        tool_label = QLabel("Select Startup Tool:")
        self.tool_combo = QComboBox()
        self.tool_combo.addItems([
            "None",
            "Production Calculator",
            "Quick Reference",
            "Power Grid Simulator",
            "Factory Layout Planner",
            "Production Chain Visualizer",
            "Train/Truck Route Optimizer",
            "Inventory/Storage Calculator",
            "Performance Monitor"
        ])
        tool_select_layout.addWidget(tool_label)
        tool_select_layout.addWidget(self.tool_combo)
        layout.addLayout(tool_select_layout)
        # Apply button
        apply_btn = QPushButton("Set Startup Tool")
        apply_btn.clicked.connect(self.set_startup_tool)
        layout.addWidget(apply_btn)

    def set_startup_tool(self):
        selected_tool = self.tool_combo.currentText()
        QMessageBox.information(self, "Startup Tool", f"Startup tool set to: {selected_tool} (Functionality to apply on next launch coming soon).")

    def set_continuous_conveyor_enabled(self, enabled):
        self.continuous_conveyor_enabled = enabled

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for a modern look
    
    # Set application-wide font
    font = QFont("Arial", 10)
    app.setFont(font)
    
    window = SatisfactoryGuide()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 