import os
import sqlite3
import base64
import json as json_lib
from datetime import datetime
from uuid import uuid4
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash


DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            slug TEXT UNIQUE,
            created_at TEXT NOT NULL
        );
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS boards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            data TEXT,
            preview_path TEXT,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """
    )
    conn.commit()
    conn.close()


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    conn.close()
    return user


def require_login():
    if not session.get("user_id"):
        abort(401)


def json_dumps(data: dict) -> str:
    return json_lib.dumps(data, separators=(",", ":"))


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
    os.makedirs(os.path.join("static", "previews"), exist_ok=True)
    init_db()

    @app.get("/")
    def index():
        user = current_user()
        return render_template("index.html", user=user, board_data=None)

    @app.get("/b/<slug>")
    def load_board(slug: str):
        conn = get_db()
        board = conn.execute("SELECT * FROM boards WHERE slug=?", (slug,)).fetchone()
        conn.close()
        if not board:
            return redirect(url_for("index"))
        user = current_user()
        return render_template("index.html", user=user, board_data=board["data"])  # JSON string

    @app.get("/my")
    def my_drawings():
        user = current_user()
        if not user:
            return redirect(url_for("login"))
        conn = get_db()
        board = conn.execute("SELECT * FROM boards WHERE user_id=?", (user["id"],)).fetchone()
        conn.close()
        return render_template("my_drawings.html", user=user, board=board)

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if not username or not password:
                return render_template("register.html", error="Please fill all fields")
            pw_hash = generate_password_hash(password)
            slug = uuid4().hex[:10]
            now = datetime.utcnow().isoformat()
            try:
                conn = get_db()
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO users(username, password_hash, slug, created_at) VALUES (?,?,?,?)",
                    (username, pw_hash, slug, now),
                )
                conn.commit()
                user_id = cur.lastrowid
            except sqlite3.IntegrityError:
                return render_template("register.html", error="Username is already taken")
            finally:
                conn.close()
            session["user_id"] = user_id
            return redirect(url_for("index"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            conn = get_db()
            user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
            conn.close()
            if not user or not check_password_hash(user["password_hash"], password):
                return render_template("login.html", error="Invalid credentials")
            session["user_id"] = user["id"]
            return redirect(url_for("index"))
        return render_template("login.html")

    @app.get("/logout")
    def logout():
        session.pop("user_id", None)
        return redirect(url_for("index"))

    @app.post("/api/save")
    def api_save():
        require_login()
        payload = request.get_json(silent=True) or {}
        data = payload.get("data")  # JSON-serializable dict {paths, view}
        preview = payload.get("preview")  # dataURL png
        if not isinstance(data, dict) or not isinstance(preview, str) or not preview.startswith("data:image/png"):
            return jsonify({"error": "Bad payload"}), 400
        uid = session["user_id"]
        conn = get_db()
        cur = conn.cursor()
        board = conn.execute("SELECT * FROM boards WHERE user_id=?", (uid,)).fetchone()
        now = datetime.utcnow().isoformat()
        if board:
            slug = board["slug"]
            cur.execute(
                "UPDATE boards SET data=?, updated_at=? WHERE user_id=?",
                (json_dumps(data), now, uid),
            )
        else:
            slug = uuid4().hex[:12]
            cur.execute(
                "INSERT INTO boards(user_id, slug, data, updated_at) VALUES (?,?,?,?)",
                (uid, slug, json_dumps(data), now),
            )
        conn.commit()
        conn.close()
        # save preview image
        try:
            header, b64 = preview.split(",", 1)
            img_bytes = base64.b64decode(b64)
            preview_dir = os.path.join("static", "previews")
            os.makedirs(preview_dir, exist_ok=True)
            img_path = os.path.join(preview_dir, f"{slug}.png")
            with open(img_path, "wb") as f:
                f.write(img_bytes)
            # store preview_path
            conn = get_db()
            conn.execute("UPDATE boards SET preview_path=? WHERE slug=?", (img_path.replace("\\", "/"), slug))
            conn.commit()
            conn.close()
        except Exception:
            pass
        url = url_for("load_board", slug=slug, _external=True)
        return jsonify({"url": url})

    return app


app = create_app()


if __name__ == "__main__":
    # Geliştirme için basit yerel sunucu
    app.run(host="0.0.0.0", port=5000, debug=True)


