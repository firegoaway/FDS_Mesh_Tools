import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import re
import math
import configparser

def split_mesh(original_mesh, num_splits):
    ijk = original_mesh['IJK']
    xb = original_mesh['XB']
    x1, x2, y1, y2, z1, z2 = xb

    # Вычисляем количество разбиений по осям
    num_splits_x = int(math.sqrt(num_splits))
    num_splits_y = num_splits // num_splits_x

    dx = (x2 - x1) / num_splits_x
    dy = (y2 - y1) / num_splits_y
    dz = (z2 - z1) / 1  # Не трогаем (1 разбиение)

    ni = ijk[0] // num_splits_x
    nj = ijk[1] // num_splits_y
    nk = ijk[2] // 1

    split_meshes = []

    mesh_id = 1
    for ix in range(num_splits_x):
        for iy in range(num_splits_y):
            xb_new = [x1 + ix * dx, x1 + (ix + 1) * dx,
                      y1 + iy * dy, y1 + (iy + 1) * dy,
                      z1, z2]
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

def read_ini_file(ini_file):
    config = configparser.ConfigParser()
    with open(ini_file, 'r', encoding='utf-16') as f:
        config.read_file(f)
    return config['filePath']['filePath']

def open_file():
    ini_path = 'filePath.ini'
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
            raise ValueError("Число должно быть целым положительным и больше 1.")
        modified_lines = process_fds_content(fds_lines, partition_value)
        if modified_lines:
            write_fds_file(fds_file_path, modified_lines)
            messagebox.showinfo("Успех!", f"Расчетная область поделена на {partition_value}")
            root.quit()  # Завершить выполнение программы после сообщения об успешном разбиении
    except ValueError as ve:
        messagebox.showerror("Ошибка", str(ve))

# Основное окно GUI
root = tk.Tk()
root.iconbitmap('.gitpics\\Partition.ico')
root.wm_iconbitmap('.gitpics\\Partition.ico')

# Создаём надписи, элементы ввода и кнопки непосредственно в корневом окне
partition_label = tk.Label(root, text="Число разбиений:")
partition_label.pack(pady=5)

global partition_entry
partition_entry = tk.Entry(root)
partition_entry.pack(padx=25, pady=5)
partition_entry.config(state=tk.DISABLED)  # Изначально отключен

partition_button = tk.Button(root, text="Разбить", command=on_partition_button)
partition_button.pack(pady=5)
partition_button.config(state=tk.DISABLED)  # Изначально отключен

# Сразу читаем файл
root.after(0, open_file)

# Открываем окно GUI
root.mainloop()