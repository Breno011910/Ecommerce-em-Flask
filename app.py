from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps


app = Flask(__name__)

app.config["SECRET_KEY"] = "chave-secreta"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ecommerce.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)

login_manager.login_view = "login"
login_manager.login_message = "Você precisa estar logado para acessar esta página."
login_manager.login_message_category = "danger"


# =========================
# MODELOS
# =========================

class Usuario(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)
    data_cadastro = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    anuncios = db.relationship(
        "Anuncio",
        backref="proprietario",
        lazy=True
    )

    perguntas = db.relationship(
        "Pergunta",
        backref="autor",
        lazy=True
    )

    compras = db.relationship(
        "Compra",
        backref="comprador",
        lazy=True
    )

    favoritos = db.relationship(
        "Favorito",
        backref="usuario",
        lazy=True,
        cascade="all, delete-orphan"
    )


@login_manager.user_loader
def carregar_usuario(user_id):

    return db.session.get(
        Usuario,
        int(user_id)
    )


class Categoria(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nome = db.Column(
        db.String(80),
        unique=True,
        nullable=False
    )

    descricao = db.Column(
        db.String(255)
    )

    anuncios = db.relationship(
        "Anuncio",
        backref="categoria",
        lazy=True
    )


class Anuncio(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    titulo = db.Column(
        db.String(120),
        nullable=False
    )

    descricao = db.Column(
        db.Text,
        nullable=False
    )

    preco = db.Column(
        db.Float,
        nullable=False
    )

    quantidade = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Ativo"
    )

    data_publicacao = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id"),
        nullable=False
    )

    categoria_id = db.Column(
        db.Integer,
        db.ForeignKey("categoria.id"),
        nullable=False
    )

    perguntas = db.relationship(
        "Pergunta",
        backref="anuncio",
        lazy=True,
        cascade="all, delete-orphan"
    )

    compras = db.relationship(
        "Compra",
        backref="anuncio",
        lazy=True,
        cascade="all, delete-orphan"
    )

    favoritos = db.relationship(
        "Favorito",
        backref="anuncio",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Pergunta(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    texto = db.Column(
        db.Text,
        nullable=False
    )

    resposta = db.Column(
        db.Text
    )

    data_pergunta = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    data_resposta = db.Column(
        db.DateTime
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id"),
        nullable=False
    )

    anuncio_id = db.Column(
        db.Integer,
        db.ForeignKey("anuncio.id"),
        nullable=False
    )


class Compra(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    data_compra = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    quantidade = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )

    valor_unitario = db.Column(
        db.Float,
        nullable=False
    )

    valor_total = db.Column(
        db.Float,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        nullable=False,
        default="Concluída"
    )

    comprador_id = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id"),
        nullable=False
    )

    anuncio_id = db.Column(
        db.Integer,
        db.ForeignKey("anuncio.id"),
        nullable=False
    )


class Favorito(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    data_favorito = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    usuario_id = db.Column(
        db.Integer,
        db.ForeignKey("usuario.id"),
        nullable=False
    )

    anuncio_id = db.Column(
        db.Integer,
        db.ForeignKey("anuncio.id"),
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            "usuario_id",
            "anuncio_id",
            name="uq_usuario_anuncio_favorito"
        ),
    )


# =========================
# AUTENTICAÇÃO
# =========================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if current_user.is_authenticated:
        return redirect(
            url_for("index")
        )

    if request.method == "POST":

        email = request.form["email"]
        senha = request.form["senha"]

        usuario = Usuario.query.filter_by(
            email=email
        ).first()

        if usuario and check_password_hash(
            usuario.senha,
            senha
        ):

            login_user(usuario)

            flash(
                "Login realizado com sucesso.",
                "success"
            )

            return redirect(
                url_for("index")
            )

        flash(
            "E-mail ou senha incorretos.",
            "danger"
        )

    return render_template(
        "login.html"
    )

# ==============================
# CADASTRO
#===============================

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if current_user.is_authenticated:
        return redirect(
            url_for("index")
        )

    if request.method == "POST":

        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]

        usuario_existente = Usuario.query.filter_by(
            email=email
        ).first()

        if usuario_existente:
            flash(
                "Este e-mail já está cadastrado.",
                "danger"
            )

            return redirect(
                url_for("cadastro")
            )

        senha_hash = generate_password_hash(
            senha
        )

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha=senha_hash
        )

        db.session.add(
            novo_usuario
        )

        db.session.commit()

        flash(
            "Cadastro realizado com sucesso. Faça login.",
            "success"
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "cadastro.html"
    )

@app.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "Você saiu do sistema.",
        "success"
    )

    return redirect(
        url_for("login")
    )


# =========================
# PÁGINA INICIAL
# =========================

@app.route("/")
def index():

    return render_template(
        "index.html",
        total_usuarios=Usuario.query.count(),
        total_categorias=Categoria.query.count(),
        total_anuncios=Anuncio.query.count(),
        total_compras=Compra.query.count()
    )


# =========================
# USUÁRIOS
# =========================

@app.route("/usuarios")
@login_required
def usuarios():

    registros = Usuario.query.order_by(
        Usuario.id.desc()
    ).all()

    return render_template(
        "usuarios/lista.html",
        registros=registros
    )


@app.route(
    "/usuarios/novo",
    methods=["GET", "POST"]
)
@login_required
def usuario_novo():

    if request.method == "POST":

        senha_hash = generate_password_hash(
            request.form["senha"]
        )

        usuario = Usuario(
            nome=request.form["nome"],
            email=request.form["email"],
            senha=senha_hash
        )

        db.session.add(usuario)

        try:

            db.session.commit()

            flash(
                "Usuário cadastrado com sucesso.",
                "success"
            )

            return redirect(
                url_for("usuarios")
            )

        except Exception:

            db.session.rollback()

            flash(
                "Erro ao cadastrar usuário. "
                "Verifique se o e-mail já existe.",
                "danger"
            )

    return render_template(
        "usuarios/form.html",
        registro=None
    )


@app.route(
    "/usuarios/editar/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def usuario_editar(id):

    registro = db.get_or_404(
        Usuario,
        id
    )

    if request.method == "POST":

        registro.nome = request.form["nome"]
        registro.email = request.form["email"]

        registro.senha = generate_password_hash(
            request.form["senha"]
        )

        try:

            db.session.commit()

            flash(
                "Usuário atualizado com sucesso.",
                "success"
            )

            return redirect(
                url_for("usuarios")
            )

        except Exception:

            db.session.rollback()

            flash(
                "Erro ao atualizar usuário.",
                "danger"
            )

    return render_template(
        "usuarios/form.html",
        registro=registro
    )


@app.post("/usuarios/excluir/<int:id>")
@login_required
def usuario_excluir(id):

    registro = db.get_or_404(
        Usuario,
        id
    )

    db.session.delete(registro)

    try:

        db.session.commit()

        flash(
            "Usuário excluído com sucesso.",
            "success"
        )

    except Exception:

        db.session.rollback()

        flash(
            "Não foi possível excluir este usuário.",
            "danger"
        )

    return redirect(
        url_for("usuarios")
    )


# =========================
# CATEGORIAS
# =========================

@app.route("/categorias")
@login_required
def categorias():

    registros = Categoria.query.order_by(
        Categoria.nome
    ).all()

    return render_template(
        "categorias/lista.html",
        registros=registros
    )


@app.route(
    "/categorias/novo",
    methods=["GET", "POST"]
)
@login_required
def categoria_novo():

    if request.method == "POST":

        categoria = Categoria(
            nome=request.form["nome"],
            descricao=request.form["descricao"]
        )

        db.session.add(categoria)

        try:

            db.session.commit()

            flash(
                "Categoria cadastrada com sucesso.",
                "success"
            )

            return redirect(
                url_for("categorias")
            )

        except Exception:

            db.session.rollback()

            flash(
                "Erro ao cadastrar categoria.",
                "danger"
            )

    return render_template(
        "categorias/form.html",
        registro=None
    )


@app.route(
    "/categorias/editar/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def categoria_editar(id):

    registro = db.get_or_404(
        Categoria,
        id
    )

    if request.method == "POST":

        registro.nome = request.form["nome"]
        registro.descricao = request.form["descricao"]

        try:

            db.session.commit()

            flash(
                "Categoria atualizada com sucesso.",
                "success"
            )

            return redirect(
                url_for("categorias")
            )

        except Exception:

            db.session.rollback()

            flash(
                "Erro ao atualizar categoria.",
                "danger"
            )

    return render_template(
        "categorias/form.html",
        registro=registro
    )


@app.post("/categorias/excluir/<int:id>")
@login_required
def categoria_excluir(id):

    registro = db.get_or_404(
        Categoria,
        id
    )

    if registro.anuncios:

        flash(
            "Não é possível excluir uma categoria "
            "que possui anúncios.",
            "danger"
        )

        return redirect(
            url_for("categorias")
        )

    db.session.delete(registro)

    db.session.commit()

    flash(
        "Categoria excluída com sucesso.",
        "success"
    )

    return redirect(
        url_for("categorias")
    )


# =========================
# ANÚNCIOS
# =========================

@app.route("/anuncios")
@login_required
def anuncios():

    registros = Anuncio.query.order_by(
        Anuncio.id.desc()
    ).all()

    return render_template(
        "anuncios/lista.html",
        registros=registros
    )


@app.route("/anuncios/<int:id>")
@login_required
def anuncio_detalhes(id):

    anuncio = db.get_or_404(
        Anuncio,
        id
    )

    return render_template(
        "anuncios/detalhes.html",
        anuncio=anuncio
    )


@app.route(
    "/anuncios/novo",
    methods=["GET", "POST"]
)
@login_required
def anuncio_novo():

    usuarios = Usuario.query.order_by(
        Usuario.nome
    ).all()

    categorias = Categoria.query.order_by(
        Categoria.nome
    ).all()

    if request.method == "POST":

        anuncio = Anuncio(
            titulo=request.form["titulo"],
            descricao=request.form["descricao"],
            preco=float(request.form["preco"]),
            quantidade=int(request.form["quantidade"]),
            status=request.form["status"],
            usuario_id=int(
                request.form["usuario_id"]
            ),
            categoria_id=int(
                request.form["categoria_id"]
            )
        )

        db.session.add(anuncio)

        db.session.commit()

        flash(
            "Anúncio cadastrado com sucesso.",
            "success"
        )

        return redirect(
            url_for("anuncios")
        )

    return render_template(
        "anuncios/form.html",
        registro=None,
        usuarios=usuarios,
        categorias=categorias
    )


@app.route(
    "/anuncios/editar/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def anuncio_editar(id):

    registro = db.get_or_404(
        Anuncio,
        id
    )

    usuarios = Usuario.query.order_by(
        Usuario.nome
    ).all()

    categorias = Categoria.query.order_by(
        Categoria.nome
    ).all()

    if request.method == "POST":

        registro.titulo = request.form["titulo"]
        registro.descricao = request.form["descricao"]

        registro.preco = float(
            request.form["preco"]
        )

        registro.quantidade = int(
            request.form["quantidade"]
        )

        registro.status = request.form["status"]

        registro.usuario_id = int(
            request.form["usuario_id"]
        )

        registro.categoria_id = int(
            request.form["categoria_id"]
        )

        db.session.commit()

        flash(
            "Anúncio atualizado com sucesso.",
            "success"
        )

        return redirect(
            url_for("anuncios")
        )

    return render_template(
        "anuncios/form.html",
        registro=registro,
        usuarios=usuarios,
        categorias=categorias
    )


@app.post("/anuncios/excluir/<int:id>")
@login_required
def anuncio_excluir(id):

    registro = db.get_or_404(
        Anuncio,
        id
    )

    db.session.delete(registro)

    db.session.commit()

    flash(
        "Anúncio excluído com sucesso.",
        "success"
    )

    return redirect(
        url_for("anuncios")
    )


# =========================
# PERGUNTAS
# =========================

@app.route("/perguntas")
@login_required
def perguntas():

    registros = Pergunta.query.order_by(
        Pergunta.id.desc()
    ).all()

    return render_template(
        "perguntas/lista.html",
        registros=registros
    )


@app.route(
    "/perguntas/novo",
    methods=["GET", "POST"]
)
@login_required
def pergunta_novo():

    usuarios = Usuario.query.order_by(
        Usuario.nome
    ).all()

    anuncios = Anuncio.query.order_by(
        Anuncio.titulo
    ).all()

    if request.method == "POST":

        pergunta = Pergunta(
            texto=request.form["texto"],
            usuario_id=int(
                request.form["usuario_id"]
            ),
            anuncio_id=int(
                request.form["anuncio_id"]
            )
        )

        db.session.add(pergunta)

        db.session.commit()

        flash(
            "Pergunta cadastrada com sucesso.",
            "success"
        )

        return redirect(
            url_for("perguntas")
        )

    return render_template(
        "perguntas/form.html",
        registro=None,
        usuarios=usuarios,
        anuncios=anuncios
    )


@app.route(
    "/perguntas/editar/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def pergunta_editar(id):

    registro = db.get_or_404(
        Pergunta,
        id
    )

    usuarios = Usuario.query.order_by(
        Usuario.nome
    ).all()

    anuncios = Anuncio.query.order_by(
        Anuncio.titulo
    ).all()

    if request.method == "POST":

        registro.texto = request.form["texto"]

        registro.usuario_id = int(
            request.form["usuario_id"]
        )

        registro.anuncio_id = int(
            request.form["anuncio_id"]
        )

        db.session.commit()

        flash(
            "Pergunta atualizada com sucesso.",
            "success"
        )

        return redirect(
            url_for("perguntas")
        )

    return render_template(
        "perguntas/form.html",
        registro=registro,
        usuarios=usuarios,
        anuncios=anuncios
    )


@app.route(
    "/perguntas/responder/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def pergunta_responder(id):

    registro = db.get_or_404(
        Pergunta,
        id
    )

    if request.method == "POST":

        registro.resposta = request.form["resposta"]

        registro.data_resposta = datetime.utcnow()

        db.session.commit()

        flash(
            "Resposta cadastrada com sucesso.",
            "success"
        )

        return redirect(
            url_for("perguntas")
        )

    return render_template(
        "perguntas/responder.html",
        registro=registro
    )


@app.post("/perguntas/excluir/<int:id>")
@login_required
def pergunta_excluir(id):

    registro = db.get_or_404(
        Pergunta,
        id
    )

    db.session.delete(registro)

    db.session.commit()

    flash(
        "Pergunta excluída com sucesso.",
        "success"
    )

    return redirect(
        url_for("perguntas")
    )


# =========================
# COMPRAS
# =========================

@app.route("/compras")
@login_required
def compras():

    registros = Compra.query.order_by(
        Compra.id.desc()
    ).all()

    return render_template(
        "compras/lista.html",
        registros=registros
    )


@app.route(
    "/compras/novo",
    methods=["GET", "POST"]
)
@login_required
def compra_novo():

    anuncios = Anuncio.query.filter_by(
        status="Ativo"
    ).order_by(
        Anuncio.titulo
    ).all()

    if request.method == "POST":

        anuncio = db.get_or_404(
            Anuncio,
            int(request.form["anuncio_id"])
        )

        quantidade = int(
            request.form["quantidade"]
        )

        # Verifica se o anúncio ainda está disponível
        if anuncio.status != "Ativo":

            flash(
                "Este anúncio não está mais disponível.",
                "danger"
            )

            return redirect(
                url_for("compras")
            )

        # Impede o usuário de comprar o próprio anúncio
        if anuncio.usuario_id == current_user.id:

            flash(
                "Você não pode comprar o seu próprio anúncio.",
                "danger"
            )

            return redirect(
                url_for("compras")
            )

        # Verifica quantidade
        if (
            quantidade <= 0
            or quantidade > anuncio.quantidade
        ):

            flash(
                "Quantidade inválida ou superior ao estoque.",
                "danger"
            )

            return render_template(
                "compras/form.html",
                registro=None,
                anuncios=anuncios
            )

        # Cria a compra usando automaticamente
        # o usuário que está logado
        compra = Compra(
            quantidade=quantidade,
            valor_unitario=anuncio.preco,
            valor_total=anuncio.preco * quantidade,
            status="Concluída",
            comprador_id=current_user.id,
            anuncio_id=anuncio.id
        )

        # Atualiza o estoque
        anuncio.quantidade -= quantidade

        # Se acabou o estoque, marca como vendido
        if anuncio.quantidade == 0:
            anuncio.status = "Vendido"

        db.session.add(compra)

        db.session.commit()

        flash(
            "Compra realizada com sucesso.",
            "success"
        )

        return redirect(
            url_for("compras")
        )

    return render_template(
        "compras/form.html",
        registro=None,
        anuncios=anuncios
    )


@app.route(
    "/compras/editar/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def compra_editar(id):

    registro = db.get_or_404(
        Compra,
        id
    )

    usuarios = Usuario.query.order_by(
        Usuario.nome
    ).all()

    anuncios = Anuncio.query.order_by(
        Anuncio.titulo
    ).all()

    if request.method == "POST":

        registro.quantidade = int(
            request.form["quantidade"]
        )

        registro.valor_unitario = float(
            request.form["valor_unitario"]
        )

        registro.valor_total = (
            registro.quantidade
            * registro.valor_unitario
        )

        registro.status = request.form["status"]

        registro.comprador_id = int(
            request.form["comprador_id"]
        )

        registro.anuncio_id = int(
            request.form["anuncio_id"]
        )

        db.session.commit()

        flash(
            "Compra atualizada com sucesso.",
            "success"
        )

        return redirect(
            url_for("compras")
        )

    return render_template(
        "compras/form.html",
        registro=registro,
        usuarios=usuarios,
        anuncios=anuncios
    )


@app.post("/compras/excluir/<int:id>")
@login_required
def compra_excluir(id):

    registro = db.get_or_404(
        Compra,
        id
    )

    db.session.delete(registro)

    db.session.commit()

    flash(
        "Compra excluída com sucesso.",
        "success"
    )

    return redirect(
        url_for("compras")
    )


# =========================
# FAVORITOS
# =========================

@app.route("/favoritos")
@login_required
def favoritos():

    registros = Favorito.query.order_by(
        Favorito.id.desc()
    ).all()

    return render_template(
        "favoritos/lista.html",
        registros=registros
    )


@app.route(
    "/favoritos/novo",
    methods=["GET", "POST"]
)
@login_required
def favorito_novo():

    usuarios = Usuario.query.order_by(
        Usuario.nome
    ).all()

    anuncios = Anuncio.query.order_by(
        Anuncio.titulo
    ).all()

    if request.method == "POST":

        usuario_id = int(
            request.form["usuario_id"]
        )

        anuncio_id = int(
            request.form["anuncio_id"]
        )

        existente = Favorito.query.filter_by(
            usuario_id=usuario_id,
            anuncio_id=anuncio_id
        ).first()

        if existente:

            flash(
                "Esse anúncio já está nos favoritos.",
                "danger"
            )

            return render_template(
                "favoritos/form.html",
                registro=None,
                usuarios=usuarios,
                anuncios=anuncios
            )

        favorito = Favorito(
            usuario_id=usuario_id,
            anuncio_id=anuncio_id
        )

        db.session.add(favorito)

        db.session.commit()

        flash(
            "Favorito cadastrado com sucesso.",
            "success"
        )

        return redirect(
            url_for("favoritos")
        )

    return render_template(
        "favoritos/form.html",
        registro=None,
        usuarios=usuarios,
        anuncios=anuncios
    )


@app.route(
    "/favoritos/editar/<int:id>",
    methods=["GET", "POST"]
)
@login_required
def favorito_editar(id):

    registro = db.get_or_404(
        Favorito,
        id
    )

    usuarios = Usuario.query.order_by(
        Usuario.nome
    ).all()

    anuncios = Anuncio.query.order_by(
        Anuncio.titulo
    ).all()

    if request.method == "POST":

        registro.usuario_id = int(
            request.form["usuario_id"]
        )

        registro.anuncio_id = int(
            request.form["anuncio_id"]
        )

        db.session.commit()

        flash(
            "Favorito atualizado com sucesso.",
            "success"
        )

        return redirect(
            url_for("favoritos")
        )

    return render_template(
        "favoritos/form.html",
        registro=registro,
        usuarios=usuarios,
        anuncios=anuncios
    )


@app.post("/favoritos/excluir/<int:id>")
@login_required
def favorito_excluir(id):

    registro = db.get_or_404(
        Favorito,
        id
    )

    db.session.delete(registro)

    db.session.commit()

    flash(
        "Favorito excluído com sucesso.",
        "success"
    )

    return redirect(
        url_for("favoritos")
    )


# =========================
# RELATÓRIOS
# =========================

@app.route("/relatorios/vendas")
@login_required
def relatorio_vendas():

    registros = Compra.query.order_by(
        Compra.data_compra.desc()
    ).all()

    return render_template(
        "relatorios/vendas.html",
        registros=registros
    )


@app.route("/relatorios/compras")
@login_required
def relatorio_compras():

    registros = Compra.query.order_by(
        Compra.data_compra.desc()
    ).all()

    return render_template(
        "relatorios/compras.html",
        registros=registros
    )


# =========================
# BANCO DE DADOS
# =========================

with app.app_context():

    db.create_all()


# =========================
# EXECUÇÃO
# =========================

if __name__ == "__main__":

    app.run(debug=True)