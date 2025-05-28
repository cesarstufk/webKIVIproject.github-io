import flet as ft
import random
import networkx as nx
import matplotlib.pyplot as plt
from collections import deque
import io
from PIL import Image
import base64

# Paleta de colores personalizada
my_colors = {
    "bg": "#ECEFF1",          # fondo claro
    "primary": "#0D47A1",     # azul fuerte
    "accent": "#37474F",      # gris oscuro
    "button": "#1E88E5",      # azul medio
    "text_light": "#FFFFFF",
    "text_dark": "#212121",
    "footer": "#546E7A",
}

# --- Generar cursos y dependencias aleatorias ---
def generar_datos_cursos():
    cursos = {f"C{i}": (random.randint(0, 2) if i <= 45 else 0) for i in range(1, 51)}
    dependencias = {curso: [] for curso in cursos}
    grados_entrada = {curso: 0 for curso in cursos}
    cursos_lista = list(cursos.keys())

    for curso, cantidad in cursos.items():
        curso_num = int(curso[1:])
        if cantidad > 0 and curso_num <= 45:
            posibles_dependientes = [
                c for c in cursos_lista if int(c[1:]) > curso_num and int(c[1:]) <= curso_num + 2
            ]
            seleccionados = random.sample(posibles_dependientes, min(len(posibles_dependientes), cantidad))
            dependencias[curso] = seleccionados
            for dep in seleccionados:
                grados_entrada[dep] += 1

    cola = deque([c for c, g in grados_entrada.items() if g == 0])
    ordenados = []

    while cola:
        curso = cola.popleft()
        ordenados.append(curso)
        for dep in dependencias[curso]:
            grados_entrada[dep] -= 1
            if grados_entrada[dep] == 0:
                cola.append(dep)

    for i in range(46, 51):
        c = f"C{i}"
        if c not in ordenados:
            ordenados.append(c)

    return cursos, dependencias, ordenados

# --- Generar texto para mostrar datos ---
def generar_texto_datos(cursos, dependencias, ordenados):
    texto = "📚 Cursos ordenados respetando las dependencias:\n\n"
    for curso in ordenados:
        texto += f"{curso} ({cursos[curso]}) |R => {dependencias[curso]}\n"
    return texto

# --- Generar texto y ciclos ---
def generar_texto_ciclos(ordenados):
    ciclos = {i: [] for i in range(1, 11)}
    ciclo_actual = 1
    for curso in ordenados:
        num = int(curso[1:])
        if num <= 45:
            if ciclo_actual <= 9:
                if len(ciclos[ciclo_actual]) < 5:
                    ciclos[ciclo_actual].append(curso)
                else:
                    ciclo_actual += 1
                    if ciclo_actual <= 9:
                        ciclos[ciclo_actual].append(curso)
        else:
            ciclos[10].append(curso)

    texto = "📆 Cursos agrupados en ciclos (5 cursos por ciclo):\n\n"
    for ciclo, cursos_en_ciclo in ciclos.items():
        texto += f"Ciclo {ciclo}: {', '.join(cursos_en_ciclo)}\n"

    return texto, ciclos

# --- Generar diagrama con matplotlib y networkx ---
def generar_diagrama_matplotlib(dependencias, ordenados):
    G = nx.DiGraph()
    cursos_unicos = list(dict.fromkeys(ordenados))
    G.add_nodes_from(cursos_unicos)

    curso_a_ciclo = {}
    ciclos = {i: [] for i in range(1, 11)}
    ciclo_actual = 1

    for curso in cursos_unicos:
        if int(curso[1:]) <= 45:
            if len(ciclos[ciclo_actual]) < 5:
                ciclos[ciclo_actual].append(curso)
            else:
                ciclo_actual += 1
                ciclos[ciclo_actual].append(curso)
        else:
            ciclos[10].append(curso)

    for ciclo, cursos_en_ciclo in ciclos.items():
        for curso in cursos_en_ciclo:
            curso_a_ciclo[curso] = ciclo

    for curso, dependientes in dependencias.items():
        ciclo_origen = curso_a_ciclo.get(curso, 0)
        for dependiente in dependientes:
            ciclo_destino = curso_a_ciclo.get(dependiente, 0)
            if ciclo_destino > ciclo_origen:
                G.add_edge(curso, dependiente)

    pos = {}
    x_spacing = 5
    y_spacing = 1
    for ciclo, cursos_en_ciclo in ciclos.items():
        for i, curso in enumerate(cursos_en_ciclo):
            pos[curso] = (ciclo * x_spacing, -i * y_spacing)

    colores = [
        "#A8DADC", "#F4A261", "#E9C46A", "#2A9D8F", "#E76F51",
        "#8D99AE", "#F6BD60", "#84A59D", "#F28482", "#B5E48C"
    ]
    node_colors = [
        colores[(curso_a_ciclo.get(curso, 1) - 1) % len(colores)]
        for curso in cursos_unicos
    ]

    plt.figure(figsize=(18, 12))
    nx.draw_networkx_nodes(G, pos, node_size=2500, node_color=node_colors, node_shape='s')
    nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
    nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, arrowstyle='->', connectionstyle='arc3,rad=0.05')

    for ciclo in range(1, 11):
        plt.text(ciclo * x_spacing, 1, f"Ciclo {ciclo}",
                 fontsize=12, ha='center', va='center', color='black')

    plt.title("Diagrama de Hasse de Cursos (MALLA CURRICULAR)")
    plt.axis('off')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf

# --- Main app ---
def main(page: ft.Page):
    page.scroll = ft.ScrollMode.AUTO
    page.title = "Malla Curricular - UPC"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = my_colors["bg"]

    header = ft.Text(
        "📘 Malla Curricular - Relacion de Orden Parcial y Diagrama de Hasse",
        size=24,
        weight="bold",
        color=my_colors["primary"],
    )

    texto = ft.Text("", selectable=True, color=my_colors["accent"])
    imagen_diagrama = ft.Image(src="", visible=False, width=800, height=500, fit=ft.ImageFit.CONTAIN)

    cursos, dependencias, ordenados = generar_datos_cursos()

    def mostrar_datos(e):
        texto.value = generar_texto_datos(cursos, dependencias, ordenados)
        imagen_diagrama.visible = False
        page.update()

    def mostrar_ciclos(e):
        texto.value, _ = generar_texto_ciclos(ordenados)
        imagen_diagrama.visible = False
        page.update()

    def mostrar_diagrama(e):
        buf = generar_diagrama_matplotlib(dependencias, ordenados)
        img = Image.open(buf)
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        imagen_diagrama.src_base64 = img_str
        imagen_diagrama.visible = True
        page.update()

    botones = ft.ResponsiveRow([
        ft.ElevatedButton("📄 Ver Cursos Ordenados", on_click=mostrar_datos, style=ft.ButtonStyle(bgcolor=my_colors["button"], color=my_colors["text_light"])),
        ft.ElevatedButton("🗂 Ver Ciclos", on_click=mostrar_ciclos, style=ft.ButtonStyle(bgcolor=my_colors["button"], color=my_colors["text_light"])),
        ft.ElevatedButton("📊 Ver Diagrama", on_click=mostrar_diagrama, style=ft.ButtonStyle(bgcolor=my_colors["button"], color=my_colors["text_light"])),
    ], alignment=ft.MainAxisAlignment.CENTER)

    footer = ft.Text(
        "👨‍💻 Mendoza | Napa | Quispe | Velasquez M. | Velasquez R.",
        text_align="center",
        size=16,
        color=my_colors["footer"]
    )

    page.add(
        ft.Column(
            [
                header,
                botones,
                texto,
                imagen_diagrama,
                footer,
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
    )

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
