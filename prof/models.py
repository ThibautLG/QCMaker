#-*- coding:utf-8 -*-

from django.db import models
from datetime import datetime
from django.core.files.storage import FileSystemStorage
import shutil,os,cv2

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
	formule = models.CharField(max_length=200,default='(v+f==1)*(1*v-0.5*f)')


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
	nom = models.CharField(max_length=2)
	texte = models.CharField(max_length=2000)
	position = models.IntegerField()
	
class CoreQcmPdf(models.Model):
	def getpts(self,page):
		pts = self.positionspts.split(';')
		ipts = ((int(pts[page-1].split(',')[0]),int(pts[page-1].split(',')[1])),(int(pts[page-1].split(',')[2]),int(pts[page-1].split(',')[3])),(int(pts[page-1].split(',')[4]),int(pts[page-1].split(',')[5])))
		print('ipts: '+str(ipts))
		return ipts
	def getcases(self,page):
		cases = self.positionscases.split(';')
		cases = [(int(case.split(',')[1]),int(case.split(',')[2])) for case in cases if case.split(',')[0]==str(page)]
		print('Cases: '+str(cases))
		return cases
	def getnote(self):
		nbreponses = {}
		irep = 0
		note = 0.0
		for qexo in sorted(CoreExoQcmPdf.objects.filter(qcmpdf=self), key=lambda r: int(r.position)):
			for reponse in sorted(qexo.exo.corereponse_set.all(), key=lambda r: int(r.position)):
				try:
					nbreponses[reponse.nom]+=int(self.reponses[irep])
				except Exception, er:
					nbreponses[reponse.nom]=int(self.reponses[irep])
				irep+=1
			note += (nbreponses['v']+nbreponses['f']==1)*(1*nbreponses['v']-0.5*nbreponses['f'])
			nbreponses = {}
		return max(note,0)
	def getreponses(self):
		irep = 0
		listereponses = list()
		for qexo in sorted(CoreExoQcmPdf.objects.filter(qcmpdf=self), key=lambda r: int(r.position)):
			listereponsesexo = list()
			for reponse in sorted(qexo.exo.corereponse_set.all(), key=lambda r: int(r.position)):
				try:
					listereponsesexo.append(int(self.reponses[irep]))
				except Exception, er:
					print(er)
					return list()
				irep+=1
			listereponses.append(listereponsesexo)
		return listereponses

	def setreponses(self,reponses):
		if len(self.reponses)==len(reponses):
			for r in reponses:
				if r not in '01':
					return 1
		else:
			return 1
		self.reponses = reponses
		self.save()
		print('setreponses: '+self.reponses)
		for copie in self.corecopie_set.all():
			copie.setimage()
		return 0

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
	def getpage(self,page):
		return self.fichiers.split(';')[page-1]
	def setimage(self):
		w,h = 21,21
		reponses = self.qcmpdf.reponses
		for page in [i+1 for i in range(self.qcmpdf.pages)]:
			cases = self.qcmpdf.getcases(page)
			imgFichier = self.getpage(page)[:-13]+'.jpg'
			img = cv2.imread(imgFichier,1)
			i = 0
			for pt in cases:
				print(pt,i)
				if reponses[i]=='1':
					cv2.rectangle(img,(pt[0]-w/2,pt[1]-h/2), (pt[0] + 3*w/2, pt[1] + 3*h/2), (0,0,255), 2)
				i+=1
			cv2.imwrite(self.getpage(page),img)

	eleve = models.ForeignKey(Eleve)
	qcmpdf = models.ForeignKey(CoreQcmPdf)
	fichiers = models.CharField(max_length=1000,default="")
	malcorrigee = models.BooleanField(default=0)
	
class CoreCopies(models.Model):
	def renommage(instance, nom):
		return("ups/"+str(instance.qcm.prof.id)+"/"+str(instance.qcm.id)+"/copies/"+nom)
	qcm = models.ForeignKey(CoreQcm)
	fichier = models.FileField(upload_to=renommage, verbose_name="Copies")
	corrigees = models.BooleanField(default=0)
	nom = models.CharField(max_length=200)




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


