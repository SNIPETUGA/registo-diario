import os
import json
import io
from flask import Flask, render_template, request, jsonify, send_file
from pdf_generator import gerar_pdf

app = Flask(__name__)

# ── BASE DE DADOS ─────────────────────────────────────────────────────────
# Em produção usa DATABASE_URL (PostgreSQL no Railway)
# Em desenvolvimento usa SQLite local
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    import psycopg2
    import psycopg2.extras

    def get_db():
        conn = psycopg2.connect(DATABASE_URL)
        return conn

    def init_db():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS registos (
                id SERIAL PRIMARY KEY,
                criado_em TIMESTAMP DEFAULT NOW(),
                data TEXT NOT NULL,
                central TEXT, carro_n TEXT, marca TEXT, matricula TEXT, empresa TEXT,
                hora_entrada TEXT, hora_almoco TEXT, hora_saida TEXT, horas_extras TEXT,
                km_inicio TEXT, km_fim TEXT, km_percorridos TEXT,
                horas_finais_motor TEXT, horas_finais_bomba TEXT,
                horas_iniciais_motor TEXT, horas_iniciais_bomba TEXT,
                hora_ligou TEXT, hora_desligou TEXT, horas_motor_desligou TEXT,
                motorista_nome TEXT, numero TEXT, assinatura TEXT, responsavel TEXT,
                viatura_limpa_int INTEGER DEFAULT 0,
                viatura_limpa_ext INTEGER DEFAULT 0,
                viatura_lubrificada INTEGER DEFAULT 0,
                oleo_motor_ok INTEGER DEFAULT 0, oleo_motor_naook INTEGER DEFAULT 0, oleo_motor_notas TEXT,
                oleo_sis_ok INTEGER DEFAULT 0, oleo_sis_naook INTEGER DEFAULT 0, oleo_sis_notas TEXT,
                agua_rad_ok INTEGER DEFAULT 0, agua_rad_naook INTEGER DEFAULT 0, agua_rad_notas TEXT,
                observacoes TEXT, obras TEXT, gasoleo TEXT
            )
        """)
        conn.commit()
        cur.close()
        conn.close()

    def db_fetchall(query, params=()):
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close(); conn.close()
        return [dict(r) for r in rows]

    def db_fetchone(query, params=()):
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query, params)
        row = cur.fetchone()
        cur.close(); conn.close()
        return dict(row) if row else None

    def db_execute(query, params=()):
        conn = get_db()
        cur = conn.cursor()
        cur.execute(query, params)
        lastid = None
        try: lastid = cur.fetchone()[0]
        except: pass
        conn.commit()
        cur.close(); conn.close()
        return lastid

else:
    # desenvolvimento local — SQLite
    import sqlite3

    DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db")
    os.makedirs(DB_DIR, exist_ok=True)
    DB = os.path.join(DB_DIR, "registos.db")

    def get_db():
        conn = sqlite3.connect(DB)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db():
        conn = get_db()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS registos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                criado_em TEXT DEFAULT (datetime('now')),
                data TEXT NOT NULL,
                central TEXT, carro_n TEXT, marca TEXT, matricula TEXT, empresa TEXT,
                hora_entrada TEXT, hora_almoco TEXT, hora_saida TEXT, horas_extras TEXT,
                km_inicio TEXT, km_fim TEXT, km_percorridos TEXT,
                horas_finais_motor TEXT, horas_finais_bomba TEXT,
                horas_iniciais_motor TEXT, horas_iniciais_bomba TEXT,
                hora_ligou TEXT, hora_desligou TEXT, horas_motor_desligou TEXT,
                motorista_nome TEXT, numero TEXT, assinatura TEXT, responsavel TEXT,
                viatura_limpa_int INTEGER DEFAULT 0,
                viatura_limpa_ext INTEGER DEFAULT 0,
                viatura_lubrificada INTEGER DEFAULT 0,
                oleo_motor_ok INTEGER DEFAULT 0, oleo_motor_naook INTEGER DEFAULT 0, oleo_motor_notas TEXT,
                oleo_sis_ok INTEGER DEFAULT 0, oleo_sis_naook INTEGER DEFAULT 0, oleo_sis_notas TEXT,
                agua_rad_ok INTEGER DEFAULT 0, agua_rad_naook INTEGER DEFAULT 0, agua_rad_notas TEXT,
                observacoes TEXT, obras TEXT, gasoleo TEXT
            )
        """)
        conn.commit()
        conn.close()

    def db_fetchall(query, params=()):
        conn = get_db()
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def db_fetchone(query, params=()):
        conn = get_db()
        row = conn.execute(query, params).fetchone()
        conn.close()
        return dict(row) if row else None

    def db_execute(query, params=()):
        conn = get_db()
        cur = conn.execute(query, params)
        conn.commit()
        lastid = cur.lastrowid
        conn.close()
        return lastid


def adapt_query(query):
    """Converte ? (SQLite) para %s (PostgreSQL) se necessário."""
    if DATABASE_URL:
        return query.replace("?", "%s")
    return query


# ── ROTAS ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/registos", methods=["GET"])
def listar_registos():
    rows = db_fetchall("SELECT id, data, matricula, numero, motorista_nome, obras FROM registos ORDER BY data DESC, id DESC")
    resultado = []
    for r in rows:
        obras = json.loads(r["obras"] or "[]")
        total_m3 = sum(float(o.get("m3") or 0) for o in obras)
        n_obras = len([o for o in obras if o.get("cliente") or o.get("guia")])
        resultado.append({
            "id": r["id"], "data": r["data"], "matricula": r["matricula"],
            "numero": r["numero"], "motorista_nome": r["motorista_nome"],
            "n_obras": n_obras, "total_m3": round(total_m3, 1),
        })
    return jsonify(resultado)


@app.route("/api/registos", methods=["POST"])
def criar_registo():
    d = request.get_json()
    obras_json   = json.dumps(d.get("obras", []))
    gasoleo_json = json.dumps(d.get("gasoleo", []))

    if DATABASE_URL:
        query = """
            INSERT INTO registos (
                data, central, carro_n, marca, matricula, empresa,
                hora_entrada, hora_almoco, hora_saida, horas_extras,
                km_inicio, km_fim, km_percorridos,
                horas_finais_motor, horas_finais_bomba, horas_iniciais_motor, horas_iniciais_bomba,
                hora_ligou, hora_desligou, horas_motor_desligou,
                motorista_nome, numero, assinatura, responsavel,
                viatura_limpa_int, viatura_limpa_ext, viatura_lubrificada,
                oleo_motor_ok, oleo_motor_naook, oleo_motor_notas,
                oleo_sis_ok, oleo_sis_naook, oleo_sis_notas,
                agua_rad_ok, agua_rad_naook, agua_rad_notas,
                observacoes, obras, gasoleo
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING id
        """
    else:
        query = """
            INSERT INTO registos (
                data, central, carro_n, marca, matricula, empresa,
                hora_entrada, hora_almoco, hora_saida, horas_extras,
                km_inicio, km_fim, km_percorridos,
                horas_finais_motor, horas_finais_bomba, horas_iniciais_motor, horas_iniciais_bomba,
                hora_ligou, hora_desligou, horas_motor_desligou,
                motorista_nome, numero, assinatura, responsavel,
                viatura_limpa_int, viatura_limpa_ext, viatura_lubrificada,
                oleo_motor_ok, oleo_motor_naook, oleo_motor_notas,
                oleo_sis_ok, oleo_sis_naook, oleo_sis_notas,
                agua_rad_ok, agua_rad_naook, agua_rad_notas,
                observacoes, obras, gasoleo
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """

    params = (
        d.get("data",""), d.get("central",""), d.get("carro_n",""), d.get("marca",""),
        d.get("matricula",""), d.get("empresa",""), d.get("hora_entrada",""),
        d.get("hora_almoco",""), d.get("hora_saida",""), d.get("horas_extras",""),
        d.get("km_inicio",""), d.get("km_fim",""), d.get("km_percorridos",""),
        d.get("horas_finais_motor",""), d.get("horas_finais_bomba",""),
        d.get("horas_iniciais_motor",""), d.get("horas_iniciais_bomba",""),
        d.get("hora_ligou",""), d.get("hora_desligou",""), d.get("horas_motor_desligou",""),
        d.get("motorista_nome",""), d.get("numero",""), d.get("assinatura",""),
        d.get("responsavel",""), d.get("viatura_limpa_int",0), d.get("viatura_limpa_ext",0),
        d.get("viatura_lubrificada",0), d.get("oleo_motor_ok",0), d.get("oleo_motor_naook",0),
        d.get("oleo_motor_notas",""), d.get("oleo_sis_ok",0), d.get("oleo_sis_naook",0),
        d.get("oleo_sis_notas",""), d.get("agua_rad_ok",0), d.get("agua_rad_naook",0),
        d.get("agua_rad_notas",""), d.get("observacoes",""), obras_json, gasoleo_json,
    )
    novo_id = db_execute(query, params)
    return jsonify({"id": novo_id, "mensagem": "Registo guardado com sucesso"}), 201


@app.route("/api/registos/<int:registo_id>", methods=["GET"])
def obter_registo(registo_id):
    row = db_fetchone(adapt_query("SELECT * FROM registos WHERE id = ?"), (registo_id,))
    if not row:
        return jsonify({"erro": "Registo não encontrado"}), 404
    row["obras"]   = json.loads(row["obras"] or "[]")
    row["gasoleo"] = json.loads(row["gasoleo"] or "[]")
    return jsonify(row)


@app.route("/api/registos/<int:registo_id>", methods=["PUT"])
def atualizar_registo(registo_id):
    d = request.get_json()
    obras_json   = json.dumps(d.get("obras", []))
    gasoleo_json = json.dumps(d.get("gasoleo", []))
    ph = "%s" if DATABASE_URL else "?"

    query = f"""
        UPDATE registos SET
            data={ph}, central={ph}, carro_n={ph}, marca={ph}, matricula={ph}, empresa={ph},
            hora_entrada={ph}, hora_almoco={ph}, hora_saida={ph}, horas_extras={ph},
            km_inicio={ph}, km_fim={ph}, km_percorridos={ph},
            horas_finais_motor={ph}, horas_finais_bomba={ph},
            horas_iniciais_motor={ph}, horas_iniciais_bomba={ph},
            hora_ligou={ph}, hora_desligou={ph}, horas_motor_desligou={ph},
            motorista_nome={ph}, numero={ph}, assinatura={ph}, responsavel={ph},
            viatura_limpa_int={ph}, viatura_limpa_ext={ph}, viatura_lubrificada={ph},
            oleo_motor_ok={ph}, oleo_motor_naook={ph}, oleo_motor_notas={ph},
            oleo_sis_ok={ph}, oleo_sis_naook={ph}, oleo_sis_notas={ph},
            agua_rad_ok={ph}, agua_rad_naook={ph}, agua_rad_notas={ph},
            observacoes={ph}, obras={ph}, gasoleo={ph}
        WHERE id={ph}
    """
    params = (
        d.get("data",""), d.get("central",""), d.get("carro_n",""), d.get("marca",""),
        d.get("matricula",""), d.get("empresa",""), d.get("hora_entrada",""),
        d.get("hora_almoco",""), d.get("hora_saida",""), d.get("horas_extras",""),
        d.get("km_inicio",""), d.get("km_fim",""), d.get("km_percorridos",""),
        d.get("horas_finais_motor",""), d.get("horas_finais_bomba",""),
        d.get("horas_iniciais_motor",""), d.get("horas_iniciais_bomba",""),
        d.get("hora_ligou",""), d.get("hora_desligou",""), d.get("horas_motor_desligou",""),
        d.get("motorista_nome",""), d.get("numero",""), d.get("assinatura",""),
        d.get("responsavel",""), d.get("viatura_limpa_int",0), d.get("viatura_limpa_ext",0),
        d.get("viatura_lubrificada",0), d.get("oleo_motor_ok",0), d.get("oleo_motor_naook",0),
        d.get("oleo_motor_notas",""), d.get("oleo_sis_ok",0), d.get("oleo_sis_naook",0),
        d.get("oleo_sis_notas",""), d.get("agua_rad_ok",0), d.get("agua_rad_naook",0),
        d.get("agua_rad_notas",""), d.get("observacoes",""), obras_json, gasoleo_json,
        registo_id,
    )
    db_execute(query, params)
    return jsonify({"mensagem": "Registo atualizado com sucesso"})


@app.route("/api/registos/<int:registo_id>", methods=["DELETE"])
def apagar_registo(registo_id):
    db_execute(adapt_query("DELETE FROM registos WHERE id = ?"), (registo_id,))
    return jsonify({"mensagem": "Registo apagado"})


@app.route("/api/registos/<int:registo_id>/pdf", methods=["GET"])
def exportar_pdf(registo_id):
    row = db_fetchone(adapt_query("SELECT * FROM registos WHERE id = ?"), (registo_id,))
    if not row:
        return jsonify({"erro": "Registo não encontrado"}), 404
    row["obras"]   = json.loads(row["obras"] or "[]")
    row["gasoleo"] = json.loads(row["gasoleo"] or "[]")
    pdf_bytes = gerar_pdf(row)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"registo_{row['data'].replace('/', '-')}_folha{row['numero']}.pdf"
    )


# inicializa DB
init_db()

if __name__ == "__main__":
    print("🚀 A correr em http://localhost:5000")
    app.run(debug=True)
