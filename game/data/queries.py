import sqlite3

def fetch_cars(conn, profile_id):
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        """SELECT id,
                  name,
                  image_path AS image,
                  display_order,
                  top_speed,
                  acceleration,
                  handling,
                  offroad,
                  engine_type
           FROM cars
           WHERE profile_id=?
           ORDER BY display_order, id""",
        (profile_id,)
    )
    return [dict(row) for row in cur.fetchall()]

def get_max_stats(conn, profile_id):
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        """SELECT
               MAX(top_speed) AS max_top_speed,
               MAX(acceleration) AS max_acceleration,
               MAX(handling) AS max_handling,
               MAX(offroad) AS max_offroad
           FROM cars
           WHERE profile_id=?""",
        (profile_id,)
    )
    row = cur.fetchone()
    return dict(row) if row else {
        "max_top_speed": 0,
        "max_acceleration": 0,
        "max_handling": 0,
        "max_offroad": 0
    }

def fetch_levels(conn: sqlite3.Connection, profile_id: int):
    cur = conn.execute(
        """SELECT id,name,code,ground_r,ground_g,ground_b,laps,music_path,display_order
           FROM levels
           WHERE profile_id=?
           ORDER BY display_order,id""",
        (profile_id,),
    )
    return _rowdicts(cur)

def _rowdicts(cur):
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]