#-*- coding:utf-8 -*-

from django.db import models
from datetime import datetime
from django.core.files.storage import FileSystemStorage
import shutil,os

# Modeles pour le core.py
class Enseignant(models.Model):
	nom=models.CharField(max_length=200)
    
class Eleve(models.Model):
	nom=models.CharField(max_length=200)
	
class CoreBanque(models.Model):
	nom = models.CharField(max_length=200)
	prof = models.ForeignKey(Enseignant)
	
class CoreQcm(models.Model):
	prof = models.ForeignKey(Enseignant)
	nom = models.CharField(max_length=200)
	nomTeX = models.CharField(max_length=200,default="Matière - 2014/2015")
	texteTeX = models.CharField(max_length=2000,default="\\centerline{Durée 30 minutes}\n\\medskip \n{\\it \n\\noindent\\underline{La correction est automatisée, {\\bf noircir}  les cases des réponses justes et laisser vides les autres cases.} \\\ \nAucun document autorisé, téléphones portables et calculatrices interdits.\\\ \nUn seule réponse juste par exercice. \\\ \nBarème: réponse juste = 1pt, réponse fausse  = -0.5pt \n}")
	nbexos = models.ManyToManyField(CoreBanque, through='CoreNbExos')
	erreurtex =  models.BooleanField(default=True)
	generation = models.IntegerField(default=0)
	nmax = models.IntegerField(default=0)


class CoreNbExos(models.Model):
	nb = models.IntegerField()
	banque = models.ForeignKey(CoreBanque)
	qcm = models.ForeignKey(CoreQcm)
	position = models.IntegerField()
	
class CoreExo(models.Model):
	def reponses(self):
		return sorted(self.corereponse_set.all(), key=lambda r: int(r.position))

	question = models.CharField(max_length=2000, default="En quoi l'escalade est un super sport?")
	corrige = models.CharField(max_length=2000, default="Parce qu'il n'y a pas mieux!\n\\[\n\\int_0^\\infty e^{-x}dx = 1 \n\\]" )
	type = models.CharField(max_length=200)
	banque = models.ForeignKey(CoreBanque)
	erreurtex = models.BooleanField(default=True)
	
class CoreReponse(models.Model):
	exo = models.ForeignKey(CoreExo)
	nom = models.CharField(max_length=1)
	texte = models.CharField(max_length=2000)
	position = models.IntegerField()
	
class CoreQcmPdf(models.Model):
	numero = models.IntegerField()
	code = models.CharField(max_length=200)
	qcm = models.ForeignKey(CoreQcm)
	paquet = models.IntegerField()
	exos = models.ManyToManyField(CoreExo,through='CoreExoQcmPdf')
	reponses = models.CharField(max_length=200, default='')
	positionscases = models.CharField(max_length=1000, default='')
	pages = models.IntegerField(default=0)
	positionspts = models.CharField(max_length=1000, default='')
	
class CoreExoQcmPdf(models.Model):
	qcmpdf = models.ForeignKey(CoreQcmPdf)
	exo = models.ForeignKey(CoreExo)
	position = models.IntegerField()

class CoreCopie(models.Model):
	eleve = models.ForeignKey(Eleve)
	qcmpdf = models.ForeignKey(CoreQcmPdf)
	reponsescases = models.CharField(max_length=200,default="")
	
class CoreCopies(models.Model):
	def renommage(instance, nom):
		return("ups/"+str(instance.qcm.prof.id)+"/"+str(instance.qcm.id)+"/copies/"+nom)
	qcm = models.ForeignKey(CoreQcm)
	fichier = models.FileField(upload_to=renommage, verbose_name="Copies")
	corrigees=models.BooleanField(default=0)
	nom=models.CharField(max_length=200)




# Create your models here.

	
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
	texteTeX=models.CharField(max_length=2000,default="\\centerline{Durée 30 minutes}\n\\medskip \n{\\it \n\\noindent\\underline{La correction est automatisée, \\textbf{noircir} les cases des réponses justes et laisser vides les autres cases.} \\\ \nAucun document autorisé, téléphones portables et calculatrices interdits.\\\ \nUn seule réponse juste par exercice. \\\ \nBarème: réponse juste = 1pt, réponse fausse  = -0.5pt \n}")
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

class CopieCorrigee(models.Model):
	eleve=models.ForeignKey(Eleve)
	numero=models.IntegerField()
	copies=models.ForeignKey(CoreCopies)
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


