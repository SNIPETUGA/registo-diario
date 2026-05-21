from flask import Flask, render_template, request, jsonify, send_file
import sqlite3
import json
import io
from datetime import datetime
from pdf_generator import gerar_pdf

import os

DB_DIR = os.path.join(os.path.dirname(__file__), "db")
os.makedirs(DB_DIR, exist_ok=True)
DB = os.path.join(DB_DIR, "registos.db")


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row  # permite aceder por nome de coluna
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS registos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            criado_em TEXT DEFAULT (datetime('now')),
            data TEXT NOT NULL,
            central TEXT,
            carro_n TEXT,
            marca TEXT,
            matricula TEXT,
            empresa TEXT,
            hora_entrada TEXT,
            hora_almoco TEXT,
            hora_saida TEXT,
            horas_extras TEXT,
            km_inicio TEXT,
            km_fim TEXT,
            km_percorridos TEXT,
            horas_finais_motor TEXT,
            horas_finais_bomba TEXT,
            horas_iniciais_motor TEXT,
            horas_iniciais_bomba TEXT,
            hora_ligou TEXT,
            hora_desligou TEXT,
            horas_motor_desligou TEXT,
            motorista_nome TEXT,
            numero TEXT,
            assinatura TEXT,
            responsavel TEXT,
            viatura_limpa_int INTEGER DEFAULT 0,
            viatura_limpa_ext INTEGER DEFAULT 0,
            viatura_lubrificada INTEGER DEFAULT 0,
            oleo_motor_ok INTEGER DEFAULT 0,
            oleo_motor_naook INTEGER DEFAULT 0,
            oleo_motor_notas TEXT,
            oleo_sis_ok INTEGER DEFAULT 0,
            oleo_sis_naook INTEGER DEFAULT 0,
            oleo_sis_notas TEXT,
            agua_rad_ok INTEGER DEFAULT 0,
            agua_rad_naook INTEGER DEFAULT 0,
            agua_rad_notas TEXT,
            observacoes TEXT,
            obras TEXT,      -- JSON com lista de obras
            gasoleo TEXT     -- JSON com lista de abastecimentos
        )
    """)
    conn.commit()
    conn.close()


# ── ROTAS ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/registos", methods=["GET"])
def listar_registos():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, data, matricula, viatura_limpa_int, numero, motorista_nome, obras FROM registos ORDER BY data DESC, id DESC"
    ).fetchall()
    conn.close()

    resultado = []
    for r in rows:
        obras = json.loads(r["obras"] or "[]")
        total_m3 = sum(float(o.get("m3") or 0) for o in obras)
        n_obras = len([o for o in obras if o.get("cliente") or o.get("guia")])
        resultado.append({
            "id": r["id"],
            "data": r["data"],
            "matricula": r["matricula"],
            "numero": r["numero"],
            "motorista_nome": r["motorista_nome"],
            "n_obras": n_obras,
            "total_m3": round(total_m3, 1),
        })

    return jsonify(resultado)


@app.route("/api/registos", methods=["POST"])
def criar_registo():
    dados = request.get_json()

    obras_json = json.dumps(dados.get("obras", []))
    gasoleo_json = json.dumps(dados.get("gasoleo", []))

    conn = get_db()
    cursor = conn.execute("""
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
        ) VALUES (
            :data, :central, :carro_n, :marca, :matricula, :empresa,
            :hora_entrada, :hora_almoco, :hora_saida, :horas_extras,
            :km_inicio, :km_fim, :km_percorridos,
            :horas_finais_motor, :horas_finais_bomba, :horas_iniciais_motor, :horas_iniciais_bomba,
            :hora_ligou, :hora_desligou, :horas_motor_desligou,
            :motorista_nome, :numero, :assinatura, :responsavel,
            :viatura_limpa_int, :viatura_limpa_ext, :viatura_lubrificada,
            :oleo_motor_ok, :oleo_motor_naook, :oleo_motor_notas,
            :oleo_sis_ok, :oleo_sis_naook, :oleo_sis_notas,
            :agua_rad_ok, :agua_rad_naook, :agua_rad_notas,
            :observacoes, :obras, :gasoleo
        )
    """, {
        "data":                 dados.get("data", ""),
        "central":              dados.get("central", ""),
        "carro_n":              dados.get("carro_n", ""),
        "marca":                dados.get("marca", ""),
        "matricula":            dados.get("matricula", ""),
        "empresa":              dados.get("empresa", ""),
        "hora_entrada":         dados.get("hora_entrada", ""),
        "hora_almoco":          dados.get("hora_almoco", ""),
        "hora_saida":           dados.get("hora_saida", ""),
        "horas_extras":         dados.get("horas_extras", ""),
        "km_inicio":            dados.get("km_inicio", ""),
        "km_fim":               dados.get("km_fim", ""),
        "km_percorridos":       dados.get("km_percorridos", ""),
        "horas_finais_motor":   dados.get("horas_finais_motor", ""),
        "horas_finais_bomba":   dados.get("horas_finais_bomba", ""),
        "horas_iniciais_motor": dados.get("horas_iniciais_motor", ""),
        "horas_iniciais_bomba": dados.get("horas_iniciais_bomba", ""),
        "hora_ligou":           dados.get("hora_ligou", ""),
        "hora_desligou":        dados.get("hora_desligou", ""),
        "horas_motor_desligou": dados.get("horas_motor_desligou", ""),
        "motorista_nome":       dados.get("motorista_nome", ""),
        "numero":               dados.get("numero", ""),
        "assinatura":           dados.get("assinatura", ""),
        "responsavel":          dados.get("responsavel", ""),
        "viatura_limpa_int":    dados.get("viatura_limpa_int", 0),
        "viatura_limpa_ext":    dados.get("viatura_limpa_ext", 0),
        "viatura_lubrificada":  dados.get("viatura_lubrificada", 0),
        "oleo_motor_ok":        dados.get("oleo_motor_ok", 0),
        "oleo_motor_naook":     dados.get("oleo_motor_naook", 0),
        "oleo_motor_notas":     dados.get("oleo_motor_notas", ""),
        "oleo_sis_ok":          dados.get("oleo_sis_ok", 0),
        "oleo_sis_naook":       dados.get("oleo_sis_naook", 0),
        "oleo_sis_notas":       dados.get("oleo_sis_notas", ""),
        "agua_rad_ok":          dados.get("agua_rad_ok", 0),
        "agua_rad_naook":       dados.get("agua_rad_naook", 0),
        "agua_rad_notas":       dados.get("agua_rad_notas", ""),
        "observacoes":          dados.get("observacoes", ""),
        "obras":                obras_json,
        "gasoleo":              gasoleo_json,
    })
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()

    return jsonify({"id": novo_id, "mensagem": "Registo guardado com sucesso"}), 201


@app.route("/api/registos/<int:registo_id>", methods=["GET"])
def obter_registo(registo_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM registos WHERE id = ?", (registo_id,)).fetchone()
    conn.close()

    if not row:
        return jsonify({"erro": "Registo não encontrado"}), 404

    dados = dict(row)
    dados["obras"] = json.loads(dados["obras"] or "[]")
    dados["gasoleo"] = json.loads(dados["gasoleo"] or "[]")
    return jsonify(dados)


@app.route("/api/registos/<int:registo_id>", methods=["DELETE"])
def apagar_registo(registo_id):
    conn = get_db()
    conn.execute("DELETE FROM registos WHERE id = ?", (registo_id,))
    conn.commit()
    conn.close()
    return jsonify({"mensagem": "Registo apagado"})


@app.route("/api/registos/<int:registo_id>/pdf", methods=["GET"])
def exportar_pdf(registo_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM registos WHERE id = ?", (registo_id,)).fetchone()
    conn.close()

    if not row:
        return jsonify({"erro": "Registo não encontrado"}), 404

    dados = dict(row)
    dados["obras"] = json.loads(dados["obras"] or "[]")
    dados["gasoleo"] = json.loads(dados["gasoleo"] or "[]")

    pdf_bytes = gerar_pdf(dados)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"registo_{dados['data'].replace('/', '-')}_folha{dados['numero']}.pdf"
    )


if __name__ == "__main__":
    init_db()
    print("✅ Base de dados iniciada")
    print("🚀 A correr em http://localhost:5000")
    app.run(debug=True)
else:
    # produção (gunicorn): inicializa a DB ao importar
    init_db()
