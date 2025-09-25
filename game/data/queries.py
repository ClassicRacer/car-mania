import sqlite3

def fetch_cars(conn, profile_id):
    cur = conn.execute(
        """SELECT id,name,image_path,display_order
           FROM cars
           WHERE profile_id=?
           ORDER BY display_order, id""",
        (profile_id,)
    )
    out = []
    for row in cur.fetchall():
        out.append({
            "id": row[0],
            "name": row[1],
            "image": row[2] if row[2] else row[3],
        })
    return out