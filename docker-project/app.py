import time
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_appbuilder import AppBuilder, SQLA
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView
from sqlalchemy.exc import OperationalError
import logging

app = Flask(__name__)

# Configuração da chave secreta para sessões
app.config['SECRET_KEY'] = 'minha_chave_secreta_super_secreta'  # Substitua por uma chave segura

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root_password@mariadb/school_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar o banco de dados e o AppBuilder
db = SQLAlchemy(app)
appbuilder = AppBuilder(app, db.session)

# Configuração do log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Função para verificar e criar a tabela 'aluno' explicitamente
def verificar_criar_tabela_aluno():
    # Criação da tabela se não existir
    if not db.engine.has_table('aluno'):
        logger.warning("Tabela 'aluno' não encontrada. Tentando criar tabela manualmente.")
        db.create_all()
        if db.engine.has_table('aluno'):
            logger.info("Tabela 'aluno' criada com sucesso.")
        else:
            logger.error("Falha ao criar a tabela 'aluno'.")


# Tentativa de conectar até o MariaDB estar pronto e criar as tabelas
attempts = 20  # Aumentado o número de tentativas para garantir mais tempo para o MariaDB inicializar
for i in range(attempts):
    try:
        with app.app_context():
            # Criar todas as tabelas
            db.create_all()
            
            # Log das tabelas atualmente no banco de dados
            tables = db.engine.table_names()
            logger.info("Tabelas atuais no banco de dados: %s", tables)
            
              # Confirmação se a tabela Aluno existe
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"Tabelas atuais no banco de dados: {tables}")

            # Verificar se a tabela 'aluno' foi criada
            if 'aluno' in tables:
                logger.info("Tabela 'Aluno' criada com sucesso.")
            else:
                logger.warning("Tabela 'Aluno' não foi encontrada no banco de dados.")
            
            # Criar um usuário administrador padrão, se ainda não existir
            if not appbuilder.sm.find_user(username='admin'):
                appbuilder.sm.add_user(
                    username='admin',
                    first_name='Admin',
                    last_name='User',
                    email='admin@admin.com',
                    role=appbuilder.sm.find_role(appbuilder.sm.auth_role_admin),
                    password='lil'
                )
            logger.info("Banco de dados inicializado com sucesso.")
        break
    except OperationalError:
        if i < attempts - 1:
            logger.warning("Tentativa de conexão com o banco de dados falhou. Tentando novamente em 5 segundos...")
            time.sleep(5)  # Aguarda 5 segundos antes de tentar novamente
        else:
            logger.error("Não foi possível conectar ao banco de dados após várias tentativas.")
            raise

# Modelo de Aluno - Definição da tabela 'Aluno' no banco de dados
class Aluno(db.Model):
    __tablename__ = 'aluno'  # Definindo o nome explícito da tabela
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    sobrenome = db.Column(db.String(50), nullable=False)
    turma = db.Column(db.String(50), nullable=False)
    disciplinas = db.Column(db.String(200), nullable=False)

# Visão do modelo Aluno para o painel administrativo
class AlunoModelView(ModelView):
    datamodel = SQLAInterface(Aluno)
    list_columns = ['id', 'nome', 'sobrenome', 'turma', 'disciplinas']

# Adicionar a visão do modelo ao AppBuilder
appbuilder.add_view(
    AlunoModelView,
    "Lista de Alunos",
    icon="fa-folder-open-o",
    category="Alunos",
)

# Função para verificar e criar a tabela 'aluno' explicitamente
def verificar_criar_tabela_aluno():
    # Criação da tabela se não existir
    if not db.engine.has_table('aluno'):
        logger.warning("Tabela 'aluno' não encontrada. Tentando criar tabela manualmente.")
        db.create_all()
        if db.engine.has_table('aluno'):
            logger.info("Tabela 'aluno' criada com sucesso.")
        else:
            logger.error("Falha ao criar a tabela 'aluno'.")


# Rota para listar todos os alunos - Método GET
@app.route('/alunos', methods=['GET'])
def listar_alunos():
    alunos = Aluno.query.all()
    output = [{'id': aluno.id, 'nome': aluno.nome, 'sobrenome': aluno.sobrenome, 'turma': aluno.turma, 'disciplinas': aluno.disciplinas} for aluno in alunos]
    return jsonify(output)

# Rota para adicionar um aluno - Método POST
@app.route('/alunos', methods=['POST'])
def adicionar_aluno():
    data = request.get_json()
    novo_aluno = Aluno(nome=data['nome'], sobrenome=data['sobrenome'], turma=data['turma'], disciplinas=data['disciplinas'])
    db.session.add(novo_aluno)
    db.session.commit()
    logger.info(f"Aluno {data['nome']} {data['sobrenome']} adicionado com sucesso!")
    return jsonify({'message': 'Aluno adicionado com sucesso!'}), 201

# Rota para criar um novo usuário - Método POST
@app.route('/usuarios', methods=['POST'])
def criar_usuario():
    data = request.get_json()
    username = data.get('username')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    password = data.get('password')
    role_name = data.get('role', 'Public')  # Define 'Public' como padrão, caso o papel não seja fornecido

    # Busca o papel do usuário no sistema de autenticação do AppBuilder
    role = appbuilder.sm.find_role(role_name)
    if not role:
        return jsonify({'error': f"Papel '{role_name}' não encontrado."}), 400

    # Verifica se o usuário já existe
    if appbuilder.sm.find_user(username=username):
        return jsonify({'error': 'Usuário já existe.'}), 400

    # Cria o novo usuário
    try:
        appbuilder.sm.add_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role,
            password=password
        )
        logger.info(f"Usuário {username} criado com sucesso!")
        return jsonify({'message': 'Usuário criado com sucesso!'}), 201
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {e}")
        return jsonify({'error': 'Erro ao criar usuário.'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
 