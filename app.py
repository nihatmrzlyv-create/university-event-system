import streamlit as st
import sqlite3
from datetime import datetime

# Bazadan məlumatları oxumaq üçün köməkçi funksiyalar
def get_connection():
    return sqlite3.connect('university_events.db')

st.set_page_config(page_title="Universitet Tədbirləri Sistemi", page_icon="🎓", layout="wide")

st.title("🎓 Universitet Tədbirlərinin İdarə Edilməsi və Qeydiyyat Sistemi")

# Menyunu sidebar-da yaradaq
menu = st.sidebar.selectbox("Menyu", ["Tədbirlər və Qeydiyyat", "Yeni Tədbir Yarat (Admin)", "Statistika"])

# 1. TƏDBİRLƏR VƏ QEYDİYYAT
if menu == "Tədbirlər və Qeydiyyat":
    st.header("📅 Mövcud Tədbirlər")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Kateqoriyaları çəkək
    cursor.execute("SELECT id, name FROM categories")
    categories = cursor.fetchall()
    cat_dict = {cat[1]: cat[0] for cat in categories}
    
    # Axtarış və Filtrlər
    col1, col2 = st.columns(2)
    with col1:
        search_query = st.text_input("🔍 Tədbir adına görə axtarış:")
    with col2:
        selected_cat = st.selectbox("📂 Kateqoriya seçin:", ["Hamısı"] + list(cat_dict.keys()))
        
    # SQL sorğusunu quraq
    query = """
        SELECT e.id, e.title, e.description, c.name, e.event_date, e.location, e.max_capacity 
        FROM events e 
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE 1=1
    """
    params = []
    
    if search_query:
        query += " AND e.title LIKE ?"
        params.append(f"%{search_query}%")
        
    if selected_cat != "Hamısı":
        query += " AND c.name = ?"
        params.append(selected_cat)
        
    cursor.execute(query, params)
    events = cursor.fetchall()
    
    if not events:
        st.warning("⚠️ Axtarışınıza uyğun tədbir tapılmadı.")
    else:
        for event in events:
            ev_id, title, desc, cat_name, ev_date, location, max_cap = event
            
            # Cari qeydiyyat sayını hesablayaq
            cursor.execute("SELECT COUNT(*) FROM registrations WHERE event_id = ?", (ev_id,))
            reg_count = cursor.fetchone()[0]
            
            # Keçmiş və gələcək tədbirin yoxlanılması
            current_date = datetime.now().strftime("%Y-%m-%d")
            is_past = ev_date < current_date
            
            with st.expander(f"{'🔴 [Keçmiş]' if is_past else '🟢'} {title} ({ev_date}) - {cat_name}"):
                st.write(f"**Təsvir:** {desc}")
                st.write(f"**Məkan:** {location}")
                st.write(f"👥 **Qeydiyyatlar:** {reg_count} / {max_cap} yer")
                
                if not is_past:
                    st.subheader("Qeydiyyatdan keç")
                    with st.form(f"reg_form_{ev_id}"):
                        user_name = st.text_input("Ad Soyad", key=f"name_{ev_id}")
                        user_email = st.text_input("Email", key=f"email_{ev_id}")
                        submit_reg = st.form_submit_button("Təsdiq et")
                        
                        if submit_reg:
                            if not user_name or not user_email:
                                st.error("Zəhmət olmasa bütün sahələri doldurun!")
                            else:
                                try:
                                    # İstifadəçini yoxlayaq və ya əlavə edək
                                    cursor.execute("SELECT id FROM users WHERE email = ?", (user_email,))
                                    user = cursor.fetchone()
                                    if user:
                                        user_id = user[0]
                                    else:
                                        cursor.execute("INSERT INTO users (full_name, email) VALUES (?, ?)", (user_name, user_email))
                                        conn.commit()
                                        user_id = cursor.lastrowid
                                        
                                    # Limiti yoxlayaq
                                    if reg_count >= max_cap:
                                        st.error("Tədbirin iştirakçı limiti dolub!")
                                    else:
                                        # Qeydiyyat əlavə et (UNIQUE constraint təkrar qeydiyyatı əngəlləyir)
                                        cursor.execute("INSERT INTO registrations (user_id, event_id) VALUES (?, ?)", (user_id, ev_id))
                                        conn.commit()
                                        st.success("🎉 Tədbirə uğurla qeydiyyatdan keçdiniz!")
                                        st.rerun()
                                except sqlite3.IntegrityError:
                                    st.error("⚠️ Siz artıq bu tədbirə qeydiyyatdan keçmisiniz!")
                else:
                    st.info("Bu tədbir artıq baş tutub.")
                    
    conn.close()

# 2. YENİ TƏDBİR YARATMAK (ADMIN)
elif menu == "Yeni Tədbir Yarat (Admin)":
    st.header("🛠 Yeni Tədbir Əlavə Et")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM categories")
    categories = cursor.fetchall()
    cat_dict = {cat[1]: cat[0] for cat in categories}
    
    with st.form("new_event_form"):
        title = st.text_input("Tədbirin Adı")
        description = st.text_area("Tədbir Haqqında Təsvir")
        category_name = st.selectbox("Kateqoriya", list(cat_dict.keys()))
        event_date = st.date_input("Tədbir Tarixi")
        location = st.text_input("Keçirilmə Yeri")
        max_capacity = st.number_input("Maksimum İştirakçı Sayı", min_value=1, value=20)
        
        submitted = st.form_submit_button("Tədbiri Yarat")
        
        if submitted:
            if not title or not location:
                st.error("Məcburi sahələri doldurun!")
            elif str(event_date) < datetime.now().strftime("%Y-%m-%d"):
                st.error("Tədbir tarixi keçmiş tarix ola bilməz!")
            else:
                cat_id = cat_dict[category_name]
                cursor.execute("""
                    INSERT INTO events (title, description, category_id, event_date, location, max_capacity)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, description, cat_id, str(event_date), location, max_capacity))
                conn.commit()
                st.success("✅ Tədbir uğurla yaradıldı!")
    conn.close()

# 3. STATİSTİKA
elif menu == "Statistika":
    st.header("📊 Sistem Statistikası")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM registrations")
    total_regs = cursor.fetchone()[0]
    
    col1, col2 = st.columns(2)
    col1.metric("Ümumi Tədbir Sayı", total_events)
    col2.metric("Ümumi Qeydiyyat Sayı", total_regs)
    
    st.subheader("🏆 Ən çox qeydiyyat olan tədbirlər")
    cursor.execute("""
        sub_query = e.title, COUNT(r.id) as reg_count 
        FROM events e 
        LEFT JOIN registrations r ON e.id = r.event_id 
        GROUP BY e.id 
        ORDER BY reg_count DESC LIMIT 3
    """)
    # Üstteki sorguyu düzəldək
    cursor.execute("""
        SELECT e.title, COUNT(r.id) as reg_count 
        FROM events e 
        LEFT JOIN registrations r ON e.id = r.event_id 
        GROUP BY e.id 
        ORDER BY reg_count DESC LIMIT 3
    """)
    top_events = cursor.fetchall()
    for ev in top_events:
        st.write(- f"**{ev[0]}** - {ev[1]} iştirakçı")
        
    conn.close()