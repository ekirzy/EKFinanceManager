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
C_BG = "#F7F9FC"
C_WHITE = "#FFFFFF"       
C_TEXT = "#2D3436"
C_BORDER = "#BDBDBD"

# Skema warna untuk Pie Chart
CHART_COLORS = ["#FF4081", "#3F51B5", "#00BCD4", "#FFC107", "#8BC34A", "#E91E63", "#673AB7", "#4CAF50", "#FF9800", "#9E9E9E"]

CAT_EXPENSE = ["Makanan", "Transportasi", "Belanja", "Tagihan", "Hiburan", "Kesehatan", "Pendidikan", "Honorarium", "Bahan", "Barang Non Operasional",  "Lainnya"]
CAT_INCOME = ["Gaji", "Bonus", "Investasi", "Hadiah", "Lainnya"]

def main(page: ft.Page):
    page.title = "EKFinanceManager"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = C_BG
    page.padding = 0
    page.window_width = 400
    page.window_height = 850

    current_user = None 

    # --- DATABASE ENGINE ---
    def muat_data_server():
        try:
            response = requests.get(URL_BIN, headers=HEADERS)
            if response.status_code == 200:
                data = response.json().get("record", [])
                if isinstance(data, list): return data
            return []
        except: return []

    def simpan_data_server(data):
        try: requests.put(URL_BIN, headers=HEADERS, json=data)
        except: pass

    # --- HELPER FORMAT ---
    def fmt_rp(val): return f"Rp {val:,}".replace(",", ".")

    # =================================================================
    # HALAMAN 1: LOGIN
    # =================================================================
    def show_auth_page():
        page.clean()
        
        is_register = False
        
        user_input = ft.TextField(label="Username", border_color=C_PRIMARY, prefix_icon=ft.Icons.PERSON, bgcolor=C_WHITE, border_radius=12)
        pass_input = ft.TextField(label="Password / PIN", password=True, can_reveal_password=True, border_color=C_PRIMARY, prefix_icon=ft.Icons.LOCK, bgcolor=C_WHITE, border_radius=12)
        btn_action = ft.ElevatedButton("MASUK", bgcolor=C_PRIMARY, color="white", width=float("inf"), height=50, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)))
        txt_switch = ft.TextButton("Belum punya akun? Daftar", width=float("inf"))
        loading = ft.ProgressBar(width=100, color=C_PRIMARY, visible=False)

        def toggle_mode(e):
            nonlocal is_register
            is_register = not is_register
            btn_action.text = "DAFTAR SEKARANG" if is_register else "MASUK"
            txt_switch.text = "Sudah punya akun? Login" if is_register else "Belum punya akun? Daftar"
            page.update()

        def process_auth(e):
            u = user_input.value.strip().lower()
            p = pass_input.value.strip()
            if not u or not p:
                page.open(ft.SnackBar(ft.Text("Isi semua kolom!"), bgcolor="red"))
                page.update()
                return
            
            btn_action.visible = False
            loading.visible = True
            page.update()
            
            all_data = muat_data_server()
            
            success = False
            if is_register:
                if any(x.get('type') == 'user' and x.get('username') == u for x in all_data):
                    page.open(ft.SnackBar(ft.Text("Username sudah dipakai!"), bgcolor="red"))
                else:
                    all_data.append({"type": "user", "username": u, "password": p})
                    simpan_data_server(all_data)
                    page.open(ft.SnackBar(ft.Text("Berhasil Daftar! Silakan Login."), bgcolor="green"))
                    toggle_mode(None)
            else:
                if any(x.get('type') == 'user' and x.get('username') == u and x.get('password') == p for x in all_data):
                    nonlocal current_user
                    current_user = u
                    success = True
                else:
                    page.open(ft.SnackBar(ft.Text("Login Gagal!"), bgcolor="red"))

            loading.visible = False
            btn_action.visible = True
            page.update()

            if success:
                show_main_app()

        btn_action.on_click = process_auth
        txt_switch.on_click = toggle_mode

        page.add(
            ft.Container(
                gradient=ft.LinearGradient(colors=[C_BG, "#E3F2FD"], begin=ft.alignment.top_center, end=ft.alignment.bottom_center),
                expand=True, padding=30, alignment=ft.alignment.center,
                content=ft.Column([
                    ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, size=80, color=C_PRIMARY),
                    ft.Text("EKFinance Manager Pro", size=24, weight="bold", color=C_PRIMARY),
                    ft.Divider(height=40, color="transparent"),
                    user_input, pass_input, 
                    ft.Container(content=loading, alignment=ft.alignment.center, height=10),
                    btn_action, txt_switch
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER)
            )
        )

    # =================================================================
    # HALAMAN 2: APLIKASI UTAMA
    # =================================================================
    def show_main_app():
        page.clean()
        now = datetime.now()

        # --- DATA HELPERS ---
        def get_my_data():
            all_data = muat_data_server()
            my_data = [x for x in all_data if x.get('type') == 'transaksi' and x.get('username') == current_user]
            return my_data, all_data

        def simpan_transaksi_user(item_baru):
            _, all_data = get_my_data()
            item_baru['username'] = current_user 
            item_baru['type'] = 'transaksi'
            all_data.append(item_baru)
            simpan_data_server(all_data)

        def hapus_transaksi_user(id_target):
            all_data = muat_data_server()
            new_data = [x for x in all_data if not (x.get('id') == id_target and x.get('username') == current_user)]
            simpan_data_server(new_data)
            refresh_data()
            page.open(ft.SnackBar(ft.Text("Data berhasil dihapus!"), bgcolor="red"))

        def edit_transaksi_user(item_asli, baru_nom, baru_ket):
            all_data = muat_data_server()
            for x in all_data:
                if x.get('id') == item_asli['id'] and x.get('username') == current_user:
                    x['nominal'] = baru_nom
                    x['keterangan'] = baru_ket
                    break
            simpan_data_server(all_data)
            refresh_data()

        # --- UI COMPONENTS ---
        dd_bulan = ft.Dropdown(label="Bulan", width=100, text_size=12, bgcolor=C_WHITE, border_radius=10, border_color=C_BORDER, content_padding=10, focused_border_color=C_PRIMARY, value=str(now.month), options=[ft.dropdown.Option(str(i+1), b) for i, b in enumerate(["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agt", "Sep", "Okt", "Nov", "Des"])])
        dd_tahun = ft.Dropdown(label="Tahun", width=110, text_size=12, bgcolor=C_WHITE, border_radius=10, border_color=C_BORDER, content_padding=10, focused_border_color=C_PRIMARY, value=str(now.year), options=[ft.dropdown.Option(str(y)) for y in range(2024, 2030)])
        
        header_app = ft.Container(
            bgcolor=C_WHITE, padding=15,
            content=ft.Row([
                ft.Row([ft.Icon(ft.Icons.PERSON, color=C_PRIMARY), ft.Text(f"Halo, {current_user}", weight="bold", color=C_TEXT)]),
                ft.IconButton(ft.Icons.LOGOUT, icon_color="red", tooltip="Logout", on_click=lambda _: show_auth_page())
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            shadow=ft.BoxShadow(blur_radius=5, color="#05000000")
        )

        container_saldo = ft.Container()
        list_view_transaksi = ft.ListView(expand=True, spacing=10)
        
        input_nom = ft.TextField(label="Nominal", keyboard_type=ft.KeyboardType.NUMBER, border_color=C_BORDER, bgcolor=C_WHITE, border_radius=10, text_size=14, content_padding=15)
        input_ket = ft.TextField(label="Keterangan", border_color=C_BORDER, bgcolor=C_WHITE, border_radius=10, text_size=14, content_padding=15)
        dd_tipe = ft.Dropdown(label="Tipe", bgcolor=C_WHITE, border_radius=10, border_color=C_BORDER, content_padding=12, options=[ft.dropdown.Option("Pengeluaran"), ft.dropdown.Option("Pemasukan")], value="Pengeluaran", expand=True, text_size=14)
        dd_kategori = ft.Dropdown(label="Kategori", bgcolor=C_WHITE, border_radius=10, border_color=C_BORDER, content_padding=12, options=[ft.dropdown.Option(k) for k in CAT_EXPENSE], value="Makanan", expand=True, text_size=14)

        def on_tipe_change(e):
            dd_kategori.options = [ft.dropdown.Option(k) for k in (CAT_INCOME if dd_tipe.value == "Pemasukan" else CAT_EXPENSE)]
            dd_kategori.value = dd_kategori.options[0].key
            page.update()
        dd_tipe.on_change = on_tipe_change

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
            simpan_transaksi_user(data_baru)
            input_nom.value = ""; input_ket.value = ""
            refresh_data()
            page.open(ft.SnackBar(ft.Text("Disimpan!"), bgcolor="green"))

        btn_simpan = ft.ElevatedButton("SIMPAN TRANSAKSI", on_click=tambah_klik, bgcolor=C_PRIMARY, color="white", width=float("inf"), height=50, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))

        def edit_transaksi_dlg(item):
            e_nom = ft.TextField(label="Nominal", value=str(item['nominal']), keyboard_type=ft.KeyboardType.NUMBER)
            e_ket = ft.TextField(label="Keterangan", value=item['keterangan'])
            def save_e(e):
                edit_transaksi_user(item, int(e_nom.value), e_ket.value)
                dlg.open = False
                page.update()
            dlg = ft.AlertDialog(title=ft.Text("Edit"), content=ft.Column([e_nom, e_ket], height=150, tight=True), actions=[ft.TextButton("Simpan", on_click=save_e)])
            page.open(dlg)

        def export_excel(e):
            data, _ = get_my_data()
            if not data: return
            try:
                df = pd.DataFrame(data)
                for c in ['username', 'type']: 
                    if c in df.columns: del df[c]
                filename = f"Laporan_{current_user}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                df.to_excel(filename, index=False)
                page.open(ft.SnackBar(ft.Text(f"Disimpan: {filename}"), bgcolor="blue"))
            except: pass

        # -- Container untuk Chart & List --
        # Disetting Alignment Center agar konten di dalamnya ketengah
        col_chart_exp = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER) 
        col_chart_cash = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        col_detail_exp = ft.Column(spacing=10, expand=True) 
        col_detail_cash = ft.Column(spacing=10, expand=True)

        # --- SUSUN LAYOUT HALAMAN ---
        tab_transaksi_content = ft.Column([
            container_saldo,
            ft.Container(padding=ft.padding.symmetric(horizontal=20), content=ft.Row([ft.Row([dd_bulan, dd_tahun]), ft.IconButton(ft.Icons.DOWNLOAD_ROUNDED, icon_color=C_PRIMARY, on_click=export_excel, tooltip="Download Excel")], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)),
            ft.Container(bgcolor=C_WHITE, padding=20, margin=20, border_radius=15, border=ft.border.all(1, "#E0E0E0"), content=ft.Column([ft.Text("Input Transaksi", weight="bold"), ft.Row([dd_tipe, dd_kategori]), input_nom, input_ket, btn_simpan], spacing=15)),
            ft.Container(content=ft.Text("Riwayat", weight="bold", size=16), padding=ft.padding.only(left=25)),
            ft.Container(content=list_view_transaksi, padding=20, expand=True)
        ], scroll="auto")

        tab_analisis_content = ft.Column([
            # Judul Arus Kas (Centered)
            ft.Container(content=ft.Text("Arus Kas", weight="bold", size=16, text_align="center"), width=float("inf"), padding=20),
            
            ft.Container(bgcolor=C_WHITE, padding=20, margin=ft.margin.symmetric(horizontal=20), border_radius=15, border=ft.border.all(1, "#E0E0E0"), shadow=ft.BoxShadow(blur_radius=10, color="#10000000"),
                         content=ft.Column([
                             ft.Container(content=col_chart_cash, alignment=ft.alignment.center), # Wrapper Center
                             ft.Divider(height=20, color="transparent"), 
                             col_detail_cash
                         ])),
            
            # Judul Detail (Centered)
            ft.Container(content=ft.Text("Detail Pengeluaran", weight="bold", size=16, text_align="center"), width=float("inf"), padding=20),
            
            ft.Container(bgcolor=C_WHITE, padding=20, margin=ft.margin.symmetric(horizontal=20), border_radius=15, border=ft.border.all(1, "#E0E0E0"), shadow=ft.BoxShadow(blur_radius=10, color="#10000000"),
                         content=ft.Column([
                             ft.Container(content=col_chart_exp, alignment=ft.alignment.center), # Wrapper Center
                             ft.Divider(height=20, color="transparent"), 
                             col_detail_exp
                         ])),
            ft.Container(height=50)
        ], scroll="auto")

        tabs = ft.Tabs(
            selected_index=0, animation_duration=300, indicator_color=C_PRIMARY, label_color=C_PRIMARY, unselected_label_color="grey", divider_color="transparent",
            tabs=[ft.Tab(text="Transaksi", icon=ft.Icons.WALLET_ROUNDED, content=tab_transaksi_content), ft.Tab(text="Analisis", icon=ft.Icons.PIE_CHART_ROUNDED, content=tab_analisis_content)],
            expand=1
        )

        page.add(header_app, tabs)

        # --- LOGIKA REFRESH DATA ---
        def refresh_data(e=None):
            page.splash = ft.ProgressBar(); page.update()
            my_data, _ = get_my_data()
            s_bln, s_thn = int(dd_bulan.value), int(dd_tahun.value)
            
            filtered = []
            for x in my_data:
                try:
                    t = datetime.strptime(x['tanggal'].split(" ")[0], "%Y-%m-%d")
                    if t.month == s_bln and t.year == s_thn: filtered.append(x)
                except: pass

            masuk = sum(x['nominal'] for x in filtered if x['tipe'] == 'Pemasukan')
            keluar = sum(x['nominal'] for x in filtered if x['tipe'] == 'Pengeluaran')
            saldo = masuk - keluar

            # UPDATE TRANSAKSI
            container_saldo.content = ft.Container(
                gradient=ft.LinearGradient(colors=[C_PRIMARY, "#1565C0"], begin=ft.alignment.top_left, end=ft.alignment.bottom_right),
                padding=20, border_radius=15, margin=ft.margin.only(bottom=10),
                content=ft.Column([
                    ft.Text("Sisa Saldo (Bulan Ini)", color="white70", size=12),
                    ft.Text(fmt_rp(saldo), color="white", size=28, weight="bold"),
                    ft.Divider(color="white24", height=20),
                    ft.Row([
                        ft.Column([ft.Text("Pemasukan", color="white70", size=11), ft.Text(fmt_rp(masuk), color="white", weight="bold", size=14)]),
                        ft.Column([ft.Text("Pengeluaran", color="white70", size=11), ft.Text(fmt_rp(keluar), color="white", weight="bold", size=14)], horizontal_alignment=ft.CrossAxisAlignment.END)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ]), shadow=ft.BoxShadow(blur_radius=10, color="#4D000000")
            )

            list_view_transaksi.controls.clear()
            if not filtered: list_view_transaksi.controls.append(ft.Text("Tidak ada data.", color="grey", text_align="center"))
            for item in reversed(filtered):
                warna = C_GREEN if item['tipe'] == 'Pemasukan' else C_RED
                icon = ft.Icons.ARROW_DOWNWARD_ROUNDED if item['tipe'] == 'Pemasukan' else ft.Icons.ARROW_UPWARD_ROUNDED
                bg_icon = "#E8F5E9" if item['tipe'] == 'Pemasukan' else "#FFEBEE"
                list_view_transaksi.controls.append(
                    ft.Container(
                        bgcolor=C_WHITE, padding=12, border_radius=12, border=ft.border.all(1, "#EEEEEE"),
                        content=ft.Row([
                            ft.Container(content=ft.Icon(icon, color=warna), bgcolor=bg_icon, padding=8, border_radius=10),
                            ft.Column([ft.Text(item['kategori'], weight="bold", color=C_TEXT), ft.Text(item['keterangan'], size=12, color="grey")], expand=True),
                            ft.Column([
                                ft.Text(fmt_rp(item['nominal']), weight="bold", color=warna),
                                ft.Text(item['tanggal'].split(" ")[0], size=10, color="grey", text_align="right")
                            ]),
                            ft.IconButton(ft.Icons.EDIT, icon_color="blue", icon_size=18, on_click=lambda e, x=item: edit_transaksi_dlg(x)),
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=C_RED, icon_size=18, on_click=lambda e, id=item['id']: hapus_transaksi_user(id))
                        ], spacing=0),
                    )
                )

            # UPDATE ANALISIS
            # A. Chart Pengeluaran
            cat_sum = {}
            for x in filtered:
                if x['tipe'] == 'Pengeluaran': cat_sum[x['kategori']] = cat_sum.get(x['kategori'], 0) + x['nominal']
            
            sections_exp = []
            col_detail_exp.controls.clear()
            
            if sum(cat_sum.values()) > 0:
                sorted_c = sorted(cat_sum.items(), key=lambda i: i[1], reverse=True)
                for i, (k, v) in enumerate(sorted_c):
                    pct = (v / sum(cat_sum.values())) * 100
                    col = CHART_COLORS[i % len(CHART_COLORS)]
                    sections_exp.append(ft.PieChartSection(value=v, color=col, radius=45, title="", title_style=ft.TextStyle(size=10, color="white", weight="bold"), title_position=0.6))
                    
                    col_detail_exp.controls.append(
                        ft.Container(padding=10, border=ft.border.only(bottom=ft.border.BorderSide(1, "#F5F5F5")),
                        content=ft.Row([
                            ft.Row([ft.Container(width=30, height=30, bgcolor=col, border_radius=8, content=ft.Icon(ft.Icons.CIRCLE, size=10, color="white")), ft.Text(k, size=13, weight="bold", color=C_TEXT)]),
                            ft.Column([ft.Text(fmt_rp(v), size=13, weight="bold", text_align="right"), ft.Text(f"({pct:.1f}%)", size=11, color="grey", text_align="right")], spacing=0)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
                    )
                
                col_chart_exp.controls = [ft.Stack([
                    ft.PieChart(sections=sections_exp, sections_space=2, center_space_radius=40, height=200, center_space_color=C_BG),
                    ft.Container(content=ft.Column([ft.Text("Total Keluar", size=10, color="grey"), ft.Text(fmt_rp(keluar), weight="bold", size=14)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER), alignment=ft.alignment.center)
                ], width=220, height=220)]
            else:
                col_chart_exp.controls = [ft.Container(content=ft.Text("Belum ada pengeluaran.", color="grey", text_align="center"), padding=20)]

            # B. Chart Arus Kas
            col_detail_cash.controls.clear()
            sections_cash = []
            tot_cash = masuk + keluar
            if tot_cash > 0:
                pct_in = (masuk / tot_cash) * 100
                pct_out = (keluar / tot_cash) * 100
                sections_cash.append(ft.PieChartSection(value=masuk, color=C_GREEN, radius=45, title="", title_style=ft.TextStyle(size=10, color="white", weight="bold"), title_position=0.6))
                sections_cash.append(ft.PieChartSection(value=keluar, color=C_RED, radius=45, title="", title_style=ft.TextStyle(size=10, color="white", weight="bold"), title_position=0.6))
                
                def item_cash(label, val, pct, color):
                    return ft.Container(padding=10, border=ft.border.only(bottom=ft.border.BorderSide(1, "#F5F5F5")),
                        content=ft.Row([
                            ft.Row([ft.Container(width=30, height=30, bgcolor=color, border_radius=8, content=ft.Icon(ft.Icons.CIRCLE, size=10, color="white")), ft.Text(label, size=13, weight="bold", color=C_TEXT)]),
                            ft.Column([ft.Text(fmt_rp(val), size=13, weight="bold", text_align="right"), ft.Text(f"({pct:.1f}%)", size=11, color="grey", text_align="right")], spacing=0)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN))
                col_detail_cash.controls.append(item_cash("Pemasukan", masuk, pct_in, C_GREEN))
                col_detail_cash.controls.append(item_cash("Pengeluaran", keluar, pct_out, C_RED))
                
                col_chart_cash.controls = [ft.Stack([
                    ft.PieChart(sections=sections_cash, sections_space=2, center_space_radius=40, height=200, center_space_color=C_BG),
                    ft.Container(content=ft.Column([ft.Text("Total Arus", size=10, color="grey"), ft.Text(fmt_rp(tot_cash), weight="bold", size=14)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER), alignment=ft.alignment.center)
                ], width=220, height=220)]
            else:
                col_chart_cash.controls = [ft.Container(content=ft.Text("Belum ada data.", color="grey", text_align="center"), padding=20)]

            page.splash = None; page.update()

        dd_bulan.on_change = refresh_data
        dd_tahun.on_change = refresh_data

        refresh_data()

    show_auth_page()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    ft.app(target=main, view=ft.WEB_BROWSER, port=port, host="0.0.0.0")
