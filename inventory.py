import psycopg2
import json
import csv
from datetime import datetime, timedelta

# =========================================================
#  VERİTABANI AYARLARI
# =========================================================
DB_HOST = "localhost"
DB_NAME = "inventory_db" 
DB_USER = "postgres"
DB_PASS = "your_password_here" 

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        return conn
    except Exception as e:
        raise Exception(f"Veritabanı Bağlantı Hatası:\n{str(e)}")

# =========================================================
#  1. DEPO İŞLEMLERİ
# =========================================================

def add_item(qr_code, description, category, quantity):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT quantity FROM items WHERE qr_code = %s", (qr_code,))
        res = cur.fetchone()
        if res:
            new_qty = res[0] + quantity
            cur.execute("UPDATE items SET quantity = %s, description = %s, category = %s WHERE qr_code = %s",
                        (new_qty, description, category, qr_code))
        else:
            cur.execute("INSERT INTO items (qr_code, description, category, quantity) VALUES (%s, %s, %s, %s)",
                        (qr_code, description, category, quantity))
        conn.commit()
    except Exception as e:
        conn.rollback(); raise e
    finally:
        conn.close()

def get_all_items():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT qr_code, description, quantity, category FROM items ORDER BY entry_date DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def check_item_exists(qr_code):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM items WHERE qr_code = %s", (qr_code,))
    exists = cur.fetchone() is not None
    conn.close()
    return exists

def delete_item_from_warehouse(qr_code):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM items WHERE qr_code = %s", (qr_code,))
    conn.commit()
    conn.close()

def update_item_details(qr_code, new_desc, new_cat, new_qty):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE items SET description = %s, category = %s, quantity = %s WHERE qr_code = %s", 
                    (new_desc, new_cat, new_qty, qr_code))
        conn.commit()
    except Exception as e:
        conn.rollback(); raise e
    finally:
        conn.close()

# =========================================================
#  2. PROJE İŞLEMLERİ
# =========================================================

def create_project(name, description, start_date, end_date, prepared_by, delivered_to, phone_number, email):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO projects (name, description, start_date, end_date, prepared_by, delivered_to, phone_number, email)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (name, description, start_date, end_date, prepared_by, delivered_to, phone_number, email))
    conn.commit()
    conn.close()

def update_project_full(project_id, name, description, start_date, end_date, prepared_by, delivered_to, phone_number, email):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE projects 
            SET name=%s, description=%s, start_date=%s, end_date=%s, prepared_by=%s, delivered_to=%s, phone_number=%s, email=%s
            WHERE id=%s
        """, (name, description, start_date, end_date, prepared_by, delivered_to, phone_number, email, project_id))
        conn.commit()
    except Exception as e:
        conn.rollback(); raise e
    finally:
        conn.close()

def get_active_projects():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM projects WHERE status = 'Active' ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_project_details(project_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT description, start_date, end_date, prepared_by, status, delivered_to, phone_number, email FROM projects WHERE id = %s", (project_id,))
    row = cur.fetchone()
    conn.close()
    return row

def close_project(project_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE projects SET status = 'Closed' WHERE id = %s", (project_id,))
    conn.commit()
    conn.close()

def get_past_projects():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM projects WHERE status = 'Closed' ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_all_projects_for_calendar():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, start_date, end_date, status FROM projects")
    rows = cur.fetchall()
    conn.close()
    return rows

# =========================================================
#  3. TRANSFER İŞLEMLERİ
# =========================================================

def get_item_project_info(qr_code):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.name 
        FROM project_items pi
        JOIN projects p ON pi.project_id = p.id
        WHERE pi.qr_code = %s AND p.status = 'Active'
    """, (qr_code,))
    row = cur.fetchone()
    conn.close()
    return row

def assign_item_to_project(project_id, qr_code, count=1):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT description, category, quantity FROM items WHERE qr_code = %s", (qr_code,))
        res = cur.fetchone()
        if not res: raise Exception(f"Depoda ürün yok: {qr_code}")
        desc, cat, qty = res
        if qty < count: raise Exception(f"Yetersiz stok! Mevcut: {qty}")

        if qty > count:
            cur.execute("UPDATE items SET quantity = quantity - %s WHERE qr_code = %s", (count, qr_code))
        else:
            cur.execute("DELETE FROM items WHERE qr_code = %s", (qr_code,))

        for _ in range(count):
            cur.execute("INSERT INTO project_items (project_id, qr_code, description) VALUES (%s, %s, %s)", (project_id, qr_code, desc))
        conn.commit()
    except Exception as e:
        conn.rollback(); raise e
    finally:
        conn.close()

def get_project_items(project_id):
    """
    GÜNCELLENDİ: Artık ürünleri tek tek değil, QR Koduna göre gruplayıp
    ADET sayısıyla birlikte getiriyor.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT qr_code, description, COUNT(*) as quantity 
        FROM project_items 
        WHERE project_id = %s 
        GROUP BY qr_code, description 
        ORDER BY description ASC
    """, (project_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def return_item_to_warehouse(project_id, qr_code):
    """
    Bu fonksiyon tek bir ürünü iade alır.
    Toplu iade için bu fonksiyon döngü içinde çağrılır.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # LIMIT 1 ile gruptan sadece bir tanesini yakalıyoruz
        cur.execute("SELECT ctid, description FROM project_items WHERE project_id = %s AND qr_code = %s LIMIT 1", (project_id, qr_code))
        res = cur.fetchone()
        if not res: raise Exception("Ürün bulunamadı.")
        row_id, desc = res

        cur.execute("DELETE FROM project_items WHERE ctid = %s", (row_id,))
        cur.execute("SELECT quantity FROM items WHERE qr_code = %s", (qr_code,))
        if cur.fetchone():
            cur.execute("UPDATE items SET quantity = quantity + 1 WHERE qr_code = %s", (qr_code,))
        else:
            cur.execute("INSERT INTO items (qr_code, description, category, quantity) VALUES (%s, %s, %s, %s)", (qr_code, desc, "Diğer", 1))
        
        cur.execute("INSERT INTO archived_items (project_id, qr_code, description, category, added_date, returned_date) VALUES (%s, %s, %s, %s, NOW(), NOW())", (project_id, qr_code, desc, "Diğer"))
        conn.commit()
    except Exception as e:
        conn.rollback(); raise e
    finally:
        conn.close()

def get_archived_items(project_id):
    """Arşivlenmiş (iade edilmiş) ürünleri de gruplayarak getirir."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT qr_code, description, category, MIN(added_date), MAX(returned_date), COUNT(*) as quantity
        FROM archived_items 
        WHERE project_id = %s 
        GROUP BY qr_code, description, category
        ORDER BY MAX(returned_date) DESC
    """, (project_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

# =========================================================
#  4. BAKIM / ARIZA İŞLEMLERİ
# =========================================================

def send_item_to_maintenance(project_id, qr_code, fault_desc):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT ctid, description FROM project_items WHERE project_id = %s AND qr_code = %s LIMIT 1", (project_id, qr_code))
        res = cur.fetchone()
        if not res: raise Exception("Ürün projede bulunamadı.")
        row_id, desc = res
        
        cur.execute("SELECT name FROM projects WHERE id = %s", (project_id,))
        p_name = cur.fetchone()[0]

        cur.execute("DELETE FROM project_items WHERE ctid = %s", (row_id,))
        cur.execute("INSERT INTO maintenance_items (qr_code, description, category, fault_description, project_source) VALUES (%s, %s, %s, %s, %s)",
                    (qr_code, desc, "Diğer", fault_desc, p_name))
        
        conn.commit()
    except Exception as e:
        conn.rollback(); raise e
    finally:
        conn.close()

def get_maintenance_items():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, qr_code, description, fault_description, project_source, date_added FROM maintenance_items ORDER BY date_added DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def repair_item_return_to_stock(maintenance_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT qr_code, description, category FROM maintenance_items WHERE id = %s", (maintenance_id,))
        res = cur.fetchone()
        if not res: raise Exception("Bakım kaydı bulunamadı.")
        qr, desc, cat = res

        cur.execute("DELETE FROM maintenance_items WHERE id = %s", (maintenance_id,))
        cur.execute("SELECT quantity FROM items WHERE qr_code = %s", (qr,))
        if cur.fetchone():
            cur.execute("UPDATE items SET quantity = quantity + 1 WHERE qr_code = %s", (qr,))
        else:
            cur.execute("INSERT INTO items (qr_code, description, category, quantity) VALUES (%s, %s, %s, %s)", (qr, desc, cat, 1))
        
        conn.commit()
    except Exception as e:
        conn.rollback(); raise e
    finally:
        conn.close()

def delete_maintenance_item_permanently(maintenance_id):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM maintenance_items WHERE id = %s", (maintenance_id,))
        conn.commit()
    except Exception as e:
        conn.rollback(); raise e
    finally:
        conn.close()

# =========================================================
#  5. YEDEKLEME (BACKUP)
# =========================================================
def backup_database(folder_path):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        tables = ['items', 'projects', 'project_items', 'maintenance_items', 'archived_items']
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        
        for table in tables:
            cur.execute(f"SELECT * FROM {table}")
            rows = cur.fetchall()
            colnames = [desc[0] for desc in cur.description]
            
            filename = f"{folder_path}/{table}_{timestamp}.csv"
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(colnames)
                writer.writerows(rows)
                
        return True, f"Yedekleme başarılı: {folder_path}"
    except Exception as e:
        return False, str(e)
    finally:
        conn.close()

# =========================================================
#  6. DASHBOARD (GÜNCELLENDİ: SUM KULLANIYOR)
# =========================================================

def get_dashboard_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    # Depodaki TOPLAM ÜRÜN ADEDİ (Adetlerin toplamı)
    cur.execute("SELECT SUM(quantity) FROM items")
    total = cur.fetchone()[0] or 0
    
    # Projedeki TOPLAM ÜRÜN ADEDİ (Satır sayısı, çünkü proje tablosunda tek tek tutuluyor)
    cur.execute("SELECT COUNT(*) FROM project_items")
    in_proj = cur.fetchone()[0] or 0
    
    cur.execute("SELECT COUNT(*) FROM projects WHERE status = 'Active'")
    active = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(*) FROM maintenance_items")
    maint = cur.fetchone()[0] or 0
    conn.close()
    return total, in_proj, active, maint

def get_category_stats():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT category, SUM(quantity) FROM items GROUP BY category")
    rows = cur.fetchall()
    conn.close()
    return rows