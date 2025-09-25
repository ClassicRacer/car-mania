import argparse, sqlite3, pathlib, pickle, shutil, hashlib, time, sys
try:
    from PIL import Image
except Exception:
    Image = None

def slug(s):
    import re
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "item"

def checksum(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()

def ensure_profile(conn, name):
    cur = conn.execute("INSERT INTO profiles(name) VALUES(?) ON CONFLICT(name) DO NOTHING", (name,))
    conn.commit()
    cur = conn.execute("SELECT id FROM profiles WHERE name=?", (name,))
    r = cur.fetchone()
    if not r:
        raise SystemExit("profiles table not found or insert failed")
    return r[0]

def insert_car(conn, profile_id, name, stats):
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    cols = [c[1] for c in conn.execute("PRAGMA table_info(cars)")]
    col_image = "image_path" if "image_path" in cols else "image_relpath"

    base_cols = ["profile_id","name",col_image,"top_speed","acceleration","handling","offroad","engine_type"]
    vals = [profile_id, name, "", float(stats[0]), float(stats[1]), float(stats[2]), float(stats[3]), int(stats[4])]

    ph = ",".join("?" for _ in base_cols)
    sql = f"INSERT INTO cars({','.join(base_cols)}) VALUES({ph})"
    conn.execute(sql, vals)
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]

def update_car_image(conn, car_id, relpath, size_bytes=None, sha=None):
    cols = [c[1] for c in conn.execute("PRAGMA table_info(cars)")]
    col_image = "image_path" if "image_path" in cols else "image_relpath"
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    if all(k in cols for k in (col_image,"updated_at")):
        sets = f"{col_image}=?, updated_at=?"
        params = [relpath, now]
        if "image_size_bytes" in cols:
            sets += ", image_size_bytes=?"
            params.append(size_bytes)
        if "image_checksum" in cols:
            sets += ", image_checksum=?"
            params.append(sha)
        params.append(car_id)
        conn.execute(f"UPDATE cars SET {sets} WHERE id=?", params)
    else:
        conn.execute(f"UPDATE cars SET {col_image}=? WHERE id=?", (relpath, car_id))
    conn.commit()

def load_stats(data_bin_path):
    with open(data_bin_path, "rb") as f:
        obj = pickle.load(f)
    if isinstance(obj, (list, tuple)) and len(obj) >= 5:
        return [obj[0], obj[1], obj[2], obj[3], obj[4]]
    raise SystemExit(f"unsupported data.bin format: {data_bin_path}")

def ensure_dir(p):
    p.parent.mkdir(parents=True, exist_ok=True)

def copy_or_convert(src, dst_png):
    src = pathlib.Path(src)
    dst_png = pathlib.Path(dst_png)
    ensure_dir(dst_png)
    ext = src.suffix.lower()
    if ext == ".png":
        shutil.copy2(src, dst_png)
    elif ext in (".jpg",".jpeg") and Image:
        img = Image.open(src)
        img.save(dst_png)
    else:
        shutil.copy2(src, dst_png)
    return dst_png

def migrate(args):
    proj = pathlib.Path(args.project_root).resolve()
    dbp = pathlib.Path(args.db_path).resolve()
    cars_root = pathlib.Path(args.legacy_cars_root).resolve()
    assets_root = pathlib.Path(args.assets_root).resolve()
    conn = sqlite3.connect(str(dbp))
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    profile_id = ensure_profile(conn, args.profile)
    moved = 0
    for d in sorted(cars_root.iterdir()):
        if not d.is_dir():
            continue
        name_part = d.name.split(" - ", 1)
        if len(name_part) == 2:
            car_name = name_part[1].strip()
        else:
            car_name = d.name.strip()
        img = None
        for cand in ("car.png","car.jpg","car.jpeg"):
            p = d/cand
            if p.exists():
                img = p
                break
        data_bin = d/"data.bin"
        if not img or not data_bin.exists():
            continue
        stats = load_stats(data_bin)
        car_id = insert_car(conn, profile_id, car_name, stats)
        car_slug = slug(car_name)
        dst_dir = assets_root/"cars"/f"{car_id}_{car_slug}"
        dst_img = dst_dir/"image.png"
        out = copy_or_convert(img, dst_img)
        sha = checksum(out)
        size_bytes = out.stat().st_size
        rel = str(out.relative_to(proj))
        update_car_image(conn, car_id, rel, size_bytes, sha)
        moved += 1
        if args.verbose:
            print(f"car {car_id}: {car_name} -> {rel}")
    print(f"migrated {moved} cars")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default=".", help="project root (default: current dir)")
    ap.add_argument("--db-path", default="data/carmania.db", help="SQLite database path")
    ap.add_argument("--legacy-cars-root", default="UserData/Default/Cars", help="old Cars folder")
    ap.add_argument("--assets-root", default="assets", help="new assets root")
    ap.add_argument("--profile", default="Default")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    args.project_root = str(pathlib.Path(args.project_root).resolve())
    args.db_path = str(pathlib.Path(args.project_root) / args.db_path)
    args.legacy_cars_root = str(pathlib.Path(args.project_root) / args.legacy_cars_root)
    args.assets_root = str(pathlib.Path(args.project_root) / args.assets_root)

    migrate(args)

if __name__ == "__main__":
    main()