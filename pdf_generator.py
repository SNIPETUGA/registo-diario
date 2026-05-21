import io
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

# 16:9 landscape — A4 landscape é 297x210mm, usamos 297x167mm para 16:9 exato
W = 297 * mm
H = W * 9 / 16   # ~167mm

DARK   = colors.HexColor("#111111")
MID    = colors.HexColor("#666666")
LIGHT  = colors.HexColor("#f5f5f5")
ACCENT = colors.HexColor("#1d4ed8")
ABLUE  = colors.HexColor("#dbeafe")
WHITE  = colors.white
BLK    = colors.black
LINE   = colors.HexColor("#cccccc")


def gerar_pdf(registo: dict) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(W, H))
    M = 7 * mm
    CW = W - 2 * M

    # ── helpers ──────────────────────────────────────────────────────────
    def rect(x, y, w, h, fill=WHITE, stroke=True):
        c.setFillColor(fill)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.25)
        c.rect(x, y - h, w, h, fill=1, stroke=1 if stroke else 0)

    def cell(x, y, w, h, label="", value="", fill=WHITE,
             lfs=4.5, vfs=8, bold=False, center=False, label_top=True):
        rect(x, y, w, h, fill=fill)
        pad = 1.2 * mm
        if label:
            c.setFillColor(MID)
            c.setFont("Helvetica", lfs)
            if center:
                c.drawCentredString(x + w / 2, y - 3.2 * mm, label)
            else:
                c.drawString(x + pad, y - 3.2 * mm, label)
        if value is not None and str(value).strip():
            c.setFillColor(DARK)
            c.setFont("Helvetica-Bold" if bold else "Helvetica", vfs)
            if center:
                c.drawCentredString(x + w / 2, y - h + 2 * mm, str(value))
            else:
                c.drawString(x + pad, y - h + 2 * mm, str(value))

    def hline(y, x1=None, x2=None, w=0.25, col=LINE):
        c.setStrokeColor(col)
        c.setLineWidth(w)
        c.line(x1 or M, y, x2 or (M + CW), y)

    def vline(x, y1, y2, w=0.2):
        c.setStrokeColor(LINE)
        c.setLineWidth(w)
        c.line(x, y1, x, y2)

    def txt(x, y, s, fs=7, bold=False, col=DARK, align="left"):
        c.setFillColor(col)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", fs)
        s = str(s) if s else ""
        {"left": c.drawString, "center": c.drawCentredString, "right": c.drawRightString}[align](x, y, s)

    def v(key, default=""):
        val = registo.get(key, default)
        return str(val) if val is not None else default

    # ── HEADER STRIP ─────────────────────────────────────────────────────
    HDR = 10 * mm
    y = H

    # fundo azul escuro no header
    c.setFillColor(DARK)
    c.rect(0, H - HDR, W, HDR, fill=1, stroke=0)

    # logo / empresa
    c.setFillColor(ACCENT)
    c.circle(M + 3 * mm, H - HDR / 2, 2.5 * mm, fill=1, stroke=0)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(M + 7 * mm, H - HDR / 2 - 1.5 * mm, "PRAGOSA  BETÃO")

    # título central
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(W / 2, H - HDR / 2 - 1.5 * mm, "Registo Diário do Motorista")

    # folha + data (direita)
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.HexColor("#aaaaaa"))
    data_str = v("data")
    folha_str = f"Folha nº {v('numero')}   ·   {data_str}"
    c.drawRightString(W - M, H - HDR / 2 - 1.5 * mm, folha_str)

    y = H - HDR

    # ── ROW A: Identificação principal ───────────────────────────────────
    RA = 8.5 * mm
    row_a = [
        ("Central",      v("central"),      16*mm),
        ("Carro N.º",    v("carro_n"),       14*mm),
        ("Marca",        v("marca"),         16*mm),
        ("Matrícula",    v("matricula"),     22*mm),
        ("Empresa",      v("empresa"),       40*mm),
        ("Motorista",    v("motorista_nome"),48*mm),
        ("Nº Folha",     v("numero"),        14*mm),
    ]
    # fill remaining width with Data
    used = sum(w for _, _, w in row_a)
    row_a.append(("Data", data_str, CW - used))

    xc = M
    for lbl, val, w in row_a:
        cell(xc, y, w, RA, label=lbl, value=val, vfs=7.5, bold=True)
        xc += w
    y -= RA

    # ── ROW B: Km + Horas Motor + Horas do Dia ───────────────────────────
    RB = 12 * mm  # altura suficiente para label + valor sem sobreposição

    def subcells(bx, by, bw, bh, group_label, items, fill=LIGHT):
        """Desenha um bloco com label de grupo no topo e sub-células com label+valor."""
        rect(bx, by, bw, bh, fill=fill)
        # label do grupo — topo esquerdo, pequeno
        c.setFillColor(MID); c.setFont("Helvetica", 4.5)
        c.drawString(bx + 1.2*mm, by - 3*mm, group_label)
        # linha separadora sob o group label
        c.setStrokeColor(LINE); c.setLineWidth(0.2)
        c.line(bx, by - 4.5*mm, bx + bw, by - 4.5*mm)
        sub_w = bw / len(items)
        for i, (lbl, val) in enumerate(items):
            sx = bx + i * sub_w
            if i: vline(sx, by - 4.5*mm, by - bh)
            # label da sub-célula
            c.setFillColor(MID); c.setFont("Helvetica", 4)
            c.drawString(sx + 1*mm, by - 6.5*mm, lbl)
            # valor
            c.setFillColor(DARK); c.setFont("Helvetica-Bold", 8)
            c.drawString(sx + 1*mm, by - bh + 2.5*mm, str(val) if val else "")

    # Km
    km_w = 48 * mm
    subcells(M, y, km_w, RB, "Quilómetros", [
        ("Início",     v("km_inicio")),
        ("Fim",        v("km_fim")),
        ("Percorridos",v("km_percorridos")),
    ])

    # Horas Motor
    hm_w = 72 * mm
    hm_x = M + km_w
    subcells(hm_x, y, hm_w, RB, "Horas Motor / Grupo de Bombagem", [
        ("Ini. Motor", v("horas_iniciais_motor")),
        ("Fin. Motor", v("horas_finais_motor")),
        ("Ini. Bomba", v("horas_iniciais_bomba")),
        ("Fin. Bomba", v("horas_finais_bomba")),
    ])

    # Horas do dia — células individuais com o mesmo padrão
    hd_x = hm_x + hm_w
    hd_remaining = CW - (hd_x - M)
    hd_fields = [
        ("Entrada",          v("hora_entrada"),         1),
        ("Almoço",           v("hora_almoco"),          1),
        ("Saída",            v("hora_saida"),           1),
        ("Extras",           v("horas_extras"),         0.8),
        ("Ligou",            v("hora_ligou"),           1),
        ("Desligou",         v("hora_desligou"),        1),
        ("H. Motor desligar",v("horas_motor_desligou"), 1.2),
    ]
    total_parts = sum(p for _, _, p in hd_fields)
    xc = hd_x
    for lbl, val, parts in hd_fields:
        fw = hd_remaining * parts / total_parts
        rect(xc, y, fw, RB, fill=WHITE)
        c.setStrokeColor(LINE); c.setLineWidth(0.2)
        c.line(xc, y - 4.5*mm, xc + fw, y - 4.5*mm)
        c.setFillColor(MID); c.setFont("Helvetica", 4)
        c.drawString(xc + 1*mm, y - 6.5*mm, lbl)
        c.setFillColor(DARK); c.setFont("Helvetica-Bold", 8)
        c.drawString(xc + 1*mm, y - RB + 2.5*mm, str(val) if val else "")
        xc += fw

    y -= RB

    # ── TABELA OBRAS ─────────────────────────────────────────────────────
    col_labels = [
        "Cliente", "Guia/Nota\nServiço", "Designação",
        "Bomb.", "Dir.", "m³", "Mang.\nTubos",
        "Saída\nCentral", "Local da Descarga",
        "Ch.\nObra", "Ini.\nDesc.", "Fim\nDesc.",
        "Saída\nObra", "Ch.\nCentral",
    ]
    # Horas todas iguais a 13mm (6 colunas de hora = 78mm)
    # Fixos: Bomb(6) Dir(6) m³(8) Mang(11) Guia(17) Design(20) = 68mm
    # Restante para Cliente e Local: 283 - 78 - 68 = 137mm → Cliente 55, Local 82
    H_COL = 13 * mm  # largura uniforme para todas as horas
    col_w_mm = [55, 17, 20, 6, 6, 8, 11, H_COL/mm, 82, H_COL/mm, H_COL/mm, H_COL/mm, H_COL/mm, H_COL/mm]
    total = sum(col_w_mm)
    # ajusta Cliente para preencher exatamente CW
    col_w_mm[0] = round(col_w_mm[0] + (CW/mm - total), 1)
    col_w = [w * mm for w in col_w_mm]

    obras = registo.get("obras", [])
    N_ROWS = max(7, len(obras))
    THR_H = 13 * mm   # table header height
    TR_H  = 6.5 * mm  # table row height

    # cabeçalho da tabela
    xc = M
    for lbl, cw in zip(col_labels, col_w):
        rect(xc, y, cw, THR_H, fill=DARK)
        lines = lbl.split("\n")
        lh = 3.2 * mm
        total_h = len(lines) * lh
        sy = y - (THR_H - total_h) / 2 - 3 * mm
        for j, ln in enumerate(lines):
            c.setFillColor(WHITE)
            c.setFont("Helvetica-Bold", 5.2)
            c.drawCentredString(xc + cw / 2, sy - j * lh, ln)
        xc += cw

    # linhas de dados
    for ri in range(N_ROWS):
        ry = y - THR_H - ri * TR_H
        obra = obras[ri] if ri < len(obras) else {}
        row_fill = WHITE if ri % 2 == 0 else LIGHT
        vals = [
            obra.get("cliente",""), obra.get("guia",""), obra.get("designacao",""),
            "●" if obra.get("bombeado") else "", "●" if obra.get("directo") else "",
            obra.get("m3",""), obra.get("mangueiras",""), obra.get("hora_saida_central",""),
            obra.get("local_descarga",""), obra.get("hora_chegada_obra",""),
            obra.get("inicio_descarga",""), obra.get("fim_descarga",""),
            obra.get("hora_saida_obra",""), obra.get("hora_chegada_central",""),
        ]
        xc = M
        for vi, (val, cw) in enumerate(zip(vals, col_w)):
            rect(xc, ry, cw, TR_H, fill=row_fill)
            if val:
                is_bullet = val == "●"
                c.setFillColor(ACCENT if is_bullet else DARK)
                fs = 9 if is_bullet else (6 if len(str(val)) > 12 else 7)
                c.setFont("Helvetica-Bold" if is_bullet else "Helvetica", fs)
                c.drawCentredString(xc + cw / 2, ry - TR_H + 2 * mm, str(val))
            xc += cw
        # nº linha
        c.setFillColor(MID); c.setFont("Helvetica", 5)
        c.drawRightString(M - 1.5*mm, ry - TR_H + 2*mm, str(ri + 1))

    y -= THR_H + N_ROWS * TR_H

    # total m3
    total_m3 = sum(float(o.get("m3") or 0) for o in obras)
    txt(M + CW - 1*mm, y - 3*mm, f"Total: {total_m3:.1f} m³", fs=6.5, bold=True, col=ACCENT, align="right")

    # ── ROW: Gasóleo ─────────────────────────────────────────────────────
    RG = 7 * mm
    y -= RG + 2*mm

    gasoleo = registo.get("gasoleo", [])
    gas_section_w = CW * 0.6
    gas_cols = [
        ("Fornecedor", 0.32), ("Req. Nº", 0.15), ("Litros", 0.13), ("Hora", 0.13), ("Designação", 0.27)
    ]

    # header gasóleo
    rect(M, y, gas_section_w, RG, fill=DARK)
    txt(M + gas_section_w/2, y - RG/2 - 1.5*mm, "Gasóleo / Óleos", fs=5.5, bold=True, col=WHITE, align="center")

    xc = M
    for lbl, pct in gas_cols:
        gw = gas_section_w * pct
        rect(xc, y - RG, gw, RG, fill=LIGHT)
        c.setFillColor(MID); c.setFont("Helvetica", 4.5)
        c.drawCentredString(xc + gw/2, y - RG - 3*mm, lbl)
        xc += gw

    for ri in range(2):
        gas = gasoleo[ri] if ri < len(gasoleo) else {}
        ry = y - RG - (ri + 1) * RG
        xc = M
        for (lbl, pct), val in zip(gas_cols, [
            gas.get("fornecedor",""), gas.get("req_n",""),
            gas.get("litros",""), gas.get("hora",""), gas.get("designacao",""),
        ]):
            gw = gas_section_w * pct
            rect(xc, ry, gw, RG, fill=WHITE if ri==0 else LIGHT)
            if val:
                c.setFillColor(DARK); c.setFont("Helvetica", 7)
                c.drawCentredString(xc + gw/2, ry - RG + 2*mm, str(val))
            xc += gw

    # ── Verificação (à direita do gasóleo) ───────────────────────────────
    ver_x = M + gas_section_w + 4*mm
    ver_w = CW - gas_section_w - 4*mm
    ver_y = y

    rect(ver_x, ver_y, ver_w, RG, fill=DARK)
    txt(ver_x + ver_w/2, ver_y - RG/2 - 1.5*mm, "Verificação da Viatura", fs=5.5, bold=True, col=WHITE, align="center")

    ver_items = [
        ("Limpa Interior",  registo.get("viatura_limpa_int", 0)),
        ("Limpa Exterior",  registo.get("viatura_limpa_ext", 0)),
        ("Lubrificada",     registo.get("viatura_lubrificada", 0)),
        ("Óleo Motor",      registo.get("oleo_motor_ok", 0)),
        ("Óleo Betoneira",  registo.get("oleo_sis_ok", 0)),
        ("Água Radiador",   registo.get("agua_rad_ok", 0)),
    ]
    item_w = ver_w / len(ver_items)
    vxc = ver_x
    for lbl, ok in ver_items:
        rect(vxc, ver_y - RG, item_w, RG * 3, fill=ABLUE if ok else WHITE)
        c.setFillColor(ACCENT if ok else MID)
        c.setFont("Helvetica-Bold" if ok else "Helvetica", 8)
        c.drawCentredString(vxc + item_w/2, ver_y - RG - 5*mm, "✓" if ok else "–")
        c.setFillColor(DARK); c.setFont("Helvetica", 4.5)
        # wrap label
        words = lbl.split()
        if len(words) == 1:
            c.drawCentredString(vxc + item_w/2, ver_y - RG - 12*mm, lbl)
        else:
            c.drawCentredString(vxc + item_w/2, ver_y - RG - 11*mm, " ".join(words[:1]))
            c.drawCentredString(vxc + item_w/2, ver_y - RG - 14.5*mm, " ".join(words[1:]))
        vxc += item_w

    # ── Observações ───────────────────────────────────────────────────────
    obs_y = ver_y - RG * 4
    obs_h = RG * 2
    obs_x = M
    obs_w_total = CW

    rect(obs_x, obs_y, obs_w_total, RG * 0.7, fill=DARK)
    txt(obs_x + 2*mm, obs_y - RG*0.5, "Observações / Avarias", fs=5, bold=True, col=WHITE)

    rect(obs_x, obs_y - RG*0.7, obs_w_total, obs_h, fill=WHITE)
    obs_text = v("observacoes")
    if obs_text:
        words = obs_text.split()
        lines_obs, line = [], ""
        for w in words:
            test = (line + " " + w).strip()
            if c.stringWidth(test, "Helvetica", 7) < obs_w_total - 4*mm:
                line = test
            else:
                lines_obs.append(line); line = w
        if line: lines_obs.append(line)
        for li, ln in enumerate(lines_obs[:3]):
            c.setFillColor(DARK); c.setFont("Helvetica", 7)
            c.drawString(obs_x + 2*mm, obs_y - RG*0.7 - 4*mm - li*4*mm, ln)

    # ── Assinaturas ───────────────────────────────────────────────────────
    sig_y = obs_y - RG*0.7 - obs_h - 1.5*mm
    sig_h = 12 * mm
    sig_labels = ["O Motorista", "O Responsável", "Designação"]
    sig_w = CW / 3
    for i, lbl in enumerate(sig_labels):
        sx = M + i * sig_w
        rect(sx, sig_y, sig_w, sig_h, fill=LIGHT)
        # label topo
        c.setFillColor(MID); c.setFont("Helvetica", 4.5)
        c.drawString(sx + 2*mm, sig_y - 3.5*mm, lbl)
        # linha separadora
        c.setStrokeColor(LINE); c.setLineWidth(0.2)
        c.line(sx, sig_y - 5*mm, sx + sig_w, sig_y - 5*mm)
        # valor em baixo
        if i == 0:
            c.setFillColor(DARK); c.setFont("Helvetica-Bold", 8)
            c.drawString(sx + 2*mm, sig_y - sig_h + 3*mm, v("motorista_nome"))

    # ── Footer ────────────────────────────────────────────────────────────
    c.setFillColor(colors.HexColor("#eeeeee"))
    c.rect(0, 0, W, 5*mm, fill=1, stroke=0)
    c.setFillColor(MID); c.setFont("Helvetica", 4.2)
    c.drawString(M, 2*mm,
        "Solicita-se o registo de todas as movimentações da viatura, incluindo deslocações à oficina, "
        "aos pré-fabricados, lavagens da viatura, entre outras, bem como o preenchimento de todos os campos constantes nesta folha.")
    c.drawRightString(W - M, 2*mm, f"Pragosa Betão  ·  Folha nº {v('numero')}  ·  {data_str}")

    c.save()
    buffer.seek(0)
    return buffer.read()
