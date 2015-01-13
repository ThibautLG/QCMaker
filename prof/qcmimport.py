#!/usr/bin/python
#-*- coding: utf-8 -*-
import numpy as np
import cv2
import io
import pickle
import os
import subprocess as sp
import random


class ConfigurationImport():
	
	def __init__(self,dossier):
		
		
		self.dossier=dossier
		self.caseVide="case_vide.jpg"
		self.sep=cv2.imread("sep.jpg",0)
		self.pts=[cv2.imread("pt1.jpg",0),cv2.imread("pt2.jpg",0),cv2.imread("pt3.jpg",0),]
		self.zones=[[(1000,1700),(0,400)],[(1300,1700),(2100,2400)],[(0,400),(2100,2300)]]
		self.thresholdCase=0.75
		self.dl=600
		

		
#classe commune aux élèves et aux originaux vierges
class Copie():
	
	def __init__(self):
		pass
	
	#méthode pour lire les chiffres du code (la suite de 0101 en haut à droite)
	def lireChiffres(self):
		
		nmax=self.conf.nmax
		tcode=list()
		w,h=self.imgCode.shape[::-1]
		tt=list()
		code=list()
		for i in range(nmax):
			itcode=self.imgCode[:,np.round(i*w/nmax):np.round((i+1)*w/nmax)]
			tloc=np.where(itcode>200)
			tloc=zip(*tloc[::-1])
			tt.append(len(tloc))
		t0=sorted(tt,reverse=True)[0]	
		for i in range(nmax):
			if tt[i]>=t0*self.conf.thresholdCase:
				code.append('0')
			else:
				code.append('1')
		code="".join(code)
		self.code=code
		
	#méthode pour trouver les trois repères de la copie, qui serviront à mettre l'élève et l'original à la même échelle
	def trouverpt(self,i):
		method = 'cv2.TM_CCOEFF_NORMED'	
		method = eval(method)
		res = cv2.matchTemplate(self.img[self.conf.zones[i][1][0]:self.conf.zones[i][1][1],self.conf.zones[i][0][0]:self.conf.zones[i][0][1]],self.conf.pts[i],method)
		min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
		loc = np.where( res >= max_val)
		loc = zip(*loc[::-1])
		ret=(loc[0][0]+self.conf.zones[i][0][0],loc[0][1]+self.conf.zones[i][1][0])
		return ret
		
	#recherche le séparateur entre le code en 01010 et celui d'avant. Utilisé pour trouver l'image du code
	def trouverSep(self):
		
		thresholdCoeff = 1
		method = 'cv2.TM_SQDIFF_NORMED'
		method = eval(method)
		
		template = self.conf.sep
		w, h = template.shape[::-1]
		
		res = cv2.matchTemplate(self.img,template,method)
		min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
		loc = np.where( res <= min_val)
		loc = zip(*loc[::-1])
		return loc[0]
	
	#enregistre l'image du code
	def lireN(self):
		locCode=self.trouverSep()
		w, h = self.conf.sep.shape[::-1]
		self.imgCode=self.img[locCode[1]:locCode[1]+h,locCode[0]+w:self.pts[0][0]]

		
	
#classe pour les versions originales
class Original(Copie):
	
	def __init__(self,imgFichier,conf):

		self.conf=conf
		self.lire(imgFichier,conf.caseVide)
		self.pts=[self.trouverpt(0),self.trouverpt(1),self.trouverpt(2)]
		self.lireN()
		self.lireChiffres()
		del self.img
		del self.template
		del self.imgCode
		del self.res
		
	#l'essentiel est fait ici: on charge, on trouve les cases vides pour qu'on sache où les trouver sur la copie de l'élève
	def lire(self,imgFichier,templateFichier):
		
		#on charge et on tronque
		self.img = cv2.imread(imgFichier,0)
		self.template = cv2.imread(templateFichier,0)
		self.dimCV = self.template.shape[::-1]
		w,h = self.dimCV
		
		thresholdCoeff = 800
		method = 'cv2.TM_SQDIFF_NORMED'		
		method = eval(method)
		self.res = cv2.matchTemplate(self.img[:,:self.conf.dl],self.template,method)
		min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(self.res)
		threshold = thresholdCoeff*min_val
		loc = np.where( self.res <= threshold)
		loc = zip(*loc[::-1])
		n=len(loc)
		
		
		#trop de cases pour être des cases
		if n>100:
			self.cases=list()
			return
		self.cases=loc


class Eleve(Copie):
	
	def __init__(self,imgFichier,conf):
		#on charge et on tronque PAS
		self.conf=conf
		self.imgFichier=imgFichier
		self.img = cv2.imread(imgFichier,0)
		self.imgRGB = cv2.imread(imgFichier,1)
		ret,self.img = cv2.threshold(self.img,200,255,cv2.THRESH_BINARY)
		self.pts=[self.trouverpt(0),self.trouverpt(1),self.trouverpt(2)]
		self.lireN()
		self.lireChiffres()
		
		
	#on compare la copie à l'original (on met la copie de l'élève à l'échelle de l'original, on lit les cases, et on décide si elles sont cochées ou non
	def compare(self,original):
		
		w, h = original.dimCV
		M=cv2.getAffineTransform(np.array(self.pts,dtype="float32"),np.array(original.pts,dtype="float32"))
		rows,cols = self.img.shape
		self.img = cv2.warpAffine(self.img,M,(cols,rows))
		self.imgRGB = cv2.warpAffine(self.imgRGB,M,(cols,rows))
		
		self.reponses=list()
		tt=list()
		for pt in original.cases:
			timg=self.img[pt[1]:pt[1]+h,pt[0]:pt[0]+w]
			tloc=np.where(timg>200)
			tloc=zip(*tloc[::-1])
			tt.append(len(tloc))
			
		tt.sort(reverse=True)
		for pt in original.cases:
			timg=self.img[pt[1]:pt[1]+h,pt[0]:pt[0]+w]
			tloc=np.where(timg>200)
			tloc=zip(*tloc[::-1])
			tn=len(tloc)
			if tn>=tt[0]*self.conf.thresholdCase:
				self.reponses.append('0')
			else:
				self.reponses.append('1')
				timg=self.img[pt[1]:pt[1]+h,pt[0]:pt[0]+w]
				cv2.rectangle(self.imgRGB, (pt[0],pt[1]), (pt[0] + w-1, pt[1] + h-1), (0,0,255), 2)
		
		#cv2.imwrite(self.conf.dossier+"/copie-"+self.code+"-"+str(random.random())+".jpg",self.imgRGB)
		cv2.imwrite(self.imgFichier,self.imgRGB)
		
		del self.imgRGB
		del self.img
		del self.imgCode
		

#classe qui coordonne tout, en fonction d'une configuration donnée (essentiellement  la liste des copies et des originaux et des paramètres)
class Traitement():
	
	def __init__(self,conf):
		###chargement ou création des originaux à partir de la configuration (qui contient la liste des originaux)
		self.conf=conf
		if self.conf.pickle != 1:
			try:
				with open(self.conf.pickle) as f:
					self.originaux = pickle.load(f)
					if len(self.originaux)==0:
						raise
					print("loaded!")
			except:
				self.originaux=list()
				for i in range(len(self.conf.listeFichiersOriginaux)):
					ori=Original(self.conf.dossierOriginaux+self.conf.listeFichiersOriginaux[i],self.conf)
					if len(self.originaux)==0:
						self.originaux.append([ori])
					else:
						if ori.code == self.originaux[-1][0].code:
							self.originaux[-1].append(ori)
						else:
							self.originaux.append([ori])
				with open(self.conf.pickle, 'w') as f:
					pickle.dump(self.originaux, f)
		
	#on corrige les copies (dont la liste est donnée dans la configuration)
	def correction(self):
		copies=list()
		copies.append([Eleve(self.conf.dossierCopies+self.conf.listeFichiersCopies[0],self.conf)])
		for i in range(len(self.conf.listeFichiersCopies)-1):	
			cop=Eleve(self.conf.dossierCopies+self.conf.listeFichiersCopies[i+1],self.conf)
			### les copies doivent être scannées dans l'ordre
			if cop.code == copies[-1][0].code:
				copies[-1].append(cop)
			else:
				copies.append([cop])
				
		listeCodes=[o[0].code for o in self.originaux]
		
		print(listeCodes)
		for cc in copies:
			for i in range(len(cc)):
				cc[i].compare(self.originaux[listeCodes.index(cc[i].code)][i])
				
		self.listeRep=list()
		for i in range(len(copies)):
			self.listeRep.append([copies[i][0].code,"".join(copies[i][0].reponses)])
			for j in range(len(copies[i])-1):
				self.listeRep[-1][1]+="".join(copies[i][j+1].reponses)
		print(self.listeRep)
	
	#on enregistre toutes les réponses trouvées dans un CSV qui pourra être lu par qcmcorrecteur
	def imprimerCSV(self,fichier):
		fichierCSV=io.FileIO(fichier,'w')
		for rep in self.listeRep:
			fichierCSV.write(","+str(int(rep[0],2))+","+rep[1])
			fichierCSV.write("\n")
		fichierCSV.close()
		

#config=Configuration("configPROB")
#go=Traitement(config)
#go.correction()
#go.imprimerCSV(config.dossier+"corr.csv")
		
