#-*- coding:utf-8 -*-

from django.db import models
from datetime import datetime
from django.core.files.storage import FileSystemStorage
import shutil,os


# Create your models here.
class Enseignant(models.Model):
	nom=models.CharField(max_length=200)

	
class Exo(models.Model):
	
	def renommage(instance, nom):
		#nom_fichier = os.path.splitext(nom)[0] # on retire l'extension
		instance.nom=nom
		print(instance.id)
		return("ups/"+str(instance.prof.id)+"/"+str(instance.id)+".exos")
		
	prof = models.ForeignKey(Enseignant)
	fichier = models.FileField(upload_to=renommage, verbose_name="Exos")
	nom = models.CharField(max_length=200)
	
	def __str__(self):
		return self.nom
	
class Qcm(models.Model):
	def renommage(instance, nom):
		return("ups/"+str(instance.prof.id)+"/"+str(instance.id)+"/template.tex")
		
	prof=models.ForeignKey(Enseignant)
	nom=models.CharField(max_length=200)
	date=models.DateTimeField(default=datetime.now())
	exos=models.ManyToManyField(Exo,through='NbExos')
	gen=models.BooleanField(default=0)
	nbpdfs=models.CharField(max_length=200)
	nomTeX=models.CharField(max_length=200,default="Matière - 2014/2015")
	texteTeX=models.CharField(max_length=2000,default="\\centerline{Durée 30 minutes}\n\\medskip \n{\\it \n\\noindent\\underline{La correction est automatisée, \textbf{noircir} les cases des réponses justes et laisser vides les autres cases.} \\\ \nAucun document autorisé, téléphones portables et calculatrices interdits.\\\ \nUn seule réponse juste par exercice. \\\ \nBarème: réponse juste = 1pt, réponse fausse  = -0.5pt \n}")
	template=models.FileField(upload_to=renommage, verbose_name="Template")
	nmax=models.IntegerField(default=0)

	def delete(self, *args, **kwargs):
		try:
			shutil.rmtree(os.path.dirname(self.template.path))
			super(Qcm, self).delete(*args, **kwargs) # Call the "real" save() method.
		except Exception, er:
			print('Impossible de supprimer le dossier du QCM:',er)
		

	def __str__(self):
		return self.nom

class QcmPdf(models.Model):
	qcm = models.ForeignKey(Qcm)
	fichier = models.CharField(max_length=200)
	nom = models.CharField(max_length=200)
	traite = models.BooleanField(default=False)

class NbExos(models.Model):
    nbexos = models.IntegerField()
    qcm = models.ForeignKey(Qcm)
    exo = models.ForeignKey(Exo)
    
class Eleve(models.Model):
	nom=models.CharField(max_length=200)
	
class Copies(models.Model):
	def renommage(instance, nom):
		return("ups/"+str(instance.qcm.prof.id)+"/"+str(instance.qcm.id)+"/copies/"+nom)
	qcm = models.ForeignKey(Qcm)
	fichier = models.FileField(upload_to=renommage, verbose_name="Copies")
	corrigees=models.BooleanField(default=0)
	nom=models.CharField(max_length=200)

class CopieCorrigee(models.Model):
	eleve=models.ForeignKey(Eleve)
	numero=models.IntegerField()
	copies=models.ForeignKey(Copies)
	note=models.FloatField(default=0)
	qcm = models.ForeignKey(Qcm)

class CopieJPG(models.Model):
	fichier = models.CharField(max_length=200)
	copiecorrigee = models.ForeignKey(CopieCorrigee)

	def delete(self, *args, **kwargs):
		try:
			os.remove(self.fichier)
			super(Qcm, self).delete(*args, **kwargs) # Call the "real" save() method.
		except Exception, er:
			print('Impossible de supprimer le dossier du QCM:',er)


