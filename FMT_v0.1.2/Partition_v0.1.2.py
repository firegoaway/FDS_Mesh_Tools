import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import re
import math
import configparser
import os

class Tooltip:
    """Создаёт всплывающие подсказки"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)  # Убираем косметику
        self.tooltip_window.geometry(f"+{x}+{y}")  # Размещаем тултип

        label = tk.Label(self.tooltip_window, text=self.text, background="lightyellow", borderwidth=1, relief="solid")
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

def split_mesh(original_mesh, num_splits):
    ijk = original_mesh['IJK']
    xb = original_mesh['XB']
    x1, x2, y1, y2, z1, z2 = xb

    def find_best_factors(n):
        """Finds factors of n that provide a balanced division across two axes"""
        best_factors = (1, n)
        min_difference = float('inf')

        for i in range(1, int(n**0.5) + 1):
            if n % i == 0:
                factor_x = i
                factor_y = n // i
                difference = abs(factor_x - factor_y)

                if difference < min_difference:
                    min_difference = difference
                    best_factors = (factor_x, factor_y)

        return best_factors

    def divide_into_parts(length, parts):
        part_length = length / parts
        offsets = [i * part_length for i in range(parts)]
        return offsets, [part_length] * parts

    num_splits_x, num_splits_y = find_best_factors(num_splits)

    x_offsets, dx_sizes = divide_into_parts(x2 - x1, num_splits_x)
    y_offsets, dy_sizes = divide_into_parts(y2 - y1, num_splits_y)
    dz = z2 - z1

    ni = max(1, ijk[0] // num_splits_x)
    nj = max(1, ijk[1] // num_splits_y)

    split_meshes = []

    mesh_id = 1
    for ix in range(num_splits_x):
        for iy in range(num_splits_y):
            xb_new = [
                x1 + x_offsets[ix], x1 + x_offsets[ix] + dx_sizes[ix],
                y1 + y_offsets[iy], y1 + y_offsets[iy] + dy_sizes[iy],
                z1, z2
            ]
            ijk_new = [ni, nj, ijk[2]]
            mesh = {
                'ID': f'Mesh{mesh_id:02d}',
                'IJK': ijk_new,
                'XB': xb_new
            }
            split_meshes.append(mesh)
            mesh_id += 1

    return split_meshes

def split_mesh_homo(original_mesh, num_splits):
    ijk = original_mesh['IJK']
    xb = original_mesh['XB']
    x1, x2, y1, y2, z1, z2 = xb

    if num_splits <= 0:
        raise ValueError("num_splits must be greater than 0")

    num_splits_z = 1 if ijk[2] < 4 else max(1, min(num_splits, 2))
    remaining_splits = num_splits // num_splits_z

    num_splits_x = max(1, int(math.sqrt(remaining_splits)))
    num_splits_y = max(1, remaining_splits // num_splits_x)

    while num_splits_x * num_splits_y * num_splits_z < num_splits:
        if num_splits_y < num_splits_x:
            num_splits_y += 1
        else:
            num_splits_x += 1

    while num_splits_x * num_splits_y * num_splits_z > num_splits:
        if num_splits_y > num_splits_x:
            num_splits_y -= 1
        else:
            num_splits_x -= 1
    
    dx = (x2 - x1) / num_splits_x
    dy = (y2 - y1) / num_splits_y
    dz = (z2 - z1) / num_splits_z
    
    ni = ijk[0] // num_splits_x
    nj = ijk[1] // num_splits_y
    nk = ijk[2] // num_splits_z

    split_meshes = []
    mesh_id = 1

    for ix in range(num_splits_x):
        for iy in range(num_splits_y):
            for iz in range(num_splits_z):
                xb_new = [
                    x1 + ix * dx,
                    x1 + (ix + 1) * dx,
                    y1 + iy * dy,
                    y1 + (iy + 1) * dy,
                    z1 + iz * dz,
                    z1 + (iz + 1) * dz
                ]
                ijk_new = [ni, nj, nk]
                mesh = {
                    'ID': f'Mesh{mesh_id:02d}',
                    'IJK': ijk_new,
                    'XB': xb_new
                }
                split_meshes.append(mesh)
                mesh_id += 1

    return split_meshes

def read_fds_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    return lines

def write_fds_file(file_path, lines):
    with open(file_path, 'w') as file:
        file.writelines(lines)

def process_fds_content(lines, partition_value):
    mesh_line_indices = [i for i, line in enumerate(lines) if line.startswith('&MESH')]
    if len(mesh_line_indices) != 1:
        messagebox.showerror("Ошибка", "Файл сценария .fds должен иметь только одну расчетную область")
        return None

    original_mesh_line = lines[mesh_line_indices[0]]
    
    # Регексим IJK и XB
    ijk_match = re.search(r'IJK=\s*(\d+),(\d+),(\d+)', original_mesh_line)
    xb_match = re.search(r'XB=\s*([-+]?\d*\.?\d+),([-+]?\d*\.?\d+),([-+]?\d*\.?\d+),([-+]?\d*\.?\d+),([-+]?\d*\.?\d+),([-+]?\d*\.?\d+)', original_mesh_line)
    
    if not ijk_match or not xb_match:
        messagebox.showerror("Ошибка", "Убедитесь, что .fds файл не поврежден. Значения IJK or XB не обнаружены.")
        return None

    ijk = list(map(int, ijk_match.groups()))
    xb = list(map(float, xb_match.groups()))

    original_mesh = {'IJK': ijk, 'XB': xb}
    num_splits = partition_value  # Регулировка разбиения относительно осей X и Y
    split_meshes = split_mesh(original_mesh, num_splits)
    mesh_lines = []
    for mesh in split_meshes:
        xb = mesh['XB']
        ijk = mesh['IJK']
        mesh_line = f"&MESH ID='{mesh['ID']}', IJK={ijk[0]},{ijk[1]},{ijk[2]}, XB={xb[0]},{xb[1]},{xb[2]},{xb[3]},{xb[4]},{xb[5]} /\n"
        mesh_lines.append(mesh_line)
    lines = lines[:mesh_line_indices[0]] + mesh_lines + lines[mesh_line_indices[0] + 1:]
    return lines
    
def process_fds_content_homo(lines, partition_value):
    mesh_line_indices = [i for i, line in enumerate(lines) if line.startswith('&MESH')]
    if len(mesh_line_indices) != 1:
        messagebox.showerror("Ошибка", "Файл сценария .fds должен иметь только одну расчетную область")
        return None

    original_mesh_line = lines[mesh_line_indices[0]]
    
    # Регексим IJK и XB
    ijk_match = re.search(r'IJK=\s*(\d+),(\d+),(\d+)', original_mesh_line)
    xb_match = re.search(r'XB=\s*([-+]?\d*\.?\d+),([-+]?\d*\.?\d+),([-+]?\d*\.?\d+),([-+]?\d*\.?\d+),([-+]?\d*\.?\d+),([-+]?\d*\.?\d+)', original_mesh_line)
    
    if not ijk_match or not xb_match:
        messagebox.showerror("Ошибка", "Убедитесь, что .fds файл не поврежден. Значения IJK or XB не обнаружены.")
        return None

    ijk = list(map(int, ijk_match.groups()))
    xb = list(map(float, xb_match.groups()))

    original_mesh = {'IJK': ijk, 'XB': xb}
    num_splits = partition_value  # Регулировка разбиения относительно осей X и Y
    split_meshes = split_mesh_homo(original_mesh, num_splits)
    mesh_lines = []
    for mesh in split_meshes:
        xb = mesh['XB']
        ijk = mesh['IJK']
        mesh_line = f"&MESH ID='{mesh['ID']}', IJK={ijk[0]},{ijk[1]},{ijk[2]}, XB={xb[0]},{xb[1]},{xb[2]},{xb[3]},{xb[4]},{xb[5]} /\n"
        mesh_lines.append(mesh_line)
    lines = lines[:mesh_line_indices[0]] + mesh_lines + lines[mesh_line_indices[0] + 1:]
    return lines

def read_ini_file(ini_file):
    config = configparser.ConfigParser()
    with open(ini_file, 'r', encoding='utf-16') as f:
        config.read_file(f)
    return config['filePath']['filePath']

def open_file():
    current_directory = os.path.dirname(__file__)
    parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
    inis_path = os.path.join(parent_directory, 'inis')
        
    ini_path = os.path.join(inis_path, 'filePath.ini')
        
    file_path = read_ini_file(ini_path)
    
    if file_path:
        lines = read_fds_file(file_path)
        global fds_file_path, fds_lines
        fds_file_path = file_path
        fds_lines = lines
        if any(line.startswith('&MESH') for line in fds_lines):
            partition_label.config(state=tk.NORMAL)
            partition_entry.config(state=tk.NORMAL)
            partition_button.config(state=tk.NORMAL)
        else:
            messagebox.showerror("Ошибка", "Расчетная область не найдена.")

def on_partition_button():
    try:
        partition_value = int(partition_entry.get())
        if partition_value <= 1:
            raise ValueError("Число должно быть целым положительным и больше 1")
        
        if homomorph_var.get() == 1:
            modified_lines = process_fds_content_homo(fds_lines, partition_value)
        else:
            modified_lines = process_fds_content(fds_lines, partition_value)   
        
        if modified_lines:
            write_fds_file(fds_file_path, modified_lines)
            messagebox.showinfo("Успех!", f"Расчетная область поделена на {partition_value}")
            root.quit()  # Завершить выполнение программы после сообщения об успешном разбиении
    except ValueError as ve:
        messagebox.showerror("Ошибка", str(ve))

# Основное окно GUI
root = tk.Tk()

current_directory = os.path.dirname(__file__)
parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
icon_path = os.path.join(parent_directory, '.gitpics', 'Partition.ico')

root.title("FMT Mesh Partition Tool v0.1.2")
root.iconbitmap(icon_path)
root.wm_iconbitmap(icon_path)

# Создаём надписи, элементы ввода и кнопки непосредственно в корневом окне
partition_label = tk.Label(root, text="Число разбиений:")
partition_label.pack(pady=5)

global partition_entry
partition_entry = tk.Entry(root)
partition_entry.pack(padx=25, pady=5)
partition_entry.config(state=tk.DISABLED)  # Изначально отключен
Tooltip(partition_entry, "Введите целое положительное ненулевое число.")

# Создаём переменную для хранения состояния флажка
homomorph_var = tk.IntVar(value=1)
homomorph_checkbox = tk.Checkbutton(root, text="Сохранять гомоморфизм разбиений", variable=homomorph_var)
homomorph_checkbox.pack(pady=5)
Tooltip(homomorph_checkbox, "Соблюсти пропорции размеров сетки.")

partition_button = tk.Button(root, text="Разбить", command=on_partition_button)
partition_button.pack(pady=5)
partition_button.config(state=tk.DISABLED)  # Изначально отключен

# Сразу читаем файл
root.after(0, open_file)

# Открываем окно GUI
root.mainloop()