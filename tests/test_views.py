#-*- coding:utf-8 -*-

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser, User
from prof.models import *
from prof.views import *
import os,time
import worker_test

import unittest


class ProfHomeTest(TestCase):
	def setUp(self):
		self.prof = Enseignant(nom='tle-gouic')
		self.prof.save()
      		
		self.factory = RequestFactory()
		self.user = User.objects.create_user(username='tle-gouic')
		
	def test_simple(self):
		request = self.factory.get('/')
		request.user=self.user
		response = home(request)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(is_prof(self.prof.nom),True)

class ProfQcmakerTest(TestCase):
	def setUp(self):
		self.prof = Enseignant(nom='tle-gouic')
		self.prof.save()
      		
		self.qcm = Qcm(prof=self.prof,nom='Test')
		self.qcm.save()
		
		self.factory = RequestFactory()
		self.user = User.objects.create_user(username='tle-gouic')
		
	def test_simple(self):
		request = self.factory.get('qcmaker')
		request.user=self.user
		response = home(request)
		self.assertEqual(response.status_code, 200)
		self.assertIn("tle-gouic",response.content)
		self.assertEqual(is_prof(self.prof.nom),True)

	def test_nouveauqcm(self):
		request = self.factory.post('/qcmaker',{'titre':'test2'})
		request.user=self.user
		request.session={}
		response = qcmaker(request)
		
		self.assertIsInstance(CoreQcm.objects.get(nom='test2'),CoreQcm)
		self.assertIn("test2",response.content)
		self.assertEqual(is_prof(self.prof.nom),True)
		self.assertFalse(CoreQcm.objects.filter(nom='test2')==[])


	def test_ajoutbanque(self):
		""" Ajoute une banque depuis la view home """
		request = self.factory.post('/home',{'nouvellebanque':'Lebesgue'})
		request.user=self.user
		request.session={}
		reponse = home(request)
		self.assertEqual(reponse.status_code, 302)
		self.assertIsInstance(CoreBanque.objects.get(nom='Lebesgue'),CoreBanque)

	def test_ajoutexo(self):
		"""Ajoute un exo dans la banque Lebesgue que l'on vient de creer"""
		request = self.factory.post('/home',{'nouvellebanque':'Lebesgue2'})
		request.user=self.user
		request.session={}
		reponse = home(request)
		self.assertEqual(reponse.status_code, 302)
		self.assertIsInstance(CoreBanque.objects.get(nom='Lebesgue2'),CoreBanque)
		req = request
		request = self.factory.post('/banque',{'nouvelexo':True})
		request.user = self.user
		request.session = req.session
		reponse = banque(request)
		self.assertEqual(reponse.status_code, 302)
		corebanque = CoreBanque.objects.get(nom='Lebesgue2')
		self.assertIsInstance(CoreExo.objects.get(banque=corebanque),CoreExo)
		
	def test_uploadfichierexos(self):
		"""Charge un fichier d'exos dans une nouvelle banque puis génère un qcm"""
		
		request = self.factory.post('/home',{'nouvellebanque':'Lebesgue3'})
		request.user=self.user
		request.session={}
		reponse = home(request)
		self.assertEqual(reponse.status_code, 302)
		self.assertIsInstance(CoreBanque.objects.get(nom='Lebesgue3'),CoreBanque)
		req = request
	
		print(os.getcwd())
		with open('tests/Lebesgue1.exos') as fp:
			request = self.factory.post('/banque',{'fichierexos':fp})
		request.user = self.user
		request.session = req.session
		reponse = banque(request)
		corebanque = CoreBanque.objects.get(nom='Lebesgue3')
		worker_test.launch()
		self.assertEqual(len(CoreExo.objects.filter(banque=corebanque)),12)
		self.assertEqual(len(CoreExo.objects.filter(banque=corebanque,erreurtex=False)),12)




