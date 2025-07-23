from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf import CSRFProtect
from flask_login import UserMixin

# Cria a aplicação Flask
app = Flask(__name__)

# Configuração do banco de dados SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///comunidade.db"

# Chave secreta usada para segurança de sessões e formulários
app.config["SECRET_KEY"] = "chave_segura_grande"

# Pasta para uploads de imagens (ex: avatares de usuários)
app.config["UPLOAD_FOLDER"] = r"static/assets/images"

# Proteção contra ataques CSRF (Cross Site Request Forgery)
csrf = CSRFProtect(app)

# Inicializa o SQLAlchemy (ORM para o banco de dados)
database = SQLAlchemy(app)

# Inicializa o Bcrypt (para hash de senhas)
bcrypt = Bcrypt(app)

# Gerenciador de login do Flask-Login
login_manager = LoginManager(app)

# Define para onde o usuário será redirecionado se não estiver logado
login_manager.login_view = "login"

# Importa as rotas da aplicação (deve ficar no final para evitar importações circulares)
from Infinity import routes
