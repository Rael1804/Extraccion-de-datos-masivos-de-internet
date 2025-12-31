import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import requests
import time
import math
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import difflib
import os
import json
from datetime import datetime

def guardar_json(nombre_funcion, data):
    os.makedirs("json_results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"json_results/{nombre_funcion}_{timestamp}.json"

    if isinstance(data, pd.DataFrame):
        content = data.to_dict(orient="records")
    else:
        content = data

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

    print(f" JSON guardado: {filename}")


API_KEY = "9579770cd9174df481ee1cd3c42d4b08"
BASE_URL = "https://api.rawg.io/api"
REQUEST_DELAY = 1.0
MAX_PAGES = 50


def rawg_get(path, params=None, allow_pages=False, max_pages=5):
    if params is None:
        params = {}
    params['key'] = API_KEY

    results = []
    url = f"{BASE_URL}{path}"
    page_count = 0

    while url and (not allow_pages or page_count < max_pages):
        while True:
            r = requests.get(url, params=params if page_count == 0 else None)
            if r.status_code == 429:
                retry_after = 5
                try:
                    detail = r.json().get('detail', '')
                    if 'in' in detail:
                        import re
                        m = re.search(r'in (\d+) second', detail)
                        if m:
                            retry_after = int(m.group(1))
                except Exception:
                    pass
                print(f"429 detectado, esperando {retry_after}s...")
                time.sleep(retry_after)
                continue
            elif r.status_code != 200:
                raise RuntimeError(f"Error HTTP {r.status_code}: {r.text}")
            break

        data = r.json()
        if allow_pages and 'results' in data:
            results.extend(data['results'])
            url = data.get('next')
            page_count += 1
            time.sleep(REQUEST_DELAY)
        else:
            return data

    return results


def juegos_por_fecha(fecha_inicio, fecha_fin, max_pages=5):
    path = '/games'
    params = {'dates': f'{fecha_inicio},{fecha_fin}', 'ordering': '-rating', 'page_size': 40}
    juegos = rawg_get(path, params=params, allow_pages=True, max_pages=min(max_pages, MAX_PAGES))
    guardar_json("juegos_por_fecha", juegos)
    df = pd.DataFrame([{
        'id': j.get('id'),
        'name': j.get('name'),
        'released': j.get('released'),
        'rating': j.get('rating'),
        'metacritic': j.get('metacritic')
    } for j in juegos])
   
    return df


def juegos_de_desarrollador(nombre_dev, max_pages=10):
    data = rawg_get('/developers', params={'search': nombre_dev, 'page_size': 10})
    guardar_json("desarrolladores",data)
    devs = data.get('results', []) if isinstance(data, dict) else []
    if not devs:
        return pd.DataFrame()
    dev_id = devs[0]['id']
    juegos = rawg_get(f'/games', params={'developers': dev_id, 'page_size': 40}, allow_pages=True, max_pages=min(max_pages, MAX_PAGES))
    guardar_json("juegos_de_desarrollador", juegos)
    df = pd.DataFrame([{'id': j['id'], 'name': j['name'], 'released': j.get('released'), 'rating': j.get('rating')} for j in juegos])
 
    return df

def top_juegos_genero(nombre_genero, top_n=20):
    data = rawg_get('/genres', params={'search': nombre_genero})
    guardar_json("generos",data)
    results = data.get('results', []) if isinstance(data, dict) else []

    if not results:
        print(f"Género '{nombre_genero}' no encontrado.")
        return pd.DataFrame()

    nombres_generos = [g['name'] for g in results]
    mejor_coincidencia = difflib.get_close_matches(nombre_genero, nombres_generos, n=1, cutoff=0.4)

    if mejor_coincidencia:
        match = next(g for g in results if g['name'] == mejor_coincidencia[0])
    else:
        match = results[0] 

    slug = match['slug']  

    juegos = rawg_get(
        '/games',
        params={'genres': slug, 'ordering': '-rating', 'page_size': 40},
        allow_pages=True,
        max_pages=3
    )
    guardar_json("top_juegos_genero", juegos)

    df = pd.DataFrame([
        {'name': j['name'], 'rating': j.get('rating'), 'released': j.get('released')}
        for j in juegos if j.get('released') and j.get('rating')
    ])

   

    return df.head(top_n)


def top_juegos_tags(nombre_tag, top_n=20):
    data = rawg_get('/tags', params={'search': nombre_tag})
    guardar_json("tags",data)
    results = data.get('results', []) if isinstance(data, dict) else []

    if not results:
        print(f"Etiqueta '{nombre_tag}' no encontrada.")
        return pd.DataFrame()

    match = results[0] 
    slug = match['slug']

    juegos = rawg_get(
        '/games',
        params={'tags': slug, 'ordering': '-rating', 'page_size': 40},
        allow_pages=True,
        max_pages=3
    )
    guardar_json("top_juegos_tags", juegos)
    df = pd.DataFrame([
        {'name': j['name'], 'rating': j.get('rating'), 'released': j.get('released')}
        for j in juegos if j.get('released') and j.get('rating')
    ])

    return df.head(top_n)


def proximos_lanzamientos(meses_hacia_adelante=3, top_n=50):
    hoy = datetime.utcnow().date()
    fin = hoy + pd.DateOffset(months=meses_hacia_adelante)
    path = '/games'
    params = {'dates': f'{hoy},{fin.date()}', 'ordering': 'released', 'page_size': 40}
    juegos = rawg_get(path, params=params, allow_pages=True, max_pages=3)
    df = pd.DataFrame([{'name': j['name'], 'released': j.get('released'), 'rating': j.get('rating')} for j in juegos])
  
    return df.head(top_n)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('RAWG Explorer - Israel Aznar Villegas')
        self.geometry('1100x700')

        self.left = ttk.Frame(self, width=300)
        self.left.pack(side='left', fill='y')
        self.right = ttk.Frame(self)
        self.right.pack(side='right', expand=True, fill='both')

        self.btns = [
            ('Títulos y calificaciones por fechas', self.ui_juegos_por_fechas),
            ('Juegos de un desarrollador', self.ui_juegos_de_dev),
            ('Top juegos por género', self.ui_top_por_genero),
            ('Top juegos por tag', self.ui_top_por_tag),
            ('Próximos lanzamientos', self.ui_proximos)

        ]

        for (txt, fn) in self.btns:
            b = ttk.Button(self.left, text=txt, command=lambda f=fn: self.call_and_clear(f))
            b.pack(fill='x', padx=6, pady=3)

        self.input_frame = ttk.LabelFrame(self.right, text='Parámetros')
        self.input_frame.pack(side='top', fill='x', padx=6, pady=6)

        self.result_frame = ttk.LabelFrame(self.right, text='Resultados')
        self.result_frame.pack(side='top', expand=True, fill='both', padx=6, pady=6)

        self.text = scrolledtext.ScrolledText(self.result_frame)
        self.text.pack(side='left', expand=True, fill='both')

        self.plot_canvas = None

    def clear_inputs(self):
        for w in self.input_frame.winfo_children():
            w.destroy()

    def show_df(self, df):
        self.text.delete('1.0', tk.END)
        if df is None or df.empty:
            self.text.insert(tk.END, 'Sin resultados')
            return
        self.text.insert(tk.END, df.to_string(index=False))

    def call_and_clear(self, func):
        self.clear_inputs()
        self.text.delete('1.0', tk.END)  

        func()

    def ui_juegos_por_fechas(self):
        self.clear_inputs()
        ttk.Label(self.input_frame, text='Fecha inicio (YYYY-MM-DD)').pack(side='left')
        e1 = ttk.Entry(self.input_frame); e1.pack(side='left')
        ttk.Label(self.input_frame, text='Fecha fin (YYYY-MM-DD)').pack(side='left')
        e2 = ttk.Entry(self.input_frame); e2.pack(side='left')
        ttk.Label(self.input_frame, text='Páginas (max)').pack(side='left')
        p = ttk.Entry(self.input_frame, width=4); p.pack(side='left')

        def run():
            inicio = e1.get().strip(); fin = e2.get().strip(); pages = int(p.get() or 2)
            df = juegos_por_fecha(inicio, fin, max_pages=pages)
            self.show_df(df)
        ttk.Button(self.input_frame, text='Ejecutar', command=run).pack(side='left')

    def ui_juegos_de_dev(self):
        self.clear_inputs()
        ttk.Label(self.input_frame, text='Nombre desarrollador').pack(side='left')
        e = ttk.Entry(self.input_frame); e.pack(side='left')
        ttk.Label(self.input_frame, text='Páginas').pack(side='left')
        pg = ttk.Entry(self.input_frame, width=4); pg.pack(side='left')
        def run():
            df = juegos_de_desarrollador(e.get().strip(), max_pages=int(pg.get() or 3))
            self.show_df(df)
        ttk.Button(self.input_frame, text='Ejecutar', command=run).pack(side='left')



    def ui_top_por_genero(self):
        self.clear_inputs()
        ttk.Label(self.input_frame, text='Género').pack(side='left')
        e = ttk.Entry(self.input_frame); e.pack(side='left')
        ttk.Label(self.input_frame, text='Top N').pack(side='left')
        n = ttk.Entry(self.input_frame, width=4); n.pack(side='left')
        def run():
            df = top_juegos_genero(e.get().strip(), top_n=int(n.get() or 20))
            self.show_df(df)
        ttk.Button(self.input_frame, text='Ejecutar', command=run).pack(side='left')

    def ui_top_por_tag(self):
        self.clear_inputs()
        ttk.Label(self.input_frame, text='Tag').pack(side='left')
        e = ttk.Entry(self.input_frame); e.pack(side='left')
        ttk.Label(self.input_frame, text='Top N').pack(side='left')
        n = ttk.Entry(self.input_frame, width=4); n.pack(side='left')
        def run():
            df = top_juegos_tags(e.get().strip(), top_n=int(n.get() or 20))
            self.show_df(df)
        ttk.Button(self.input_frame, text='Ejecutar', command=run).pack(side='left')

    def ui_proximos(self):
        self.clear_inputs()
        ttk.Label(self.input_frame, text='Meses adelante').pack(side='left')
        e = ttk.Entry(self.input_frame, width=6); e.pack(side='left')
        def run():
            df = proximos_lanzamientos(meses_hacia_adelante=int(e.get() or 3))
            self.show_df(df)
        ttk.Button(self.input_frame, text='Ejecutar', command=run).pack(side='left')



if __name__ == '__main__':
    if not API_KEY:
        print('ERROR: Pon tu API_KEY en la variable API_KEY dentro del archivo.')
    else:
        app = App()
        app.mainloop()

