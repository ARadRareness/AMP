import sys
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QTextEdit,
    QPushButton,
    QComboBox,
    QLabel,
)
from amp_lib import OpenAIClient


class PromptTester(QWidget):
    def __init__(self):
        super().__init__()
        self.client = OpenAIClient(api_key="", base_url="http://127.0.0.1:17173")
        self.models = [model.id for model in self.client.models.list()]
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Top section: System message, Input, and Submit button
        top_layout = QHBoxLayout()

        # System message
        system_layout = QVBoxLayout()
        system_label = QLabel("System Message:")
        self.system_input = QTextEdit()
        self.system_input.setFixedHeight(100)
        system_layout.addWidget(system_label)
        system_layout.addWidget(self.system_input)

        # User prompt
        prompt_layout = QVBoxLayout()
        prompt_label = QLabel("User Prompt:")
        self.prompt_input = QTextEdit()
        self.prompt_input.setFixedHeight(100)
        prompt_layout.addWidget(prompt_label)
        prompt_layout.addWidget(self.prompt_input)

        self.submit_button = QPushButton("Submit")
        self.submit_button.clicked.connect(self.on_submit)

        top_layout.addLayout(system_layout, stretch=2)
        top_layout.addLayout(prompt_layout, stretch=2)
        top_layout.addWidget(self.submit_button, stretch=1)
        layout.addLayout(top_layout)

        # Grid section: 3x3 grid of model selectors and text fields
        grid_layout = QGridLayout()
        self.cells = []
        for row in range(3):
            for col in range(3):
                cell_layout = QVBoxLayout()
                model_selector = QComboBox()
                model_selector.addItems([""] + self.models)

                # Set a default model if available
                index = row * 3 + col
                if index < len(self.models):
                    model_selector.setCurrentText(self.models[index])

                text_field = QTextEdit()
                cell_layout.addWidget(model_selector)
                cell_layout.addWidget(text_field)
                grid_layout.addLayout(cell_layout, row, col)
                self.cells.append((model_selector, text_field))
        layout.addLayout(grid_layout)

        self.setLayout(layout)
        self.setWindowTitle("Prompt Tester")
        self.show()

    def on_submit(self):
        system_message = self.system_input.toPlainText().strip()
        user_prompt = self.prompt_input.toPlainText()

        for model_selector, text_field in self.cells:
            model = model_selector.currentText()
            if model:
                messages = []
                if system_message:
                    messages.append({"role": "system", "content": system_message})
                messages.append({"role": "user", "content": user_prompt})

                for i in range(3):
                    try:
                        response = self.client.chat_completion(
                            model=model,
                            messages=messages,
                            max_tokens=8192,
                        )
                        # Extract only the content from the response
                        content = response["choices"][0]["message"]["content"]
                        text_field.setText(content)
                        break
                    except Exception as e:
                        print(e)
            else:
                text_field.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = PromptTester()
    sys.exit(app.exec())
