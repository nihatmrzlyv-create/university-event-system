import sqlite3

def init_db():
    conn = sqlite3.connect('university_events.db')
    cursor = conn.cursor()
    
    # Kateqoriyalar cədvəli
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # İstifadəçilər cədvəli
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Tədbirlər cədvəli
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            category_id INTEGER,
            event_date TEXT NOT NULL,
            location TEXT NOT NULL,
            max_capacity INTEGER NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories (id)
        )
    ''')
    
    # Qeydiyyatlar cədvəli (Unikal məhdudiyyət ilə - təkrar qeydiyyatın qarşısını alır)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            event_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (event_id) REFERENCES events (id),
            UNIQUE(user_id, event_id)
        )
    ''')
    
    # İlkin kateqoriyalar əlavə edək (əgər yoxdursa)
    categories = ['Konfrans', 'Seminar', 'Təlim', 'Müsabiqə']
    for cat in categories:
        cursor.execute('INSERT OR IGNORE INTO categories (name) VALUES (?)', (cat,))
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Verilənlər bazası uğurla yaradıldı!")