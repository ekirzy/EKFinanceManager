import flet as ft
import requests
import json
import os
import uuid
import pandas as pd
from datetime import datetime

# ==========================================
# ISI KEMBALI KUNCI DATABASE KAMU DISINI
# ==========================================
BIN_ID = "691d9f4d43b1c97be9b6fa69" 
API_KEY = "$2a$10$jPsVvsNEv8vRiqykJQrqOeQz7vwBCmFWqhS5fnJG/HyZGc4EOxPHK" 
# ==========================================

URL_BIN = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
HEADERS = {
    "X-Master-Key": API_KEY,
    "Content-Type": "application/json"
}

# --- WARNA & STYLE ---
C_PRIMARY = "#2962FF"     
C_GREEN = "#00C853"       
C_RED = "#FF3D00"         
C_BG = "#F5F7FA"          
C_WHITE = "#FFFFFF"       
C_TEXT = "#2D3436"
C_GREY = "#757575"
C_BORDER = "#9E9E9E" # Warna border lebih gelap agar jelas

# Data Kategori
CAT_EXPENSE = ["Makanan", "Transportasi", "Belanja", "Tagihan", "Hiburan", "Kesehatan", "Pendidikan", "Lainnya"]
CAT_INCOME = ["Gaji", "Bonus", "Investasi", "Hadiah", "Lainnya"]

def main(page: ft.Page):
    page.title = "Dompet V23 (Edit & Borders)"
    page.theme_mode = ft.ThemeMode.LIGHT 
    page.bgcolor = C_BG
    page.padding = 0
    page.window_width = 400
    page.window_height = 850

    # --- DATABASE ---
    def muat_data():
        try:
            response = requests.get(URL_BIN, headers=HEADERS)
            if response.status_code == 200:
                data = response.json().get("record", [])
                if isinstance(data, list): return data
            return []
        except: return []

    def simpan_data(data):
        try: requests.put(URL_BIN, headers=HEADERS, json=data)
        except: pass

    def hapus_transaksi(id_target):
        data = [x for x in muat_data() if x.get('id') != id_target]
        simpan_data(data)
        refresh_data()
        page.snack_bar = ft.SnackBar(ft.Text("Terhapus!"), bgcolor="red"); page.snack_bar.open = True; page.update()

    def export_excel(e):
        data = muat_data()
        if not data: return
        try:
            df = pd.DataFrame(data)
            filename = f"Laporan_{datetime.now().strftime('%Y%m%d')}.xlsx"
            df.to_excel(filename, index=False)
            page.snack_bar = ft.SnackBar(ft.Text(f"Disimpan: {filename}"), bgcolor="green"); page.snack_bar.open = True; page.update()
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {str(ex)}"), bgcolor="red"); page.snack_bar.open = True; page.update()

    # --- FITUR EDIT / RENAME ---
    def edit_transaksi(item_asli):
        # Buat Dialog Edit
        edit_nom = ft.TextField(label="Nominal", value=str(item_asli['nominal']), keyboard_type=ft.KeyboardType.NUMBER, border_color=C_BORDER)
        edit_ket = ft.TextField(label="Keterangan", value=item_asli['keterangan'], border_color=C_BORDER)
        
        def save_edit(e):
            try:
                baru_nom = int(edit_nom.value)
                baru_ket = edit_ket.value
                
                # Update data
                all_data = muat_data()
                for x in all_data:
                    if x.get('id') == item_asli['id']:
                        x['nominal'] = baru_nom
                        x['keterangan'] = baru_ket
                        break
                
                simpan_data(all_data)
                dlg_edit.open = False
                page.update()
                refresh_data()
                page.snack_bar = ft.SnackBar(ft.Text("Data diperbarui!"), bgcolor="green"); page.snack_bar.open = True; page.update()
            except:
                pass

        dlg_edit = ft.AlertDialog(
            title=ft.Text("Edit Transaksi"),
            content=ft.Column([edit_nom, edit_ket], height=150, tight=True),
            actions=[
                ft.TextButton("Batal", on_click=lambda e: page.close(dlg_edit)),
                ft.ElevatedButton("Simpan", on_click=save_edit, bgcolor=C_PRIMARY, color="white")
            ]
        )
        page.open(dlg_edit)

    # --- HELPER FORMAT ---
    def fmt_rp(val):
        return f"Rp {val:,}".replace(",", ".")

    # --- KOMPONEN UI ---
    now = datetime.now()
    
    # Style Dropdown dengan Border Jelas
    def style_dropdown(lbl, width, val, opts):
        return ft.Dropdown(
            label=lbl, width=width, value=val, options=opts,
            text_size=12, bgcolor=C_WHITE, border_radius=8, 
            border_color=C_BORDER, border_width=1, content_padding=10,
            focused_border_color=C_PRIMARY
        )

    dd_bulan = style_dropdown("Bulan", 100, str(now.month), [ft.dropdown.Option(str(i+1), b) for i, b in enumerate(["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agt", "Sep", "Okt", "Nov", "Des"])])
    dd_tahun = style_dropdown("Tahun", 90, str(now.year), [ft.dropdown.Option(str(y)) for y in range(2024, 2030)])

    # Style Input dengan Border Jelas
    def style_input(lbl, kb=None):
        return ft.TextField(
            label=lbl, keyboard_type=kb, 
            border_color=C_BORDER, border_width=1, 
            bgcolor=C_WHITE, border_radius=10, 
            text_size=14, content_padding=15, color=C_TEXT
        )

    input_nom = style_input("Nominal (Rp)", ft.KeyboardType.NUMBER)
    input_ket = style_input("Keterangan")
    
    dd_tipe = ft.Dropdown(label="Tipe", bgcolor=C_WHITE, border_radius=10, border_color=C_BORDER, border_width=1, content_padding=12, options=[ft.dropdown.Option("Pengeluaran"), ft.dropdown.Option("Pemasukan")], value="Pengeluaran", expand=True, text_size=14)
    dd_kategori = ft.Dropdown(label="Kategori", bgcolor=C_WHITE, border_radius=10, border_color=C_BORDER, border_width=1, content_padding=12, options=[ft.dropdown.Option(k) for k in CAT_EXPENSE], value="Makanan", expand=True, text_size=14)

    def ganti_tipe(e):
        opts = CAT_INCOME if dd_tipe.value == "Pemasukan" else CAT_EXPENSE
        dd_kategori.options = [ft.dropdown.Option(k) for k in opts]
        dd_kategori.value = opts[0]
        page.update()
    dd_tipe.on_change = ganti_tipe

    def tambah_klik(e):
        if not input_nom.value: return
        data_baru = {
            "id": str(uuid.uuid4())[:8],
            "tanggal": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "tipe": dd_tipe.value,
            "kategori": dd_kategori.value,
            "nominal": int(input_nom.value),
            "keterangan": input_ket.value
        }
        d = muat_data()
        d.append(data_baru)
        simpan_data(d)
        
        input_nom.value = ""; input_ket.value = ""
        page.snack_bar = ft.SnackBar(ft.Text("Disimpan!"), bgcolor="green"); page.snack_bar.open = True; page.update()
        refresh_data()

    btn_simpan = ft.ElevatedButton("SIMPAN TRANSAKSI", on_click=tambah_klik, bgcolor=C_PRIMARY, color="white", width=float("inf"), height=50, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))

    # --- AREA KONTEN ---
    container_saldo = ft.Container()
    list_view = ft.ListView(expand=True, spacing=10)
    col_analisis = ft.Column(scroll="auto")

    # --- LOGIKA REFRESH UTAMA ---
    def refresh_data(e=None):
        page.splash = ft.ProgressBar(); page.update()
        
        data = muat_data()
        sel_bln = int(dd_bulan.value)
        sel_thn = int(dd_tahun.value)
        
        filtered = []
        for x in data:
            try:
                tgl_str = x['tanggal'].split(" ")[0]
                tgl = datetime.strptime(tgl_str, "%Y-%m-%d")
                if tgl.month == sel_bln and tgl.year == sel_thn:
                    filtered.append(x)
            except: pass

        # --------------------------
        # 1. UPDATE TAB TRANSAKSI
        # --------------------------
        masuk = sum(x['nominal'] for x in filtered if x['tipe'] == 'Pemasukan')
        keluar = sum(x['nominal'] for x in filtered if x['tipe'] == 'Pengeluaran')
        saldo = masuk - keluar

        # Kartu Saldo
        container_saldo.content = ft.Container(
            gradient=ft.LinearGradient(colors=[C_PRIMARY, "#1565C0"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
            padding=20, border_radius=15, margin=ft.margin.only(bottom=10),
            content=ft.Column([
                ft.Text("Sisa Saldo (Bulan Ini)", color="white70", size=12),
                ft.Text(fmt_rp(saldo), color="white", size=28, weight="bold"),
                ft.Divider(color="white24", height=20),
                ft.Row([
                    ft.Column([
                        ft.Text("Pemasukan", color="white70", size=11),
                        ft.Text(fmt_rp(masuk), color="white", weight="bold", size=14)
                    ]),
                    ft.Column([
                        ft.Text("Pengeluaran", color="white70", size=11),
                        ft.Text(fmt_rp(keluar), color="white", weight="bold", size=14)
                    ], horizontal_alignment=ft.CrossAxisAlignment.END)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ]),
            shadow=ft.BoxShadow(blur_radius=10, color="#4D000000")
        )

        # List Riwayat
        list_view.controls.clear()
        if not filtered: list_view.controls.append(ft.Text("Tidak ada data.", color="grey", text_align="center"))
        
        for item in reversed(filtered):
            warna = C_GREEN if item['tipe'] == 'Pemasukan' else C_RED
            icon = ft.Icons.ARROW_DOWNWARD_ROUNDED if item['tipe'] == 'Pemasukan' else ft.Icons.ARROW_UPWARD_ROUNDED
            bg_icon = "#E8F5E9" if item['tipe'] == 'Pemasukan' else "#FFEBEE"
            
            list_view.controls.append(
                ft.Container(
                    bgcolor=C_WHITE, padding=12, border_radius=12,
                    border=ft.border.all(1, "#EEEEEE"), # Border tipis di list item
                    content=ft.Row([
                        ft.Container(content=ft.Icon(icon, color=warna), bgcolor=bg_icon, padding=8, border_radius=10),
                        ft.Column([
                            ft.Text(item['kategori'], weight="bold", color=C_TEXT),
                            ft.Text(item['keterangan'], size=12, color="grey")
                        ], expand=True),
                        ft.Column([
                            ft.Text(fmt_rp(item['nominal']), weight="bold", color=warna),
                            ft.Text(item['tanggal'].split(" ")[0], size=10, color="grey", text_align="right")
                        ]),
                        # TOMBOL EDIT & DELETE
                        ft.IconButton(ft.Icons.EDIT, icon_color="blue", icon_size=18, on_click=lambda e, x=item: edit_transaksi(x)),
                        ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=C_RED, icon_size=18, on_click=lambda e, id=item['id']: hapus_transaksi(id))
                    ], spacing=0),
                )
            )

        # --------------------------
        # 2. UPDATE TAB ANALISIS
        # --------------------------
        col_analisis.controls.clear()

        # HELPER BUAT PIE CHART + LIST
        def create_analysis_section(title, chart_data_list, colors):
            total_section = sum(x['value'] for x in chart_data_list)
            sections = []
            list_widgets = []

            if total_section > 0:
                for i, item in enumerate(chart_data_list):
                    val = item['value']
                    label = item['label']
                    pct = (val / total_section) * 100
                    color = colors[i % len(colors)]

                    # Pie Section
                    sections.append(ft.PieChartSection(value=val, color=color, radius=40, title=f"{int(pct)}%", title_style=ft.TextStyle(size=10, color="white", weight="bold")))

                    # List Detail Widget
                    list_widgets.append(
                        ft.Container(
                            padding=10, border=ft.border.only(bottom=ft.border.BorderSide(1, "#F0F0F0")),
                            content=ft.Row([
                                ft.Row([
                                    ft.Container(width=12, height=12, bgcolor=color, border_radius=3),
                                    ft.Text(label, size=12, weight="bold", color=C_TEXT)
                                ]),
                                ft.Row([
                                    ft.Text(fmt_rp(val), size=12, weight="bold"),
                                    ft.Text(f"({pct:.1f}%)", size=11, color="grey")
                                ])
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                        )
                    )
            else:
                 sections.append(ft.PieChartSection(value=1, color="#EEEEEE", radius=40, title=""))
                 list_widgets.append(ft.Text("Data kosong.", color="grey", size=12, text_align="center"))

            # Return Container Section
            return ft.Container(
                bgcolor=C_WHITE, padding=20, border_radius=15, margin=ft.margin.only(bottom=20),
                border=ft.border.all(1, "#E0E0E0"),
                content=ft.Column([
                    ft.Text(title, weight="bold", size=16, color=C_TEXT),
                    ft.Divider(height=10, color="transparent"),
                    ft.PieChart(sections=sections, sections_space=2, center_space_radius=30, height=200),
                    ft.Divider(height=20, color="transparent"),
                    ft.Column(list_widgets)
                ])
            )

        # A. Analisis Arus Kas (Masuk vs Keluar)
        data_cashflow = [
            {"label": "Pemasukan", "value": masuk},
            {"label": "Pengeluaran", "value": keluar}
        ]
        col_analisis.controls.append(create_analysis_section("Arus Kas (Pemasukan vs Pengeluaran)", data_cashflow, [C_GREEN, C_RED]))

        # B. Analisis Kategori Pengeluaran
        cat_sum = {}
        for x in filtered:
            if x['tipe'] == 'Pengeluaran':
                cat_sum[x['kategori']] = cat_sum.get(x['kategori'], 0) + x['nominal']
        
        # Sort kategori dari terbesar
        sorted_cats = sorted(cat_sum.items(), key=lambda item: item[1], reverse=True)
        data_cat = [{"label": k, "value": v} for k, v in sorted_cats]
        colors_cat = ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"]
        
        col_analisis.controls.append(create_analysis_section("Detail Kategori Pengeluaran", data_cat, colors_cat))
        
        # Spacer bawah
        col_analisis.controls.append(ft.Container(height=50))

        page.splash = None; page.update()

    dd_bulan.on_change = refresh_data
    dd_tahun.on_change = refresh_data

    # --- LAYOUT TABS ---
    
    # Konten Tab Transaksi
    tab_transaksi = ft.Column([
        container_saldo,
        
        # Area Filter & Excel
        ft.Container(
            padding=ft.padding.symmetric(horizontal=20),
            content=ft.Row([
                ft.Row([dd_bulan, dd_tahun]),
                ft.IconButton(ft.Icons.DOWNLOAD_ROUNDED, icon_color=C_PRIMARY, on_click=export_excel, tooltip="Download Excel")
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        ),
        
        # Area Input (Dengan Border)
        ft.Container(
            bgcolor=C_WHITE, padding=20, margin=20, border_radius=15,
            border=ft.border.all(1, "#E0E0E0"), # Border kotak form
            content=ft.Column([
                ft.Text("Input Transaksi", weight="bold"),
                ft.Row([dd_tipe, dd_kategori]),
                input_nom,
                input_ket,
                btn_simpan
            ], spacing=15),
        ),
        
        ft.Container(content=ft.Text("Riwayat", weight="bold", size=16), padding=ft.padding.only(left=25)),
        ft.Container(content=list_view, padding=20, expand=True)
    ], scroll="auto")

    # Tab Utama
    t = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        indicator_color=C_PRIMARY,
        label_color=C_PRIMARY,
        unselected_label_color="grey",
        divider_color="transparent",
        tabs=[
            ft.Tab(text="Transaksi", icon=ft.Icons.WALLET_ROUNDED, content=tab_transaksi),
            ft.Tab(text="Analisis", icon=ft.Icons.PIE_CHART_ROUNDED, content=ft.Container(content=col_analisis, padding=20)),
        ],
        expand=1,
    )

    page.add(t)
    refresh_data()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(target=main, view=ft.WEB_BROWSER, port=port, host="0.0.0.0")