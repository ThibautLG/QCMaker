#!/usr/bin/python
#-*- coding: utf-8 -*-
import io
import sys

#format des réponses: un fichier .csv où chaque ligne est de la forme:
#	nom de l'élève,numéro de son qcm, liste de 01 qui signifie dans l'ordre que la ième case a été cochée si 1 et non cochée si 0

class correction():
	def __init__(self,Corr,Rep):
		self.tableauCoeff=list()
		self.nomsEleves=list()
		self.numeroEleves=list()
		self.reponsesEleves=list()
		self.reponseEleves=list()
		self.numeroCoeff=list()
		self.note=list()
		#self.Notes=Notes
		
		self.fichierRep=io.FileIO(Rep)
		self.reponsesElevesBrut=self.fichierRep.readlines()
		for i in range(len(self.reponsesElevesBrut)):
			if len(self.reponsesElevesBrut[i])>2:
				self.reponsesEleves.append(self.reponsesElevesBrut[i].partition("\n")[0])
				self.reponsesEleves[i]=self.reponsesEleves[i].rsplit(",")
				self.reponsesEleves[i][-1]=''.join(self.reponsesEleves[i][-1].rsplit(" "))
				#print(i)
		self.nbeleves=len(self.reponsesEleves)
		
		fichierCoeff=io.FileIO(Corr)
		self.tempTableau=fichierCoeff.readlines()
		for ligne in self.tempTableau:
			self.tableauCoeff.append(ligne.rsplit(","))
			self.tableauCoeff[-1][-1]=self.tableauCoeff[-1][-1][:-1]	#on enlève le \n de la fin de ligne
			self.numeroCoeff.append(self.tableauCoeff[-1][0])
		
		
	def calculer(self):
		for i in range(self.nbeleves):
			tempNote=0
			#print(self.reponsesEleves[i])
			indexEleve=self.numeroCoeff.index(str(self.reponsesEleves[i][1]))
			if len(self.reponsesEleves[i][2]) != len(self.tableauCoeff[indexEleve])-1:
				print("Pas le nombre de réponses à la ligne "+str(i+1)+" des réponses (réponse de "+self.reponsesEleves[i][0]+").\nIl en fallait " +str(len(self.tableauCoeff[indexEleve])-1)+" et il y en a "+str(len(self.reponsesEleves[i][2])))
				quit()
			for j in range(len(self.reponsesEleves[i][2])):
				tempNote+=int(self.reponsesEleves[i][2][j])*float(self.tableauCoeff[indexEleve][j+1])
			if tempNote<0:
				tempNote=0
			self.note.append([self.reponsesEleves[i][1],tempNote])
			
	def imprimer(self):
		fichierCSV=io.FileIO(self.Notes,'w')
		for i in range(len(self.note)):
			fichierCSV.write(self.note[i][0]+","+str(self.note[i][1])+","+str(self.note[i][2])+"\n")
			
	def moyenne(self):
		tmean=0
		for i in range(len(self.note)):
			tmean+=self.note[i][2]
		return tmean/len(self.note)

