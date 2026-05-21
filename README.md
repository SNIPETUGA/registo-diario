# Registo Diário — Pragosa / Betão

App para registar o diário do motorista: obras, quilómetros, horas de motor, verificação da viatura e exportação para PDF.

---

## Como instalar e correr (primeira vez)

### 1. Instalar Python
Se ainda não tens, vai a https://python.org e instala a versão 3.11 ou superior.

### 2. Abrir o terminal na pasta do projeto
```
cd registo_diario
```

### 3. Criar um ambiente virtual (boa prática)
```
python -m venv venv
```

Activar:
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

### 4. Instalar as dependências
```
pip install -r requirements.txt
```

### 5. Correr a app
```
python app.py
```

Abre o browser em: **http://localhost:5000**

---

## Como usar nas próximas vezes

```
cd registo_diario
venv\Scripts\activate      # Windows
python app.py
```

---

## Estrutura do projeto

```
registo_diario/
│
├── app.py                  # Servidor Flask (backend)
├── pdf_generator.py        # Gerador de PDFs
├── requirements.txt        # Dependências Python
│
├── db/
│   └── registos.db         # Base de dados SQLite (criada automaticamente)
│
├── templates/
│   └── index.html          # Página web
│
└── static/
    ├── css/style.css        # Estilos
    └── js/app.js            # Lógica frontend
```

---

## O que faz cada ficheiro

| Ficheiro | O que faz |
|---|---|
| `app.py` | Recebe pedidos do browser, guarda/lê da base de dados, envia PDFs |
| `pdf_generator.py` | Cria o PDF com o formato da folha original |
| `index.html` | O que o utilizador vê no browser |
| `style.css` | Cores, tamanhos, layout |
| `app.js` | Botões, formulários, comunicação com o servidor |
| `registos.db` | Base de dados com todos os registos guardados |
