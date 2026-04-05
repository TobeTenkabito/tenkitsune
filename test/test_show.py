import tkinter as tk

def show_input():
    print("当前输入框内容:", enemy_number_entry.get())

root = tk.Tk()
root.geometry("300x200")

tk.Label(root, text="输入敌人编号").pack(pady=5)
enemy_number_entry = tk.Entry(root)
enemy_number_entry.pack(pady=5)

tk.Button(root, text="测试输入", command=show_input).pack(pady=10)

root.mainloop()