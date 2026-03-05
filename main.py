import sys
import os
import json
import requests
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QTextEdit, QLineEdit, QPushButton, QHBoxLayout, QLabel)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QFont, QIcon, QLinearGradient, QColor, QPalette, QImage, QPixmap
from chat_history import ChatHistory
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class NumenorChatbot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.chat_history = ChatHistory(agent_name="numenor")
        self.conversation_context = []
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.type_next_word)
        self.current_message = ""
        self.words_to_type = []
        self.current_word_index = 0
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Numenor Chatbot")
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setFixedSize(400, 600)  # Reverted to original size
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Create top section with info and logo
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)
        
        # Add info panel in top left
        info_panel = QLabel()
        info_panel.setStyleSheet("""
            QLabel {
                background-color: rgba(42, 42, 42, 0.9);
                color: #50C878;
                border: 2px solid #CD7F32;
                border-radius: 8px;
                padding: 8px;
                font-family: 'Times New Roman', serif;
                min-width: 130px;
                max-width: 130px;
            }
        """)
        info_text = """
        <b>NUMENOR</b><br>
        <i>Salamanders Chapter</i><br>
        <br>
        A battle-hardened Astartes<br>
        of the XVIII Legion.<br>
        <br>
        Known for his wisdom and<br>
        devotion to Vulkan's teachings.<br>
        <br>
        <i>"Into the fires of battle,<br>
        unto the anvil of war!"</i>
        """
        info_panel.setText(info_text)
        info_panel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        top_layout.addWidget(info_panel)
        
        # Add logo in top right
        logo_label = QLabel()
        try:
            logo_pixmap = QPixmap("image/28255106a5c0812bcd5e7bd491a2c6fb.jpg")
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
        
        # Chat display area with metallic frame
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #2a2a2a;
                color: #50C878;
                border: 3px solid;
                border-image: linear-gradient(45deg, #CD7F32, #B87333, #CD7F32) 1;
                border-radius: 8px;
                padding: 10px;
                font-family: 'Times New Roman', serif;
            }
        """)
        layout.addWidget(self.chat_display, 1)  # Added stretch factor
        
        # Input area with metallic frame
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        self.input_field = QLineEdit()
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #2a2a2a;
                color: #ffffff;
                border: 3px solid;
                border-image: linear-gradient(45deg, #CD7F32, #B87333, #CD7F32) 1;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)
        
        send_button = QPushButton("Send")
        send_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #006400,
                    stop: 0.5 #005000,
                    stop: 1 #006400
                );
                color: white;
                border: 2px solid #004000;
                border-radius: 8px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #008000,
                    stop: 0.5 #006400,
                    stop: 1 #008000
                );
                border: 2px solid #005000;
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #004000,
                    stop: 0.5 #003000,
                    stop: 1 #004000
                );
            }
        """)
        send_button.clicked.connect(self.send_message)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(send_button)
        layout.addLayout(input_layout)
        
        # Set the background with enhanced bronze gradient
        central_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #CD7F32,
                    stop: 0.25 #B87333,
                    stop: 0.5 #8B0000,
                    stop: 0.75 #B87333,
                    stop: 1 #CD7F32
                );
                border: 2px solid #004000;
                border-radius: 15px;
                margin: 10px;
            }
            
            QWidget::hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #D2691E,
                    stop: 0.25 #CD7F32,
                    stop: 0.5 #A52A2A,
                    stop: 0.75 #CD7F32,
                    stop: 1 #D2691E
                );
            }
        """)
        
        # Set the window background color to match the border
        self.setStyleSheet("""
            QMainWindow {
                background-color: #004000;
            }
        """)
        
        # Add initial greeting
        initial_greeting = "Brother, I am Numenor. The fires of Nocturne burn within our hearts. How may I assist you in our sacred duty to the Emperor?"
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
            self.chat_display.append(f"<p style='color: #50C878;'><b>Numenor:</b> {self.current_message}</p>")
            self.current_word_index += 1
        else:
            self.typing_timer.stop()
            # Add the final message to chat history
            self.chat_display.append("")  # Add a blank line after the message
        
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
                "You are Numenor, a battle-hardened Astartes of the Salamanders Chapter. "
                "Speak in brief, direct, and stoic phrases. Use formal, grim, and brotherly tone. "
                "Avoid long elaborations. Mention Nocturne, fire, and duty only if context demands. "
                "Responses must be 1–2 sentences only. Address the user as 'Brother'."
            )

            messages = [
                {"role": "system", "content": system_message}
            ] + self.conversation_context[-4:]

            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "qwen2.5vl:7b",
                    "messages": messages,
                    "stream": False
                },
                timeout=30
            )

            if response.status_code == 200:
                content = response.json()["message"]["content"]
                max_word_count = 35
                shortened = ' '.join(content.split()[:max_word_count])
                return shortened
            else:
                print(f"API Error: {response.status_code} - {response.text}")
                return "Brother, the machine spirit is troubled. Let us try again."
                
        except requests.exceptions.Timeout:
            print("Request timed out")
            return "Brother, the machine spirit is slow. Let us try again."
        except requests.exceptions.ConnectionError:
            print("Connection error")
            return "Brother, I cannot reach the machine spirit. Verify the rites."
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "Brother, something stirs in the code. We endure."

    def add_user_message(self, message: str):
        """Add a user message to the chat display."""
        self.chat_display.append(f"<p style='color: #ffffff;'><b>You:</b> {message}</p>")
        
    def mousePressEvent(self, event):
        """Handle window dragging."""
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        """Handle window dragging."""
        delta = event.globalPosition().toPoint() - self.oldPos
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for a modern look
    
    # Set application-wide font
    font = QFont("Times New Roman", 10)
    app.setFont(font)
    
    window = NumenorChatbot()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 