from datetime import datetime
from decimal import Decimal
import os
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY', 'galardo-secret-key-2026-secure'
)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///galardo.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Modelos de Dados (SQLAlchemy)
class Profissional(db.Model):
  __tablename__ = 'profissional'
  id = db.Column(db.Integer, primary_key=True)
  nome = db.Column(db.String(100), nullable=False)
  vinculo = db.Column(db.String(50), nullable=False)  # Contratado ou Socio
  percentual_comissao = db.Column(db.Numeric(5, 2), default=30.00)
  veiculo = db.Column(db.String(50), nullable=False)
  fechamentos = db.relationship(
      'FechamentoDiario', backref='profissional', lazy=True
  )


class FechamentoDiario(db.Model):
  __tablename__ = 'fechamento_diario'
  id = db.Column(db.Integer, primary_key=True)
  data_fechamento = db.Column(db.Date, nullable=False, default=datetime.utcnow)
  profissional_id = db.Column(
      db.Integer, db.foreign_key('profissional.id'), nullable=False
  )
  valor_bruto = db.Column(db.Numeric(10, 2), nullable=False)
  combustivel = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
  despesas_extras = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
  repasse_calculado = db.Column(db.Numeric(10, 2), nullable=False)
  saldo_liquido = db.Column(db.Numeric(10, 2), nullable=False)
  observacao = db.Column(db.String(255))


with app.app_context():
  db.create_all()


# Rotas do MVP (MVC)
@app.route('/')
def index():
  profissionais = Profissional.query.all()
  return render_template('index.html', profissionais=profissionais)


@app.route('/fechamento', methods=['GET', 'POST'])
def fechamento():
  profissionais = Profissional.query.all()
  if request.method == 'POST':
    try:
      prof_id = int(request.form.get('profissional_id'))
      bruto = Decimal(request.form.get('valor_bruto', '0'))
      comb = Decimal(request.form.get('combustivel', '0'))
      extras = Decimal(request.form.get('despesas_extras', '0'))
      obs = request.form.get('observacao', '')

      if bruto < 0 or comb < 0 or extras < 0:
        flash(
            'Erro: Os valores financeiros nao podem ser negativos.', 'danger'
        )
        return redirect(url_for('fechamento'))

      prof = Profissional.query.get_or_404(prof_id)

      # Regra de Negocio: Contratado = 30% bruto sem desconto; Socio = rateio 50% custos
      if prof.vinculo == 'Contratado':
        repasse = bruto * (prof.percentual_comissao / Decimal('100'))
        saldo = bruto - repasse
      else:
        # Socio: divide 50% de combustivel e extras
        total_despesas = comb + extras
        rateio_despesas = total_despesas / Decimal('2')
        repasse = rateio_despesas
        saldo = bruto - repasse

      novo_fecho = FechamentoDiario(
          profissional_id=prof.id,
          valor_bruto=bruto,
          combustivel=comb,
          despesas_extras=extras,
          repasse_calculado=repasse,
          saldo_liquido=saldo,
          observacao=obs,
      )
      db.session.add(novo_fecho)
      db.session.commit()

      flash(
          f'Fecho gravado com sucesso! Repasse: R$ {repasse:.2f} | Saldo Empresa:'
          f' R$ {saldo:.2f}',
          'success',
      )
      return redirect(url_for('historico'))
    except Exception as e:
      flash(f'Erro ao processar o fecho: {str(e)}', 'danger')

  return render_template('fechamento.html', profissionais=profissionais)


@app.route('/historico')
def historico():
  fechamentos = FechamentoDiario.query.order_by(
      FechamentoDiario.data_fechamento.desc()
  ).all()
  return render_template('historico.html', fechamentos=fechamentos)


if __name__ == '__main__':
  app.run(debug=True)
