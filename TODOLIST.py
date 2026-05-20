import tkinter as tk
import re
from tkinter import filedialog, messagebox, simpledialog


class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Todo List")
        self.root.geometry("650x500")

        self.todos = []
        self.normal_font = ("Arial", 14)
        self.done_font = ("Arial", 14, "overstrike")
        self.button_font = ("Arial", 11)
        self.active_text_color = "#1f4e79"
        self.done_text_color = "#8a8a8a"
        self.add_color = "#e8f4ff"
        self.edit_color = "#f0e8ff"
        self.save_color = "#eaf7ea"
        self.open_color = "#fff3d9"
        self.delete_color = "#ffe8e8"

        input_frame = tk.Frame(root)
        input_frame.pack(fill="x", padx=10, pady=10)

        self.entry = tk.Entry(input_frame, font=self.normal_font, fg=self.active_text_color)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", lambda event: self.add_todo())

        add_button = tk.Button(
            input_frame,
            text="Add",
            command=self.add_todo,
            font=self.button_font,
            bg=self.add_color
        )
        add_button.pack(side="left", padx=(8, 0))

        save_button = tk.Button(
            input_frame,
            text="Save",
            command=self.save_todos,
            font=self.button_font,
            bg=self.save_color
        )
        save_button.pack(side="left", padx=(8, 0))

        open_button = tk.Button(
            input_frame,
            text="Open",
            command=self.open_todos,
            font=self.button_font,
            bg=self.open_color
        )
        open_button.pack(side="left", padx=(8, 0))

        self.list_frame = tk.Frame(root)
        self.list_frame.pack(fill="both", expand=True, padx=10)

        remove_button = tk.Button(
            root,
            text="Remove Completed",
            command=self.remove_completed,
            font=self.button_font,
            bg=self.delete_color
        )
        remove_button.pack(fill="x", padx=10, pady=10)

    def create_todo(self, text, done=False):
        todo = {
            "text": text,
            "done": tk.BooleanVar(value=done),
            "children": []
        }
        return todo

    def add_todo(self):
        text = self.entry.get().strip()

        if not text:
            messagebox.showwarning("Empty task", "Please enter a todo item.")
            return

        self.todos.append(self.create_todo(text))
        self.entry.delete(0, tk.END)
        self.refresh_list()

    def add_subtodo(self, todo):
        text = simpledialog.askstring("Add subtask", "Enter subtask:")

        if text and text.strip():
            todo["children"].append(self.create_todo(text.strip()))
            self.refresh_list()

    def edit_todo(self, todo):
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit item")
        edit_window.geometry("460x260")
        edit_window.transient(self.root)
        edit_window.grab_set()

        text_box = tk.Text(
            edit_window,
            height=7,
            width=42,
            wrap="word",
            font=self.normal_font,
            fg=self.active_text_color
        )
        text_box.pack(fill="both", expand=True, padx=12, pady=(12, 8))
        text_box.insert("1.0", todo["text"])
        text_box.focus_set()

        button_frame = tk.Frame(edit_window)
        button_frame.pack(fill="x", padx=12, pady=(0, 12))

        def save_edit():
            text = text_box.get("1.0", tk.END).strip()

            if not text:
                messagebox.showwarning(
                    "Empty task",
                    "Todo item text cannot be empty.",
                    parent=edit_window
                )
                return

            todo["text"] = text
            edit_window.destroy()
            self.refresh_list()

        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            width=8,
            command=edit_window.destroy,
            font=self.button_font,
            bg="#f3f3f3"
        )
        cancel_button.pack(side="right", padx=(8, 0))

        save_button = tk.Button(
            button_frame,
            text="Save",
            width=8,
            command=save_edit,
            font=self.button_font,
            bg=self.save_color
        )
        save_button.pack(side="right")

        edit_window.bind("<Control-Return>", lambda event: save_edit())

    def save_todos(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if not file_path:
            return

        lines = []
        self.add_todos_to_lines(self.todos, lines)

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write("\n".join(lines))
        except OSError as error:
            messagebox.showerror("Save failed", f"Could not save the list:\n{error}")

    def add_todos_to_lines(self, todos, lines, parent_number="", depth=0):
        for index, todo in enumerate(todos):
            number = f"{parent_number}{index + 1}"
            marker = "[x]" if todo["done"].get() else "[ ]"
            indent = "    " * depth
            lines.append(f"{indent}{marker} {number}. {todo['text']}")

            self.add_todos_to_lines(
                todo["children"],
                lines,
                parent_number=f"{number}.",
                depth=depth + 1
            )

    def open_todos(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()
        except OSError as error:
            messagebox.showerror("Open failed", f"Could not open the list:\n{error}")
            return

        try:
            self.todos = self.parse_todos_from_lines(lines)
        except ValueError as error:
            messagebox.showerror("Invalid file", str(error))
            return

        self.update_all_parent_statuses(self.todos)
        self.refresh_list()

    def parse_todos_from_lines(self, lines):
        parsed_todos = []
        stack = []
        pattern = re.compile(r"^\s*\[( |x|X)\]\s+((?:\d+\.)+)\s+(.*)$")

        for line_number, line in enumerate(lines, start=1):
            line = line.rstrip("\n")

            if not line.strip():
                continue

            match = pattern.match(line)
            if not match:
                raise ValueError(f"Line {line_number} is not in the saved todo format.")

            done = match.group(1).lower() == "x"
            number = match.group(2)
            text = match.group(3).strip()
            depth = number.count(".") - 1

            if not text:
                raise ValueError(f"Line {line_number} has an empty todo item.")

            todo = self.create_todo(text, done)

            if depth == 0:
                parsed_todos.append(todo)
            else:
                if depth > len(stack):
                    raise ValueError(f"Line {line_number} skips a parent todo level.")

                stack[depth - 1]["children"].append(todo)

            if depth < len(stack):
                stack = stack[:depth]

            stack.append(todo)

        return parsed_todos

    def refresh_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        self.render_todos(self.todos)

    def render_todos(self, todos, parent_number="", indent=0, parent=None):
        for index, todo in enumerate(todos):
            number = f"{parent_number}{index + 1}"
            self.render_todo_row(todo, todos, index, number, indent, parent)

            if todo["children"]:
                self.render_todos(
                    todo["children"],
                    parent_number=f"{number}.",
                    indent=indent + 30,
                    parent=todo
                )

    def render_todo_row(self, todo, todo_list, index, number, indent, parent):
        row = tk.Frame(self.list_frame)
        row.pack(fill="x", pady=3)

        spacer = tk.Frame(row, width=indent)
        spacer.pack(side="left")

        checkbutton = tk.Checkbutton(
            row,
            text=f"{number}. {todo['text']}",
            variable=todo["done"],
            anchor="w",
            font=self.done_font if todo["done"].get() else self.normal_font,
            fg=self.done_text_color if todo["done"].get() else self.active_text_color,
            selectcolor="#f0f0f0",
            command=lambda: self.toggle_todo(todo, parent)
        )
        checkbutton.pack(side="left", fill="x", expand=True)

        add_sub_button = tk.Button(
            row,
            text="Add Sub",
            width=8,
            command=lambda: self.add_subtodo(todo),
            font=self.button_font,
            bg=self.add_color
        )
        add_sub_button.pack(side="left", padx=2)

        edit_button = tk.Button(
            row,
            text="Edit",
            width=6,
            command=lambda: self.edit_todo(todo),
            font=self.button_font,
            bg=self.edit_color
        )
        edit_button.pack(side="left", padx=2)

        up_button = tk.Button(
            row,
            text="Up",
            width=6,
            command=lambda: self.move_up(todo_list, index),
            font=self.button_font,
            bg="#f3f3f3"
        )
        up_button.pack(side="left", padx=2)

        down_button = tk.Button(
            row,
            text="Down",
            width=6,
            command=lambda: self.move_down(todo_list, index),
            font=self.button_font,
            bg="#f3f3f3"
        )
        down_button.pack(side="left", padx=2)

        delete_button = tk.Button(
            row,
            text="Delete",
            width=6,
            command=lambda: self.delete_todo(todo_list, index),
            font=self.button_font,
            bg=self.delete_color
        )
        delete_button.pack(side="left", padx=2)

    def toggle_todo(self, todo, parent):
        self.set_children_done(todo, todo["done"].get())

        if parent:
            self.update_parent_status(parent)

        self.refresh_list()

    def set_children_done(self, todo, status):
        for child in todo["children"]:
            child["done"].set(status)
            self.set_children_done(child, status)

    def update_parent_status(self, todo):
        if todo["children"]:
            all_children_done = all(child["done"].get() for child in todo["children"])
            todo["done"].set(all_children_done)

        self.update_all_parent_statuses(self.todos)

    def update_all_parent_statuses(self, todo_list):
        for todo in todo_list:
            self.update_all_parent_statuses(todo["children"])

            if todo["children"]:
                all_children_done = all(child["done"].get() for child in todo["children"])
                todo["done"].set(all_children_done)

    def move_up(self, todo_list, index):
        if index > 0:
            todo_list[index], todo_list[index - 1] = todo_list[index - 1], todo_list[index]
            self.refresh_list()

    def move_down(self, todo_list, index):
        if index < len(todo_list) - 1:
            todo_list[index], todo_list[index + 1] = todo_list[index + 1], todo_list[index]
            self.refresh_list()

    def delete_todo(self, todo_list, index):
        del todo_list[index]
        self.update_all_parent_statuses(self.todos)
        self.refresh_list()

    def remove_completed(self):
        self.todos = self.remove_completed_from_list(self.todos)
        self.update_all_parent_statuses(self.todos)
        self.refresh_list()

    def remove_completed_from_list(self, todo_list):
        remaining = []

        for todo in todo_list:
            todo["children"] = self.remove_completed_from_list(todo["children"])

            if not todo["done"].get():
                remaining.append(todo)

        return remaining


if __name__ == "__main__":
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()
