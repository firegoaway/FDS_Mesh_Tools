import re
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import configparser
import math

def calculate_cs(xmin, xmax, imin):
    return (xmax - xmin) / imin

def read_ini_file(ini_file):
    config = configparser.ConfigParser()
    with open(ini_file, 'r', encoding='utf-16') as f:
        config.read_file(f)
    return config['filePath']['filePath']

def open_file():
    if len(sys.argv) > 1:
        ProcessID = int(sys.argv[1])
        print(f"Process ID received from AHK: {ProcessID}")
    else:
        print("No Process ID received.")

    current_directory = os.path.dirname(__file__)
    parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
    inis_path = os.path.join(parent_directory, 'inis')
        
    ini_path = os.path.join(inis_path, f'filePath_{ProcessID}.ini')
    
    file_path = None
    
    if os.path.exists(ini_path):
        try:
            file_path = read_ini_file(ini_path)
            parse_file(file_path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось прочесть {ini_path}: {e}")
            file_path = filedialog.askopenfilename(filetypes=[("Файлы формата FDS", "*.fds"), ("Все файлы", "*.*")])
            if not file_path:
                return
            parse_file(file_path)
    else:
        file_path = filedialog.askopenfilename(filetypes=[("Файлы формата FDS", "*.fds"), ("Все файлы", "*.*")])
        if not file_path:
            return
        parse_file(file_path)

def parse_file(file_path):
    with open(file_path, 'r') as file:
        contents = file.readlines()
        lb.delete(0, tk.END)  # Очистить листбокс

    global meshes
    meshes = []
    lb.delete(0, tk.END)  # Очистить листбокс

    for line in contents:
        match = re.search(r'&MESH\s.*?\bIJK=(\d+,\d+,\d+)\b.*?\bXB=([-\d\.]+,[-\d\.]+,[-\d\.]+,[-\d\.]+,[-\d\.]+,[-\d\.]+)\b', line)
        if match:
            IJK = match.group(1).split(',')
            XB = match.group(2).split(',')
            I, J, K = map(int, IJK)
            Xmin, Xmax, Ymin, Ymax, Zmin, Zmax = map(float, XB)
            Cs_x = calculate_cs(Xmin, Xmax, I)
            Cs_y = calculate_cs(Ymin, Ymax, J)
            Cs_z = calculate_cs(Zmin, Zmax, K)
            Cs = min(Cs_x, Cs_y, Cs_z)
            lb.insert(tk.END, f"{line.strip()}    Cs={Cs:.6f}")
            meshes.append((I, J, K, Xmin, Xmax, Ymin, Ymax, Zmin, Zmax, contents.index(line)))

    cs_entry.config(state='normal')
    cs_entry.delete(0, tk.END)
    cs_entry.insert(0, f"{Cs:.6f}")
    cs_entry.config(state='disabled')

def refine_mesh():
    try:
        Csw = float(csw_entry.get())
        if Csw <= 0:
            messagebox.showerror("Ошибка ввода", "Значение Csw должно быть положительным!")
            return

        selected_indices = lb.curselection()
        if not selected_indices:
            messagebox.showerror("Ошибка выбора", "Выберите хотя бы одну расчётную область из списка.")
            return

        # file_path = filedialog.askopenfilename(filetypes=[("Файлы формата FDS", "*.fds"), ("Все файлы", "*.*")])
        
        current_directory = os.path.dirname(__file__)
        parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
        inis_path = os.path.join(parent_directory, 'inis')
        
        ini_path = os.path.join(inis_path, f'filePath_{ProcessID}.ini')
        
        file_path = read_ini_file(ini_path)
        if not file_path:
            return

        with open(file_path, "r") as file:
            contents = file.readlines()

        for index in selected_indices:
            I, J, K, Xmin, Xmax, Ymin, Ymax, Zmin, Zmax, line_index = meshes[index]
            Cs = min(calculate_cs(Xmin, Xmax, I), calculate_cs(Ymin, Ymax, J), calculate_cs(Zmin, Zmax, K))
            new_I = int(I * (Cs / Csw))
            new_J = int(J * (Cs / Csw))
            new_K = int(K * (Cs / Csw))

            original_line = lb.get(index).split('    ')[0]
            new_line = re.sub(r'IJK=\d+,\d+,\d+', f'IJK={new_I},{new_J},{new_K}', original_line)
            contents[line_index] = new_line + "\n"

        with open(file_path, "w") as file:
            file.writelines(contents)
            
        messagebox.showinfo("Успех!", "Расчётные области преобразованы и сохранены.")
        app.quit() # Закрыть окно утилиты после сообщения об успешном преобразовании
    
    except ValueError:
        messagebox.showerror("Ошибка ввода", "Значение Csw должно быть рациональным положительным.")

def merge_meshes():
    try:
        current_directory = os.path.dirname(__file__)
        parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
        ini_path = os.path.join(parent_directory, 'inis', f'filePath_{ProcessID}.ini')
        file_path = read_ini_file(ini_path)
        
        with open(file_path, 'r') as file:
            lines = file.readlines()

        meshes = []
        for line in lines:
            if line.strip().startswith('&MESH'):
                xb_part = line.split('XB=')[-1].split('/')[0]
                try:
                    xb = [float(val.split('/')[0].strip()) for val in xb_part.split(',')]
                    meshes.append(xb)
                except ValueError:
                    continue

        if not meshes:
            messagebox.showerror("Ошибка", "MESH записи не найдены!")
            return

        x_min = min(m[0] for m in meshes)
        x_max = max(m[1] for m in meshes)
        y_min = min(m[2] for m in meshes)
        y_max = max(m[3] for m in meshes)
        z_min = min(m[4] for m in meshes)
        z_max = max(m[5] for m in meshes)

        try:
            csw = float(csw_entry.get())
        except Exception:
            min_cs = []
            for line in lines:
                match = re.search(r'&MESH\s.*?IJK=(\d+,\d+,\d+).*?XB=([-\d\.]+,[^,]+,[^,]+,[^,]+,[^,]+,[^,]+)', line)
                if match:
                    ijk = list(map(int, match.group(1).split(',')))
                    xb_values = [float(val.split('/')[0].strip()) for val in match.group(2).split(',')]
                    cs_x = (xb_values[1] - xb_values[0]) / ijk[0]
                    cs_y = (xb_values[3] - xb_values[2]) / ijk[1]
                    cs_z = (xb_values[5] - xb_values[4]) / ijk[2]
                    min_cs.append(min(cs_x, cs_y, cs_z))
            csw = min(min_cs) if min_cs else 0.1

        i = int((x_max - x_min) / csw)
        j = int((y_max - y_min) / csw)
        k = int((z_max - z_min) / csw)

        new_mesh = (
            f"&MESH IJK={i},{j},{k}, XB={x_min:.6f},{x_max:.6f},"
            f"{y_min:.6f},{y_max:.6f},{z_min:.6f},{z_max:.6f}/\n"
        )

        mesh_pattern = re.compile(r"&MESH")

        new_lines = []
        for line in lines:
            if not mesh_pattern.search(line):
                new_lines.append(line)
        new_lines.insert(0, new_mesh)

        with open(file_path, 'w') as file:
            file.writelines(new_lines)
        
        messagebox.showinfo("Успех", "Все MESH объединены в один!")
        app.quit()

    except Exception as e:
        messagebox.showerror("Ошибка", str(e))

def select_all():
    lb.select_set(0, tk.END)

def unselect_all():
    lb.select_clear(0, tk.END)

app = tk.Tk()

if len(sys.argv) > 1:
    ProcessID = int(sys.argv[1])
    print(f"Process ID received from AHK: {ProcessID}")
else:
    print("No Process ID received.")

current_directory = os.path.dirname(__file__)
parent_directory = os.path.abspath(os.path.join(current_directory, os.pardir))
icon_path = os.path.join(parent_directory, '.gitpics', 'Refiner-Coarsener.ico')

app.title(f"FDS Mesh Refiner-Coarsener v0.2.0 ID: {ProcessID}")
app.iconbitmap(icon_path)
app.wm_iconbitmap(icon_path)

frame = ttk.Frame(app, padding="10")
frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

button_frame = ttk.Frame(frame)
button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

open_button = ttk.Button(button_frame, text="Выбрать .fds", command=open_file)
open_button.grid(row=0, column=0, padx=5, pady=5)

cs_label = ttk.Label(frame, text="Cs:")
cs_label.grid(row=0, column=1, sticky=tk.W, padx=5)

cs_entry = ttk.Entry(frame, state='disabled')
cs_entry.grid(row=0, column=2, sticky=tk.W, padx=5)

csw_label = ttk.Label(frame, text="Csw:")
csw_label.grid(row=0, column=3, sticky=tk.W, padx=5)

csw_entry = ttk.Entry(frame)
csw_entry.grid(row=0, column=4, sticky=tk.W, padx=5)

refine_button = ttk.Button(frame, text="Преобразовать", command=refine_mesh)
refine_button.grid(row=0, column=5, sticky=tk.W, padx=5)

lb = tk.Listbox(frame, selectmode=tk.MULTIPLE, width=120, height=20)
lb.grid(row=2, column=0, columnspan=5, pady=10)

select_all_button = ttk.Button(button_frame, text="Выбрать все", command=select_all)
select_all_button.grid(row=1, column=0, padx=5, pady=5)

unselect_all_button = ttk.Button(button_frame, text="Снять выбор", command=unselect_all)
unselect_all_button.grid(row=1, column=1, padx=5, pady=5)

merge_button = ttk.Button(frame, text="Объединить", command=merge_meshes)
merge_button.grid(row=0, column=6, sticky=tk.W, padx=5)

meshes = []

app.mainloop()