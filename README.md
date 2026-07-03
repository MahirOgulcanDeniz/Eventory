# 📦 Eventory - Inventory and Entrustment Management System

Eventory is an Inventory Management System developed using Python and PostgreSQL. Follow the steps below to set up and run the project on a clean machine.

---

## 1. Prerequisites

Download and install the following software from their official websites:

1. **Python (3.10 or higher):**
   * Download Link: `https://www.python.org/downloads/`
   * **⚠️ IMPORTANT:** Ensure you check the **"Add Python to PATH"** checkbox during installation.

2. **PostgreSQL (Database):**
   * Download Link: `https://www.postgresql.org/download/windows/`
   * Remember the password set during installation (default in the code is set to `12345`; if you configure a different password, update the `DB_PASS` variable accordingly).

3. **ZBar DLL File (For Barcode/QR Scanning):**
   * Download `libzbar-64.dll` from the internet (or copy it from the existing project files).
   * Place this file in the root directory where `app.py` and `inventory.py` are located.

---

## 2. Database Setup (SQL)

1. Open **pgAdmin 4** on your machine.
2. Right-click on `Databases` and select **Create > Database**.
3. Name the database `inventory_db` and save it.
4. Right-click on the newly created `inventory_db` and open the **Query Tool**.
5. Copy and paste the entire SQL script below into the query tool and click the **Execute (Play/▶)** button:

```sql
-- 1. Inventory Stock Table
CREATE TABLE items (
    qr_code VARCHAR(255) PRIMARY KEY,
    description TEXT,
    category VARCHAR(100),
    quantity INTEGER DEFAULT 1,
    entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Projects Table
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    start_date DATE,
    end_date DATE,
    prepared_by VARCHAR(255),
    status VARCHAR(50) DEFAULT 'Active',
    delivered_to VARCHAR(255),
    phone_number VARCHAR(50),
    email VARCHAR(255)
);

-- 3. Items Assigned to Projects
CREATE TABLE project_items (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    qr_code VARCHAR(255),
    description TEXT,
    assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. History / Archive Table
CREATE TABLE archived_items (
    id SERIAL PRIMARY KEY,
    project_id INTEGER,
    qr_code VARCHAR(255),
    description TEXT,
    category VARCHAR(100),
    added_date TIMESTAMP,
    returned_date TIMESTAMP
);

-- 5. Maintenance and Malfunction Table
CREATE TABLE maintenance_items (
    id SERIAL PRIMARY KEY,
    qr_code VARCHAR(255),
    description TEXT,
    category VARCHAR(100),
    fault_description TEXT,
    project_source VARCHAR(255),
    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
3. Installation & Dependencies
Install the required Python libraries to run the application.

Navigate to the project root directory, hold Shift + Right Click, and open PowerShell or Terminal.

Run the following command:


pip install PyQt5 qtawesome matplotlib reportlab qrcode[pil] opencv-python pyzbar psycopg2
(Note: If you encounter an error installing psycopg2, try installing pip install psycopg2-binary instead.)

4. Running the Application
Once the configuration is complete, start the application using the following command:


python app.py
5. Building an Executable (Optional)
To generate a standalone .exe file for machines without Python installed:

Install PyInstaller:


pip install pyinstaller
Execute the following build command (Ensure your icon file is placed at icons/app_icon.ico):


python -m PyInstaller --noconsole --onedir --name="Eventory" --icon="icons/app_icon.ico" --add-data "icons;icons" --add-binary "libzbar-64.dll;." --hidden-import=cv2 --hidden-import=qrcode --hidden-import=psycopg2 --hidden-import=reportlab.platypus --hidden-import=reportlab.pdfbase --collect-all opencv_python --collect-all qtawesome app.py
Once complete, you can find the executable inside the dist/Eventory directory.

⚠️ Configuration Note: Do not forget to update the SENDER_EMAIL and SENDER_PASSWORD fields in app.py with your Gmail address and Google App Password to enable email functionality.