import time
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_appbuilder import AppBuilder, SQLA
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView
from sqlalchemy.exc import OperationalError
from sqlalchemy import JSON
import logging

app = Flask(__name__)

# Configuração da chave secreta para sessões
app.config['SECRET_KEY'] = 'minha_chave_secreta_super_secreta'

# Configuração do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root_password@mariadb/school_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar o banco de dados e o AppBuilder
db = SQLAlchemy(app)
appbuilder = AppBuilder(app, db.session)

# Configuração do log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tentar conectar até o MariaDB estar pronto
attempts = 5
for i in range(attempts):
    try:
        with app.app_context():
            db.create_all()  # Inicializa o banco de dados
            if not appbuilder.sm.find_user(username='admin'):
                appbuilder.sm.add_user(
                    username='admin',
                    first_name='Admin',
                    last_name='User',
                    email='admin@admin.com',
                    role=appbuilder.sm.find_role(appbuilder.sm.auth_role_admin),
                    password='admin'
                )
        logger.info("Banco de dados inicializado com sucesso.")
        break
    except OperationalError:
        if i < attempts - 1:
            logger.warning("Tentativa de conexão com o banco de dados falhou. Tentando novamente em 5 segundos...")
            time.sleep(5)
        else:
            logger.error("Não foi possível conectar ao banco de dados após várias tentativas.")
            raise

# Modelo de Aluno
class Aluno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    sobrenome = db.Column(db.String(80), nullable=False)
    turma = db.Column(db.String(20), nullable=False)
    disciplinas = db.Column(JSON, nullable=False)

# Visão do modelo Aluno
class AlunoModelView(ModelView):
    datamodel = SQLAInterface(Aluno)
    list_columns = ['id', 'nome', 'sobrenome', 'turma', 'disciplinas']

appbuilder.add_view(
    AlunoModelView,
    "Lista de Alunos",
    icon="fa-folder-open-o",
    category="Alunos",
)

# Rota para listar todos os alunos
@app.route('/alunos', methods=['GET'])
def listar_alunos():
    alunos = Aluno.query.all()
    output = [{'id': aluno.id, 'nome': aluno.nome, 'sobrenome': aluno.sobrenome, 'turma': aluno.turma, 'disciplinas': aluno.disciplinas} for aluno in alunos]
    return jsonify(output)

# Rota para adicionar um aluno
@app.route('/alunos', methods=['POST'])
def adicionar_aluno():
    try:
        data = request.get_json()
        # Verificação adicional para garantir que os dados estão corretos
        if not all(key in data for key in ['nome', 'sobrenome', 'turma', 'disciplinas']):
            return jsonify({'erro': 'Dados incompletos.'}), 400
        
        novo_aluno = Aluno(
            nome=data['nome'], 
            sobrenome=data['sobrenome'], 
            turma=data['turma'], 
            disciplinas=data['disciplinas']
        )
        db.session.add(novo_aluno)
        db.session.commit()
        logger.info(f"Aluno {data['nome']} {data['sobrenome']} adicionado com sucesso!")
        return jsonify({'message': 'Aluno adicionado com sucesso!'}), 201
    except Exception as e:
        logger.error(f"Erro ao adicionar aluno: {str(e)}")
        db.session.rollback()
        return jsonify({'erro': 'Erro ao adicionar aluno. Tente novamente mais tarde.'}), 500

# Iniciar a aplicação Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
