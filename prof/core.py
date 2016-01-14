#!/usr/bin/python
#-*- coding: utf-8 -*-

#le principe: on a des listes d'exos dans des fichiers.
#chaque exo est de la forme @@@QCM
#							question
#							note@reponse1
#							note@reponse2
#on veut tirer un certain nombre de questions au hasard dans chaque liste d'exos que l'on se donne

import sys			
import random		# pour tirer des exos aléatoirement, et pour les identifiants des qcm
import io			
import subprocess as sp	# pour appliquer le compilateur LaTex pour produire des énoncés mathématiques.
import os		# permet la gestion des fichiers, au travers du code Python. (supprimer, créer des dossiers.)
import time			
import shutil as sh	# appelé une seule fois pour copier un dossier.	
import numpy as np	# les fonctions mahtématiques pour python: la troncature, , ...
import cv2		# appliqué pour reconnaitre des éléments sur les feuilles numérisées (cases remplies, balises)
from prof.models import *  # La base de données, donc les qcm, les exos, les copies des élèves, et ainsi de suite.
import codecs		# Ouverture des fichiers pour lire ou pour les mettre à jour en écrivant dedans.

#variables utilisées

sepTeXExos = "%%%exos\n"
sepCodeExo = "%%%codeExo\n"
sepNom = "%%%nomQCM\n"
sepTexte = "%%%texteQCM\n"

# On doit pouvoir reconnaitre des cases numérisés pour pouvoir:
	# - reconnaitre un questionnaire numérisé par son code de carrés
	# - évaluer la réponse donnée par une élève (les cases qu'il a noircis)
caseVide = "case_vide.jpg"	 # le chemin d'une image d'une case vide
dimCaseVide = cv2.imread(caseVide,0).shape[::-1]	
sep=cv2.imread("sep.jpg",0)
pts=[cv2.imread("pt1.jpg",0),cv2.imread("pt2.jpg",0),cv2.imread("pt3.jpg",0),]
zones=[[(1000,1700),(0,400)],[(1300,1700),(2100,2400)],[(0,400),(2100,2300)]]
thresholdCaseCode=0.75
thresholdCase=0.5 #0.75
dl=600
		


def exo2tex(exo,correction):
	
	"""
	entrée:		un objet de type CoreExo.
			un booléén qui indique s'il faut que la correction soit indiquée dans la sortie.
	sortie:		une liste des morceaux d'exos en code Tex brut. Les moreceaux sont des chaînes.
	
	Cette fonction est appelée dans genererTexHtml et dans genererTex. 
	La forme de l'objet renvoyé s'explique par le fait suivant:
	Les lignes doivent être mises une par une au bon endroit dans un gabarit HTML. 
	"""

    TeXexo=list() #liste contenant le code TeX pour la liste aGen d'exos,  
    TeXexo.append(u"\\begin{exo}\n")
    TeXexo.append(exo.question+u"\n")
    if exo.corereponse_set.all():	# Si les réponses possibles sont enregistrées dans la base de données
    	TeXexo.append(u"\n\\medskip\n\\begin{minipage}{ \\textwidth}\\begin{itemize}[label=$\\square$]\n")
    	# La ligne ci-dessus force LaTex d'appliquer la mise en forme typique d'une question à multiple choix.
    	for reponse in sorted(exo.corereponse_set.all(), key=lambda r: int(r.position)):
    		# à chaque tour de boucle on ajoute une question.
		if reponse.nom == "v" and correction:	# la bonne réponse est affiché en vert si correction=True.
			TeXexo.append(u"\item {\\color{green}"+reponse.texte+u"}\n")
		else:	# Sinon on ne précise rien sur la couleur de l'affichage
			TeXexo.append(u"\item "+reponse.texte+u"\n")
   	TeXexo.append(u"\\end{itemize}\end{minipage}\n") # Indique la fin de la mise en forme particulière des réponses. 
    TeXexo.append(u"\\end{exo}\n\\bigskip\n")	# Indique la fin de l'exo et laisse quelques lignes en blanc après.
    if correction:	# Si la valeur d'entrée "correction vaut True", la correction est rajouté en bas en rouge.
	TeXexo.append(u"\\begin{cor}\n{\\color{red}")	
	TeXexo.append(exo.corrige)	# BOULOT expliquer les mots-clés begin{} et end{}
	TeXexo.append(u"}\n\\end{cor}\n\\bigskip")
    return TeXexo

    
def ntosymb(n,nmax):
"""
Entrée:		une chaîne qui contient des 1 et des 0, appelé n.
		un nombre qui indique la longueur de la suite renvoyée par la fonction
Sortie:		une chaîne qui contient le code LaTex d'une suite de carrés noirs ou blancs.

Pour chaque 1, un carré noir est ajouté à la suite dont obtient le code LaTex.
Pour chaque 0, un carré blanc est ajouté.
Pour finir, au début de la suite bdes carrés blancs sont ajoutés 
de telle sorte que la suite ait nmax cases.

Quelques exemples:
ntosymb(5,"101") 	renvoie le code de	blanc, blanc, noir, blanc, noir
ntosymb(5,"1") 		renvoie le code de	blanc, blanc, blanc, blanc, blanc
ntosymb(4,"110") 	renvoie le code de	blanc, noir, noir, blanc

Avec cette suite de cases, on peut produire un "code de carrés" au moyen de laquelle
un QCM peut être reconnu par des les fonctions décrites dans Core,
au travers du module openCV de Python.



"""
    symb=""    
    for i in range(nmax-len(n)):
    	# on met des cases blanches au début pourqu'il y ait nmax carrés.
    	
    	
        symb=symb+u"\\Box"
    for i in n:
        if i=='1':
            symb=symb+u"\\blacksquare"
        if i=='0':
            symb=symb+u"\\Box"
    return symb
    

def genererTeXHTML(exo,template):

"""
entrée:		un objet de type CoreExo
		un gabarit HTML (template)
sortie:		Une liste de chaînes, en partie code TeX, en partie code HTML.

Les composants de la liste, s'ils sont mis bout à bout, 
forment le gabarit avec les éléments de l'exo insérés aux bons endroits.
Dans les exos, les valeurs des réponses ont étées marquées. (bonne réponse en vert)
La fonction elle-même utilise exo2tex pour produire les lignes de code latex de l'exo.
La fonction est appelée dans genererSvg où le code sera traité plus loin.
"""

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
"""
entrée:		un objet de type CoreQcm
		un gabarit HTML (template)
sortie:		Une liste de chaînes, en partie code TeX, en partie code HTML.

Les composants de la liste, s'ils sont mis bout à bout, 
forment le gabarit avec les éléments de l'aperçu de QCM insérés aux bons endroits.

La fonction elle-même utilise ntosymb.
La fonction est appelée dans genererSvgQcm où le code sera traité plus loin.
"""

    with codecs.open(template, 'r', 'utf-8') as f:
        TeX=f.readlines()
    indexExos=TeX.index(sepTeXExos) 
    TeX.insert(TeX.index(sepNom),qcm.nomTeX)
    TeX.insert(TeX.index(sepTexte),qcm.texteTeX)
    TeX.insert(TeX.index(sepCodeExo),u"17-168748 \\Huge + $ "+ntosymb('1010101',7)+u" $ \\normalsize")

    return TeX


def genererTeX(qcmpdf,template):
	
"""
entrée:		un objet de type CoreQcmPdf
		un gabarit HTML (template)
sortie:		une liste de chaînes qui contiennent du code HTMl et du code LaTex.
		L'ensemble de chaînes reliées les unes aux autres est le corps d'un QCM en code brut. 

Le gabarit est ouvert et coupé en lignes. Ensuite les exos sont produits (avec tex2exo) et insérés.
À partir du nombre d'élèves est déduit le "code de carrés" qui est mis au lieu souhaité,
ainsi que les renseignements sur les moyens permis.

Dans cette fonction les fonctions tex2exo et ntosymb sont à l'oeuvre. 
"""
    
    with codecs.open(template, 'r', 'utf-8') as f:	# Le gabarit est ouvert.
        TeX=f.readlines()		# On en garde un gabarit découpé.	
    indexExos=TeX.index(sepTeXExos)	# L'endroit où commencent les exos du questionnaire.
    TeX.remove(sepTeXExos)		# Ligne inutile.

    for exoqcmpdf in sorted(CoreExoQcmPdf.objects.filter(qcmpdf=qcmpdf), key=lambda r: int(r.position)):
	exo = exoqcmpdf.exo		
        texexo = exo2tex(exo,False)
        for ligne in texexo:
            TeX.insert(indexExos,ligne)
            indexExos+=1
    nmax=int(np.trunc(np.log2(len(qcmpdf.qcm.coreqcmpdf_set.all())))+1)
    #nmax est le nombre de cases dont on a besoin pour que chaque copie (BOULOT) ait un code de carré unique.
    TeX.insert(TeX.index(sepCodeExo),str(qcmpdf.code)+u" \\Huge + $ "+ntosymb(str(bin(qcmpdf.numero)[2:]),nmax)+u" $ \\normalsize")
    TeX.insert(TeX.index(sepNom),qcmpdf.qcm.nomTeX)
    TeX.insert(TeX.index(sepTexte),qcmpdf.qcm.texteTeX)

    return TeX


def genererSvg(exo,dossier):
"""
entrée:		un objet de type CoreExo
		un nom de dossier dans lequel est fait un ficher à préciser (BOULOT) 
sortie:		comme produit secondaire:
		-0 si la compilation du code LaTex s'est bien déroulé.
		-une erreur de compilation (chaîne), bien mise en forme, si la compilation LaTex échoue.

Cette fonction fait un fichier qui contient un gabarit HTML avec des formules compilés. 
La compilation s'est fait à l'aide du module Python subprocess,
qui permet d'appliquer des logiciels de l'extérieur et de récupérer des erreur qu'il renvoie en cas de malheur.
"""
    
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

"""
entrée:		un objet de type CoreQcm
		un nom de dossier dans lequel est fait un ficher à préciser (BOULOT) 
sortie:		comme produit secondaire:
		-0 si la compilation du code LaTex s'est bien déroulé.
		-une erreur de compilation (chaîne), bien mise en forme, si la compilation LaTex échoue.

Cette fonction fait l'en-tête du questionnaire avec des formules compilés.
PAS LE QCM TOUT ENTIER comme le nom de la fonction le laisse penser.
La compilation s'est fait à l'aide du module Python subprocess,
qui permet d'appliquer des logiciels de l'extérieur et de récupérer des erreur qu'il renvoie en cas de malheur.
"""

    with codecs.open(dossier+'/qcm-prev-'+str(qcm.id)+'.tex','w','utf-8') as f:
	for ligne in genererTeXQcmPreview(qcm,'template.tex'):
	    f.write(ligne.decode())
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
"""
entrée:		Une paire dont:
		- le premier composant est l'identifiant d'un QCM.
		- le premier est le nom d'un dossier
sortie:		aucune

Dans un premier temps la fonction essaie de faire une arborescence de dossiers ayant le nom renseigné,
afin d'enregistrer le pdf que va produire la fonction.
"""
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
    print(os.getcwd())		# cwd = Current Working Directory
    template="template.tex"	
    pdfuniteArg=list()		# Ici on mettre tous les chemin des pdf produits qu'on unira plus tard.	
    pdfuniteArg.append('pdfunite')	# Il s'agit bien du mot anglais unite, pas d'unité
    paquet=1
    i=0			# i va servir à numéroter les pdfs qu'on produit.
    while qcm.coreqcmpdf_set.filter(paquet=paquet):
        asupprimer=list() # recense les fichiers (pdf,tex) faits par le compilateur LaTex qui deviendront inutiles. 
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
	# maintenant le jour n'est joué que pour le premier paquet!
	# BOULOT: 	Tirer au clair la suite du déroulement du procédé. 
	
        pdfuniteArg=list()
        pdfuniteArg.append('pdfunite')
        paquet+=1
    qcm.generation=2
    qcm.save()

def randomSample(taillesample,taillebanque,ntotal):
"""
entrée:		la taille d'un ensemble de nombres qu'on tire aléatoirement, à plusieurs reprises.
		La taille de l'ensemble duquel les nombres seront tirés.
		Le nombre de fois qu'on répète ce tirage.
sortie:		une liste de listes, donc une suite d'ensemble tirés au hasard comme expliqué.

Va servir à choisir aléatoirement des exos de la banque,
en ayant soin de ne pas mettre deux fois le même exo dans un questionnaire.

La fonction est utilisée dans genererQcm.
C'est par ailleurs la seule fonction utilisant Random pour vraiment faire intervenir le hasard.
"""
	random.seed()
	ret = list()
	for i in range(ntotal):
		ret.append(random.sample(range(taillebanque),taillesample))
		# random.sample(ens,m) = tire m nombres distincts de l'ensemble "ens".  
	return ret

def genererQcm(args):
"""
entrée:		une liste
		-dont le premier composant est un objet de type CoreQcm
		-dont le deuxième composant est une chaîne qui motre
		 comment les qcm sont répartis en paquets:
		 exemple: pour 200 qcm ont peut choisir "30, 70, 100"
		 donc un paquet de 30 qcm, un paquet de 70 et un de 100.
sortie:		aucune valeur.
Même si cette fontion ne renvoie ne renvoie rien elle fait beaucoup au niveau des modèles:
Les champs du QCM pris en entrée sont mis à jour sont mis à jour  
"""

    qcm=args[0]
    nbpdfstexte=args[1] # une chaîne qui montre comment les versions sont réparties en paquets.
    nbpdfstexte=nbpdfstexte.split(',') # on en fait une liste.
    nbpdfs=list()	
    ntotal=0		# On aditionne les tailles de tous les paquest pour compter le nombre de qcm requis.
    for nb in nbpdfstexte:
        nbpdfs.append(int(nb))
        ntotal+=int(nb)
	# nmax = le nombre de carrés noirs/blancs dont on a besoin pour donner un code unique à chaque qcm.
	# autrement dit la longueur du code carrés.
    nmax=int(np.trunc(np.log2(ntotal))+1)	
    qcm.nmax=nmax	# mise à jour de cette longueur dans l'enregistrement qcm du modèle CoreQcm 
    qcm.save()		# la sauvegarde (ceci a été décrit dans le corps d'une fonction après tout.)
    codes=range(100000)	# les fameux codes aux travers desquels on récupère les bons attributs du qcm.
    random.seed(float('0.'+str(qcm.id)))
    random.shuffle(codes)
    random.shuffle(codes)
    random.shuffle(codes)

    paquet=0	# Dans un premier temps on traite le premier paquet de qcm.
    numero=1	# BOULOT: le sens du numéro est à éclaircir.
    print("gQCM 1")
    # Fait une liste d'objets par le biais desquels on peut atteindre les banques d'exos dont doivent être tirés les exos.
    listebanques = sorted(CoreNbExos.objects.filter(qcm=qcm), key=lambda r: int(r.position))
    rand = list()
    for nbexos in listebanques:		# Pour chaque banque...
    	# On tire un autant d'ensembles de numéros d'exos de la taille requise qu'on en a besoin
    	# pour pouvoir tous les qcm en questions.
	rand.append(randomSample(nbexos.nb,len(nbexos.banque.coreexo_set.all()),ntotal))

    print("gQCM 2")
    	
    for nb in nbpdfs:	# rappel: nbpfs est maintenant une liste de nombres de qcm par paquet
        paquet+=1	# on passe au paquet suivant.
	for i in range(nb):	# pour chaque qcm qu'on doit faire dans le paquet
	    position=1		
	    # on crée un nouvel enregistrement du modèle CoreQcmPdf, avec les données qu'on a créées
	    qcmpdf=CoreQcmPdf(numero=numero,code=str(qcm.id)+"-"+str(codes[numero]),qcm=qcm,paquet=paquet)
            qcmpdf.save()	# sauvegarde pourque ce changement soit maintenu quand l'appel à la fonction s'achève.
	    print('gQCM 3:'+str(i))	
	    numerobanque = 0	
	    # Dans cette boucle les exos aléatoires dont on a déjà sorti les nombres sont enfin attribués.
            for nbexos in listebanques:		# pour chaque "objet" par lequel on passe pour accéder à la banque
                listeexos = nbexos.banque.coreexo_set.all()	# on rassemble tous les exos dans cette banque
                #r=random.sample(range(len(listeexos)),nbexos.nb)
		r=rand[numerobanque][numero-1]	# rappel: rand est une suite de tirages d'ensembles de numéros d'exos.	
                for i in r:	# Du coup on parcourt ici tous les numéros d'exos d'un tirage en particulier.
                    exoqcmpdf = CoreExoQcmPdf(qcmpdf=qcmpdf,exo=listeexos[i],position=position)
                    exoqcmpdf.save()	# Ajout et sauvegarde d'un objet qui rattache une copie à une banque. 
		    position += 1	# (BOULOT à préciser)

		numerobanque += 1
            numero+=1
    print('gQCM nmax:'+str(qcm.nmax)+' ou '+str(nmax))		# BOULOT: à éclaircir.

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
		
		hardthreshold = 0.0001
		method = 'cv2.TM_SQDIFF_NORMED'		
		method = eval(method)
		self.res = cv2.matchTemplate(self.img[:,:dl],self.template,method)
		loc = np.where( self.res <= hardthreshold)
		loc = zip(*loc[::-1])
		n=len(loc)
		#if n>0:
			#loc.sort(key=lambda x: x[0])
			
		##on supprime s'il y a des doublons
		#aSupprimer=list()
		#for i in range(n):
			#for j in range(i+1,n):
				#if abs(loc[j][0]-loc[i][0])<w and j not in aSupprimer and i not in aSupprimer:
					#aSupprimer.append(j)
		#aSupprimer.sort(reverse=True)
		#for j in aSupprimer:
			#del loc[j]
			
		
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
		
		cv2.imwrite(self.imgFichier,self.imgRGB)
		self.reponses=list()
		#tt=list()
		#for pt in originalcases:
		#	timg=self.img[pt[1]:pt[1]+h,pt[0]:pt[0]+w]
		#	tloc=np.where(timg>200)
		#	tloc=zip(*tloc[::-1])
		#	tt.append(len(tloc))
			
		#tt.sort(reverse=True)
		for pt in originalcases:
			timg=self.img[pt[1]:pt[1]+h,pt[0]:pt[0]+w]
			tloc=np.where(timg>200)
			tloc=zip(*tloc[::-1])
			tn=len(tloc)
			if tn>=w*h*thresholdCase:
				self.reponses.append('0')
			#	cv2.rectangle(self.imgRGB, (pt[0]-w/2,pt[1]-h/2), (pt[0] + 3*w/2, pt[1] + 3*h/2), (0,255,255), 2)
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
			fichiers = ''
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
					fichiers += copie[i].imgFichier[:-4]+'-corrigee.jpg;'
				qcmpdf.save()
				cp = CoreCopie(eleve=eleveinconnu,qcmpdf=qcmpdf,fichiers=fichiers)
				cp.save()
			except Exception, er:
				print('Erreur de correction: lecture des cases et points: '+str(er))
 		cps.corrigees=True
		cps.save()
	except Exception,er:
		print("Erreur lors de la correction",er)
		copies.delete()
