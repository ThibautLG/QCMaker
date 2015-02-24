#!/usr/bin/python
#-*- coding: utf-8 -*-

#le principe: on a des listes d'exos dans des fichiers.
#chaque exo est de la forme @@@QCM
#							question
#							note@reponse1
#							note@reponse2
#on veut tirer un certain nombre de questions au hasard dans chaque liste d'exos que l'on se donne

import sys
import random
import io
import subprocess as sp
import os
import time
import shutil as sh
import numpy as np
import cv2
from prof.models import *
import codecs

#variables utilisées

sepTeXExos = "%%%exos\n"
sepCodeExo = "%%%codeExo\n"
sepNom = "%%%nomQCM\n"
sepTexte = "%%%texteQCM\n"

caseVide = "case_vide.jpg"
dimCaseVide = cv2.imread(caseVide,0).shape[::-1]
sep=cv2.imread("sep.jpg",0)
pts=[cv2.imread("pt1.jpg",0),cv2.imread("pt2.jpg",0),cv2.imread("pt3.jpg",0),]
zones=[[(1000,1700),(0,400)],[(1300,1700),(2100,2400)],[(0,400),(2100,2300)]]
thresholdCaseCode=0.75
thresholdCase=0.5 #0.75
dl=600
		


def exo2tex(exo,correction):

    TeXexo=list() #liste contenant le code TeX pour la liste aGen d'exos, aGen est une list() de numéros d'exos de cette instance de classe, dont on doit générer le 
    TeXexo.append(u"\\begin{exo}\n")
    TeXexo.append(exo.question+u"\n")
    if exo.corereponse_set.all():
    	TeXexo.append(u"\n\\medskip\n\\begin{minipage}{ \\textwidth}\\begin{itemize}[label=$\\square$]\n")
    	for reponse in sorted(exo.corereponse_set.all(), key=lambda r: int(r.position)):
		if reponse.nom == "v" and correction:
			TeXexo.append(u"\item {\\color{green}"+reponse.texte+u"}\n")
		else:
			TeXexo.append(u"\item "+reponse.texte+u"\n")
   	TeXexo.append(u"\\end{itemize}\end{minipage}\n")
    TeXexo.append(u"\\end{exo}\n\\bigskip\n")
    if correction:
	TeXexo.append(u"\\begin{cor}\n{\\color{red}")
	TeXexo.append(exo.corrige)
	TeXexo.append(u"}\n\\end{cor}\n\\bigskip")
    return TeXexo

    
def ntosymb(n,nmax):
    symb=""    
    for i in range(nmax-len(n)):
        symb=symb+u"\\Box"
    for i in n:
        if i=='1':
            symb=symb+u"\\blacksquare"
        if i=='0':
            symb=symb+u"\\Box"

    return symb
    

def genererTeXHTML(exo,template):

    with codecs.open(template, 'r', 'utf-8') as f:
        TeX=f.readlines()
    indexExos=TeX.index(sepTeXExos)
    TeX.remove(sepTeXExos)
    texexo = exo2tex(exo,True)
    for ligne in texexo:
	TeX.insert(indexExos,ligne)
	indexExos+=1
    return TeX


def genererTeXQcmPreview(qcm,template):

    with codecs.open(template, 'r', 'utf-8') as f:
        TeX=f.readlines()
    indexExos=TeX.index(sepTeXExos) 
    TeX.insert(TeX.index(sepNom),qcm.nomTeX)
    TeX.insert(TeX.index(sepTexte),qcm.texteTeX)
    TeX.insert(TeX.index(sepCodeExo),u"17-168748 \\Huge + $ "+ntosymb('1010101',7)+u" $ \\normalsize")

    return TeX



def genererTeX(qcmpdf,template):
    
    with codecs.open(template, 'r', 'utf-8') as f:
        TeX=f.readlines()
    indexExos=TeX.index(sepTeXExos)
    TeX.remove(sepTeXExos)

    for exoqcmpdf in sorted(CoreExoQcmPdf.objects.filter(qcmpdf=qcmpdf), key=lambda r: int(r.position)):
	exo = exoqcmpdf.exo
        texexo = exo2tex(exo,False)
        for ligne in texexo:
            TeX.insert(indexExos,ligne)
            indexExos+=1
    nmax=int(np.trunc(np.log2(len(qcmpdf.qcm.coreqcmpdf_set.all())))+1)
    TeX.insert(TeX.index(sepCodeExo),str(qcmpdf.code)+u" \\Huge + $ "+ntosymb(str(bin(qcmpdf.numero)[2:]),nmax)+u" $ \\normalsize")
    TeX.insert(TeX.index(sepNom),qcmpdf.qcm.nomTeX)
    TeX.insert(TeX.index(sepTexte),qcmpdf.qcm.texteTeX)

    return TeX


def genererSvg(exo,dossier):
    
    template = "templateHTML.tex"

    with codecs.open(dossier+'/exo-'+str(exo.id)+'.tex','w','utf-8') as f:
	for ligne in genererTeXHTML(exo,'templateHTML.tex'):
	    f.write(ligne)
    try:
	 sp.check_output(['pdflatex','-output-directory',dossier,dossier+'/exo-'+str(exo.id)+'.tex'])
	 sp.call(['pdftocairo','-svg','-l','1',dossier+'/exo-'+str(exo.id)+'.pdf',dossier+'/exo-'+str(exo.id)+'.svg'])
   	 os.remove(dossier+'/exo-'+str(exo.id)+'.aux')
 	 os.remove(dossier+'/exo-'+str(exo.id)+'.log')
   	 os.remove(dossier+'/exo-'+str(exo.id)+'.tex')
   	 os.remove(dossier+'/exo-'+str(exo.id)+'.pdf')
    except sp.CalledProcessError as er:
	erreurtemp=er.output.split('\n')
	erreur=""
	for ligne in erreurtemp:
		if ligne[:1] == "!":
	    		erreur += ligne+"\n"
		#if ligne[:2] == "l.":
			#ligneerreur = int(ligne.split(' ',1)[0][2:])
			#with codecs.open(dossier+'/exo-'+str(exo.id)+'.tex','r','utf-8') as f:
			#	texerreurs = f.readlines()
			#print('\n'.join(texerreurs[ligneerreur:ligneerreur+2]))
			#break
	print(erreur)
	return erreur 
    return 0
	
def genererSvgQcm(qcm,dossier):


    with codecs.open(dossier+'/qcm-prev-'+str(qcm.id)+'.tex','w','utf-8') as f:
	for ligne in genererTeXQcmPreview(qcm,'template.tex'):
	    f.write(ligne)
    try:
	 sp.check_output(['pdflatex','-output-directory',dossier,dossier+'/qcm-prev-'+str(qcm.id)+'.tex'])
	 sp.call(['pdftocairo','-svg','-l','1',dossier+'/qcm-prev-'+str(qcm.id)+'.pdf',dossier+'/qcm-prev-'+str(qcm.id)+'.svg'])
   	 os.remove(dossier+'/qcm-prev-'+str(qcm.id)+'.aux')
 	 os.remove(dossier+'/qcm-prev-'+str(qcm.id)+'.log')
   	 os.remove(dossier+'/qcm-prev-'+str(qcm.id)+'.tex')
   	 os.remove(dossier+'/qcm-prev-'+str(qcm.id)+'.pdf')
    except sp.CalledProcessError as er:
	erreurtemp=er.output.split('\n')
	erreur=""
	for ligne in erreurtemp:
		if ligne[:1] == "!":
	    		erreur += ligne+"\n"
	print(erreur)
	return erreur 
    return 0



def genererPdfs(args):
    
    idqcm=args[0]
    dossier=args[1]
    qcm=CoreQcm.objects.get(id=idqcm)
    print('gPDF nmax:'+str(qcm.nmax))
            
    try:
	os.mkdir(dossier)
    except:
	print('Impossible de créer le dossier '+dossier)
    try:
	os.mkdir(dossier+'/originaux')
	os.mkdir(dossier+'/copies')
    except:
	print('Impossible de créer les dossiers '+dossier+'/...')
	pass
    print(os.getcwd())
    template="template.tex"
    pdfuniteArg=list()
    pdfuniteArg.append('pdfunite')
    paquet=1
    i=0
    while qcm.coreqcmpdf_set.filter(paquet=paquet):
        asupprimer=list()
        for qcmpdf in sorted(qcm.coreqcmpdf_set.filter(paquet=paquet), key=lambda r: int(r.id)):
            i+=1
            with codecs.open(dossier+'/originaux/exos'+str(i)+".tex",'w','utf-8') as f:
                for ligne in genererTeX(qcmpdf,template):
                    f.write(ligne)
            print('ok')
            sp.check_output(['pdflatex','-output-directory',dossier+'/originaux',dossier+'/originaux/exos'+str(i)+".tex"])
            asupprimer.append(dossier+'/originaux/exos'+str(i)+".tex")
            asupprimer.append(dossier+'/originaux/exos'+str(i)+".pdf")
            os.remove(dossier+'/originaux/exos'+str(i)+".aux")
            os.remove(dossier+'/originaux/exos'+str(i)+".log")
            pdfuniteArg.append(dossier+'/originaux/exos'+str(i)+'.pdf')
        pdfuniteArg.append(dossier+"/originaux/exos-"+str(paquet)+'.pdf')
        if len(pdfuniteArg) > 3:
            sp.call(pdfuniteArg)
        else:
            sh.copy(dossier+'/originaux/exos'+str(i)+'.pdf',dossier+"/originaux/exos-"+str(paquet)+'.pdf')
        for fichier in asupprimer:
            os.remove(fichier)

        pdfuniteArg=list()
        pdfuniteArg.append('pdfunite')
        paquet+=1
    qcm.generation=2
    qcm.save()

def randomSample(taillesample,taillebanque,ntotal):
	
	random.seed()
	ret = list()
	for i in range(ntotal):
		ret.append(random.sample(range(taillebanque),taillesample))

	return ret

def genererQcm(args):
    qcm=args[0]
    nbpdfstexte=args[1]
    nbpdfstexte=nbpdfstexte.split(',')
    nbpdfs=list()
    ntotal=0
    for nb in nbpdfstexte:
        nbpdfs.append(int(nb))
        ntotal+=int(nb)

    nmax=int(np.trunc(np.log2(ntotal))+1)
    qcm.nmax=nmax
    qcm.save()
    codes=range(100000)
    random.seed(float('0.'+str(qcm.id)))
    random.shuffle(codes)
    random.shuffle(codes)
    random.shuffle(codes)

    paquet=0
    numero=1
    print("gQCM 1")
    listebanques = sorted(CoreNbExos.objects.filter(qcm=qcm), key=lambda r: int(r.position))
    rand = list()
    for nbexos in listebanques:
	rand.append(randomSample(nbexos.nb,len(nbexos.banque.coreexo_set.all()),ntotal))

    print("gQCM 2")
    for nb in nbpdfs:
        paquet+=1
	for i in range(nb):
	    position=1
	    qcmpdf=CoreQcmPdf(numero=numero,code=str(qcm.id)+"-"+str(codes[numero]),qcm=qcm,paquet=paquet)
            qcmpdf.save()
	    print('gQCM 3:'+str(i))
	    numerobanque = 0
            for nbexos in listebanques:
                listeexos = nbexos.banque.coreexo_set.all()
                #r=random.sample(range(len(listeexos)),nbexos.nb)
		r=rand[numerobanque][numero-1]
                for i in r:
                    exoqcmpdf = CoreExoQcmPdf(qcmpdf=qcmpdf,exo=listeexos[i],position=position)
                    exoqcmpdf.save()
		    position += 1

		numerobanque += 1
            numero+=1
    print('gQCM nmax:'+str(qcm.nmax)+' ou '+str(nmax))

##### correction

class Copie():
	
	def __init__(self):
		pass
	
	def ptsstr(self):
		ptsstr = []
		for pt in self.pts:
			for c in pt:
				ptsstr.append(str(c))
		return ','.join(ptsstr)
	
	#méthode pour lire les chiffres du code (la suite de 0101 en haut à droite)
	def lireChiffres(self):
		
		nmax=self.nmax
		print('nmax dans lireChiffres:'+str(nmax))
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
			if tt[i]>=t0*thresholdCaseCode:
				code.append('0')
			else:
				code.append('1')
		code="".join(code)
		self.code=code
		self.numero = int(code,2)
		print(self.code)
		
	#méthode pour trouver les trois repères de la copie, qui serviront à mettre l'élève et l'original à la même échelle
	def trouverpt(self,i):
		method = 'cv2.TM_CCOEFF_NORMED'	
		method = eval(method)
		print('trouverpt: avant res')
		res = cv2.matchTemplate(self.img[zones[i][1][0]:zones[i][1][1],zones[i][0][0]:zones[i][0][1]],pts[i],method)
		print('trouverpt: ok')
		min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
		loc = np.where( res >= max_val)
		loc = zip(*loc[::-1])
		ret=(loc[0][0]+zones[i][0][0],loc[0][1]+zones[i][1][0])
		return ret
		
	#recherche le séparateur entre le code en 01010 et celui d'avant. Utilisé pour trouver l'image du code
	def trouverSep(self):
		
		method = 'cv2.TM_SQDIFF_NORMED'
		method = eval(method)
		
		template = sep
		w, h = template.shape[::-1]
		
		res = cv2.matchTemplate(self.img,template,method)
		min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
		loc = np.where( res <= min_val)
		loc = zip(*loc[::-1])
		return loc[0]
	
	#enregistre l'image du code
	def lireN(self):
		locCode=self.trouverSep()
		w, h = sep.shape[::-1]
		self.imgCode=self.img[locCode[1]:locCode[1]+h,locCode[0]+w:self.pts[0][0]]

		
	
#classe pour les versions originales
class Original(Copie):
	
	def __init__(self,imgFichier,nmax):

		self.nmax = nmax
		self.lire(imgFichier,caseVide)
		self.pts=[self.trouverpt(0),self.trouverpt(1),self.trouverpt(2)]
		print(self.pts)
		self.lireN()
		print("ok lireN")
		self.lireChiffres()
		print("ok lireChiffres")
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
		self.res = cv2.matchTemplate(self.img[:,:dl],self.template,method)
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


class CopieEleve(Copie):
	
	def __init__(self,imgFichier,nmax):
		#on charge et on tronque PAS
		self.nmax = nmax
		self.imgFichier=imgFichier
		self.img = cv2.imread(imgFichier,0)
		self.imgRGB = cv2.imread(imgFichier,1)
		ret,self.img = cv2.threshold(self.img,200,255,cv2.THRESH_BINARY)
		print('Eleve: lecture ok')
		self.pts=[self.trouverpt(0),self.trouverpt(1),self.trouverpt(2)]
		print(self.pts)
		self.lireN()
		print('Eleve: lireN ok')
		self.lireChiffres()
		print('Eleve: lireChiffres ok')
		
		
	#on compare la copie à l'original (on met la copie de l'élève à l'échelle de l'original, on lit les cases, et on décide si elles sont cochées ou non
	def compare(self,originalpts,originalcases):
		
		w, h = dimCaseVide
		M = cv2.getAffineTransform(np.array(self.pts,dtype="float32"),np.array(originalpts,dtype="float32"))
		rows,cols = self.img.shape
		self.img = cv2.warpAffine(self.img,M,(cols,rows))
		self.imgRGB = cv2.warpAffine(self.imgRGB,M,(cols,rows))
		
		self.reponses=list()
		tt=list()
		for pt in originalcases:
			timg=self.img[pt[1]:pt[1]+h,pt[0]:pt[0]+w]
			tloc=np.where(timg>200)
			tloc=zip(*tloc[::-1])
			tt.append(len(tloc))
			
		tt.sort(reverse=True)
		for pt in originalcases:
			timg=self.img[pt[1]:pt[1]+h,pt[0]:pt[0]+w]
			tloc=np.where(timg>200)
			tloc=zip(*tloc[::-1])
			tn=len(tloc)
			if tn>=tt[0]*thresholdCase:
				self.reponses.append('0')
			else:
				self.reponses.append('1')
				timg=self.img[pt[1]:pt[1]+h,pt[0]:pt[0]+w]
				cv2.rectangle(self.imgRGB, (pt[0]-w/2,pt[1]-h/2), (pt[0] + 3*w/2, pt[1] + 3*h/2), (0,0,255), 2)
		
		#cv2.imwrite(self.conf.dossier+"/copie-"+self.code+"-"+str(random.random())+".jpg",self.imgRGB)
		cv2.imwrite(self.imgFichier[:-4]+"-corrigee.jpg",self.imgRGB)
		
		del self.imgRGB
		del self.img
		del self.imgCode
	

def importOriginal(qcm,fichier,dossier):
	sp.check_call(["convert", "-density", '200', fichier, dossier+"/original.jpg"])
	listeoriginaux=sorted([x for x in os.listdir(dossier) if x.endswith('.jpg')], key=lambda r: int(''.join(x for x in r if x.isdigit())))
	print('importOriginal,listeoriginaux:'+str(','.join(listeoriginaux)))
	for i in range(len(listeoriginaux)):
		print('importOriginal:'+str(i))
		ori=Original(dossier+"/"+listeoriginaux[i],qcm.nmax)
		qcmpdf = CoreQcmPdf.objects.get(qcm=qcm,numero=ori.numero)
		qcmpdf.pages += 1
		print(ori.cases)
		for case in ori.cases:
			print(case)
			qcmpdf.positionscases += str(qcmpdf.pages)+','+str(case[0])+','+str(case[1])+';'
		qcmpdf.positionspts += ori.ptsstr()+";"
		print(qcmpdf.positionspts)
		qcmpdf.save()
		os.remove(dossier+"/"+listeoriginaux[i])
	

def importOriginaux(idqcm):
	qcm=CoreQcm.objects.get(id=idqcm)
	dossier='media/ups/'+str(qcm.prof.id)+'/'+str(qcm.id)+'/'
	nmax=qcm.nmax
	print('importOriginaux nmax:'+str(nmax))
	print('importOriginaux qcm:'+str(qcm))
	for fichier in [x for x in os.listdir(dossier+"originaux") if x.endswith('.pdf')]:
		importOriginal(qcm,dossier+'originaux/'+fichier,dossier+'originaux')
	qcm.generation = 3
	qcm.save()


def correctionCopies(args):
	idqcm = args[0]
	cps = args[1]
	qcm = CoreQcm.objects.get(id=idqcm)
	dossier = 'media/ups/'+str(qcm.prof.id)+'/'+str(qcm.id)
	try:
		os.mkdir(dossier+"/copies/"+str(cps.id))
		#sp.check_call(["convert", "-size", "1653x2338", cps.fichier.path, dossier+"/copies/"+str(cps.id)+"/copies.jpg"])
		sp.check_call(["convert", "-density", '200' , cps.fichier.path, dossier+"/copies/"+str(cps.id)+"/copies.jpg"])
		print('On y est!')
		listecopies=sorted([x for x in os.listdir(dossier+"/copies/"+str(cps.id)) if x.endswith('.jpg')], key=lambda r: int(''.join(x for x in r if x.isdigit())))
		copies=list()
		copies.append([CopieEleve(dossier+"/copies/"+str(cps.id)+"/"+listecopies[0],qcm.nmax)])
		for i in range(len(listecopies)-1):	
			cop=CopieEleve(dossier+"/copies/"+str(cps.id)+"/"+listecopies[i+1],qcm.nmax)
		 ### les copies doivent être scannées dans l'ordre
			if cop.code == copies[-1][0].code:
				copies[-1].append(cop)
			else:
				copies.append([cop])

		eleveinconnu,creation=Eleve.objects.get_or_create(nom="Élève non associé")
		for copie in copies:
			try:
				qcmpdf = CoreQcmPdf.objects.get(numero=copie[0].numero,qcm=cps.qcm)
				if len(copie) != qcmpdf.pages:
					raise NameError('Erreur de correction: pas le bon nombre de pages')
				if qcmpdf.reponses != '':
					raise NameError('Erreur de correction: copie déjà corrigée: '+str(copie[0].imgFichier))
				for i in range(len(copie)):
					print("correctionCopie: ",copie[i].imgFichier)
					copie[i].compare(qcmpdf.getpts(i+1),qcmpdf.getcases(i+1))
					print('réponses trouvées :'+''.join(copie[i].reponses))
					qcmpdf.reponses+=''.join(copie[i].reponses)
				qcmpdf.save()
			except Exception, er:
				print('Erreur de correction: lecture des cases et points: '+str(er))
	except Exception,er:
		print("Erreur lors de la correction",er)


