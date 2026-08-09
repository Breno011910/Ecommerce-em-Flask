from flask import Flask, render_template

app = Flask(__name__)

# Rotas principais
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/usuarios")
def usuarios():
    return render_template("usuarios.html")

@app.route("/categorias")
def categorias():
    return render_template("categorias.html")

@app.route("/anuncios")
def anuncios():
    return render_template("anuncios.html")

@app.route("/perguntas")
def perguntas():
    return render_template("perguntas.html")

@app.route("/compras")
def compras():
    return render_template("compras.html")

@app.route("/favoritos")
def favoritos():
    return render_template("favoritos.html")

@app.route("/relatorios/vendas")
def relatorio_vendas():
    return render_template("relatorio_vendas.html")

@app.route("/relatorios/compras")
def relatorio_compras():
    return render_template("relatorio_compras.html")


if __name__ == "__main__":
    app.run(debug=True)
