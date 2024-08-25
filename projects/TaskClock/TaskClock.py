import tkinter as tk
from tkinter import messagebox, simpledialog
import json
import json
import os

from amp_lib import AmpClient


class TaskClock:
    def __init__(self, master):
        self.master = master
        self.master.title("Task Clock")
        self.data_filename = f"{os.path.splitext(os.path.basename(__file__))[0]}.dat"
        self.tasks = self.load_tasks()
        self.current_task_index = None
        self.remaining_time = 0
        self.timer_running = False
        self.auto_reset = tk.BooleanVar()
        self.use_telegram = tk.BooleanVar(value=True)  # Set default value to True
        self.use_messagebox = tk.BooleanVar()
        self.timer_job = None  # Add this line to initialize the timer job
        self.amp_client = AmpClient()
        self.create_widgets()

    def create_widgets(self):
        # Task input
        tk.Label(self.master, text="Task:").grid(row=0, column=0, sticky="e")
        self.task_entry = tk.Entry(self.master, width=30)
        self.task_entry.grid(row=0, column=1, columnspan=2, padx=5, pady=5)
        tk.Button(self.master, text="Add Task", command=self.add_task).grid(
            row=0, column=3, padx=5, pady=5
        )

        # Task list
        self.task_listbox = tk.Listbox(self.master, width=40, height=10)
        self.task_listbox.grid(row=1, column=0, columnspan=3, padx=5, pady=5)
        self.update_task_list()

        # Move buttons
        tk.Button(self.master, text="↑", command=self.move_up).grid(
            row=1, column=3, sticky="n", padx=5, pady=5
        )
        tk.Button(self.master, text="↓", command=self.move_down).grid(
            row=1, column=3, sticky="s", padx=5, pady=5
        )

        # Task management buttons
        tk.Button(self.master, text="Change Name", command=self.change_name).grid(
            row=2, column=0, padx=5, pady=5
        )
        tk.Button(self.master, text="Edit Duration", command=self.edit_duration).grid(
            row=2, column=1, padx=5, pady=5
        )
        tk.Button(self.master, text="Remove Task", command=self.remove_task).grid(
            row=2, column=2, padx=5, pady=5
        )

        # Add a new button to reset completed tasks
        tk.Button(
            self.master, text="Reset Completed", command=self.reset_completed_tasks
        ).grid(row=2, column=3, padx=5, pady=5)

        # Timer display
        self.timer_label = tk.Label(self.master, text="00:00", font=("Arial", 24))
        self.timer_label.grid(row=3, column=0, columnspan=4, pady=10)

        # Start/Pause button and time adjustment buttons
        button_frame = tk.Frame(self.master)
        button_frame.grid(row=4, column=0, columnspan=4, pady=5)

        self.start_pause_button = tk.Button(
            button_frame, text="Start Timer", command=self.toggle_timer
        )
        self.start_pause_button.pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="+1", command=lambda: self.adjust_timer(1)).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(button_frame, text="-1", command=lambda: self.adjust_timer(-1)).pack(
            side=tk.LEFT, padx=5
        )
        # Add restart button
        tk.Button(button_frame, text="Restart", command=self.restart_timer).pack(
            side=tk.LEFT, padx=5
        )

        # Modify the auto-reset checkbox row
        self.auto_reset_checkbox = tk.Checkbutton(
            self.master, text="Auto-reset and restart", variable=self.auto_reset
        )
        self.auto_reset_checkbox.grid(row=5, column=0, columnspan=2, pady=5, sticky="w")

        # Update the Telegram checkbox
        self.telegram_checkbox = tk.Checkbutton(
            self.master, text="Telegram", variable=self.use_telegram
        )
        self.telegram_checkbox.select()  # Select the checkbox by default
        self.telegram_checkbox.grid(row=5, column=2, pady=5, sticky="w")

        # Add Messagebox checkbox
        self.messagebox_checkbox = tk.Checkbutton(
            self.master, text="Messagebox", variable=self.use_messagebox
        )
        self.messagebox_checkbox.grid(row=5, column=3, pady=5, sticky="w")

    def add_task(self):
        task_name = self.task_entry.get().strip()
        if task_name:
            duration = simpledialog.askinteger(
                "Task Duration",
                "Enter task duration (minutes):",
                initialvalue=20,
                minvalue=0,
                maxvalue=180,
            )
            if duration is not None:
                self.tasks.append({"name": task_name, "duration": duration})
                self.task_entry.delete(0, tk.END)
                self.update_task_list()
                self.save_tasks()

    def edit_duration(self):
        selected = self.task_listbox.curselection()
        if selected:
            index = selected[0]
            task = self.tasks[index]
            new_duration = simpledialog.askinteger(
                "Edit Duration",
                f"Enter new duration for '{task['name']}' (minutes):",
                initialvalue=task["duration"],
                minvalue=0,
                maxvalue=180,
            )
            if new_duration is not None:
                task["duration"] = new_duration
                self.update_task_list()
                self.save_tasks()

    def change_name(self):
        selected = self.task_listbox.curselection()
        if selected:
            index = selected[0]
            task = self.tasks[index]
            new_name = simpledialog.askstring(
                "Change Name",
                f"Enter new name for '{task['name']}':",
                initialvalue=task["name"],
            )
            if new_name:
                task["name"] = new_name
                self.update_task_list()
                self.save_tasks()

    def remove_task(self):
        selected = self.task_listbox.curselection()
        if selected:
            index = selected[0]
            task = self.tasks[index]
            if messagebox.askyesno(
                "Remove Task", f"Are you sure you want to remove '{task['name']}'?"
            ):
                del self.tasks[index]
                self.update_task_list()
                self.save_tasks()

    def update_task_list(self):
        self.task_listbox.delete(0, tk.END)
        for i, task in enumerate(self.tasks):
            task_text = f"{task['name']} ({task['duration']} min)"
            if "completed" in task and task["completed"]:
                task_text = f"✓ {task_text}"
            if self.current_task_index is not None and i == self.current_task_index:
                task_text = f"* {task_text}"
            self.task_listbox.insert(tk.END, task_text)

    def move_up(self):
        selected = self.task_listbox.curselection()
        if selected and selected[0] > 0:
            index = selected[0]
            self.tasks[index - 1], self.tasks[index] = (
                self.tasks[index],
                self.tasks[index - 1],
            )
            self.update_task_list()
            self.task_listbox.selection_set(index - 1)
            self.save_tasks()

    def move_down(self):
        selected = self.task_listbox.curselection()
        if selected and selected[0] < len(self.tasks) - 1:
            index = selected[0]
            self.tasks[index], self.tasks[index + 1] = (
                self.tasks[index + 1],
                self.tasks[index],
            )
            self.update_task_list()
            self.task_listbox.selection_set(index + 1)
            self.save_tasks()

    def toggle_timer(self):
        if not self.timer_running:
            if self.current_task_index is None:
                self.restart_timer()
            else:
                self.start_timer()
        else:
            self.pause_timer()

    def start_timer(self):
        if self.current_task_index is None:
            self.current_task_index = next(
                (
                    i
                    for i, task in enumerate(self.tasks)
                    if not task.get("completed", False)
                ),
                None,
            )
            if self.current_task_index is not None:
                self.remaining_time = (
                    self.tasks[self.current_task_index]["duration"] * 60
                )

        self.timer_running = True
        self.start_pause_button.config(text="Pause Timer")
        self.update_timer()
        self.update_task_list()

    def pause_timer(self):
        self.timer_running = False
        self.start_pause_button.config(text="Start Timer")

    def update_timer(self):
        if self.timer_running and self.remaining_time > 0:
            self.update_timer_display()
            self.remaining_time -= 1
            self.timer_job = self.master.after(1000, self.update_timer)
        elif self.timer_running:
            self.timer_label.config(text="00:00")
            current_task = self.tasks[self.current_task_index]

            # Mark the current task as completed
            current_task["completed"] = True

            # Send notifications only if the task duration is not 0
            if current_task["duration"] > 0:
                if self.use_telegram.get():
                    self.telegram(current_task)
                if self.use_messagebox.get():
                    self.show_task_completed_messagebox(current_task)

            # Find the next uncompleted task
            self.current_task_index = next(
                (
                    i
                    for i, task in enumerate(self.tasks)
                    if not task.get("completed", False)
                ),
                None,
            )

            if self.current_task_index is not None:
                self.remaining_time = (
                    self.tasks[self.current_task_index]["duration"] * 60
                )
                self.update_task_list()
                self.update_timer()
            else:
                self.pause_timer()
                self.update_task_list()

                if self.auto_reset.get():
                    self.reset_completed_tasks()
                    self.start_timer()

    def show_task_completed_messagebox(self, task):
        messagebox.showinfo("Task Completed", f"Task '{task['name']}' is completed!")

    def telegram(self, task):
        print(f"Sending Telegram notification for completed task: {task['name']}")
        self.amp_client.send_telegram_message("Task finished: " + task["name"])

    def reset_completed_tasks(self):
        for task in self.tasks:
            task.pop("completed", None)
        self.current_task_index = None
        self.update_task_list()
        self.save_tasks()

    def save_tasks(self):
        with open(self.data_filename, "w") as f:
            json.dump(self.tasks, f)

    def load_tasks(self):
        print(f"Loading tasks from {self.data_filename}")
        try:
            with open(self.data_filename, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def adjust_timer(self, minutes):
        if self.current_task_index is not None:
            self.remaining_time += minutes * 60
            self.remaining_time = max(
                0, self.remaining_time
            )  # Ensure time doesn't go negative
            self.update_timer_display()

    def update_timer_display(self):
        minutes, seconds = divmod(self.remaining_time, 60)
        self.timer_label.config(text=f"{minutes:02d}:{seconds:02d}")

    def restart_timer(self):
        self.pause_timer()
        self.timer_running = False  # Ensure the timer is stopped

        # Only cancel the timer job if it exists
        if self.timer_job is not None:
            self.master.after_cancel(self.timer_job)
            self.timer_job = None

        self.current_task_index = next(
            (
                i
                for i, task in enumerate(self.tasks)
                if not task.get("completed", False)
            ),
            None,
        )
        if self.current_task_index is not None:
            self.remaining_time = self.tasks[self.current_task_index]["duration"] * 60
            self.update_timer_display()
            self.update_task_list()
            self.start_timer()
        else:
            messagebox.showinfo(
                "No Tasks",
                "All tasks are completed. Please add new tasks or reset completed tasks.",
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = TaskClock(root)
    root.mainloop()
