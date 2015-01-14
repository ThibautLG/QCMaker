from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser, User
from prof.models import *
from prof.views import *

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

	def test_nouveautemplate(self):
		request = self.factory.post('/qcmaker',{'titre':'test2'})
		request.user=self.user
		request.session={}
		response = qcmaker(request)
		
		self.assertIsInstance(Qcm.objects.get(nom='test2'),Qcm)
		self.assertIn("test2",response.content)
		self.assertEqual(is_prof(self.prof.nom),True)
		self.assertFalse(Qcm.objects.filter(nom='test2')==[])







