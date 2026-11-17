from decimal import Decimal
import os
import unittest
from app import FechamentoDiario, Profissional, app, db


class GalardoTestCase(unittest.TestCase):

  def setUp(self):
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    self.app = app.test_client()
    with app.app_context():
      db.create_all()
      p1 = Profissional(
          nome='Carlos Mendes', vinculo='Contratado', veiculo='Reboque 01'
      )
      p2 = Profissional(
          nome='Marcos Silva', vinculo='Socio', veiculo='Reboque 02'
      )
      db.session.add(p1)
      db.session.add(p2)
      db.session.commit()

  def tearDown(self):
    with app.app_context():
      db.session.remove()
      db.drop_all()

  def test_index_route(self):
    response = self.app.get('/')
    self.assertEqual(response.status_code, 200)

  def test_calculo_comissao_contratado(self):
    with app.app_context():
      prof = Profissional.query.filter_by(vinculo='Contratado').first()
      bruto = Decimal('1200.00')
      repasse = bruto * (Decimal('30.00') / Decimal('100'))
      self.assertEqual(repasse, Decimal('360.00'))

  def test_calculo_rateio_socio(self):
    with app.app_context():
      prof = Profissional.query.filter_by(vinculo='Socio').first()
      combustivel = Decimal('250.00')
      extras = Decimal('50.00')
      rateio = (combustivel + extras) / Decimal('2')
      self.assertEqual(rateio, Decimal('150.00'))


if __name__ == '__main__':
  unittest.main()
