import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

# =========================================================
#  MAİL AYARLARI (BURAYI DOLDURMAYI UNUTMA)
# =========================================================
SENDER_EMAIL = "senin_mailin@gmail.com"
SENDER_PASSWORD = "buraya_google_uygulama_sifresi_gelecek" 
# =========================================================

# --- PLUGIN VE KÜTÜPHANE AYARLARI ---
import PyQt5
qt_app_path = os.path.dirname(PyQt5.__file__)
plugin_path = os.path.join(qt_app_path, "Qt5", "plugins")
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

from PyQt5.QtCore import Qt, QDate, QSize, QTimer, QEvent, QSettings, pyqtSignal
if hasattr(Qt, 'AA_EnableHighDpiScaling'):
    from PyQt5.QtWidgets import QApplication
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QMessageBox, QTableWidget, QTableWidgetItem,
    QComboBox, QHBoxLayout, QFileDialog, QInputDialog, QScrollArea,
    QGroupBox, QCheckBox, QHeaderView, QAbstractItemView, QFrame,
    QAbstractButton, QSizePolicy, QDialog, QFormLayout, QDialogButtonBox,
    QDateEdit, QListWidget, QListWidgetItem, QSpinBox, QStackedWidget,
    QCalendarWidget
)
from PyQt5.QtGui import QIcon, QFont, QPainter, QColor, QPen, QBrush, QIntValidator, QTextCharFormat

import qtawesome as qta 
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

if getattr(sys, 'frozen', False):
    dll_path = os.path.join(sys._MEIPASS, "libzbar-64.dll")
    os.environ['PATH'] = dll_path + os.pathsep + os.environ['PATH']

# Backend Bağlantıları
from inventory import (
    add_item, get_all_items, check_item_exists, get_item_project_info,
    create_project, get_active_projects,
    assign_item_to_project, get_project_items,
    return_item_to_warehouse, close_project,
    delete_item_from_warehouse, update_item_details,
    get_project_details, get_past_projects, get_archived_items,
    get_dashboard_stats, get_category_stats, update_project_full,
    send_item_to_maintenance, get_maintenance_items, repair_item_return_to_stock,
    delete_maintenance_item_permanently,
    backup_database, get_all_projects_for_calendar
)

# PDF Kütüphaneleri
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# =============================================================================
#  STİL DOSYASI (CSS)
# =============================================================================
STYLESHEET = """
    QWidget { font-family: 'Segoe UI', sans-serif; font-size: 14px; color: #333; }
    QFrame#sidebar { background-color: #ffffff; border-right: 1px solid #e0e0e0; min-width: 240px; max-width: 240px; }
    QPushButton#menu_btn {
        background-color: transparent; color: #5f6368; border: none; border-radius: 8px;
        text-align: left; padding: 12px 20px; font-size: 15px; font-weight: 600; margin: 4px 10px;
    }
    QPushButton#menu_btn:hover { background-color: #f1f3f4; color: #1a73e8; }
    QPushButton#menu_btn:checked { background-color: #e8f0fe; color: #1a73e8; font-weight: bold; }
    QFrame#content_area { background-color: #f8f9fa; }
    QGroupBox { background-color: white; border: 1px solid #dadce0; border-radius: 8px; margin-top: 20px; padding-top: 20px; font-weight: bold; }
    QTableWidget { background-color: white; border: 1px solid #dadce0; border-radius: 6px; gridline-color: #f1f3f4; selection-background-color: #1a73e8; selection-color: white;}
    QHeaderView::section { background-color: #f1f3f4; padding: 10px; border: none; font-weight: bold; color: #5f6368; }
    QLineEdit, QComboBox, QDateEdit, QSpinBox { background-color: white; border: 1px solid #dadce0; border-radius: 4px; padding: 8px; }
    QLineEdit:focus, QComboBox:focus { border: 2px solid #1a73e8; }
    
    QPushButton#action_btn { background-color: #1a73e8; color: white; border-radius: 4px; padding: 8px 16px; font-weight: bold; border: none; }
    QPushButton#danger_btn { background-color: #d93025; color: white; border-radius: 4px; padding: 8px; border: none; }
    QPushButton#success_btn { background-color: #1e8e3e; color: white; border-radius: 4px; padding: 8px; border: none; }
    QPushButton#warning_btn { background-color: #e37400; color: white; border-radius: 4px; padding: 8px; border: none; }
    QPushButton#warning_btn:hover { background-color: #d66c00; }
    QPushButton#secondary_btn { background-color: #5f6368; color: white; border-radius: 4px; padding: 8px; border: none; }
    
    QFrame#stat_card:hover { background-color: #f1f3f4; border: 1px solid #1a73e8; }
    QFrame#stat_card { background-color: white; border-radius: 8px; border-bottom: 4px solid #1a73e8; border: 1px solid #dadce0; border-bottom-width: 4px; }
    QLabel#stat_title { color: #5f6368; font-size: 13px; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }
    QLabel#stat_value { color: #202124; font-size: 32px; font-weight: 800; }

    /* TAKVİM MODERN STİL */
    QCalendarWidget QWidget { alternate-background-color: #f8f9fa; }
    QCalendarWidget QToolButton { color: white; background-color: #1a73e8; icon-size: 18px; border: none; margin: 2px; border-radius: 4px; font-weight: bold; }
    QCalendarWidget QToolButton:hover { background-color: #1669bb; }
    QCalendarWidget QMenu { width: 150px; left: 20px; color: white; font-size: 14px; background-color: #1a73e8; }
    QCalendarWidget QSpinBox { width: 50px; font-size: 14px; color: white; background-color: #1a73e8; selection-background-color: #0d47a1; selection-color: white; }
    QCalendarWidget QSpinBox::up-button { subcontrol-origin: border; subcontrol-position: top right; width: 16px; }
    QCalendarWidget QSpinBox::down-button { subcontrol-origin: border; subcontrol-position: bottom right; width: 16px; }
    QCalendarWidget QAbstractItemView:enabled { font-size: 14px; color: #333; background-color: white; selection-background-color: #1a73e8; selection-color: white; }
    QCalendarWidget QAbstractItemView:disabled { color: #999; }
"""

# =============================================================================
#  MAİL VE PDF YARDIMCILARI
# =============================================================================
def send_email_with_pdf(to_email, subject, body, pdf_path):
    if not SENDER_EMAIL or "gmail" in SENDER_EMAIL and not SENDER_PASSWORD:
        return False, "Mail ayarları (SENDER_EMAIL/PASSWORD) app.py içinde eksik."
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        with open(pdf_path, "rb") as attachment:
            p = MIMEBase('application', 'octet-stream')
            p.set_payload(attachment.read())
            encoders.encode_base64(p)
            p.add_header('Content-Disposition', f"attachment; filename= {os.path.basename(pdf_path)}")
            msg.attach(p)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        text = msg.as_string()
        server.sendmail(SENDER_EMAIL, to_email, text)
        server.quit()
        return True, "Mail gönderildi."
    except Exception as e:
        return False, str(e)

def create_pdf_internal(file_path, project_details, items, is_history=False):
    try: pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf')); font_name = 'Arial'
    except: font_name = 'Helvetica'
    doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    title_text = "ZİMMET TUTANAĞI (GEÇMİŞ)" if is_history else "ZİMMET TUTANAĞI"
    title_style = ParagraphStyle(name='TitleTR', parent=styles['Title'], fontName=font_name, fontSize=18, spaceAfter=20)
    header_style = ParagraphStyle(name='HeaderTR', parent=styles['Heading2'], fontName=font_name, fontSize=12, spaceAfter=10)
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 10))
    p_name = project_details.get('name', '-')
    p_desc = project_details.get('desc', '-')
    s_date = project_details.get('start', '-')
    e_date = project_details.get('end', '-')
    hazirlayan = project_details.get('prep', 'Belirtilmedi')
    teslim_alan = project_details.get('deliv', 'Belirtilmedi')
    telefon = project_details.get('phone', '-')
    email = project_details.get('email', '-')
    bugun = datetime.now().strftime("%d.%m.%Y %H:%M")
    info_data = [
        ["Proje Adı:", p_name], ["Açıklama:", p_desc], ["Proje Tarihleri:", f"{s_date} - {e_date}"],
        ["Hazırlayan:", hazirlayan], ["Teslim Alan:", teslim_alan], ["Telefon:", telefon], ["Email:", email], ["Oluşturulma Tarihi:", bugun]
    ]
    t_info = Table(info_data, colWidths=[120, 350])
    t_info.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), font_name), ('FONTSIZE', (0,0), (-1,-1), 10), ('TEXTCOLOR', (0,0), (0,-1), colors.black), ('ALIGN', (0,0), (-1,-1), 'LEFT'), ('FONTNAME', (0,0), (0,-1), font_name), ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('PADDING', (0,0), (-1,-1), 6)]))
    elements.append(t_info)
    elements.append(Spacer(1, 20))
    list_title = "Teslim Edilen Ürünler Listesi (Arşiv):" if is_history else "Teslim Edilen Ürünler Listesi:"
    elements.append(Paragraph(list_title, header_style))
    
    table_data = [["Sıra", "QR Kod", "Ürün Açıklaması", "Adet"]]
    for i, item in enumerate(items, 1):
        qr = item[0]
        desc = item[1]
        # Arşivden 6 eleman gelir, Aktif projeden 3 eleman.
        if is_history and len(item) > 5:
             qty = item[5]
        elif len(item) > 2:
             qty = item[2]
        else:
             qty = "1"
             
        table_data.append([str(i), qr, desc, str(qty)])

    col_widths = [30, 100, 250, 40]
    t_items = Table(table_data, colWidths=col_widths, repeatRows=1)
    t_items.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), font_name), ('BACKGROUND', (0,0), (-1,0), colors.darkblue), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('ALIGN', (0,0), (-1,-1), 'LEFT'), ('ALIGN', (0,0), (0,-1), 'CENTER'), ('ALIGN', (-1,0), (-1,-1), 'CENTER'), ('GRID', (0,0), (-1,-1), 0.5, colors.black), ('FONTSIZE', (0,0), (-1,-1), 9), ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.whitesmoke])]))
    elements.append(t_items)
    elements.append(Spacer(1, 40))
    sig_data = [["TESLİM EDEN", f"TESLİM ALAN\n({telefon})"], [f"\n\n\n{hazirlayan}\n(İmza)", f"\n\n\n{teslim_alan}\n(İmza)"]]
    t_sig = Table(sig_data, colWidths=[250, 250])
    t_sig.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), font_name), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'TOP'), ('FONTSIZE', (0,0), (-1,-1), 10)]))
    elements.append(t_sig)
    doc.build(elements)

# =============================================================================
#  YARDIMCI PENCERELER
# =============================================================================
class ClickableFrame(QFrame):
    clicked = pyqtSignal() 
    def __init__(self, parent=None):
        super().__init__(parent); self.setCursor(Qt.PointingHandCursor) 
    def mousePressEvent(self, event): self.clicked.emit() 

class ProjectAssignDialog(QDialog):
    def __init__(self, qr_code, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Projeye Ata"); self.setMinimumSize(400, 250); self.setWindowModality(Qt.ApplicationModal)
        layout = QVBoxLayout(); layout.setSpacing(20)
        info = QLabel(f"ÜRÜN DEPODA MEVCUT:\n\n<b>{qr_code}</b>\n\nBu ürünü hangi projeye atamak istersiniz?")
        info.setAlignment(Qt.AlignCenter); info.setStyleSheet("font-size: 16px; color: #2c3e50;"); layout.addWidget(info)
        self.combo = QComboBox(); self.combo.addItem("Proje Seçiniz...", None)
        try:
            active_projects = get_active_projects()
            for pid, name in active_projects: self.combo.addItem(name, pid)
        except: pass
        self.combo.setStyleSheet("padding: 10px; font-size: 16px;"); layout.addWidget(self.combo)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.validate_and_accept); btn_box.rejected.connect(self.reject); layout.addWidget(btn_box)
        self.setLayout(layout)
    def validate_and_accept(self):
        if self.combo.currentData(): self.accept()
        else: QMessageBox.warning(self, "Uyarı", "Lütfen listeden bir proje seçin.")
    def get_selected_project(self): return self.combo.currentData()

class BulkScanDialog(QDialog):
    def __init__(self, project_id, project_name, mode='assign', parent=None):
        super().__init__(parent)
        self.project_id = project_id; self.project_name = project_name; self.mode = mode 
        title = "Seri EKLEME" if mode == 'assign' else "Seri İADE"
        self.setWindowTitle(f"{title} Modu - {project_name}"); self.setMinimumSize(500, 600); self.setWindowModality(Qt.ApplicationModal)
        self.scan_timer = QTimer(); self.scan_timer.setSingleShot(True); self.scan_timer.setInterval(200); self.scan_timer.timeout.connect(self.process_scan)
        layout = QVBoxLayout()
        color = "#1e8e3e" if mode == 'assign' else "#e37400"
        action = "projeye eklenecektir." if mode == 'assign' else "DEPOYA ALINACAKTIR."
        info_label = QLabel(f"Aktif Proje: {project_name}\n\nLütfen ürünleri sırayla okutun.\nHer okutma {action}")
        info_label.setAlignment(Qt.AlignCenter); info_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};"); layout.addWidget(info_label)
        self.scan_input = QLineEdit(); self.scan_input.setPlaceholderText("Buraya okutun...")
        self.scan_input.setStyleSheet(f"font-size: 20px; padding: 15px; border: 2px solid {color};")
        self.scan_input.textChanged.connect(self.handle_text_change); layout.addWidget(self.scan_input)
        self.log_list = QListWidget(); layout.addWidget(self.log_list)
        close_btn = QPushButton("İşlemi Bitir"); close_btn.setMinimumHeight(50); close_btn.clicked.connect(self.accept); layout.addWidget(close_btn)
        self.setLayout(layout); self.scan_input.setFocus()
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter): self.process_scan(); event.accept()
        else: super().keyPressEvent(event)
    def handle_text_change(self): self.scan_timer.start()
    def process_scan(self):
        self.scan_timer.stop(); qr_code = self.scan_input.text().strip(); 
        if not qr_code: return
        try:
            if self.mode == 'assign': assign_item_to_project(self.project_id, qr_code); self.log_message(f"✅ EKLENDİ: {qr_code}", "green")
            else: return_item_to_warehouse(self.project_id, qr_code); self.log_message(f"↩️ İADE ALINDI: {qr_code}", "orange")
        except Exception as e:
            err_msg = str(e)
            if "Depoda ürün yok" in err_msg or "bulunamadı" in err_msg: self.log_message(f"❌ HATA: {qr_code} ({err_msg})", "red"); QApplication.beep()
            else: self.log_message(f"⚠️ UYARI: {err_msg}", "red"); QApplication.beep()
        self.scan_input.clear(); self.scan_input.setFocus()
    def log_message(self, message, color):
        item = QListWidgetItem(message)
        if color == "green": item.setForeground(QColor("#1e8e3e"))
        elif color == "red": item.setForeground(QColor("#d93025"))
        elif color == "orange": item.setForeground(QColor("#e37400"))
        self.log_list.insertItem(0, item) 

class QRGeneratorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("Toplu QR Kod Oluşturucu"); self.setMinimumSize(400, 300)
        layout = QFormLayout(); layout.setSpacing(15)
        self.prefix_input = QLineEdit(); self.prefix_input.setPlaceholderText("Örn: PC-")
        self.start_num_input = QSpinBox(); self.start_num_input.setRange(1, 999999); self.start_num_input.setValue(1)
        self.count_input = QSpinBox(); self.count_input.setRange(1, 1000); self.count_input.setValue(10)
        gen_btn = QPushButton("Oluştur ve Kaydet"); gen_btn.setMinimumHeight(45); gen_btn.setIcon(qta.icon('fa5s.save', color='black'))
        gen_btn.clicked.connect(self.generate_qrs)
        layout.addRow("Ön Ek (Prefix):", self.prefix_input); layout.addRow("Başlangıç No:", self.start_num_input)
        layout.addRow("Kaç Adet:", self.count_input); layout.addRow("", gen_btn); self.setLayout(layout)
    def generate_qrs(self):
        import qrcode
        from PIL import Image, ImageDraw, ImageFont
        prefix = self.prefix_input.text(); start = self.start_num_input.value(); count = self.count_input.value()
        folder = QFileDialog.getExistingDirectory(self, "Klasör Seç"); 
        if not folder: return
        try:
            for i in range(count):
                num = start + i; code_text = f"{prefix}{str(num).zfill(3)}"
                qr = qrcode.QRCode(box_size=10, border=2); qr.add_data(code_text); qr.make(fit=True)
                qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
                width, height = qr_img.size; extra_height = 50 
                new_img = Image.new('RGB', (width, height + extra_height), 'white'); new_img.paste(qr_img, (0, 0))
                draw = ImageDraw.Draw(new_img)
                try: font = ImageFont.truetype("arial.ttf", 26)
                except: font = ImageFont.load_default()
                bbox = draw.textbbox((0, 0), code_text, font=font); text_w = bbox[2] - bbox[0]
                text_x = (width - text_w) / 2; text_y = height + (extra_height - (bbox[3] - bbox[1])) / 2 - 5 
                draw.text((text_x, text_y), code_text, fill="black", font=font)
                new_img.save(os.path.join(folder, f"{code_text}.png"))
            QMessageBox.information(self, "Başarılı", f"{count} adet QR oluşturuldu!"); self.accept()
        except Exception as e: QMessageBox.critical(self, "Hata", str(e))

class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(); self.layout.setSpacing(20); self.layout.setContentsMargins(20, 20, 20, 20)
        self.cards_layout = QHBoxLayout()
        self.card_stock = self.create_card("📦 TOPLAM STOK", "#1a73e8")
        self.card_in_project = self.create_card("🚀 SAHADAKİ ÜRÜNLER", "#e37400")
        self.card_active_proj = self.create_card("📅 AKTİF PROJE", "#1e8e3e")
        self.card_maint = self.create_card("🛠️ ARIZA / KAYIP", "#d93025") 
        self.cards_layout.addWidget(self.card_stock); self.cards_layout.addWidget(self.card_in_project)
        self.cards_layout.addWidget(self.card_active_proj); self.cards_layout.addWidget(self.card_maint)
        self.layout.addLayout(self.cards_layout)
        chart_group = QGroupBox("Kategori Dağılımı")
        chart_layout = QVBoxLayout()
        self.figure = plt.figure(figsize=(5, 4)); self.canvas = FigureCanvas(self.figure)
        chart_layout.addWidget(self.canvas); chart_group.setLayout(chart_layout); self.layout.addWidget(chart_group)
        self.setLayout(self.layout)
    def create_card(self, title, color):
        frame = ClickableFrame(); frame.setObjectName("stat_card")
        frame.setStyleSheet(f"QFrame#stat_card {{ border-bottom: 4px solid {color}; background: white; border-radius: 8px; }}")
        lay = QVBoxLayout()
        lbl_title = QLabel(title); lbl_title.setObjectName("stat_title"); lbl_title.setAlignment(Qt.AlignCenter)
        lbl_value = QLabel("0"); lbl_value.setObjectName("stat_value"); lbl_value.setAlignment(Qt.AlignCenter)
        lbl_value.setStyleSheet(f"color: {color};"); lay.addWidget(lbl_title); lay.addWidget(lbl_value)
        frame.setLayout(lay); frame.lbl_value = lbl_value; return frame
    def refresh_data(self):
        try:
            total, in_proj, active, maint = get_dashboard_stats()
            self.card_stock.lbl_value.setText(str(total)); self.card_in_project.lbl_value.setText(str(in_proj))
            self.card_active_proj.lbl_value.setText(str(active)); self.card_maint.lbl_value.setText(str(maint))
        except: pass
        try:
            self.figure.clear(); cat_data = get_category_stats()
            if cat_data:
                labels = [x[0] if x[0] else "Diğer" for x in cat_data]; sizes = [x[1] for x in cat_data]
                colors = ['#4285f4', '#ea4335', '#fbbc04', '#34a853', '#ff6d01', '#46bdc6']
                ax = self.figure.add_subplot(111); ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors)
                ax.axis('equal')
            self.canvas.draw()
        except: pass

class InventoryApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Eventory - Envanter Yönetim Sistemi")
        icon_path = resource_path("icons/app_icon.ico")
        if os.path.exists(icon_path): self.setWindowIcon(QIcon(icon_path))
        self.setGeometry(100, 100, 1400, 850); self.setStyleSheet(STYLESHEET)
        QApplication.instance().installEventFilter(self)
        self.scan_buffer = ""; self.last_selected_project_id = None; self.settings = QSettings("MyCompany", "Eventory")
        self.main_layout = QHBoxLayout(); self.main_layout.setContentsMargins(0, 0, 0, 0); self.main_layout.setSpacing(0)
        
        self.sidebar = QFrame(); self.sidebar.setObjectName("sidebar")
        self.sidebar_layout = QVBoxLayout(); self.sidebar_layout.setContentsMargins(10, 30, 10, 20); self.sidebar_layout.setSpacing(8)
        app_title = QLabel("📦 EVENTORY"); app_title.setAlignment(Qt.AlignCenter); app_title.setStyleSheet("color: #202124; font-size: 20px; font-weight: 800; margin-bottom: 30px;")
        self.sidebar_layout.addWidget(app_title)
        
        self.btn_dash = self.create_menu_btn("  Genel Durum", "fa5s.chart-line", 0)
        self.btn_depo = self.create_menu_btn("  Depo Stok", "fa5s.boxes", 1)
        self.btn_new = self.create_menu_btn("  Proje Oluştur", "fa5s.plus-circle", 2)
        self.btn_active = self.create_menu_btn("  Aktif Projeler", "fa5s.rocket", 3)
        self.btn_hist = self.create_menu_btn("  Proje Geçmişi", "fa5s.history", 4)
        self.btn_maint = self.create_menu_btn("  Arıza / Kayıp", "fa5s.tools", 5) 
        self.btn_cal = self.create_menu_btn("  Takvim", "fa5s.calendar-alt", 6) 
        self.sidebar_layout.addStretch()
        
        btn_backup = QPushButton("Yedekle"); btn_backup.setIcon(qta.icon('fa5s.save', color='#9aa0a6'))
        btn_backup.setStyleSheet("background: transparent; color: #9aa0a6; border: none; text-align: left; padding-left: 20px;")
        btn_backup.clicked.connect(self.run_backup); self.sidebar_layout.addWidget(btn_backup)
        
        footer = QLabel("vEventory.Final.2"); footer.setStyleSheet("color: #9aa0a6; padding-left: 10px; font-size: 12px;")
        self.sidebar_layout.addWidget(footer); self.sidebar.setLayout(self.sidebar_layout); self.main_layout.addWidget(self.sidebar)
        
        self.content_area = QFrame(); self.content_area.setObjectName("content_area")
        self.content_layout = QVBoxLayout(); self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.pages = QStackedWidget()
        self.dashboard_page = DashboardWidget()
        self.dashboard_page.card_stock.clicked.connect(lambda: self.switch_page(1))
        self.dashboard_page.card_active_proj.clicked.connect(lambda: self.switch_page(3))
        self.dashboard_page.card_maint.clicked.connect(lambda: self.switch_page(5)) 
        
        self.depo_page = self.setup_depo_page()
        self.create_page = self.setup_create_page()
        self.active_page = self.setup_active_page()
        self.history_page = self.setup_history_page()
        self.maint_page = self.setup_maintenance_page() 
        self.cal_page = self.setup_calendar_page() 
        
        self.pages.addWidget(self.dashboard_page); self.pages.addWidget(self.depo_page)
        self.pages.addWidget(self.create_page); self.pages.addWidget(self.active_page)
        self.pages.addWidget(self.history_page); self.pages.addWidget(self.maint_page)
        self.pages.addWidget(self.cal_page)
        
        self.content_layout.addWidget(self.pages); self.content_area.setLayout(self.content_layout); self.main_layout.addWidget(self.content_area)
        self.setLayout(self.main_layout); self.btn_dash.click() 

    def eventFilter(self, source, event):
        if event.type() == QEvent.KeyPress:
            if QApplication.activeModalWidget(): return super().eventFilter(source, event)
            if self.pages.currentIndex() in [1, 3]:
                focused_widget = self.focusWidget()
                is_input_field = isinstance(focused_widget, (QLineEdit, QSpinBox))
                if not is_input_field:
                    if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                        if self.scan_buffer: self.qr_input.setText(self.scan_buffer); self.process_logic_scan(); self.scan_buffer = "" 
                        return True 
                    elif event.text(): self.scan_buffer += event.text(); return True 
        return super().eventFilter(source, event)

    def create_menu_btn(self, text, icon_name, index):
        btn = QPushButton(text); btn.setIcon(qta.icon(icon_name, color='#5f6368')); btn.setIconSize(QSize(20, 20))
        btn.setObjectName("menu_btn"); btn.setCheckable(True); btn.setAutoExclusive(True); btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda: self.switch_page(index)); self.sidebar_layout.addWidget(btn)
        return btn

    def switch_page(self, index):
        buttons = [self.btn_dash, self.btn_depo, self.btn_new, self.btn_active, self.btn_hist, self.btn_maint, self.btn_cal]
        if 0 <= index < len(buttons): buttons[index].setChecked(True)
        self.pages.setCurrentIndex(index); QApplication.processEvents()
        if index == 0: self.dashboard_page.refresh_data()
        elif index == 1: self.load_items_to_table(); self.qr_input.setFocus()
        elif index == 3: self.load_project_combo()
        elif index == 4: self.load_history_combo()
        elif index == 5: self.load_maint_table()
        elif index == 6: self.refresh_calendar()

    def run_backup(self):
        folder = QFileDialog.getExistingDirectory(self, "Yedeklenecek Klasörü Seç")
        if folder:
            success, msg = backup_database(folder)
            if success: QMessageBox.information(self, "Başarılı", msg)
            else: QMessageBox.critical(self, "Hata", msg)

    # --- TAKVİM SAYFASI ---
    def setup_calendar_page(self):
        page = QWidget(); layout = QVBoxLayout()
        self.calendar = QCalendarWidget(); self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self.show_date_details)
        self.cal_list = QListWidget()
        
        self.cal_list.itemDoubleClicked.connect(self.open_project_from_calendar)
        
        layout.addWidget(QLabel("📅 PROJE TAKVİMİ (Mavi günlerde proje var)")); layout.addWidget(self.calendar)
        layout.addWidget(QLabel("Seçili Tarihteki Projeler (Gitmek için çift tıklayın):")); layout.addWidget(self.cal_list)
        page.setLayout(layout); return page

    def refresh_calendar(self):
        norm_format = QTextCharFormat(); self.calendar.setDateTextFormat(QDate(), norm_format)
        projs = get_all_projects_for_calendar()
        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QBrush(QColor("#d2e3fc"))); highlight_format.setFontWeight(QFont.Bold)
        for _, _, start, end, _ in projs: 
            if not start or not end: continue
            d_curr = QDate(start.year, start.month, start.day); d_end = QDate(end.year, end.month, end.day)
            while d_curr <= d_end: self.calendar.setDateTextFormat(d_curr, highlight_format); d_curr = d_curr.addDays(1)

    def show_date_details(self, date):
        self.cal_list.clear()
        projs = get_all_projects_for_calendar() # (id, name, start, end, status)
        sel_date = date.toPyDate()
        found = False
        
        for pid, name, start, end, status in projs:
            if start and end and start <= sel_date <= end:
                icon = "🚀" if status == 'Active' else "🏁"
                status_text = "(Aktif)" if status == 'Active' else "(Kapalı)"
                item_text = f"{icon} {name} {status_text} | {start.strftime('%d.%m')} - {end.strftime('%d.%m')}"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, pid) # ID
                item.setData(Qt.UserRole + 1, status) # Status
                if status == 'Closed': item.setForeground(QColor("gray"))
                self.cal_list.addItem(item)
                found = True
        
        if not found: self.cal_list.addItem("Bu tarihte proje yok.")

    def open_project_from_calendar(self, item):
        pid = item.data(Qt.UserRole)
        status = item.data(Qt.UserRole + 1)
        if not pid: return
        if status == 'Active':
            self.switch_page(3) 
            self.load_project_combo() 
            index = self.p_combo.findData(pid)
            if index >= 0: self.p_combo.setCurrentIndex(index)
        elif status == 'Closed':
            self.switch_page(4) 
            self.load_history_combo()
            index = self.history_combo.findData(pid)
            if index >= 0: self.history_combo.setCurrentIndex(index)

    # --- BAKIM SAYFASI ---
    def setup_maintenance_page(self):
        page = QWidget(); layout = QVBoxLayout()
        self.m_table = QTableWidget(); self.m_table.setColumnCount(5)
        self.m_table.setHorizontalHeaderLabels(["QR", "Ürün", "Arıza Nedeni", "Kaynak Proje", "İşlem"])
        self.m_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(QLabel("<h2>🛠️ Arıza ve Kayıp Listesi</h2>")); layout.addWidget(self.m_table)
        page.setLayout(layout); return page

    def load_maint_table(self):
        items = get_maintenance_items()
        self.m_table.setRowCount(len(items))
        for r, (mid, qr, desc, fault, source, date) in enumerate(items):
            self.m_table.setItem(r, 0, QTableWidgetItem(qr)); self.m_table.setItem(r, 1, QTableWidgetItem(desc))
            self.m_table.setItem(r, 2, QTableWidgetItem(fault)); self.m_table.setItem(r, 3, QTableWidgetItem(source))
            container = QWidget(); layout = QHBoxLayout(container); layout.setContentsMargins(2, 2, 2, 2); layout.setSpacing(5)
            btn_repair = QPushButton(" Depoya İade"); btn_repair.setIcon(qta.icon('fa5s.check', color='green')); btn_repair.setStyleSheet("background-color: #e6f4ea; color: #1e8e3e; border: 1px solid #1e8e3e; border-radius: 4px; padding: 4px;")
            btn_repair.clicked.connect(lambda _, x=mid: self.fix_item(x))
            btn_scrap = QPushButton(" Sil"); btn_scrap.setIcon(qta.icon('fa5s.trash', color='red')); btn_scrap.setStyleSheet("background-color: #fce8e6; color: #d93025; border: 1px solid #d93025; border-radius: 4px; padding: 4px;")
            btn_scrap.clicked.connect(lambda _, x=mid: self.scrap_item(x))
            layout.addWidget(btn_repair); layout.addWidget(btn_scrap); self.m_table.setCellWidget(r, 4, container)

    def fix_item(self, mid):
        if QMessageBox.question(self, "Onay", "Ürün onarıldı ve stoga eklenecek. Emin misin?") == QMessageBox.Yes:
            try: repair_item_return_to_stock(mid); self.load_maint_table(); QMessageBox.information(self, "Başarılı", "Ürün stoga eklendi.")
            except Exception as e: QMessageBox.critical(self, "Hata", str(e))

    def scrap_item(self, mid):
        if QMessageBox.question(self, "DİKKAT", "Bu ürün TAMAMEN SİLİNECEK (Kayıp/Hurda). Geri alınamaz.\nOnaylıyor musunuz?") == QMessageBox.Yes:
            try: delete_maintenance_item_permanently(mid); self.load_maint_table(); QMessageBox.information(self, "Silindi", "Ürün sistemden tamamen kaldırıldı.")
            except Exception as e: QMessageBox.critical(self, "Hata", str(e))

    # --- DİĞER SAYFALAR ---
    def setup_depo_page(self):
        page = QWidget(); layout = QVBoxLayout(); grp = QGroupBox("Yeni Ürün Girişi"); main_h_layout = QHBoxLayout(); inputs_layout = QVBoxLayout()
        self.qr_input = QLineEdit(); self.qr_input.setPlaceholderText("QR Kodu / ID (Tıklayıp Okutun)"); self.qr_input.setMinimumHeight(40)
        self.qr_input.returnPressed.connect(self.process_logic_scan)
        row2 = QHBoxLayout(); self.cat_input = QComboBox(); self.cat_input.addItems(["Kategori Seç...", "Görüntü", "Ses", "Işık", "Bilişim"]); self.cat_input.setMinimumWidth(200); self.cat_input.setMinimumHeight(40)
        self.qty_input = QLineEdit(); self.qty_input.setPlaceholderText("Adet (1)"); self.qty_input.setValidator(QIntValidator()); self.qty_input.setFixedWidth(80); self.qty_input.setMinimumHeight(40)
        self.desc_input = QLineEdit(); self.desc_input.setPlaceholderText("Ürün Açıklaması (Örn: Monster Abra A5)"); self.desc_input.setMinimumHeight(40)
        row2.addWidget(self.cat_input); row2.addWidget(self.qty_input); row2.addWidget(self.desc_input)
        inputs_layout.addWidget(self.qr_input); inputs_layout.addLayout(row2)
        buttons_layout = QVBoxLayout(); buttons_layout.setSpacing(10)
        btn_save = QPushButton(" Hızlı Kaydet"); btn_save.setIcon(qta.icon('fa5s.save', color='white')); btn_save.setObjectName("action_btn"); btn_save.setMinimumHeight(45); btn_save.clicked.connect(self.add_item_db)
        btn_scan = QPushButton(" Dosyadan"); btn_scan.setIcon(qta.icon('fa5s.image', color='white')); btn_scan.setObjectName("secondary_btn"); btn_scan.clicked.connect(self.scan_file)
        btn_gen = QPushButton(" QR Üret"); btn_gen.setIcon(qta.icon('fa5s.qrcode', color='white')); btn_gen.setObjectName("secondary_btn"); btn_gen.clicked.connect(self.open_qr_gen)
        buttons_layout.addWidget(btn_save); sub_btn_row = QHBoxLayout(); sub_btn_row.addWidget(btn_scan); sub_btn_row.addWidget(btn_gen); buttons_layout.addLayout(sub_btn_row)
        main_h_layout.addLayout(inputs_layout, stretch=3); main_h_layout.addLayout(buttons_layout, stretch=1); grp.setLayout(main_h_layout); layout.addWidget(grp)
        grp_tbl = QGroupBox("Depo Listesi"); t_lay = QVBoxLayout(); search_lay = QHBoxLayout()
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("🔍 Ara..."); self.search_input.textChanged.connect(self.filter_table)
        self.filter_combo = QComboBox(); self.filter_combo.addItems(["Tümü", "Görüntü", "Ses", "Işık", "Bilişim", "Diğer"]); self.filter_combo.setFixedWidth(150); self.filter_combo.currentTextChanged.connect(self.filter_table)
        search_lay.addWidget(self.search_input); search_lay.addWidget(self.filter_combo)
        self.item_table = QTableWidget(); self.item_table.setColumnCount(7); self.item_table.setHorizontalHeaderLabels(["QR", "Kategori", "Açıklama", "Adet", "Proje Ata", "Düzenle", "Sil"])
        header = self.item_table.horizontalHeader(); header.setSectionResizeMode(QHeaderView.Stretch); header.setSectionResizeMode(5, QHeaderView.ResizeToContents); header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.item_table.verticalHeader().setVisible(False); self.item_table.setAlternatingRowColors(True); self.item_table.setFocusPolicy(Qt.NoFocus) 
        t_lay.addLayout(search_lay); t_lay.addWidget(self.item_table); grp_tbl.setLayout(t_lay); layout.addWidget(grp_tbl); page.setLayout(layout); return page

    def setup_create_page(self):
        page = QWidget(); layout = QVBoxLayout(); grp = QGroupBox("Proje Detayları"); form = QFormLayout(); form.setSpacing(20)
        self.p_name = QLineEdit(); self.p_desc = QLineEdit(); self.p_user = QLineEdit(); self.p_delivered_to = QLineEdit(); self.p_phone = QLineEdit(); self.p_email = QLineEdit() 
        saved_email = self.settings.value("last_email", ""); 
        if saved_email: self.p_email.setText(str(saved_email))
        d_row = QHBoxLayout(); d_row.setSpacing(10); d_row.setContentsMargins(0,0,0,0)
        self.d_start = QDateEdit(QDate.currentDate()); self.d_start.setCalendarPopup(True); self.d_start.setFixedWidth(120)
        self.d_end = QDateEdit(QDate.currentDate().addDays(1)); self.d_end.setCalendarPopup(True); self.d_end.setFixedWidth(120)
        d_row.addWidget(QLabel("Başlangıç Tarihi:")); d_row.addWidget(self.d_start); d_row.addSpacing(20); d_row.addWidget(QLabel("Bitiş Tarihi:")); d_row.addWidget(self.d_end); d_row.addStretch()
        btn_create = QPushButton(" Projeyi Başlat"); btn_create.setIcon(qta.icon('fa5s.plus', color='white')); btn_create.setObjectName("success_btn"); btn_create.setMinimumHeight(45); btn_create.clicked.connect(self.create_proj_db)
        form.addRow("Proje Adı:", self.p_name); form.addRow("Hazırlayan:", self.p_user); form.addRow("Teslim Alan:", self.p_delivered_to); form.addRow("Telefon:", self.p_phone); form.addRow("Email:", self.p_email); form.addRow(d_row); form.addRow("Notlar:", self.p_desc); form.addRow("", btn_create)
        grp.setLayout(form); layout.addWidget(grp); layout.addStretch(); page.setLayout(layout); return page
    
    def setup_active_page(self):
        page = QWidget(); layout = QVBoxLayout(); top_bar = QHBoxLayout(); self.p_combo = QComboBox(); self.p_combo.currentIndexChanged.connect(self.load_project_items)
        btn_bulk = QPushButton(" Seri Ekle"); btn_bulk.setIcon(qta.icon('fa5s.barcode', color='white')); btn_bulk.setObjectName("success_btn"); btn_bulk.clicked.connect(lambda: self.open_bulk(mode='assign'))
        btn_bulk_return = QPushButton(" Seri İade"); btn_bulk_return.setIcon(qta.icon('fa5s.reply-all', color='white')); btn_bulk_return.setObjectName("warning_btn"); btn_bulk_return.clicked.connect(lambda: self.open_bulk(mode='return'))
        btn_edit_proj = QPushButton(" Projeyi Düzenle"); btn_edit_proj.setIcon(qta.icon('fa5s.edit', color='white')); btn_edit_proj.setObjectName("secondary_btn"); btn_edit_proj.clicked.connect(self.edit_active_project)
        btn_pdf = QPushButton(" Zimmet Fişi"); btn_pdf.setIcon(qta.icon('fa5s.file-pdf', color='white')); btn_pdf.setObjectName("secondary_btn"); btn_pdf.clicked.connect(self.gen_pdf)
        btn_close = QPushButton(" Projeyi Sonlandır"); btn_close.setIcon(qta.icon('fa5s.times-circle', color='white')); btn_close.setObjectName("danger_btn"); btn_close.clicked.connect(self.close_proj)
        top_bar.addWidget(QLabel("Proje:")); top_bar.addWidget(self.p_combo, 2); top_bar.addWidget(btn_bulk); top_bar.addWidget(btn_bulk_return); top_bar.addWidget(btn_edit_proj); top_bar.addWidget(btn_pdf); top_bar.addWidget(btn_close)
        self.info_frame = QFrame(); self.info_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 5px; margin-bottom: 5px;")
        main_info_layout = QHBoxLayout(self.info_frame); main_info_layout.setSpacing(30); main_info_layout.setContentsMargins(10, 5, 10, 5)
        def create_info_col(title, label_widget):
            v_lay = QVBoxLayout(); v_lay.setSpacing(2); title_lbl = QLabel(title); title_lbl.setStyleSheet("color: #7f8c8d; font-size: 11px; font-weight: bold;")
            label_widget.setStyleSheet("color: #2c3e50; font-size: 14px; font-weight: bold;"); v_lay.addWidget(title_lbl); v_lay.addWidget(label_widget); return v_lay
        self.lbl_p_user = QLabel("-"); self.lbl_p_date = QLabel("-"); self.lbl_p_desc = QLabel("-"); self.lbl_p_desc.setWordWrap(True)
        main_info_layout.addLayout(create_info_col("Hazırlayan", self.lbl_p_user)); main_info_layout.addLayout(create_info_col("Tarih Aralığı", self.lbl_p_date)); main_info_layout.addLayout(create_info_col("Notlar", self.lbl_p_desc)); main_info_layout.addStretch()
        self.p_table = QTableWidget(); self.p_table.setColumnCount(5); self.p_table.setHorizontalHeaderLabels(["QR", "Ürün", "Adet", "İade", "Arızalı İade"]); self.p_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); self.p_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents); self.p_table.setFocusPolicy(Qt.NoFocus)
        layout.addLayout(top_bar); layout.addWidget(self.info_frame); layout.addWidget(self.p_table); page.setLayout(layout); return page

    def setup_history_page(self):
        page = QWidget(); layout = QVBoxLayout(); h_bar = QHBoxLayout(); self.history_combo = QComboBox(); self.history_combo.currentIndexChanged.connect(self.load_history_details)
        h_bar.addWidget(QLabel("Geçmiş Projeler:")); h_bar.addWidget(self.history_combo, 1)
        btn_hist_pdf = QPushButton(" Geçmiş Zimmet Fişi"); btn_hist_pdf.setIcon(qta.icon('fa5s.file-pdf', color='white')); btn_hist_pdf.setObjectName("secondary_btn"); btn_hist_pdf.clicked.connect(self.gen_history_pdf)
        h_bar.addWidget(btn_hist_pdf); h_bar.addStretch()
        self.hist_info_frame = QFrame(); self.hist_info_frame.setStyleSheet("background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 5px; margin-bottom: 5px;")
        h_info_lay = QHBoxLayout(self.hist_info_frame); h_info_lay.setSpacing(30); h_info_lay.setContentsMargins(10, 5, 10, 5)
        def create_h_info(title, lbl):
            v = QVBoxLayout(); v.setSpacing(2); t = QLabel(title.upper()); t.setStyleSheet("color: #7f8c8d; font-size: 11px; font-weight: bold;")
            lbl.setStyleSheet("color: #2c3e50; font-size: 14px; font-weight: bold;"); v.addWidget(t); v.addWidget(lbl); return v
        self.lbl_h_user = QLabel("-"); self.lbl_h_date = QLabel("-"); self.lbl_h_desc = QLabel("-"); self.lbl_h_desc.setWordWrap(True)
        h_info_lay.addLayout(create_h_info("Hazırlayan", self.lbl_h_user)); h_info_lay.addLayout(create_h_info("Tarih", self.lbl_h_date)); h_info_lay.addLayout(create_h_info("Not", self.lbl_h_desc)); h_info_lay.addStretch()
        self.history_table = QTableWidget(); self.history_table.setColumnCount(6); self.history_table.setHorizontalHeaderLabels(["QR", "Kat.", "Ürün", "Adet", "Giriş", "Çıkış"]); self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addLayout(h_bar); layout.addWidget(self.hist_info_frame); layout.addWidget(self.history_table); page.setLayout(layout); return page

    # ==================== MANTIK MERKEZİ (İADE -> ATAMA -> YENİ) ====================
    def process_logic_scan(self):
        qr = self.qr_input.text().strip()
        if not qr: return 
        p_info = get_item_project_info(qr)
        if p_info:
            reply = QMessageBox.question(self, "İade Onayı", f"Bu ürün ({qr}) şu an '{p_info[1]}' projesinde.\nDepoya iade almak ister misiniz?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                try:
                    return_item_to_warehouse(p_info[0], qr)
                    self.setWindowTitle(f"✅ İADE ALINDI: {qr}")
                    self.load_items_to_table()
                    if self.pages.currentIndex() == 3: self.load_project_items()
                    self.qr_input.clear()
                except Exception as e: QMessageBox.critical(self, "Hata", str(e))
            else: self.qr_input.clear()
            return
        if check_item_exists(qr):
            dialog = ProjectAssignDialog(qr, self)
            if dialog.exec_():
                pid = dialog.get_selected_project()
                if pid:
                    try:
                        assign_item_to_project(pid, qr)
                        self.setWindowTitle(f"✅ ATANDI: {qr}")
                        self.load_items_to_table()
                        self.dashboard_page.refresh_data()
                    except Exception as e: QMessageBox.critical(self, "Hata", str(e))
            self.qr_input.clear()
            return
        self.desc_input.setFocus()

    def add_item_db(self):
        qr = self.qr_input.text(); cat = self.cat_input.currentText()
        desc = self.desc_input.text(); qty = self.qty_input.text()
        if not qr: return
        try:
            add_item(qr, desc, "Diğer" if "Seç" in cat else cat, int(qty) if qty else 1)
            self.load_items_to_table(); self.qr_input.clear(); self.desc_input.clear(); self.qty_input.clear()
            self.qr_input.setFocus()
        except Exception as e: QMessageBox.critical(self, "Hata", str(e))

    def load_items_to_table(self):
        self.all_items = get_all_items()
        self.filter_table()

    def filter_table(self):
        txt = self.search_input.text().lower()
        sel_cat = self.filter_combo.currentText()
        data = []
        for i in self.all_items:
            qr_txt = i[0].lower(); desc_txt = i[1].lower() if i[1] else ""
            cat_txt = i[3] if i[3] else "Diğer"
            match_txt = (txt in qr_txt or txt in desc_txt)
            match_cat = (sel_cat == "Tümü" or cat_txt == sel_cat)
            if match_txt and match_cat: data.append(i)
        self.item_table.setSortingEnabled(False)
        self.item_table.setRowCount(len(data))
        active_projs = get_active_projects()
        for r, (qr, desc, qty, cat) in enumerate(data):
            self.item_table.setItem(r, 0, QTableWidgetItem(qr))
            self.item_table.setItem(r, 1, QTableWidgetItem(cat))
            self.item_table.setItem(r, 2, QTableWidgetItem(desc))
            self.item_table.setItem(r, 3, QTableWidgetItem(str(qty)))
            cmb = QComboBox()
            cmb.addItem("Ata...", None)
            for pid, pname in active_projs: cmb.addItem(pname, pid)
            cmb.currentIndexChanged.connect(lambda i, row=r, c=cmb: self.assign_from_list(row, c))
            self.item_table.setCellWidget(r, 4, cmb)
            btn_edit = QPushButton(" Düzenle"); btn_edit.setIcon(qta.icon('fa5s.edit', color='#333'))
            btn_edit.setObjectName("table_btn")
            btn_edit.clicked.connect(lambda _, row=r: self.open_edit(row))
            self.item_table.setCellWidget(r, 5, btn_edit)
            btn_del = QPushButton(" Sil"); btn_del.setIcon(qta.icon('fa5s.trash', color='#d93025'))
            btn_del.setObjectName("table_btn")
            btn_del.clicked.connect(lambda _, row=r: self.del_item(row))
            self.item_table.setCellWidget(r, 6, btn_del)
        self.item_table.setSortingEnabled(True)

    def auto_process_scanned_qr(self, text):
        if text.endswith('\n') or text.endswith('\r'):
            self.qr_input.setText(text.strip())
            self.process_logic_scan()

    def assign_from_list(self, r, cmb):
        pid = cmb.currentData()
        if not pid: return
        qr = self.item_table.item(r, 0).text()
        current_stock = int(self.item_table.item(r, 3).text()) 
        if current_stock == 1:
            try:
                assign_item_to_project(pid, qr, 1)
                self.load_items_to_table()
                self.dashboard_page.refresh_data()
                QMessageBox.information(self, "Başarılı", f"1 adet '{qr}' projeye eklendi.")
            except Exception as e: QMessageBox.critical(self, "Hata", str(e))
        else:
            count, ok = QInputDialog.getInt(self, "Adet Seçimi", f"Kaç adet '{qr}' göndermek istiyorsunuz?", 1, 1, current_stock, 1)
            if ok:
                try:
                    assign_item_to_project(pid, qr, count)
                    self.load_items_to_table()
                    self.dashboard_page.refresh_data()
                    QMessageBox.information(self, "Başarılı", f"{count} adet ürün projeye eklendi.")
                except Exception as e: QMessageBox.critical(self, "Hata", str(e))
        cmb.setCurrentIndex(0) 

    def del_item(self, r):
        qr = self.item_table.item(r, 0).text()
        if QMessageBox.question(self, "Sil", "Emin misin?") == QMessageBox.Yes:
            delete_item_from_warehouse(qr); self.load_items_to_table()

    def open_edit(self, r):
        qr = self.item_table.item(r, 0).text().strip()
        cat = self.item_table.item(r, 1).text()
        desc = self.item_table.item(r, 2).text()
        qty_text = self.item_table.item(r, 3).text()
        qty = int(qty_text) if qty_text.isdigit() else 1
        d = QDialog(self)
        d.setWindowTitle(f"Düzenle: {qr}")
        d.setMinimumSize(300, 200)
        lay = QFormLayout(d)
        c_edit = QComboBox()
        c_edit.addItems(["Görüntü", "Ses", "Işık", "Bilişim", "Diğer"])
        c_edit.setCurrentText(cat)
        d_edit = QLineEdit(desc)
        q_edit = QSpinBox(); q_edit.setRange(1, 99999); q_edit.setValue(qty)
        lay.addRow("Kategori:", c_edit)
        lay.addRow("Ürün Adı:", d_edit)
        lay.addRow("Adet:", q_edit)
        btn = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn.accepted.connect(d.accept); btn.rejected.connect(d.reject)
        lay.addRow(btn)
        if d.exec_():
            try:
                update_item_details(qr, d_edit.text(), c_edit.currentText(), q_edit.value())
                self.load_items_to_table()
                QMessageBox.information(self, "Başarılı", "Ürün güncellendi!")
            except Exception as e: QMessageBox.critical(self, "Hata", f"Güncelleme yapılamadı:\n{str(e)}")

    def scan_file(self):
        import cv2
        import numpy as np 
        from pyzbar import pyzbar
        f, _ = QFileDialog.getOpenFileName(self, "Resim Seç", "", "Images (*.png *.jpg)")
        if f:
            img = cv2.imdecode(np.fromfile(f, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
            d = pyzbar.decode(img)
            if d: self.auto_process_scanned_qr(d[0].data.decode("utf-8") + '\n')

    def open_qr_gen(self): QRGeneratorDialog(self).exec_()
    
    def create_proj_db(self):
        name = self.p_name.text().strip()
        user = self.p_user.text().strip()
        delivered_to = self.p_delivered_to.text().strip() 
        phone = self.p_phone.text().strip()               
        email = self.p_email.text().strip()               
        desc = self.p_desc.text().strip()
        start = self.d_start.date().toString("yyyy-MM-dd")
        end = self.d_end.date().toString("yyyy-MM-dd")
        if not name:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen bir 'Proje Adı' giriniz.")
            return
        if not user:
            QMessageBox.warning(self, "Eksik Bilgi", "Lütfen 'Hazırlayan' kısmını doldurunuz.")
            return
        if email: self.settings.setValue("last_email", email)
        try:
            create_project(name, desc, start, end, user, delivered_to, phone, email)
            QMessageBox.information(self, "Başarılı", "Proje başarıyla oluşturuldu.")
            self.p_name.clear(); self.p_desc.clear(); self.p_user.clear()
            self.p_delivered_to.clear(); self.p_phone.clear()
            self.load_project_combo()
            self.pages.setCurrentIndex(3)
        except Exception as e: QMessageBox.critical(self, "Hata", str(e))

    def load_project_combo(self):
        self.p_combo.blockSignals(True)
        self.p_combo.clear()
        active_projects = get_active_projects()
        for pid, name in active_projects: self.p_combo.addItem(name, pid)
        if self.last_selected_project_id:
            index = self.p_combo.findData(self.last_selected_project_id)
            if index >= 0: self.p_combo.setCurrentIndex(index)
        self.p_combo.blockSignals(False)
        self.load_project_items()

    def load_project_items(self):
        pid = self.p_combo.currentData()
        if pid: self.last_selected_project_id = pid
        if not pid: 
            self.p_table.setRowCount(0)
            self.lbl_p_desc.setText("-"); self.lbl_p_user.setText("-"); self.lbl_p_date.setText("-")
            return
        d = get_project_details(pid)
        if d:
            desc = d[0] if d[0] else "-"
            s_date = d[1].strftime("%d.%m.%Y") if d[1] else "-"
            e_date = d[2].strftime("%d.%m.%Y") if d[2] else "-"
            prep = d[3] if d[3] else "-"
            self.lbl_p_desc.setText(desc); self.lbl_p_user.setText(prep)
            if s_date != "-" and e_date != "-": self.lbl_p_date.setText(f"{s_date} - {e_date}")
            else: self.lbl_p_date.setText("-")
        else: self.lbl_p_desc.setText("-"); self.lbl_p_user.setText("-"); self.lbl_p_date.setText("-")
        items = get_project_items(pid)
        self.p_table.setRowCount(len(items))
        for r, (qr, desc, qty) in enumerate(items):
            self.p_table.setItem(r, 0, QTableWidgetItem(qr))
            self.p_table.setItem(r, 1, QTableWidgetItem(desc))
            self.p_table.setItem(r, 2, QTableWidgetItem(str(qty)))
            
            btn_ret = QPushButton(" İade")
            btn_ret.setIcon(qta.icon('fa5s.undo', color='white')) 
            btn_ret.setObjectName("success_btn")
            btn_ret.clicked.connect(lambda _, row=r: self.ret_item(row))
            self.p_table.setCellWidget(r, 3, btn_ret)

            btn_faulty = QPushButton(" Arızalı")
            btn_faulty.setIcon(qta.icon('fa5s.tools', color='white'))
            btn_faulty.setObjectName("danger_btn")
            btn_faulty.clicked.connect(lambda _, row=r: self.return_faulty_item(row))
            self.p_table.setCellWidget(r, 4, btn_faulty)

    def ret_item(self, r):
        qr = self.p_table.item(r, 0).text()
        current_qty = int(self.p_table.item(r, 2).text()) 
        pid = self.p_combo.currentData()
        count, ok = QInputDialog.getInt(self, "İade İşlemi", f"Toplam {current_qty} adet var.\nKaç adet iade edilecek?", 1, 1, current_qty, 1)
        if ok:
            try:
                for _ in range(count): return_item_to_warehouse(pid, qr)
                self.load_project_items()
                QMessageBox.information(self, "Başarılı", f"{count} adet '{qr}' depoya iade alındı.")
            except Exception as e: QMessageBox.critical(self, "Hata", str(e))

    def return_faulty_item(self, r):
        qr = self.p_table.item(r, 0).text()
        pid = self.p_combo.currentData()
        fault_desc, ok = QInputDialog.getText(self, "Arıza Bildirimi", f"{qr} için arıza nedeni giriniz:")
        if ok and fault_desc:
            try:
                send_item_to_maintenance(pid, qr, fault_desc)
                self.load_project_items()
                QMessageBox.warning(self, "Bakım", "Ürün bakıma gönderildi.")
            except Exception as e: QMessageBox.critical(self, "Hata", str(e))

    def open_bulk(self, mode='assign'):
        pid = self.p_combo.currentData()
        if pid: BulkScanDialog(pid, self.p_combo.currentText(), mode, self).exec_(); self.load_project_items()

    def gen_pdf(self):
        pid = self.p_combo.currentData()
        if not pid: QMessageBox.warning(self, "Hata", "Lütfen önce bir proje seçin."); return
        f, _ = QFileDialog.getSaveFileName(self, "Zimmet Fişi Kaydet", "Zimmet_Fisi.pdf", "PDF (*.pdf)")
        if not f: return
        try:
            p_details = get_project_details(pid); items = get_project_items(pid)
            project_data = {'name': self.p_combo.currentText(), 'desc': p_details[0], 'start': p_details[1].strftime("%d.%m.%Y"), 'end': p_details[2].strftime("%d.%m.%Y"), 'prep': p_details[3], 'deliv': p_details[5], 'phone': p_details[6], 'email': p_details[7]}
            create_pdf_internal(f, project_data, items, is_history=False)
            QMessageBox.information(self, "Başarılı", "Zimmet fişi kaydedildi!")
        except Exception as e: QMessageBox.critical(self, "Hata", f"PDF hatası:\n{str(e)}")

    def gen_history_pdf(self):
        pid = self.history_combo.currentData()
        if not pid: return
        f, _ = QFileDialog.getSaveFileName(self, "Geçmiş Zimmet Fişi", "Gecmis_Fis.pdf", "PDF (*.pdf)")
        if not f: return
        try:
            p_details = get_project_details(pid); items = get_archived_items(pid)
            project_data = {'name': self.history_combo.currentText(), 'desc': p_details[0], 'start': p_details[1].strftime("%d.%m.%Y"), 'end': p_details[2].strftime("%d.%m.%Y"), 'prep': p_details[3], 'deliv': p_details[5], 'phone': p_details[6], 'email': p_details[7]}
            create_pdf_internal(f, project_data, items, is_history=True)
            QMessageBox.information(self, "Başarılı", "Geçmiş fiş kaydedildi!")
        except Exception as e: QMessageBox.critical(self, "Hata", str(e))

    def close_proj(self):
        pid = self.p_combo.currentData()
        if not pid: return
        items = get_project_items(pid)
        if len(items) > 0: QMessageBox.warning(self, "Kapatılamaz!", f"Bu projede hala {len(items)} adet teslim edilmemiş ürün var."); return
        if QMessageBox.question(self,"Onay","Proje SONLANDIRILSIN MI?\nBu işlem geri alınamaz ve otomatik mail gönderilecektir.") == QMessageBox.Yes:
            try: 
                QApplication.setOverrideCursor(Qt.WaitCursor)
                p_details = get_project_details(pid)
                email_to = p_details[7] if len(p_details)>7 else ""
                if email_to and "@" in email_to:
                    temp_pdf = os.path.join(os.getcwd(), f"Zimmet_{pid}_Final.pdf")
                    archived_items = get_archived_items(pid)
                    project_data = {'name': self.p_combo.currentText(), 'desc': p_details[0], 'start': p_details[1].strftime("%d.%m.%Y"), 'end': p_details[2].strftime("%d.%m.%Y"), 'prep': p_details[3], 'deliv': p_details[5], 'phone': p_details[6], 'email': email_to}
                    create_pdf_internal(temp_pdf, project_data, archived_items, is_history=True)
                    success, msg = send_email_with_pdf(email_to, f"Proje Sonlandı: {self.p_combo.currentText()}", "Merhaba,\n\nİlgili proje sonlandırılmıştır. Zimmet dökümü ektedir.\n\nİyi çalışmalar.", temp_pdf)
                    if success: QMessageBox.information(self, "Mail", f"Mail başarıyla gönderildi: {email_to}")
                    else: QMessageBox.warning(self, "Mail Hatası", f"Mail gönderilemedi: {msg}")
                    try: os.remove(temp_pdf)
                    except: pass
                close_project(pid); self.load_project_combo(); self.load_history_combo()
                QMessageBox.information(self, "Başarılı", "Proje başarıyla sonlandırıldı.")
            except Exception as e: QMessageBox.critical(self,"Hata",str(e))
            finally: QApplication.restoreOverrideCursor()

    def edit_active_project(self):
        pid = self.p_combo.currentData()
        if not pid: QMessageBox.warning(self, "Uyarı", "Lütfen düzenlemek için bir proje seçin."); return
        try:
            d = get_project_details(pid)
            if not d: return
            dialog = QDialog(self); dialog.setWindowTitle("Projeyi Düzenle"); dialog.setMinimumSize(400, 400)
            layout = QFormLayout(dialog)
            e_name = QLineEdit(self.p_combo.currentText())
            e_prep = QLineEdit(d[3] if d[3] else "")
            e_deliv = QLineEdit(d[5] if len(d)>5 and d[5] else "")
            e_phone = QLineEdit(d[6] if len(d)>6 and d[6] else "")
            e_email = QLineEdit(d[7] if len(d)>7 and d[7] else "")
            e_desc = QLineEdit(d[0] if d[0] else "")
            d_start = QDateEdit(); d_start.setCalendarPopup(True); d_start.setDate(d[1] if d[1] else QDate.currentDate())
            d_end = QDateEdit(); d_end.setCalendarPopup(True); d_end.setDate(d[2] if d[2] else QDate.currentDate())
            layout.addRow("Proje Adı:", e_name); layout.addRow("Hazırlayan:", e_prep); layout.addRow("Teslim Alan:", e_deliv); layout.addRow("Telefon:", e_phone); layout.addRow("Email:", e_email); layout.addRow("Başlangıç:", d_start); layout.addRow("Bitiş:", d_end); layout.addRow("Notlar:", e_desc)
            btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); btn_box.accepted.connect(dialog.accept); btn_box.rejected.connect(dialog.reject); layout.addRow(btn_box)
            if dialog.exec_():
                if not e_name.text().strip(): QMessageBox.warning(self, "Hata", "Proje adı boş olamaz."); return
                update_project_full(pid, e_name.text().strip(), e_desc.text().strip(), d_start.date().toString("yyyy-MM-dd"), d_end.date().toString("yyyy-MM-dd"), e_prep.text().strip(), e_deliv.text().strip(), e_phone.text().strip(), e_email.text().strip())
                self.load_project_combo(); QMessageBox.information(self, "Başarılı", "Proje bilgileri güncellendi.")
        except Exception as e: QMessageBox.critical(self, "Hata", str(e))

    def load_history_combo(self):
        self.history_combo.blockSignals(True); self.history_combo.clear()
        past_projects = get_past_projects()
        for proj in past_projects: self.history_combo.addItem(proj[1], proj[0])
        self.history_combo.blockSignals(False); self.load_history_details()

    def load_history_details(self):
        if self.history_combo.currentIndex() == -1: self.history_table.setRowCount(0); self.lbl_h_user.setText("-"); self.lbl_h_date.setText("-"); self.lbl_h_desc.setText("-"); return
        pid = self.history_combo.currentData(); d = get_project_details(pid)
        if d:
            self.lbl_h_desc.setText(d[0] if d[0] else "-"); self.lbl_h_user.setText(d[3] if d[3] else "-")
            self.lbl_h_date.setText(f"{d[1].strftime('%d.%m.%Y')} - {d[2].strftime('%d.%m.%Y')}" if d[1] and d[2] else "-")
        else: self.lbl_h_user.setText("-"); self.lbl_h_date.setText("-"); self.lbl_h_desc.setText("-")
        items = get_archived_items(pid); self.history_table.setRowCount(len(items))
        for r, (qr, desc, cat, add, ret, qty) in enumerate(items):
            self.history_table.setItem(r,0,QTableWidgetItem(qr)); self.history_table.setItem(r,1,QTableWidgetItem(cat))
            self.history_table.setItem(r,2,QTableWidgetItem(desc)); self.history_table.setItem(r,3,QTableWidgetItem(str(qty)))
            self.history_table.setItem(r,4,QTableWidgetItem(add.strftime("%d.%m.%Y %H:%M") if add else "-")); self.history_table.setItem(r,5,QTableWidgetItem(ret.strftime("%d.%m.%Y %H:%M") if ret else "-"))

def global_exception_handler(exctype, value, traceback_obj):
    import traceback; error_msg = "".join(traceback.format_exception(exctype, value, traceback_obj))
    msg = QMessageBox(); msg.setIcon(QMessageBox.Critical); msg.setWindowTitle("Beklenmeyen Hata"); msg.setText("Bir hata oluştu:"); msg.setInformativeText(str(value)); msg.setDetailedText(error_msg); msg.exec_()

if __name__ == "__main__":
    sys.excepthook = global_exception_handler
    import ctypes
    myappid = 'mycompany.eventory.vFinal' 
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app = QApplication(sys.argv)
    window = InventoryApp()
    window.show()
    sys.exit(app.exec_())