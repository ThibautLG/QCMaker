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

#variables utilisées

sepTeXExos = "%%%exos\n"
sepCodeExo = "%%%codeExo\n"
sepNom = "%%%nomQCM\n"
sepTexte = "%%%texteQCM\n"

def exo2tex(exo):

    TeXexo=list() #liste contenant le code TeX pour la liste aGen d'exos, aGen est une list() de numéros d'exos de cette instance de classe, dont on doit générer le 
    TeXexo.append("\\begin{exo}\n")
    TeXexo.append(exo.question+"\n")
    TeXexo.append("\n\\medskip\n\\begin{minipage}{ \\textwidth}\\begin{itemize}[label=$\\square$]\n")
    for reponse in sorted(exo.corereponse_set.all(), key=lambda r: int(r.id)):
        TeXexo.append("\item "+reponse.texte+"\n")
    TeXexo.append("\\end{itemize}\end{minipage}\n")
    TeXexo.append("\\end{exo}\n\\bigskip\n")

    return TeXexo

    
def ntosymb(n,nmax):
    symb=""    
    for i in range(nmax-len(n)):
        symb=symb+"\\Box"
    for i in n:
        if i=='1':
            symb=symb+"\\blacksquare"
        if i=='0':
            symb=symb+"\\Box"

    return symb
    

def genererTeX(qcmpdf,template):
    

    with open(template, 'r') as f:
        TeX=f.readlines()
    indexExos=TeX.index(sepTeXExos)
    TeX.remove(sepTeXExos)

    for exo in sorted(qcmpdf.exos.all(), key=lambda r: int(r.id)):
        texexo = exo2tex(exo)
        for ligne in texexo:
            TeX.insert(indexExos,ligne)
            indexExos+=1
    nmax=int(np.trunc(np.log2(len(qcmpdf.qcm.coreqcmpdf_set.all())))+1)
    TeX.insert(TeX.index(sepCodeExo),str(qcmpdf.code)+" \\Huge + $ "+ntosymb(str(bin(qcmpdf.numero)[2:]),nmax)+" $ \\normalsize")
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
            with open(dossier+'/originaux/exos'+str(i)+".tex",'w') as f:
                for ligne in genererTeX(qcmpdf,dossier+'/'+template):
                    f.write(ligne)
            print('ok')
            sp.call(['pdflatex','-output-directory',dossier+'/originaux',dossier+'/originaux/exos'+str(i)+".tex"])
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

    listebanques = sorted(CoreNbExos.objects.filter(qcm=qcm), key=lambda r: int(r.id))
    
    for nb in nbpdfs:
        paquet+=1
        for i in range(nb):
            qcmpdf=CoreQcmPdf(numero=numero,code=str(qcm.id)+"-"+str(codes[numero]),qcm=qcm,paquet=paquet)
            qcmpdf.save()

            for nbexos in listebanques:
                listeexos = nbexos.banque.coreexo_set.all()
                r=random.sample(range(len(listeexos)),nbexos.nb)
                for i in r:
                    exoqcmpdf = CoreExoQcmPdf(qcmpdf=qcmpdf,exo=listeexos[i])
                    exoqcmpdf.save()
            numero+=1
            
