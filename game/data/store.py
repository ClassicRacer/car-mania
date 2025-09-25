import sqlite3, pathlib, json, time

def open_db(path):
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_schema(conn):
    conn.executescript(open(pathlib.Path(__file__).with_name("schema.sql")).read())
    conn.commit()

def upsert_profile(conn, name):
    cur = conn.execute("INSERT INTO profiles(name) VALUES(?) ON CONFLICT(name) DO UPDATE SET name=excluded.name RETURNING id", (name,))
    return cur.fetchone()[0]

def add_car(conn, profile_id, name, image_path, props):
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        "INSERT INTO cars(profile_id,name,image_path,engine_type,top_speed,acceleration,handling,offroad,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
        (profile_id,name,image_path,props["engine_type"],props["top_speed"],props["acceleration"],props["handling"],props["offroad"],now,now)
    )
    conn.commit()
    return cur.lastrowid

def get_cars(conn, profile_id):
    cur = conn.execute("SELECT id,name,image_path,engine_type,top_speed,acceleration,handling,offroad FROM cars WHERE profile_id=?", (profile_id,))
    return cur.fetchall()

def add_level(conn, profile_id, meta, music_path):
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    cur = conn.execute(
        "INSERT INTO levels(profile_id,name,laps,kind,angle,color_r,color_g,color_b,music_path,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (profile_id,meta["name"],meta["laps"],meta["kind"],meta["angle"],meta["color"][0],meta["color"][1],meta["color"][2],music_path,now,now)
    )
    conn.commit()
    return cur.lastrowid

def set_level_pieces(conn, level_id, pieces):
    conn.execute("DELETE FROM level_pieces WHERE level_id=?", (level_id,))
    conn.executemany(
        "INSERT INTO level_pieces(level_id,ord,piece_type,rot,x,y,extra) VALUES(?,?,?,?,?,?,?)",
        [(level_id,i,p["type"],p["rot"],p["x"],p["y"],json.dumps(p.get("extra"))) for i,p in enumerate(pieces)]
    )
    conn.commit()

def load_level(conn, level_id):
    cur = conn.execute("SELECT name,laps,kind,angle,color_r,color_g,color_b,music_path FROM levels WHERE id=?", (level_id,))
    row = cur.fetchone()
    pcs = conn.execute("SELECT ord,piece_type,rot,x,y,extra FROM level_pieces WHERE level_id=? ORDER BY ord", (level_id,)).fetchall()
    pieces = [{"type":t,"rot":r,"x":x,"y":y,"extra":json.loads(e) if e else None} for _,t,r,x,y,e in pcs]
    meta = {"name":row[0],"laps":row[1],"kind":row[2],"angle":row[3],"color":[row[4],row[5],row[6]],"music_path":row[7]}
    return meta,pieces