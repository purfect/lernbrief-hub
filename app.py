from __future__ import annotations

import os
import sqlite3
import random
import re
import sys
import socket
import threading
import time
import webbrowser
from io import BytesIO
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, flash, g, redirect, render_template, request, send_file, url_for

BASE_DIR = Path(__file__).resolve().parent
if getattr(sys, "frozen", False):
    RESOURCE_DIR = Path(getattr(sys, "_MEIPASS", BASE_DIR))
    DATA_DIR = Path(sys.executable).resolve().parent
else:
    RESOURCE_DIR = BASE_DIR
    DATA_DIR = BASE_DIR

DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "lernbrief_hub.db"

GRADE_OPTIONS = [1, 2, 3, 4, 5, 6]
SEMESTER_PATTERN = re.compile(r"^(\d{4})/(\d{4})-(HJ[12])$")


def current_school_semester(now: datetime | None = None) -> str:
    """Return current German school semester key as YYYY/YYYY-HJ1|HJ2.

    HJ1 runs from August to January and HJ2 from February to July.
    """
    dt = now or datetime.now()
    year = dt.year
    month = dt.month

    if month >= 8:
        start_year = year
        end_year = year + 1
        half = "HJ1"
    elif month == 1:
        start_year = year - 1
        end_year = year
        half = "HJ1"
    else:
        start_year = year - 1
        end_year = year
        half = "HJ2"

    return f"{start_year}/{end_year}-{half}"


def parse_semester(value: str) -> tuple[int, int, str] | None:
    match = SEMESTER_PATTERN.match(value)
    if not match:
        return None
    start_year = int(match.group(1))
    end_year = int(match.group(2))
    half = match.group(3)
    if end_year != start_year + 1:
        return None
    return start_year, end_year, half


def semester_sort_key(value: str) -> tuple[int, int]:
    parsed = parse_semester(value)
    if parsed is None:
        return (-1, -1)
    start_year, _, half = parsed
    half_idx = 1 if half == "HJ1" else 2
    return (start_year, half_idx)


def school_semester_options(
    db: sqlite3.Connection | None = None,
    anchor: datetime | None = None,
    years_back: int | None = None,
    years_forward: int | None = None,
) -> list[str]:
    """Build selectable German school semesters around current year plus used data years."""
    dt = anchor or datetime.now()
    current = current_school_semester(dt)
    school_year_start = int(current.split("/")[0])

    back = years_back if years_back is not None else int(os.getenv("SEMESTER_YEARS_BACK", "3"))
    forward = years_forward if years_forward is not None else int(os.getenv("SEMESTER_YEARS_FORWARD", "3"))

    options: set[str] = set()
    for start_year in range(school_year_start - back, school_year_start + forward + 1):
        end_year = start_year + 1
        options.add(f"{start_year}/{end_year}-HJ1")
        options.add(f"{start_year}/{end_year}-HJ2")

    if db is not None:
        used_rows = db.execute(
            """
            SELECT semester FROM ratings
            UNION
            SELECT semester FROM letters
            """
        ).fetchall()
        for row in used_rows:
            sem = (row["semester"] or "").strip()
            if parse_semester(sem):
                options.add(sem)

    return sorted(options, key=semester_sort_key, reverse=True)


def normalize_semester(raw_value: str | None) -> str:
    value = (raw_value or "").strip()
    if parse_semester(value):
        return value
    return DEFAULT_SEMESTER


def ensure_sentence_punctuation(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return cleaned
    if cleaned[-1] not in ".!?":
        return f"{cleaned}."
    return cleaned


def make_export_filename(student_name: str, semester: str, extension: str) -> str:
    base = f"Lernbrief_{student_name}_{semester}"
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    return f"{safe}.{extension}"


def render_letter_pdf(letter: sqlite3.Row) -> BytesIO:
    from reportlab.lib.pagesizes import A4  # type: ignore[import-not-found]
    from reportlab.pdfgen import canvas  # type: ignore[import-not-found]

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(40, y, f"Lernbrief: {letter['full_name']}")
    y -= 22
    pdf.setFont("Helvetica", 10)
    pdf.drawString(40, y, f"Halbjahr: {letter['semester']}")
    y -= 16
    pdf.drawString(40, y, f"Erstellt am: {letter['created_at']}")
    y -= 24

    pdf.setFont("Helvetica", 11)
    for raw_line in letter["content"].splitlines():
        line = raw_line.strip()
        if line == "":
            y -= 12
        else:
            chunks = [line[i:i + 105] for i in range(0, len(line), 105)]
            for chunk in chunks:
                if y <= 50:
                    pdf.showPage()
                    pdf.setFont("Helvetica", 11)
                    y = height - 50
                pdf.drawString(40, y, chunk)
                y -= 14

    pdf.save()
    buffer.seek(0)
    return buffer


def render_letter_docx(letter: sqlite3.Row) -> BytesIO:
    from docx import Document  # type: ignore[import-not-found]

    document = Document()
    document.add_heading(f"Lernbrief: {letter['full_name']}", level=1)
    document.add_paragraph(f"Halbjahr: {letter['semester']}")
    document.add_paragraph(f"Erstellt am: {letter['created_at']}")
    document.add_paragraph("")

    for line in letter["content"].splitlines():
        document.add_paragraph(line)

    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer


DEFAULT_SEMESTER = current_school_semester()


def open_browser_when_ready(url: str, host: str, port: int, timeout_seconds: int = 20) -> None:
    """Wait until the local server is reachable, then open the system browser."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.5):
                webbrowser.open(url, new=2)
                return
        except OSError:
            time.sleep(0.3)


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(RESOURCE_DIR / "templates"),
        static_folder=str(RESOURCE_DIR / "static"),
    )
    app.config["SECRET_KEY"] = "lernbrief-hub-local-dev"

    def get_db() -> sqlite3.Connection:
        if "db" not in g:
            g.db = sqlite3.connect(DB_PATH)
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_: Any) -> None:
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db() -> None:
        db = get_db()
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS competencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT DEFAULT '',
                sort_order INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                competency_id INTEGER NOT NULL,
                semester TEXT NOT NULL,
                grade INTEGER NOT NULL,
                note TEXT DEFAULT '',
                UNIQUE(student_id, competency_id, semester),
                FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
                FOREIGN KEY(competency_id) REFERENCES competencies(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS sentence_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                competency_id INTEGER NOT NULL,
                grade INTEGER NOT NULL,
                semester TEXT NOT NULL DEFAULT '*',
                sentence TEXT NOT NULL,
                FOREIGN KEY(competency_id) REFERENCES competencies(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS letters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                semester TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        db.commit()

        sentence_cols = [row["name"] for row in db.execute("PRAGMA table_info(sentence_templates)")]
        if "semester" not in sentence_cols:
            db.executescript(
                """
                ALTER TABLE sentence_templates RENAME TO sentence_templates_old;

                CREATE TABLE sentence_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    competency_id INTEGER NOT NULL,
                    grade INTEGER NOT NULL,
                    semester TEXT NOT NULL DEFAULT '*',
                    sentence TEXT NOT NULL,
                    FOREIGN KEY(competency_id) REFERENCES competencies(id) ON DELETE CASCADE
                );

                INSERT INTO sentence_templates (competency_id, grade, semester, sentence)
                SELECT competency_id, grade, '*', sentence
                FROM sentence_templates_old;

                DROP TABLE sentence_templates_old;
                """
            )
            db.commit()

        competency_count = db.execute("SELECT COUNT(*) AS c FROM competencies").fetchone()["c"]
        if competency_count == 0:
            default_competencies = [
                ("Fachwissen", "Beherrscht die fachlichen Grundlagen", 1),
                ("Mitarbeit", "Bringt sich aktiv in den Unterricht ein", 2),
                ("Sozialverhalten", "Arbeitet respektvoll und kooperativ", 3),
                ("Selbstorganisation", "Plant und erledigt Aufgaben eigenständig", 4),
            ]
            db.executemany(
                "INSERT INTO competencies (name, description, sort_order) VALUES (?, ?, ?)",
                default_competencies,
            )
            db.commit()

            comp_rows = db.execute("SELECT id, name FROM competencies").fetchall()
            for comp in comp_rows:
                for grade in GRADE_OPTIONS:
                    sentence = f"In {comp['name']} erreicht { '{name}' } aktuell die Note {grade}."
                    db.execute(
                        "INSERT INTO sentence_templates (competency_id, grade, semester, sentence) VALUES (?, ?, ?, ?)",
                        (comp["id"], grade, "*", sentence),
                    )
            db.commit()

        db.execute(
            "INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)",
            ("letter_include_average_sentence", "1"),
        )
        db.execute(
            "INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)",
            (
                "letter_average_sentence_template",
                "Zusammenfassend ergibt sich eine Durchschnittsnote von {avg_grade} und damit ein insgesamt {avg_text}er Leistungsstand.",
            ),
        )
        db.commit()

    @app.before_request
    def ensure_db() -> None:
        init_db()

    def query_groups() -> list[sqlite3.Row]:
        return get_db().execute(
            """
            SELECT g.id, g.name, COUNT(s.id) AS student_count
            FROM groups g
            LEFT JOIN students s ON s.group_id = g.id
            GROUP BY g.id, g.name
            ORDER BY g.name ASC
            """
        ).fetchall()

    def query_competencies() -> list[sqlite3.Row]:
        return get_db().execute(
            "SELECT * FROM competencies ORDER BY sort_order ASC, name ASC"
        ).fetchall()

    def get_setting(key: str, default: str = "") -> str:
        row = get_db().execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
        if row is None:
            return default
        return row["value"]

    def set_setting(key: str, value: str) -> None:
        get_db().execute(
            """
            INSERT INTO app_settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )

    def build_letter(student_id: int, semester: str) -> str:
        db = get_db()
        student = db.execute(
            """
            SELECT s.id, s.full_name, g.name AS group_name
            FROM students s
            JOIN groups g ON g.id = s.group_id
            WHERE s.id = ?
            """,
            (student_id,),
        ).fetchone()

        ratings = db.execute(
            """
            SELECT c.name AS competency_name, r.competency_id, r.grade, r.note
            FROM ratings r
            JOIN competencies c ON c.id = r.competency_id
            WHERE r.student_id = ? AND r.semester = ?
            ORDER BY c.sort_order ASC, c.name ASC
            """,
            (student_id, semester),
        ).fetchall()

        if not ratings:
            raise ValueError("Keine Bewertungen für dieses Halbjahr vorhanden.")

        avg_grade = round(sum(row["grade"] for row in ratings) / len(ratings), 2)
        avg_text = (
            "sehr gut" if avg_grade <= 1.5 else
            "gut" if avg_grade <= 2.5 else
            "befriedigend" if avg_grade <= 3.5 else
            "ausreichend" if avg_grade <= 4.5 else
            "verbesserungsbedürftig"
        )

        header = [
            f"Lernbrief für {student['full_name']}",
            f"Lerngruppe: {student['group_name']}",
            f"Halbjahr: {semester}",
            "",
            (
                f"{student['full_name']} hat im aktuellen Halbjahr in den vereinbarten Kompetenzbereichen "
                f"insgesamt {avg_text}e Leistungen gezeigt."
            ),
            "",
            "Im Einzelnen zeigt sich folgende Entwicklung:",
            "",
        ]

        body_paragraphs: list[str] = []
        for idx, row in enumerate(ratings, start=1):
            template_rows = db.execute(
                """
                SELECT sentence
                FROM sentence_templates
                WHERE competency_id = ?
                  AND grade = ?
                ORDER BY id ASC
                """,
                (row["competency_id"], row["grade"]),
            ).fetchall()
            if template_rows:
                template = random.choice(template_rows)["sentence"]
            else:
                template = f"In {row['competency_name']} liegt die Leistung bei der Note {row['grade']}."
            sentence = template.replace("{name}", student["full_name"])
            if row["note"]:
                sentence = f"{sentence} Hinweis: {row['note']}"

            # Normalize multi-line template blocks into readable report paragraphs.
            paragraph = " ".join(part.strip() for part in sentence.splitlines() if part.strip())
            paragraph = ensure_sentence_punctuation(paragraph)
            body_paragraphs.append(paragraph)

            # Add a small paragraph break every two competency blocks.
            if idx % 2 == 0 and idx < len(ratings):
                body_paragraphs.append("")

        footer = [
            "",
        ]

        include_average_sentence = get_setting("letter_include_average_sentence", "1") == "1"
        average_sentence_template = get_setting(
            "letter_average_sentence_template",
            "Zusammenfassend ergibt sich eine Durchschnittsnote von {avg_grade} und damit ein insgesamt {avg_text}er Leistungsstand.",
        )

        if include_average_sentence:
            average_sentence = average_sentence_template.format(
                name=student["full_name"],
                avg_grade=avg_grade,
                avg_text=avg_text,
                semester=semester,
            )
            footer.append(ensure_sentence_punctuation(average_sentence))

        footer.append(
            (
                f"Für das kommende Halbjahr werden wir den eingeschlagenen Entwicklungsweg mit {student['full_name']} "
                "kontinuierlich fortsetzen."
            )
        )

        return "\n".join(header + body_paragraphs + footer)

    @app.route("/")
    def index() -> str:
        search_query = request.args.get("q", "").strip()
        groups = query_groups()
        recent_letters = get_db().execute(
            """
            SELECT l.id, l.semester, l.created_at, s.full_name
            FROM letters l
            JOIN students s ON s.id = l.student_id
            ORDER BY l.created_at DESC
            LIMIT 10
            """
        ).fetchall()

        student_results: list[sqlite3.Row] = []
        if search_query:
            student_results = get_db().execute(
                """
                SELECT s.id AS student_id, s.full_name, g.id AS group_id, g.name AS group_name
                FROM students s
                JOIN groups g ON g.id = s.group_id
                WHERE s.full_name LIKE ? OR g.name LIKE ?
                ORDER BY s.full_name ASC
                LIMIT 50
                """,
                (f"%{search_query}%", f"%{search_query}%"),
            ).fetchall()

        return render_template(
            "index.html",
            groups=groups,
            recent_letters=recent_letters,
            search_query=search_query,
            student_results=student_results,
            default_semester=DEFAULT_SEMESTER,
        )

    @app.route("/groups/create", methods=["POST"])
    def create_group() -> Any:
        name = request.form.get("name", "").strip()
        if not name:
            flash("Bitte einen Gruppennamen eingeben.", "error")
            return redirect(url_for("index"))

        try:
            get_db().execute("INSERT INTO groups (name) VALUES (?)", (name,))
            get_db().commit()
            flash("Lerngruppe erstellt.", "success")
        except sqlite3.IntegrityError:
            flash("Diese Lerngruppe existiert bereits.", "error")
        return redirect(url_for("index"))

    @app.route("/groups/new")
    def new_group() -> str:
        return render_template("group_new.html")

    @app.route("/groups/<int:group_id>")
    def group_detail(group_id: int) -> str:
        db = get_db()
        group = db.execute("SELECT * FROM groups WHERE id = ?", (group_id,)).fetchone()
        if group is None:
            flash("Lerngruppe nicht gefunden.", "error")
            return redirect(url_for("index"))

        students = db.execute(
            "SELECT * FROM students WHERE group_id = ? ORDER BY full_name ASC", (group_id,)
        ).fetchall()

        return render_template(
            "group_detail.html",
            group=group,
            students=students,
            default_semester=DEFAULT_SEMESTER,
        )

    @app.route("/groups/<int:group_id>/students/create", methods=["POST"])
    def create_student(group_id: int) -> Any:
        full_name = request.form.get("full_name", "").strip()
        if not full_name:
            flash("Bitte einen Schülernamen eingeben.", "error")
            return redirect(url_for("group_detail", group_id=group_id))

        get_db().execute(
            "INSERT INTO students (group_id, full_name) VALUES (?, ?)",
            (group_id, full_name),
        )
        get_db().commit()
        flash("Schüler hinzugefügt.", "success")
        return redirect(url_for("group_detail", group_id=group_id))

    @app.route("/competencies", methods=["GET", "POST"])
    def competencies() -> Any:
        db = get_db()

        if request.method == "POST":
            action = request.form.get("action", "create")

            if action == "update":
                competency_id = int(request.form.get("competency_id", "0") or 0)
                name = request.form.get("name", "").strip()
                description = request.form.get("description", "").strip()
                sort_order = int(request.form.get("sort_order", "0") or 0)

                if not competency_id or not name:
                    flash("Bitte gültige Kompetenzdaten angeben.", "error")
                    return redirect(url_for("competencies"))

                try:
                    db.execute(
                        """
                        UPDATE competencies
                        SET name = ?, description = ?, sort_order = ?
                        WHERE id = ?
                        """,
                        (name, description, sort_order, competency_id),
                    )
                    db.commit()
                    flash("Kompetenz aktualisiert.", "success")
                except sqlite3.IntegrityError:
                    flash("Eine Kompetenz mit diesem Namen existiert bereits.", "error")

                return redirect(url_for("competencies"))

            name = request.form.get("name", "").strip()
            description = request.form.get("description", "").strip()
            sort_order = int(request.form.get("sort_order", "0") or 0)

            if not name:
                flash("Kompetenzname fehlt.", "error")
                return redirect(url_for("competencies"))

            try:
                cur = db.execute(
                    "INSERT INTO competencies (name, description, sort_order) VALUES (?, ?, ?)",
                    (name, description, sort_order),
                )
                competency_id = cur.lastrowid
                for grade in GRADE_OPTIONS:
                    db.execute(
                        "INSERT INTO sentence_templates (competency_id, grade, semester, sentence) VALUES (?, ?, ?, ?)",
                        (competency_id, grade, "*", f"In {name} erreicht {{name}} aktuell die Note {grade}."),
                    )
                db.commit()
                flash("Kompetenz erstellt.", "success")
            except sqlite3.IntegrityError:
                flash("Diese Kompetenz existiert bereits.", "error")

            return redirect(url_for("competencies"))

        rows = query_competencies()
        return render_template("competencies.html", competencies=rows)

    @app.route("/templates", methods=["GET", "POST"])
    def templates_editor() -> Any:
        db = get_db()

        if request.method == "POST":
            action = request.form.get("action", "update")

            if action == "create":
                competency_id = int(request.form.get("competency_id", "0") or 0)
                grade = int(request.form.get("grade", "0") or 0)
                sentence = request.form.get("sentence", "").strip()

                if not competency_id or grade not in GRADE_OPTIONS or not sentence:
                    flash("Bitte Kompetenz, Note und Satz angeben.", "error")
                    return redirect(url_for("templates_editor"))

                db.execute(
                    "INSERT INTO sentence_templates (competency_id, grade, semester, sentence) VALUES (?, ?, ?, ?)",
                    (competency_id, grade, "*", sentence),
                )
                db.commit()
                flash("Satzbaustein hinzugefügt.", "success")
                return redirect(url_for("templates_editor"))

            if action == "update_average_sentence":
                include_average_sentence = "1" if request.form.get("include_average_sentence") == "on" else "0"
                average_sentence_template = request.form.get("average_sentence_template", "").strip()
                if not average_sentence_template:
                    average_sentence_template = (
                        "Zusammenfassend ergibt sich eine Durchschnittsnote von {avg_grade} "
                        "und damit ein insgesamt {avg_text}er Leistungsstand."
                    )

                set_setting("letter_include_average_sentence", include_average_sentence)
                set_setting("letter_average_sentence_template", average_sentence_template)
                db.commit()
                flash("Einstellung für den Abschlusssatz gespeichert.", "success")
                return redirect(url_for("templates_editor"))

            if action == "delete":
                template_id = int(request.form["template_id"])
                db.execute("DELETE FROM sentence_templates WHERE id = ?", (template_id,))
                db.commit()
                flash("Satzbaustein gelöscht.", "success")
                return redirect(url_for("templates_editor"))

            template_id = int(request.form["template_id"])
            sentence = request.form.get("sentence", "").strip()

            if not sentence:
                flash("Satz darf nicht leer sein.", "error")
                return redirect(url_for("templates_editor"))

            db.execute(
                "UPDATE sentence_templates SET sentence = ? WHERE id = ?",
                (sentence, template_id),
            )
            db.commit()
            flash("Satzbaustein gespeichert.", "success")
            return redirect(url_for("templates_editor"))

        rows = db.execute(
            """
            SELECT st.id, st.grade, st.sentence, c.name AS competency_name, c.id AS competency_id
            FROM sentence_templates st
            JOIN competencies c ON c.id = st.competency_id
            ORDER BY c.sort_order ASC, c.name ASC, st.grade ASC
            """
        ).fetchall()
        competencies_rows = query_competencies()
        include_average_sentence = get_setting("letter_include_average_sentence", "1") == "1"
        average_sentence_template = get_setting(
            "letter_average_sentence_template",
            "Zusammenfassend ergibt sich eine Durchschnittsnote von {avg_grade} und damit ein insgesamt {avg_text}er Leistungsstand.",
        )
        return render_template(
            "templates.html",
            templates=rows,
            competencies=competencies_rows,
            grade_options=GRADE_OPTIONS,
            include_average_sentence=include_average_sentence,
            average_sentence_template=average_sentence_template,
        )

    @app.route("/students/<int:student_id>/ratings", methods=["GET", "POST"])
    def ratings(student_id: int) -> Any:
        db = get_db()
        semester = normalize_semester(request.values.get("semester", DEFAULT_SEMESTER))
        semester_options = school_semester_options(db=db)
        if semester not in semester_options:
            semester_options.append(semester)
            semester_options = sorted(semester_options, key=semester_sort_key, reverse=True)

        student = db.execute(
            """
            SELECT s.id, s.full_name, g.name AS group_name
            FROM students s
            JOIN groups g ON g.id = s.group_id
            WHERE s.id = ?
            """,
            (student_id,),
        ).fetchone()
        if student is None:
            flash("Schüler nicht gefunden.", "error")
            return redirect(url_for("index"))

        competencies_rows = query_competencies()

        if request.method == "POST":
            for comp in competencies_rows:
                grade_val = request.form.get(f"grade_{comp['id']}")
                note_val = request.form.get(f"note_{comp['id']}", "").strip()
                if not grade_val:
                    continue
                grade = int(grade_val)

                db.execute(
                    """
                    INSERT INTO ratings (student_id, competency_id, semester, grade, note)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(student_id, competency_id, semester)
                    DO UPDATE SET grade = excluded.grade, note = excluded.note
                    """,
                    (student_id, comp["id"], semester, grade, note_val),
                )
            db.commit()
            flash("Bewertungen gespeichert.", "success")
            return redirect(url_for("ratings", student_id=student_id, semester=semester))

        existing_ratings = db.execute(
            "SELECT competency_id, grade, note FROM ratings WHERE student_id = ? AND semester = ?",
            (student_id, semester),
        ).fetchall()
        ratings_map = {row["competency_id"]: row for row in existing_ratings}

        letters = db.execute(
            "SELECT id, semester, created_at FROM letters WHERE student_id = ? ORDER BY created_at DESC",
            (student_id,),
        ).fetchall()

        rating_history = db.execute(
            """
            SELECT r.semester, c.name AS competency_name, r.grade, r.note
            FROM ratings r
            JOIN competencies c ON c.id = r.competency_id
            WHERE r.student_id = ?
            ORDER BY r.semester DESC, c.sort_order ASC, c.name ASC
            """,
            (student_id,),
        ).fetchall()

        semester_stats = db.execute(
            """
            SELECT semester, ROUND(AVG(grade), 2) AS avg_grade, COUNT(*) AS rating_count
            FROM ratings
            WHERE student_id = ?
            GROUP BY semester
            ORDER BY semester DESC
            """,
            (student_id,),
        ).fetchall()

        letter_stats_rows = db.execute(
            """
            SELECT semester, COUNT(*) AS letter_count, MAX(created_at) AS last_letter_created_at
            FROM letters
            WHERE student_id = ?
            GROUP BY semester
            """,
            (student_id,),
        ).fetchall()
        letter_stats = {
            row["semester"]: {
                "letter_count": row["letter_count"],
                "last_letter_created_at": row["last_letter_created_at"],
            }
            for row in letter_stats_rows
        }

        semester_overview: list[dict[str, Any]] = []
        for row in semester_stats:
            letters_info = letter_stats.get(row["semester"], {})
            semester_overview.append(
                {
                    "semester": row["semester"],
                    "avg_grade": row["avg_grade"],
                    "rating_count": row["rating_count"],
                    "letter_count": letters_info.get("letter_count", 0),
                    "last_letter_created_at": letters_info.get("last_letter_created_at", "-"),
                }
            )

        return render_template(
            "ratings.html",
            student=student,
            semester=semester,
            semester_options=semester_options,
            competencies=competencies_rows,
            ratings_map=ratings_map,
            grade_options=GRADE_OPTIONS,
            letters=letters,
            rating_history=rating_history,
            semester_overview=semester_overview,
        )

    @app.route("/students/<int:student_id>/letters/generate", methods=["POST"])
    def generate_letter(student_id: int) -> Any:
        semester = request.form.get("semester", DEFAULT_SEMESTER)

        try:
            content = build_letter(student_id, semester)
        except ValueError as exc:
            flash(str(exc), "error")
            return redirect(url_for("ratings", student_id=student_id, semester=semester))

        get_db().execute(
            "INSERT INTO letters (student_id, semester, content, created_at) VALUES (?, ?, ?, ?)",
            (student_id, semester, content, datetime.now().isoformat(timespec="seconds")),
        )
        get_db().commit()

        flash("Lernbrief wurde generiert und gespeichert.", "success")
        return redirect(url_for("ratings", student_id=student_id, semester=semester))

    @app.route("/letters/<int:letter_id>")
    def letter_detail(letter_id: int) -> Any:
        letter = get_db().execute(
            """
            SELECT l.id, l.student_id, l.content, l.semester, l.created_at, s.full_name
            FROM letters l
            JOIN students s ON s.id = l.student_id
            WHERE l.id = ?
            """,
            (letter_id,),
        ).fetchone()

        if letter is None:
            flash("Lernbrief nicht gefunden.", "error")
            return redirect(url_for("index"))

        return render_template("letter_detail.html", letter=letter)

    @app.route("/letters/<int:letter_id>/export/pdf")
    def export_letter_pdf(letter_id: int) -> Any:
        letter = get_db().execute(
            """
            SELECT l.id, l.student_id, l.content, l.semester, l.created_at, s.full_name
            FROM letters l
            JOIN students s ON s.id = l.student_id
            WHERE l.id = ?
            """,
            (letter_id,),
        ).fetchone()

        if letter is None:
            flash("Lernbrief nicht gefunden.", "error")
            return redirect(url_for("index"))

        pdf_buffer = render_letter_pdf(letter)
        filename = make_export_filename(letter["full_name"], letter["semester"], "pdf")
        return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")

    @app.route("/letters/<int:letter_id>/export/docx")
    def export_letter_docx(letter_id: int) -> Any:
        letter = get_db().execute(
            """
            SELECT l.id, l.student_id, l.content, l.semester, l.created_at, s.full_name
            FROM letters l
            JOIN students s ON s.id = l.student_id
            WHERE l.id = ?
            """,
            (letter_id,),
        ).fetchone()

        if letter is None:
            flash("Lernbrief nicht gefunden.", "error")
            return redirect(url_for("index"))

        docx_buffer = render_letter_docx(letter)
        filename = make_export_filename(letter["full_name"], letter["semester"], "docx")
        return send_file(
            docx_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    @app.route("/letters/<int:letter_id>/delete", methods=["POST"])
    def delete_letter(letter_id: int) -> Any:
        db = get_db()
        letter = db.execute(
            "SELECT id, student_id, semester FROM letters WHERE id = ?",
            (letter_id,),
        ).fetchone()

        if letter is None:
            flash("Lernbrief nicht gefunden.", "error")
            return redirect(url_for("index"))

        db.execute("DELETE FROM letters WHERE id = ?", (letter_id,))
        db.commit()
        flash("Lernbrief wurde gelöscht.", "success")

        next_target = request.form.get("next", "index")
        if next_target == "ratings":
            return redirect(
                url_for(
                    "ratings",
                    student_id=letter["student_id"],
                    semester=letter["semester"],
                )
            )

        return redirect(url_for("index"))

    return app


if __name__ == "__main__":
    app = create_app()
    host = os.getenv("LERNBRIEF_HOST", "127.0.0.1")
    port = int(os.getenv("LERNBRIEF_PORT", "5000"))
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"

    should_open_browser = os.getenv("LERNBRIEF_OPEN_BROWSER", "1") == "1"
    is_reloader_child = os.getenv("WERKZEUG_RUN_MAIN") == "true"
    if should_open_browser and (not debug_mode or is_reloader_child):
        url = f"http://{host}:{port}"
        threading.Thread(
            target=open_browser_when_ready,
            args=(url, host, port),
            daemon=True,
        ).start()

    app.run(host=host, port=port, debug=debug_mode, use_reloader=debug_mode)
