import argparse, os, sqlite3, shutil, datetime, re, sys
from pathlib import Path

def slugify(s):
    s = s.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s or "level"

def ensure_dirs(p):
    Path(p).parent.mkdir(parents=True, exist_ok=True)

def now_iso():
    return datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"

def ensure_schema(conn):
    conn.execute("""CREATE TABLE IF NOT EXISTS profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS levels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        code TEXT NOT NULL,
        ground_r INTEGER NOT NULL,
        ground_g INTEGER NOT NULL,
        ground_b INTEGER NOT NULL,
        laps INTEGER NOT NULL,
        music_path TEXT,
        display_order INTEGER,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        UNIQUE(profile_id, display_order),
        FOREIGN KEY(profile_id) REFERENCES profiles(id) ON DELETE CASCADE
    )""")
    conn.commit()

def get_or_create_default_profile(conn):
    cur = conn.execute("SELECT id FROM profiles WHERE name=?", ("Default",))
    row = cur.fetchone()
    if row:
        return row[0]
    ts = now_iso()
    cur = conn.execute("INSERT INTO profiles(name, created_at) VALUES(?,?)", ("Default", ts))
    conn.commit()
    return cur.lastrowid

def read_level_code(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    parts = {"name": None, "ground": None, "laps": None, "code": []}
    for line in lines:
        if not line.strip():
            continue
        toks = [t.strip() for t in line.split(",")]
        if toks[0] == "name" and len(toks) >= 2:
            parts["name"] = ",".join(toks[1:]).strip()
        elif toks[0] == "ground" and len(toks) >= 4:
            try:
                parts["ground"] = (int(toks[1]), int(toks[2]), int(toks[3]))
            except:
                parts["ground"] = (64,201,62)
        elif toks[0] == "laps" and len(toks) >= 2:
            try:
                parts["laps"] = int(toks[1])
            except:
                parts["laps"] = 1
        else:
            parts["code"].append(line)
    if parts["name"] is None:
        parts["name"] = "Level"
    if parts["ground"] is None:
        parts["ground"] = (64,201,62)
    if parts["laps"] is None:
        parts["laps"] = 1
    parts["code"] = "\n".join(parts["code"])
    return parts

def upsert_level(conn, profile_id, display_order, name, code, ground, laps):
    ts = now_iso()
    cur = conn.execute("SELECT id FROM levels WHERE profile_id=? AND display_order=?", (profile_id, display_order))
    row = cur.fetchone()
    if row:
        conn.execute(
            """UPDATE levels SET name=?, code=?, ground_r=?, ground_g=?, ground_b=?, laps=?, updated_at=? WHERE id=?""",
            (name, code, ground[0], ground[1], ground[2], laps, ts, row[0]),
        )
        conn.commit()
        return row[0]
    cur = conn.execute(
        """INSERT INTO levels(profile_id, name, code, ground_r, ground_g, ground_b, laps, display_order, music_path, created_at, updated_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (profile_id, name, code, ground[0], ground[1], ground[2], laps, display_order, None, ts, ts),
    )
    conn.commit()
    return cur.lastrowid

def set_level_music(conn, level_id, music_path):
    conn.execute("UPDATE levels SET music_path=?, updated_at=? WHERE id=?", (music_path, now_iso(), level_id))
    conn.commit()

def migrate(args):
    project = Path(args.project_root).resolve()
    db_path = project / args.db
    code_dir = project / "UserData" / "Default" / "Levels" / "Code"
    music_dir = project / "UserData" / "Default" / "Levels" / "Music"
    out_assets = project / "assets" / "levels"
    if not code_dir.exists():
        print(f"Missing code dir: {code_dir}", file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    try:
        ensure_schema(conn)
        profile_id = get_or_create_default_profile(conn)
        code_files = sorted([p for p in code_dir.iterdir() if p.is_file() and p.suffix.lower() == ".txt"], key=lambda p: int(p.stem) if p.stem.isdigit() else p.stem)
        for cf in code_files:
            order = int(cf.stem) if cf.stem.isdigit() else None
            if order is None:
                continue
            meta = read_level_code(cf)
            name = meta["name"] if meta["name"] != "Level" else f"Level {order}"
            lvl_id = upsert_level(conn, profile_id, order, name, meta["code"], meta["ground"], meta["laps"])
            slug = f"{lvl_id}_{slugify(name)}"
            src_music = music_dir / f"{order}.wav"
            music_rel = None
            if src_music.exists():
                dest_dir = out_assets / slug
                dest_file = dest_dir / "music.wav"
                ensure_dirs(dest_file)
                shutil.copy2(src_music, dest_file)
                music_rel = str(dest_file.relative_to(project))
            set_level_music(conn, lvl_id, music_rel)
            print(f"Migrated level {order}: id={lvl_id}, name='{name}', music={'ok' if music_rel else 'none'}")
    finally:
        conn.close()

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--db", default="data/carmania.db")
    return ap.parse_args()

if __name__ == "__main__":
    migrate(parse_args())