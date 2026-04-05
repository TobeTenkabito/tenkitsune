import tkinter as tk
from tkinter import messagebox


def add_enemy():
    # 获取输入框的内容
    number = enemy_number_entry.get()
    print(f"输入的敌人编号: '{number}'")  # 打印输入值以调试
    if not number:  # 检查输入是否为空
        messagebox.showerror("错误", "请输入敌人编号")
        return

    try:
        enemy_number = int(number.strip())  # 转换为整数
        messagebox.showinfo("成功", f"成功添加敌人编号: {enemy_number}")
        print(f"成功添加敌人编号: {enemy_number}")
    except ValueError:
        messagebox.showerror("错误", "敌人编号必须是有效数字")

# 启动程序
root = tk.Tk()
root.title("添加敌人")

# 创建输入框
enemy_number_entry = tk.Entry(root, width=10)
enemy_number_entry.pack(pady=5)

# 添加按钮
add_button = tk.Button(root, text="增加", command=add_enemy)
add_button.pack(pady=5)

# 启动Tkinter主循环
root.mainloop()