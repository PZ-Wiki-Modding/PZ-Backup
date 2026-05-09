import sys, shutil
import tkinter as tk
from tkinter import messagebox

import sv_ttk




def main():
    # Create the main window
    root = tk.Tk()
    root.title("Simple UI Example")
    root.geometry("400x300")  # width x height
    
    # Add a label (text display)
    label = tk.Label(root, text="Welcome to Tkinter!", font=("Arial", 16, "bold"))
    label.pack(pady=10)  # pady = padding on y-axis
    
    # Add an entry field (text input)
    entry = tk.Entry(root, font=("Arial", 12), width=30)
    entry.pack(pady=10)
    entry.insert(0, "Type something here...")  # default text
    
    # Function to handle button click
    def on_button_click():
        user_input = entry.get()  # Get text from entry field
        if user_input and user_input != "Type something here...":
            messagebox.showinfo("You entered", user_input)
        else:
            messagebox.showwarning("Empty!", "Please enter something first")
    
    # Add a button
    button = tk.Button(root, text="Click Me!", command=on_button_click, bg="blue", fg="white", font=("Arial", 12))
    button.pack(pady=10)
    
    # Add another button to clear
    def clear_entry():
        entry.delete(0, tk.END)  # Delete from position 0 to END
        entry.insert(0, "Type something here...")
    
    clear_button = tk.Button(root, text="Clear", command=clear_entry)
    clear_button.pack(pady=5)
    
    sv_ttk.set_theme("dark")

    # Start the GUI event loop
    root.mainloop()
    
    sys.exit(0)



if __name__ == "__main__":
    main()