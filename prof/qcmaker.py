#!/usr/bin/python
#-*- coding: utf-8 -*-

#le principe: on a des listes d'exos dans des fichiers.
#chaque exo est de la forme @@@QCM
#							question
#							note@reponse1
#							note@reponse2
#on veut tirer un certain nombre de questions au hasard dans chaque liste d'exos que l'on se donne

import random
import io
import subprocess as sp
import os
import time
import sys
import shutil as sh
import numpy as np


		#on lit le fichier config pour avoir 1) si on affiche les titres, 2) la liste des fichiers de liste d'exos
		#3) le nombre d'exos à prendre dans chaque liste et 4) le nombre de versions de qcm à faire
class ConfigurationMaker():
	
	def __init__(self,steps,numexam):
		
		
		#nombre de version à générer
		self.numexam=numexam
		self.steps=steps.split(',')
		self.steps[0]=int(self.steps[0])
		for i in range(len(self.steps)-1):
			self.steps[i+1]=int(self.steps[i+1])
			if self.steps[i+1] == 1:
				print("Il faut au moins 2 versions par paquet")
				quit()
			self.steps[i+1]=self.steps[i]+self.steps[i+1]
	
		self.ntotal=self.steps[-1]
		
			
		#définition des variables utilisées dans le code des exos

		#numéro de la première feuille, après on incrémente
		self.nfeuille=1
		self.sepQCM="@@@QCM\n"
		self.sepNote="@"
		self.sepTeXExos="%%%exos\n"
		self.sepCodeExo="%%%codeExo\n"
		self.sepNom="%%%nomQCM\n"
		self.sepTexte="%%%texteQCM\n"
		#fichiers
		self.TeXTemplate="template.tex"
		self.TeXSortie="exos"
		self.CorrSortie="corrections.csv"
		self.QSortie="questions.csv"
		
		

#classe pour chaque exo (une question)
#une instance de classe contient une question, et les reponses et leurs coeffs
class exo():
	def __init__(self,typeExo):
		self.typeExo=""
		self.question=""
		self.typeExo=typeExo
		self.reponses=[]
		self.coeff=[]
		
#classe pour chaque liste d'exos (correspond à un fichier.exos)
class listeExos():
	
	
	def __init__(self,fichierExos,config):
		self.exos=list()		#liste d'exo, chaque élément de la liste est une instance de classe exo
		self.nbExos=0			#nombre d'exos disponibles dans la liste
		self.exosBrut=list()	#lecture brute du fichier
		self.nom=""				#nom éventuellement affiché de la liste d'exos
		self.lire(fichierExos)	#on lit le fichier, pour remplir exosBrut
		self.genererExos(config)		#on génère la liste d'exos dans le self.exos à partir du exosBrut
	
	#lecture du fichier contenant la liste d'exos
	def lire(self,fichierExos):
		self.fichierExos=io.FileIO(fichierExos)
		self.exosBrut=self.fichierExos.readlines()
		
	#création d'une instance pour chaque exo
	def genererExos(self,config):
		self.nbExos=0
		self.nom=""
		nq=-1
		for i in range(len(self.exosBrut)):
			if self.exosBrut[i]==config.sepQCM:		#si on a un séparateur d'exo, on créé une nouvelle instance de class exo
				newExo=exo("QCM")				# un QCM
				self.exos.append(newExo)		#qu'on ajoute à notre liste
				self.nbExos=self.nbExos+1		#on incrémente le nombre d'exos
				nq=1							#on prévient qu'on va lire la question de l'exo ensuite
			elif config.sepNote in self.exosBrut[i]:							#si on a un séparateur note/reponse, c'est qu'on lit une nouvelle réponse
				tPart=self.exosBrut[i].partition(config.sepNote)				
				self.exos[self.nbExos-1].reponses.append(tPart[2])		#donc, on l'ajoute
				self.exos[self.nbExos-1].coeff.append(tPart[0])			#à nos réponses possibles
				nq=0													# et on prévient qu'on va continuer de lire une réponse
			elif nq==0:													#si on est en train de lire un réponse
				self.exos[self.nbExos-1].reponses[-1]+=self.exosBrut[i]	#on ajoute le texte à la réponse acutelle
			elif nq==1:													#si on est en train de lire une question
				self.exos[self.nbExos-1].question+=self.exosBrut[i]		#on ajoute à la suite de la question (elle est égale à "" au départ)
			elif nq==-1:												#si on est toujours sur le titre
				self.nom+=self.exosBrut[i]								#on ajoute au titre


	#génération d'un code TeX pour un sous-ensemble de aGen de l'ensemble des exos de l'instance de classe
	def genererTeX(self,aGen,config):
		self.TeXExos=list()		#liste contenant le code TeX pour la liste aGen d'exos, aGen est une list() de numéros d'exos de cette instance de classe, dont on doit générer le TeX
		self.TeXExos.append("\\begin{bfseries}"+self.nom+"\\end{bfseries}\n\\medskip")
		for i in range(len(aGen)):
			self.TeXExos.append("\\begin{exo}\n")
			self.TeXExos.append(self.exos[aGen[i]].question)
			self.TeXExos.append("\n\\medskip\n\\begin{minipage}{ \\textwidth}\\begin{itemize}[label=$\\square$]\n")
			for j in range(len(self.exos[aGen[i]].reponses)):
				self.TeXExos.append("\item "+self.exos[aGen[i]].reponses[j])
			self.TeXExos.append("\\end{itemize}\end{minipage}\n")
			self.TeXExos.append("\\end{exo}\n\\bigskip\n")

#classe qui génère un code TeX entier à partir d'un template, de la liste des objets de liste d'exo, et les exos qu'on veut dans chaque liste d'exo
class TeXify():
	
	def __init__(self,template,listeListesTeX, listeExosPourTeX, numero,config):
		fichierTemplate=io.FileIO(template)
		self.TeX=fichierTemplate.readlines()
		self.indexExos=self.TeX.index(config.sepTeXExos)
		self.TeX.remove(config.sepTeXExos)
		i=0
		for liste in listeListesTeX:
			liste.genererTeX(listeExosPourTeX[i],config)
			for j in range(len(liste.TeXExos)):
				self.TeX.insert(self.indexExos,liste.TeXExos[j])
				self.indexExos+=1
			i=i+1
		
		self.TeX.insert(self.TeX.index(config.sepCodeExo),str(config.numexam)+"-"+str(config.codes[int(numero,2)])+" \\Huge + $ "+self.ntosymb(numero,config)+" $ \\normalsize")
		self.TeX.insert(self.TeX.index(config.sepNom),config.nomQCM)
		self.TeX.insert(self.TeX.index(config.sepTexte),config.texteQCM)
			
	def ntosymb(self,n,config):
		symb=""
		nmax=int(np.trunc(np.log2(config.ntotal))+1)
		for i in range(nmax-len(n)):
			symb=symb+"\\Box"
		for i in n:
			if i=='1':
				symb=symb+"\\blacksquare"
			if i=='0':
				symb=symb+"\\Box"
		return symb
			
#classe qui génère la correction CSV et les questions choisies pour chaque version en CSV
class CSV():
	
	def __init__(self,fichierCorr,fichierQ):
		self.nomCSV=fichierCorr
		self.nomQCSV=fichierQ
		self.correction=list()
		self.questions=list()
	
	def ajouterC(self,i,Lex,r):
		if len(self.correction)<i+1:
			self.correction.append(list())
		for j in r:
			self.correction[i].append(Lex.exos[j].coeff)
			
	def ajouterQ(self,i,r):
		if len(self.questions)<i+1:
			self.questions.append(list())
		self.questions[i].append(r)
	
	def imprimerC(self,config):
		fichierCSV=io.FileIO(self.nomCSV,'w')
		for i in range(len(self.correction)):
			fichierCSV.write(str(config.nfeuille+i))
			for j in range(len(self.correction[i])):
				for l in range(len(self.correction[i][j])):
					fichierCSV.write(","+str(self.correction[i][j][l]))
			fichierCSV.write("\n")
		fichierCSV.close()
	
	def imprimerQ(self,lFichiers,lExos,config):
		fichierQCSV=io.FileIO(self.nomQCSV,'w')
		fichierQCSV.write("#nombre de copies: "+str(config.steps)+"\n")
		fichierQCSV.write("#listes de fichiers:\n")
		for i in range(len(lFichiers)):
			fichierQCSV.write(lFichiers[i]+":"+str(lExos[i])+"\n")
		for i in range(len(self.questions)):
			fichierQCSV.write(str(config.nfeuille+i))
			for j in range(len(self.questions[i])):
				fichierQCSV.write(";")
				for l in range(len(self.questions[i][j])):
					if l==0:
						fichierQCSV.write(str(self.questions[i][j][l]))
					else:
						fichierQCSV.write(","+str(self.questions[i][j][l]))
			fichierQCSV.write("\n")
		fichierQCSV.close()
		
#lecture de questions.csv, pour regénérer une même liste de questions
class QdeCSV():
	
	def __init__(self,fichier):
		self.listeQ=list()			#list() de questions pour chaque version
		self.listeL=list()			#list() des fichiers de listes et questions par fichier
		self.modeTest=0
		if fichier==1:
			for k in range(len(config.nbexos)):
				self.listeQ.append(range(exos[k].nbExos))
			self.modeTest=1
		else:
			self.lire(fichier)
	
	#fonction pour liste dans le fichier et remplir les listes
	def lire(self,fichier):
		fichierEntree=io.FileIO(fichier,'r')
		fichierBrut=fichierEntree.readlines()
		for ligne in fichierBrut:
			if "#" not in ligne:
				if ":" in ligne:
					self.listeL.append(ligne.partition("\n")[0].rsplit(":"))
					self.listeL[-1][-1]=int(self.listeL[-1][-1])
				elif ";" in ligne:
					ltemp=ligne.partition("\n")[0].rsplit(";")
					ttemp=list()
					itemp=list()
					for c in ltemp:
						ttemp.append(c.rsplit(","))
					for c in range(len(ttemp)):
						itemp.append(list())
						for cc in ttemp[c]:
							itemp[c].append(int(cc))
					self.listeQ.append(itemp)
				else:
					print("Problème dans la lecture de "+fichier)
					quit()
					
	def liste(self,nversion,nliste):
		if self.modeTest==1:
			return self.listeQ[nliste]
		else:
			for version in self.listeQ:
				if nversion==version[0][0]:
					return version[nliste+1]
		
	
	def listeListes(self):
		return self.listeL


