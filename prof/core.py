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
from prof.models import *
import codecs

#variables utilisées

sepTeXExos = "%%%exos\n"
sepCodeExo = "%%%codeExo\n"
sepNom = "%%%nomQCM\n"
sepTexte = "%%%texteQCM\n"

def exo2tex(exo):

    TeXexo=list() #liste contenant le code TeX pour la liste aGen d'exos, aGen est une list() de numéros d'exos de cette instance de classe, dont on doit générer le 
    TeXexo.append(u"\\begin{exo}\n")
    TeXexo.append(exo.question+u"\n")
    TeXexo.append(u"\n\\medskip\n\\begin{minipage}{ \\textwidth}\\begin{itemize}[label=$\\square$]\n")
    for reponse in sorted(exo.corereponse_set.all(), key=lambda r: int(r.position)):
        TeXexo.append(u"\item "+reponse.texte+u"\n")
    TeXexo.append(u"\\end{itemize}\end{minipage}\n")
    TeXexo.append(u"\\end{exo}\n\\bigskip\n")

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
    

def genererTeX(qcmpdf,template):
    

    with codecs.open(template, 'r', 'utf-8') as f:
        TeX=f.readlines()
    indexExos=TeX.index(sepTeXExos)
    TeX.remove(sepTeXExos)

    for exoqcmpdf in sorted(CoreExoQcmPdf.objects.filter(qcmpdf=qcmpdf), key=lambda r: int(r.position)):
	exo = exoqcmpdf.exo
        texexo = exo2tex(exo)
        for ligne in texexo:
            TeX.insert(indexExos,ligne)
            indexExos+=1
    nmax=int(np.trunc(np.log2(len(qcmpdf.qcm.coreqcmpdf_set.all())))+1)
    TeX.insert(TeX.index(sepCodeExo),str(qcmpdf.code)+u" \\Huge + $ "+ntosymb(str(bin(qcmpdf.numero)[2:]),nmax)+u" $ \\normalsize")
    TeX.insert(TeX.index(sepNom),qcmpdf.qcm.nomTeX)
    TeX.insert(TeX.index(sepTexte),qcmpdf.qcm.texteTeX)

    return TeX


def genererPdfs(qcm,dossier):
    
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
                for ligne in genererTeX(qcmpdf,dossier+'/'+template):
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
        print(asupprimer)
        for fichier in asupprimer:
            os.remove(fichier)

        pdfuniteArg=list()
        pdfuniteArg.append('pdfunite')
        paquet+=1

    
def genererQcm(qcm,nbpdfstexte):
    
    nbpdfstexte=nbpdfstexte.split(',')
    nbpdfs=list()
    ntotal=0
    for nb in nbpdfstexte:
        nbpdfs.append(int(nb))
        ntotal+=int(nb)

    nmax=int(np.trunc(np.log2(ntotal))+1)
    codes=range(100000)
    random.seed(float('0.'+str(qcm.id)))
    random.shuffle(codes)
    random.shuffle(codes)
    random.shuffle(codes)

    paquet=0
    numero=1

    listebanques = sorted(CoreNbExos.objects.filter(qcm=qcm), key=lambda r: int(r.position))
    
    for nb in nbpdfs:
        paquet+=1
	for i in range(nb):
	    position=1
	    qcmpdf=CoreQcmPdf(numero=numero,code=str(qcm.id)+"-"+str(codes[numero]),qcm=qcm,paquet=paquet)
            qcmpdf.save()

            for nbexos in listebanques:
                listeexos = nbexos.banque.coreexo_set.all()
		print(listeexos,nbexos.nb)
                r=random.sample(range(len(listeexos)),nbexos.nb)
                for i in r:
                    exoqcmpdf = CoreExoQcmPdf(qcmpdf=qcmpdf,exo=listeexos[i],position=position)
                    exoqcmpdf.save()
		    position += 1
            numero+=1
            
