import sqlite3

def initialize_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS beats
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, link TEXT, wav_link TEXT, trackout_link TEXT,
                      wav_payment_id TEXT, trackout_payment_id TEXT, exclusive_payment_id TEXT)''')
    conn.commit()
    conn.close()

def migrate_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Добавим недостающие столбцы, если они отсутствуют
    cursor.execute("PRAGMA table_info(beats)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'wav_payment_id' not in columns:
        cursor.execute("ALTER TABLE beats ADD COLUMN wav_payment_id TEXT")
    if 'trackout_payment_id' not in columns:
        cursor.execute("ALTER TABLE beats ADD COLUMN trackout_payment_id TEXT")
    if 'exclusive_payment_id' not in columns:
        cursor.execute("ALTER TABLE beats ADD COLUMN exclusive_payment_id TEXT")
    conn.commit()
    conn.close()

def add_beat(name, link, wav_link, trackout_link):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO beats (name, link, wav_link, trackout_link) VALUES (?, ?, ?, ?)",
                   (name, link, wav_link, trackout_link))
    conn.commit()
    conn.close()

def get_all_beats():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM beats")
    beats = cursor.fetchall()
    conn.close()
    return beats

def find_beat_by_link(link_or_name):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM beats WHERE link LIKE ? OR name LIKE ?", (f'%{link_or_name}%', f'%{link_or_name}%'))
    beat = cursor.fetchone()
    conn.close()
    return beat

def get_beat_by_id(beat_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM beats WHERE id=?", (beat_id,))
    beat = cursor.fetchone()
    conn.close()
    return beat

def delete_beat_by_id(beat_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM beats WHERE id=?", (beat_id,))
    conn.commit()
    conn.close()

def update_payment_ids(beat_id, wav_payment_id, trackout_payment_id, exclusive_payment_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE beats SET wav_payment_id=?, trackout_payment_id=?, exclusive_payment_id=? WHERE id=?",
                   (wav_payment_id, trackout_payment_id, exclusive_payment_id, beat_id))
    conn.commit()
    conn.close()

def get_last_transactions():
    # Имитация получения последних транзакций
    return [
        (1, 'User1', 'Beat1', 'Wav', 1, '2025-03-19'),
        (2, 'User2', 'Beat2', 'Trackout', 1, '2025-03-19')
    ]