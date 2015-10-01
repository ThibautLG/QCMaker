#!/usr/bin/python
#-*- coding: utf-8 -*-

#le principe: on a des listes d'exos dans des fichiers.
#chaque exo est de la forme @@@QCM
#							question
#							note@reponse1
#							note@reponse2
#
import sys
import random
import io
import subprocess as sp
import os
import time
import shutil as sh
import numpy as np
from prof.models import *
import prof.core as core
import codecs

#classe pour chaque banque d'exos lue (correspond à un fichier.exos)
class LectureExos():
	
	
	def __init__(self,args):
		fichierExos=args[0]
		banque=args[1]
		dossier=args[2]
		self.sepQCM="@@@QCM\n"
		self.sepCorr="@@@Correction\n"
		self.sepNote="@"
		self.banque=CoreBanque.objects.get(id=banque)
		self.dossier=dossier
		self.exosBrut=list()	#lecture brute du fichier
		self.lire(fichierExos)	#on lit le fichier, pour remplir exosBrut
		self.genererExos()		#on génère la liste d'exos dans le self.exos à partir du exosBrut
	
	#lecture du fichier contenant la liste d'exos
	def lire(self,fichierExos):
		with codecs.open(fichierExos, 'r', 'utf-8') as f:
       			self.exosBrut=f.readlines()
		#self.fichierExos=io.FileIO(fichierExos)
		#self.exosBrut=self.fichierExos.readlines()
		
	#création d'une instance pour chaque exo
	def genererExos(self):
		nq=-1
		for i in range(len(self.exosBrut)):
			if self.exosBrut[i]==self.sepQCM:		#si on a un séparateur d'exo, on créé une nouvelle instance de class exo
				if nq!=-1:				#si on termine un autre exo, on check le tex, et on l'enregistre
					errtex = core.genererSvg(newExo,self.dossier)
					if not errtex == 0:
						newExo.erreurtex = True
					else: 
						newExo.erreurtex = False
					newExo.save()

				newExo=core.CoreExo(banque=self.banque,type=1,question="",corrige="")
				newExo.save()
				nq=1					#on prévient qu'on va lire la question de l'exo ensuite

			elif self.exosBrut[i]==self.sepCorr:		#si on a un séparateur de correction
				nq=2					#on passe en mode correction

			elif self.sepNote in self.exosBrut[i]:							#si on a un séparateur note/reponse, c'est qu'on lit une nouvelle réponse
				tPart=self.exosBrut[i].partition(self.sepNote)				
				reponse=core.CoreReponse(exo=newExo,texte=tPart[2],nom=tPart[0],position=len(newExo.corereponse_set.all())+1)	#on l'ajoute
				reponse.save()
				nq=0						# et on prévient qu'on va continuer de lire une réponse

			elif nq==0:						#si on est en train de lire un réponse
				reponse.texte+=self.exosBrut[i]			#on ajoute le texte à la réponse acutelle
				reponse.save()

			elif nq==1:						#si on est en train de lire une question
				newExo.question+=self.exosBrut[i]		#on ajoute à la suite de la question (elle est égale à "" au départ)
				newExo.save()

			elif nq==2:						#si on est en train de lire une correction
				newExo.correction+=self.exosBrut[i]		#on l'ajoute
				newExo.save()
		
		if nq!=-1:				#si il y a eu au moins un exo, on check le tex, et on l'enregistre
			errtex = core.genererSvg(newExo,self.dossier)
			if not errtex == 0:
				newExo.erreurtex = True
			else: 
				newExo.erreurtex = False
			newExo.save()
