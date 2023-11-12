# Importar las bibliotecas necesarias
import tkinter as tk                                    # tkinter: Biblioteca para crear interfaces gráficas en Python
from tkinter import filedialog, StringVar, messagebox   # filedialog: Módulo de tkinter para manejar cuadros de diálogo de archivos
from PIL import Image, ImageTk                          # PIL (Python Imaging Library): Biblioteca para trabajar con imágenes
import cv2                                              # cv2: OpenCV, una biblioteca de visión por computadora
import numpy as np                                      # numpy: Biblioteca para trabajar con arreglos y operaciones matemáticas    
from collections import Counter                         # collections: Módulo para trabajar con estructuras de datos especializadas
import json                                             # json: Módulo para trabajar con archivos JSON
import os                                               # os: Módulo para interactuar con el sistema operativo
import time                                             # time: Módulo para manejar operaciones relacionadas con el tiempo
import fnmatch                                          # fnmatch: Módulo para realizar coincidencias de patrones en nombres de archivos

# Diccionario para almacenar los valores RGB y los colores circundantes
valores_rgb = {}
colores_circundantes = {}

# Función para calcular la distancia de Minkowski entre dos puntos
def minkowski_distance(x, y, p):
    if len(x) != len(y):
        raise ValueError("Los puntos x e y deben tener la misma dimensión.")

    if p == 2:
        return sum((xi - yi) ** 2 for xi, yi in zip(x, y)) ** 0.5
    if p == float('inf'):
        return max(abs(xi - yi) for xi, yi in zip(x, y))
    sum_powered_differences = sum(abs(xi - yi) ** p for xi, yi in zip(x, y))
    return sum_powered_differences ** (1 / p)

# Prototipos de colores para comparación
prototipo_rgb1 = (185, 77, 64)  # Rojo
prototipo_rgb2 = (137, 185, 65)  # Verde
prototipo_rgb3 = (230, 173, 75)  # Amarillo
prototipo_rgb4 = (255, 255, 255)  # Blanco

# Funciones para calcular la distancia para colores específicos
def roja(pixel, metrica):
    return minkowski_distance(prototipo_rgb1, pixel, metrica) if (
        pixel[0] > 50 and pixel[1] < 60 and pixel[2] < 60
    ) else None

def verde(pixel, metrica):
    return minkowski_distance(prototipo_rgb2, pixel, metrica) if (
        pixel[0] > 20 and pixel[1] > 30 and pixel[2] < 100
    ) else None

def amarilla(pixel, metrica):
    return minkowski_distance(prototipo_rgb3, pixel, metrica) if (
        pixel[0] > 50 and pixel[1] > 80 and pixel[2] < 110
    ) else None

def blanco(pixel, metrica):
    return minkowski_distance(prototipo_rgb4, pixel, metrica) if (
        pixel[0] > 200 and pixel[1] > 200 and pixel[2] > 200
    ) else None

# Función para comparar el color de un píxel con los prototipos y determinar el color dominante
def comparacion(pixel, metrica, event):
    valor_rojo = roja(pixel, metrica)
    valor_verde = verde(pixel, metrica)
    valor_amarillo = amarilla(pixel, metrica)
    valor_blanco = blanco(pixel, metrica)

    valores = {
        "Rojo": valor_rojo,
        "Verde": valor_verde,
        "Amarillo": valor_amarillo,
        "Blanco": valor_blanco,
    }

    # Filtrar valores válidos y seleccionar el color dominante
    valores_validos = {color: valor for color, valor in valores.items() if valor is not None and valor != float('inf')}

    if not valores_validos:
        return "Es fondo", "black"

    color_label = min(valores_validos, key=valores_validos.get)
    font_color = color_label.lower()

    if color_label.lower() == "blanco":
        return "Es fondo", "black"

    return f"Es manzana de color {color_label.lower()}", font_color

# Función para detectar la forma de una imagen (si es una manzana o fondo)
def detectar_forma(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
        if len(approx) >= 5:
            return "Es una manzana"

    return "Es fondo"

# Función para corregir la detección basada en los colores circundantes
def corregir_deteccion(event, metrica_seleccionada):
    x, y = event.x, event.y
    vecinos = [(x+i, y+j) for i in range(-1, 2) for j in range(-1, 2) if (0 <= x+i < width) and (0 <= y+j < height) and (i, j) != (0, 0)]

    colores = [colores_circundantes[vecino] for vecino in vecinos if vecino in colores_circundantes]
    contador_colores = Counter(colores)

    if contador_colores:
        color_mas_comun, _ = contador_colores.most_common(1)[0]
        if color_mas_comun.lower() in ["rojo", "verde", "amarillo", "blanco"]:
            label_result.config(text=f"Es {color_mas_comun.lower()}", fg=color_mas_comun.lower())

# Función para cargar una imagen y configurar la interfaz gráfica
def cargar_imagen():
    global file_path
    file_path = filedialog.askopenfilename()
    if not file_path:
        return

    # Abrir la imagen y configurar el lienzo
    original_image = Image.open(file_path)
    photo = ImageTk.PhotoImage(original_image)
    canvas.original_image = original_image
    canvas.photo_image = photo
    canvas.config(scrollregion=canvas.bbox(tk.ALL))
    canvas.create_image(0, 0, anchor=tk.NW, image=photo)
    canvas.bind('<Motion>', lambda event: color_detect(event, file_path))

    # Cargar datos previos si están disponibles
    valores_rgb_cargados, colores_circundantes_cargados = cargar_datos_desde_archivo(file_path)

    valores_rgb.clear()
    valores_rgb.update(valores_rgb_cargados)
    colores_circundantes.clear()
    colores_circundantes.update(colores_circundantes_cargados)

# Función para detectar el color de un píxel en movimiento
def color_detect(event, file_path):
    global width, height
    width, height = canvas.original_image.size

    if 0 <= event.x < width and 0 <= event.y < height:
        r, g, b = canvas.original_image.getpixel((event.x, event.y))
        metrica_seleccionada = metrica_var.get()
        metrica_dict = {"Manhattan (p=1)": 1, "Euclidiana (p=2)": 2, "Máximo (p=inf)": float('inf')}

        color_label, font_color = comparacion((r, g, b), metrica_dict[metrica_seleccionada], event)

        font_color = font_color if font_color in ["white", "red", "green", "yellow"] else "black"

        # Verificar si la posición ya existe en colores_circundantes antes de agregarla
        if (event.x, event.y) not in colores_circundantes:
            colores_circundantes[(event.x, event.y)] = color_label

            corregir_deteccion(event, metrica_seleccionada)

            label_result.config(text=color_label, fg=font_color)

# Función para guardar los datos en un archivo JSON
def guardar_datos_en_archivo():
    if not colores_circundantes:
        messagebox.showinfo("Advertencia", "No hay datos para guardar.")
        return

    if not canvas.original_image:
        messagebox.showinfo("Advertencia", "Cargue una imagen antes de guardar datos.")
        return

    # Crear el nombre del archivo JSON
    nombre_archivo_imagen = os.path.basename(file_path)
    nombre_base, _ = os.path.splitext(nombre_archivo_imagen)
    nombre_archivo_json = f'datos_{nombre_base}.json'

    colores_circundantes_str = {str(key): value for key, value in colores_circundantes.items()}

    # Guardar los datos en el archivo JSON
    datos = {'valores_rgb': valores_rgb, 'colores_circundantes': colores_circundantes_str}
    with open(nombre_archivo_json, 'w') as archivo:
        json.dump(datos, archivo)
    messagebox.showinfo("Guardado", "Datos guardados correctamente.")

# Función para cargar datos desde un archivo JSON
def cargar_datos_desde_archivo(file_path):
    nombre_archivo_imagen = os.path.basename(file_path)
    nombre_base, _ = os.path.splitext(nombre_archivo_imagen)
    patron_json = f'datos_{nombre_base}_*.json'

    archivos_json = [archivo for archivo in os.listdir() if fnmatch.fnmatch(archivo, patron_json)]

    if archivos_json:
        archivo_json_mas_reciente = max(archivos_json, key=os.path.getctime)
        with open(archivo_json_mas_reciente, 'r') as archivo:
            datos = json.load(archivo)
            valores_rgb = datos.get('valores_rgb', {})
            colores_circundantes = datos.get('colores_circundantes', {})
    else:
        valores_rgb = {}
        colores_circundantes = {}

    return valores_rgb, colores_circundantes

# Configuración de la interfaz gráfica
root = tk.Tk()
root.title("Reconocimiento de Colores")

# Configuración del menú desplegable para la métrica de distancia
metrica_var = StringVar(root)
metrica_var.set("Manhattan (p=1)")
opciones = ["Manhattan (p=1)", "Euclidiana (p=2)", "Máximo (p=inf)"]
menu_metrica = tk.OptionMenu(root, metrica_var, *opciones)
menu_metrica.pack(pady=20)
menu_metrica.configure(bg='#f0f0f0', fg='black', font=('Arial', 12))

# Botón para cargar una imagen
btn_cargar = tk.Button(root, text="Cargar Imagen", command=cargar_imagen, width=40, padx=15, font=('Arial', 18, 'bold'), background='orange', foreground='white')
btn_cargar.pack(pady=20)

# Botón para guardar datos
btn_guardar = tk.Button(root, text="Guardar Datos", command=guardar_datos_en_archivo, width=40, padx=15, font=('Arial', 18, 'bold'), background='orange', foreground='white')
btn_guardar.pack(pady=20)

# Lienzo para mostrar la imagen
canvas = tk.Canvas(root, bg='white')
canvas.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

# Barras de desplazamiento para el lienzo
scroll_x = tk.Scrollbar(root, orient="horizontal", command=canvas.xview)
scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
scroll_y = tk.Scrollbar(root, orient="vertical", command=canvas.yview)
scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

canvas.config(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

# Etiqueta para mostrar el resultado
label_result = tk.Label(root, text="", font=("Arial", 16))
label_result.pack(pady=20)

# Iniciar la interfaz gráfica
root.mainloop()