#-*- coding:utf-8 -*-

from django.shortcuts import render,redirect,HttpResponse
from prof.models import *
from prof.forms import *
import os
import mimetypes
from django.core.servers.basehttp import FileWrapper
from qcmaker import *
import pickle
import qcmimport as qcmi
import qcmcorrecteur as qcmc
from django.core.files import File
import random
from bgjob import BgJob
#from django_rq import job



def is_prof(nom):
	listeprof=['tle-gouic','jliandrat','cpouet','gchiavassa']
	if nom in listeprof:
		return True
	else:
		return False


def genererCSVnotes(qcm):
	dossier=os.path.dirname(qcm.template.path)+"/"
	codes=range(100000)
	random.seed(float('0.'+str(qcm.id)))
	random.shuffle(codes)
	random.shuffle(codes)
	random.shuffle(codes)
	listecopies=qcm.copiecorrigee_set.all()
	fichierCSV=io.FileIO(dossier+"notes.csv",'w')
	for copie in listecopies:
		fichierCSV.write(str(codes[copie.numero])+","+copie.eleve.nom.encode('ascii','replace')+","+str(copie.note))
		fichierCSV.write("\n")
	fichierCSV.close()
	return str(dossier+"notes.csv")
	

def importoriginaux(qcmpdf):
	dossier=os.path.dirname(qcmpdf.qcm.template.path)+"/"
	conf=qcmi.ConfigurationImport(dossier)
	conf.nmax=qcmpdf.qcm.nmax
	conf.pickle = qcmpdf.fichier+".pickle"
	sp.check_call(["convert", "-density", '200', qcmpdf.fichier, dossier+"originaux/original.jpg"])
	listeoriginaux=sorted([x for x in os.listdir(dossier+"originaux") if x.endswith('.jpg')], key=lambda r: int(''.join(x for x in r if x.isdigit())))
	originaux=list()
	for i in range(len(listeoriginaux)):
		ori=qcmi.Original(dossier+"originaux/"+listeoriginaux[i],conf)
		if len(originaux)==0:
			originaux.append([ori])
		else:
			if ori.code == originaux[-1][0].code:
				originaux[-1].append(ori)
			else:
				originaux.append([ori])
		os.remove(dossier+"originaux/"+listeoriginaux[i])
	with open(conf.pickle, 'w') as f:
		pickle.dump(originaux, f)
	
	qcmpdf.traite=True
	qcmpdf.save()


def correction(cps):
	
	try:
		dossier=os.path.dirname(cps.qcm.template.path)
		os.mkdir(dossier+"/copies/"+str(cps.id))
		sp.check_call(["convert", "-density", '200', cps.fichier.path, dossier+"/copies/"+str(cps.id)+"/copies.jpg"])
		listepickle=[x for x in os.listdir(dossier+"/originaux") if x.endswith('.pickle')]
		originaux=list()
		for p in listepickle:
			with open(dossier+"/originaux/"+p) as f:
				originaux += pickle.load(f)

		conf=qcmi.ConfigurationImport(dossier+"/")
		conf.nmax=cps.qcm.nmax
		listecopies=sorted([x for x in os.listdir(dossier+"/copies/"+str(cps.id)) if x.endswith('.jpg')], key=lambda r: int(''.join(x for x in r if x.isdigit())))
		copies=list()
		copies.append([qcmi.Eleve(dossier+"/copies/"+str(cps.id)+"/"+listecopies[0],conf)])
		for i in range(len(listecopies)-1):	
			cop=qcmi.Eleve(dossier+"/copies/"+str(cps.id)+"/"+listecopies[i+1],conf)
		 ### les copies doivent être scannées dans l'ordre
			if cop.code == copies[-1][0].code:
				copies[-1].append(cop)
			else:
				copies.append([cop])

		listeCodes=[o[0].code for o in originaux]
		eleveinconnu,creation=Eleve.objects.get_or_create(nom="Élève non associé")
		copiesasupprimer=list()
		for copie in copies:

			if not CopieCorrigee.objects.filter(numero=int(copie[0].code,2),qcm=cps.qcm):

				cc=CopieCorrigee(copies=cps,numero=int(copie[0].code,2),eleve=eleveinconnu,qcm=cps.qcm)
				cc.save()

				try:
					for i in range(len(copie)):
						copie[i].compare(originaux[listeCodes.index(copie[i].code)][i])
						ccjpg=CopieJPG(copiecorrigee=cc,fichier=copie[i].imgFichier)
						ccjpg.save()

				except Exception,er:
					print('Erreur de correction: ',er)
					cc.delete()
					copiesasupprimer.append(copie)
			else:
				copiesasupprimer.append(copie)

		for copie in copiesasupprimer:
			copies.remove(copie)

		listeRep=list()
		for i in range(len(copies)):
			listeRep.append([copies[i][0].code,"".join(copies[i][0].reponses)])
			for j in range(len(copies[i])-1):
				listeRep[-1][1]+="".join(copies[i][j+1].reponses)
		fichierCSV=io.FileIO(dossier+"/copies/corr-"+str(cps.id)+".csv",'w')
		for rep in listeRep:
			fichierCSV.write(","+str(int(rep[0],2))+","+rep[1])
			fichierCSV.write("\n")
	       	fichierCSV.close()

		reponsesElevesCSV=dossier+"/copies/corr-"+str(cps.id)+".csv"
		CorrSortie=dossier+"/corrections.csv"
	 #nomCSV=dossier+"/copies/notes-"+str(cps.id)+".csv"
		corr=qcmc.correction(CorrSortie,reponsesElevesCSV)
		corr.calculer()
		for note in corr.note:
			cc=CopieCorrigee.objects.get(numero=int(note[0]),copies=cps)
			cc.note=note[1]
			cc.save()

		cps.corrigees=True
		cps.save()
	except Exception,er:
		print("Erreur lors de la correction",er)
		cps.corrigees=True
		cps.save()


def generateur(qcm):

	nbexos=list()
	listexosqcm=list()
	for nb in sorted(NbExos.objects.filter(qcm=qcm), key=lambda r: int(r.id)):
		nbexos.append(nb.nbexos)
		listexosqcm.append(nb.exo.fichier.path)
	config=ConfigurationMaker(steps=qcm.nbpdfs,numexam=qcm.id)
	config.listeFichiers=listexosqcm
	config.nbexos=nbexos
	config.qcmid=qcm.id
	config.nomQCM=qcm.nomTeX.encode('utf-8','ignore')
	config.texteQCM=qcm.texteTeX.encode('utf-8','ignore')
	qcm.nmax=int(np.trunc(np.log2(config.ntotal))+1)
	qcm.save()
	config.DossierSortie=os.path.dirname(qcm.template.path)+'/'
	if 'originaux' not in os.listdir(config.DossierSortie):
		os.mkdir(config.DossierSortie+'originaux')
	if 'copies' not in os.listdir(config.DossierSortie):
		os.mkdir(config.DossierSortie+'copies')

	
	#création d'une list() d'objets "liste d'exo" (i.e. un ficher.exos), une liste d'exo pour chaque fichier
	exos=list()
	for fichier in config.listeFichiers:
		exos.append(listeExos(fichier,config))
		
		
	#on créé notre classe CSV
	sortieCSV=CSV(config.DossierSortie+config.CorrSortie,config.DossierSortie+config.QSortie)
		
	#on prépare la liste d'arguments pour le pdfunite de la sortie
	pdfuniteArg=list()
	pdfuniteArg.append('pdfunite')
	paquet=1
	
	#on génère l'aléa qui code les n° des qcms
	config.codes=range(100000)
	random.seed(float('0.'+str(config.qcmid)))
	random.shuffle(config.codes)
	random.shuffle(config.codes)
	random.shuffle(config.codes)
	
	listeqcmpdf=list()
	
	#on tire au hasard nexos[j] exos dans le fichier j, pour chaque fichier, et on répète pour avoir un total de ntotal codes tex
	for i in range(config.ntotal):
		k=0
		#list() de la liste des exos choisis pour chaque version
		listeExosSortie=list()
		for j in config.nbexos:				#pour chaque fichier de liste d'exos, j est le nombre d'exos que l'on veut choisir à l'intérieur
			if j==0:
				j=exos[k].nbExos
			r=random.sample(range(exos[k].nbExos),j)	#on en choisit donc j dans la k-ème colonne de exos (qui est dans le même ordre de la list() nexos)
			listeExosSortie.append(r)						#on ajoute à notre liste() de versions ce random
			sortieCSV.ajouterC(i,exos[k],r)					#on prévient le CSV
			sortieCSV.ajouterQ(i,r)
			k+=1											#on passe à la liste d'exos suivante
		sortie=TeXify(config.DossierSortie+config.TeXTemplate,exos,listeExosSortie,str(bin(config.nfeuille+i)[2:]),config)		#on TeX tout ça
	
		#on écrit tout ça dans un .tex
		fichierSortie=io.FileIO(config.DossierSortie+config.TeXSortie+str(i+config.nfeuille)+".tex",'w')
		for ligne in range(len(sortie.TeX)):
			fichierSortie.write(sortie.TeX[ligne])
		fichierSortie.close()
		#on le compile
		sp.check_output(['pdflatex','-output-directory',config.DossierSortie,config.DossierSortie+config.TeXSortie+str(i+config.nfeuille)+'.tex'])
      		#et on efface les fichiers inutiles
		os.remove(config.DossierSortie+config.TeXSortie+str(i+config.nfeuille)+".aux")
		os.remove(config.DossierSortie+config.TeXSortie+str(i+config.nfeuille)+".log")
		#et on ajoute à pdfunite le ficher à concaténer ensuite
		pdfuniteArg.append(config.DossierSortie+config.TeXSortie+str(i+config.nfeuille)+'.pdf')
		#si on atteint une étape de concaténation
		if i+1 in config.steps and i+1 != 1:
			#on concatène les pdf
			pdfuniteArg.append(config.DossierSortie+"originaux/"+config.TeXSortie+"-"+str(paquet)+'.pdf')
			sp.call(pdfuniteArg)
			fpdf=QcmPdf(qcm=qcm,fichier=config.DossierSortie+"originaux/"+config.TeXSortie+"-"+str(paquet)+'.pdf',nom=config.TeXSortie+"-"+str(paquet)+'.pdf')
			fpdf.save()
			listeqcmpdf.append(fpdf)
			paquet+=1
			pdfuniteArg=list()
			pdfuniteArg.append('pdfunite')
		elif i+1 in config.steps and i+1==1:
			sh.copy(config.DossierSortie+config.TeXSortie+str(i+config.nfeuille)+'.pdf',config.DossierSortie+"originaux/"+config.TeXSortie+".pdf")
			fpdf=QcmPdf(qcm=qcm,fichier=File(open(config.DossierSortie+"originaux/"+config.TeXSortie+".pdf", 'r')),nom=config.TeXSortie+".pdf")
			fpdf.save()
			listeqcmpdf.append(fpdf)
			
	#et on efface les pdf et tex de passage
	for j in range(config.ntotal):
		os.remove(config.DossierSortie+config.TeXSortie+str(j+config.nfeuille)+'.pdf')
		os.remove(config.DossierSortie+config.TeXSortie+str(j+config.nfeuille)+'.tex')
	
	qcm.gen=1
	qcm.save()
	
	#on sort le .csv des corrections
	sortieCSV.imprimerC(config)
	sortieCSV.imprimerQ(config.listeFichiers,config.nbexos,config)
	
	for qcmpdf in listeqcmpdf:
		importoriginaux(qcmpdf)


def telecharger(request,objet):
	if isinstance(objet,models.FileField):
		the_file = objet.path
	elif isinstance(objet,str):
		the_file = objet
	elif isinstance(objet,unicode):
		the_file = objet
	filename = os.path.basename(the_file)
	response = HttpResponse(FileWrapper(open(the_file)),
				content_type=mimetypes.guess_type(the_file)[0])
	response['Content-Length'] = os.path.getsize(the_file)    
	response['Content-Disposition'] = "attachment; filename=%s" % filename
	return response
   
def image(request,id_cc):
	
	if not request.user.is_active:
		return redirect('django_cas.views.login')
	nom=str(request.user.username)
	
	try:
		el=Eleve.objects.get(nom=nom)
		ccjpg=CopieJPG.objects.get(id=id_cc)
		if el==ccjpg.copiecorrigee.eleve:
			return telecharger(request,ccjpg.fichier)
		else:
			raise Exception(el.nom,ccjpg.copiecorrigee.eleve.nom)
	except:
		try:
			pr=Enseignant.objects.get(nom=nom)
			ccjpg=CopieJPG.objects.get(id=id_cc)
			if pr==ccjpg.copiecorrigee.qcm.prof:
				return telecharger(request,ccjpg.fichier)
		except Exception, er:
			print("Erreur : ",er)
			return HttpResponse("Non disponible")
	
	
def ehome(request):
	
	if not request.user.is_active:
		return redirect('django_cas.views.login')
	nom=str(request.user.username)
	el,nouveleleve=Eleve.objects.get_or_create(nom=nom)
	mi_id=-1
	if request.method == 'POST':
		formAssign=AssignerCopie(request.POST)
		formMontrerIm=MontrerImage(request.POST)
		if formAssign.is_valid():
			try:
				qcmid,numcopie=formAssign.cleaned_data['numcopie'].split('-')
				qcmid=int(qcmid)
				numcopie=int(numcopie)
				codes=range(100000)
				random.seed(float('0.'+str(qcmid)))
				random.shuffle(codes)
				random.shuffle(codes)
				random.shuffle(codes)
				numcopie=codes.index(numcopie)
				qcm=Qcm.objects.get(id=qcmid)
			except:
				err='1'
			try:
				if not el.copiecorrigee_set.filter(qcm=qcm):
					cp=CopieCorrigee.objects.get(qcm=qcm,numero=numcopie)
					if cp.eleve==Eleve.objects.get(nom="Élève non associé"):
						cp.eleve=el
						cp.save()
					else:
						err='3'
				else:
					err='4'
			except Exception, er:
				print("Erreur : ",er)
				err='2'
		elif formMontrerIm.is_valid():
			mi_id=formMontrerIm.cleaned_data['montrerimage']
			request.session['mi_id']=mi_id
				
	#creation de la liste des copies de l'élève
	listecps=list()
	listecjpgtemp=list()
	for cp in CopieCorrigee.objects.filter(eleve=el):
		listecjpgtemp=list()
		formtemp=MontrerImage(initial={'montrerimage':cp.id})
		if mi_id == cp.id:
			for ccc in cp.copiejpg_set.all():
				listecjpgtemp.append(ccc.id)
		listecps.append({'note':cp.note,'nom':cp.qcm.nomTeX,'jpg':listecjpgtemp,'formMI':formtemp})
	formAssign=AssignerCopie()
	return render(request, 'ehome.html', locals())
	
def home(request):
	
	if not request.user.is_active:
		return redirect('django_cas.views.login')
	nom=str(request.user.username)
	if not is_prof(nom):
		return redirect('prof.views.ehome')
	pr,nouveauprof=Enseignant.objects.get_or_create(nom=nom)
	if request.method == 'POST':
		formNExos = NouveauxExos(request.POST,request.FILES)
		if formNExos.is_valid():
			e,creation=Exo.objects.get_or_create(prof=pr,nom=str(formNExos.cleaned_data["exos"]))
			if creation:
				e.fichier = formNExos.cleaned_data["exos"]
				e.save()
		
		formFDel=EffacerFExo(request.POST)
		if formFDel.is_valid():
			td=Exo.objects.get(id=formFDel.cleaned_data['fexo'])
			td.delete()
			
	formFDel = EffacerFExo()
	formNQCM = NouveauQCM()
	formNExos = NouveauxExos()
	listeqcms = sorted(pr.qcm_set.all(), key=lambda r: int(r.id),reverse=True)
	listeChoix = list()
	for qcm in listeqcms:
		listeChoix.append((qcm.nom,qcm.nom))
	formChoix = QCMChoix()
	formChoix.setListe(listeChoix)
	listexostemp=pr.exo_set.all()
	listexos=list()
	for fexo in listexostemp:
		tform=EffacerFExo(initial={'fexo':fexo.id})
		listexos.append({'nom':fexo.nom,'formFDel':tform})
		
	return render(request, 'home.html', locals())

def qcmaker(request):
	
	if not request.user.is_active:
		return redirect('django_cas.views.login')
	nom=str(request.user.username)
	if not is_prof(nom):
		return redirect('prof.views.ehome')
		
	pr=Enseignant.objects.get(nom=nom)

	#on teste tous les formulaires
	formGenerer = Generer(request.POST)
	formNQCM = NouveauQCM(request.POST) 
	formNTemplate = AjoutTemplate(request.POST)
	#on remplit la liste des QCMs (pour tester le formulaire de choix de QCM)
	listeqcms=pr.qcm_set.all()
	listeChoix=list()
	for qcmt in listeqcms:
		listeChoix.append((qcmt.nom,qcmt.nom))
	formChoix = QCMChoix(request.POST)
	formChoix.setListe(listeChoix)
	formTelecharger = Telecharger(request.POST)
	formEffacer = Effacer(request.POST)
	formNExos = NouveauxExos(request.POST,request.FILES)
	
	#on remplit la liste des exos pour tester le formuler d'ajout d'exo (formExoChoix)
	listexostemp=pr.exo_set.all()
	listexos=list()
	for ex in listexostemp:
		listexos.append((ex.nom,ex.nom))
	formExoChoix = ExoChoix(request.POST)
	formExoChoix.setListe(listexos)		
	formDel=EffacerExo(request.POST)
	
	if request.method == 'POST':  # S'il s'agit d'une requête POST
	
		#si nouveau QCM
		if formNQCM.is_valid():
			qcm,creation=Qcm.objects.get_or_create(prof=pr,nom=formNQCM.cleaned_data["titre"])
			qcm.template = File(open("template.tex", 'r'))
			if creation:
				qcm.save()
			request.session['qcm']=qcm.id
		
		#si QCM existant
		elif formChoix.is_valid():
			try:
				qcm=Qcm.objects.get(prof=pr,nom=formChoix.cleaned_data['qcm'])
				request.session['qcm']=qcm.id
			except Exception, er:
				print("Erreur : ",er)
				return redirect('prof.views.home')	

		#si nouvel exo.exos	
		elif formNExos.is_valid():
			e,creation=Exo.objects.get_or_create(prof=pr,nom=str(formNExos.cleaned_data["exos"]))
			if creation:
       				e.fichier = formNExos.cleaned_data["exos"]
				e.save()
				
		#si suppression de QCM
		elif formDel.is_valid():
			td=NbExos.objects.get(id=formDel.cleaned_data['exo'])
			td.delete()
			
		#si ajout d'exo
		elif formExoChoix.is_valid():
			qcm=Qcm.objects.get(id=request.session['qcm'])
			exo=Exo.objects.get(prof=pr,nom=formExoChoix.cleaned_data["exo"])
			nbexos=formExoChoix.cleaned_data['nbexos']
			n=NbExos(qcm=qcm,exo=exo,nbexos=nbexos)
			n.save()
		
		#si ajout de template
		elif formNTemplate.is_valid():
			qcm=Qcm.objects.get(id=request.session['qcm'])
			qcm.nomTeX = formNTemplate.cleaned_data["nomTeX"]
			qcm.texteTeX = formNTemplate.cleaned_data["texteTeX"]
			qcm.save()
		
		#si génération des qcms
		elif formGenerer.is_valid():
			qcm=Qcm.objects.get(id=request.session['qcm'])
			#si aucun générateur n'est en cours
			if qcm.nbpdfs == '':
				qcm.nbpdfs=formGenerer.cleaned_data['nbpdfs']
				qcm.save()
				print('ok, on lance le générateur')
				try:
					BgJob(generateur,qcm)
					return redirect('prof.views.qcmanage')
				except Exception, er:
					qcm.delete()
					print("Erreur generateur: ",er, Exception)
					return redirect('prof.views.home')
				
	try:
		qcm=Qcm.objects.get(id=request.session['qcm'])
	except Exception,er:
		print('Erreur chargement du QCM: '+str(er))
		return redirect('prof.views.home')
	if qcm.gen or not qcm.nmax==0:
		return redirect('prof.views.qcmanage')
	#on remplit la liste des exos
	listexostemp=pr.exo_set.all()
	listexos=list()
	for ex in listexostemp:
		listexos.append((ex.nom,ex.nom))
	formExoChoix = ExoChoix()
	formExoChoix.setListe(listexos)
	#on remplit la liste des exos qcm		
	listexosqcmtemp=sorted(NbExos.objects.filter(qcm=qcm), key=lambda r: int(r.id))
	listexosqcm=list()
	for nb in listexosqcmtemp:
		tform=EffacerExo(initial={'exo':nb.id})
		listexosqcm.append({'nom':nb.exo.nom,'nb':nb.nbexos,'formDel':tform})
	formNTemplate = AjoutTemplate()
	formNTemplate.setFields(qcm)
	formNExos = NouveauxExos()
	try:
		formGenerer.erreurici
	except Exception,er:
		formGenerer = Generer()
	return render(request, 'qcmaker.html', locals())

	
def qcmanage(request):
	
	if not request.user.is_active:
		return redirect('django_cas.views.login')
	nom=str(request.user.username)
	if not is_prof(nom):
		return redirect('prof.views.ehome')
	
	try:
		pr=Enseignant.objects.get(nom=nom)
		qcm=Qcm.objects.get(id=request.session['qcm'])
	except Exception,er:
		return redirect('prof.views.home')

	mi_id=-1
	
	if request.method == 'POST':
		formTelecharger = Telecharger(request.POST)
		formAjoutCopies = AjoutCopies(request.POST,request.FILES)
		formMontrerIm = MontrerImage(request.POST)
		formEffCopie = EffacerCopie(request.POST)
		formNote = Note(request.POST)
		formGenNotes = TelechargerNotes(request.POST)
		#si téléchargement de qcmpdf
		if formTelecharger.is_valid():
			qcmpdf=QcmPdf.objects.get(fichier=formTelecharger.cleaned_data['fichieratel'])
			return telecharger(request,formTelecharger.cleaned_data['fichieratel'])
		#si upload de copie
		elif formAjoutCopies.is_valid():
			cps=Copies(qcm=qcm,fichier=formAjoutCopies.cleaned_data['fichiercp'],nom=str(formAjoutCopies.cleaned_data['fichiercp']))
			cps.save()
			try:
				BgJob(correction,cps)
			except Exception, er:
				print("Erreur : ",er)
				cps.delete()
		#si demande de montrer une copie (image)
		elif formMontrerIm.is_valid():
			mi_id=formMontrerIm.cleaned_data['montrerimage']
		#si effacement d'une copie
		elif formEffCopie.is_valid():
			CopieCorrigee.objects.get(id=formEffCopie.cleaned_data['cpid']).delete()
		#si mise à jour d'une note
		elif formNote.is_valid():
			cc=CopieCorrigee.objects.get(id=formNote.cleaned_data['copiecorrigeeid'])		
			cc.note=formNote.cleaned_data['note']
			cc.save()
		#si téléchargement des notes au format CSV
		elif formGenNotes.is_valid():
			return telecharger(request,genererCSVnotes(qcm))
		#sinon bug?
		else:
			print('rien')
			
			
	
	#on remplit la liste des exos qcm		
	listexosqcmtemp=sorted(NbExos.objects.filter(qcm=qcm), key=lambda r: int(r.id))
	listexosqcm=list()
	for nb in listexosqcmtemp:
		tform=EffacerExo(initial={'exo':nb.id})
		listexosqcm.append({'nom':nb.exo.nom,'nb':nb.nbexos,'formDel':tform})

	#on remplit la liste des pdf du qcm
	listpdfqcmtemp=QcmPdf.objects.filter(qcm=qcm)
	listpdfqcm=list()
	for pdf in listpdfqcmtemp:
		pdform = Telecharger(initial={'fichieratel':pdf.fichier})
		listpdfqcm.append({'nom':pdf.nom,'formTel':pdform})
		
	
	#creation de la liste des copies corrigées
	listecps=list()
	listecjpgtemp=list()
	codes=range(100000)
	random.seed(float('0.'+str(qcm.id)))
	random.shuffle(codes)
	random.shuffle(codes)
	random.shuffle(codes)

	for cp in [cc for cc in CopieCorrigee.objects.filter(qcm=qcm) if cc.copies.corrigees]:
		listecjpgtemp=list()
		formtemp=MontrerImage(initial={'montrerimage':cp.id})
		tform=EffacerCopie(initial={'cpid':cp.id})
		tformNote=Note(initial={'note':cp.note,'copiecorrigeeid':cp.id})
		if mi_id == cp.id:
			for ccc in cp.copiejpg_set.all():
				listecjpgtemp.append(ccc.id)
		listecps.append({'id':cp.id,'note':cp.note,'nom':cp.eleve.nom,'jpg':listecjpgtemp,'formMI':formtemp,'formEffCopie':tform,'formNote':tformNote,'code':codes[cp.numero]})
	nbcopiescorrigees=len(listecps)
		

	#on remplit la liste des copies
	listecopiestemp=Copies.objects.filter(qcm=qcm)
	listecopies=list()
	for cp in listecopiestemp:
		#le worker marche encore, correction de copies
		if not cp.corrigees:
			correctionencours=True
		listecopies.append({'nom':cp.nom,'corrigee':cp.corrigees})

	#le worker marche encore, création des pdfs
	encours=not qcm.gen
	#le worker marche encore, import des pdfs
	importpdfini = len(QcmPdf.objects.filter(qcm=qcm)) == len(QcmPdf.objects.filter(qcm=qcm,traite=True))
	formGenNotes = TelechargerNotes()
	formAjoutCopies = AjoutCopies()
					
	return render(request, 'qcmanage.html', locals())

def makexo(request):

	if not request.user.is_active:
		return redirect('django_cas.views.login')
	nom=str(request.user.username)
	if not is_prof(nom):
		return redirect('prof.views.ehome')
	try:
		pr=Enseignant.objects.get(nom=nom)
		qcm=Qcm.objects.get(id=request.session['qcm'])
	except Exception,er:
		return redirect('prof.views.home')

	banque,creation = CoreBanque.objects.get_or_create(prof=pr,nom="Banque test")
	
	if CoreExo.objects.filter(banque=banque):
		try:
			coreexo = CoreExo.objects.get(id=request.session['makexo'])
			print('1')
		except:
			coreexo = CoreExo.objects.filter(banque=banque)[0]
			request.session['makexo'] = coreexo.id
			print('2')
	else:
		coreexo = CoreExo(banque=banque)
		coreexo.save()
		
	if request.method == 'POST':
		formMain = MakexoMain(request.POST)
		formAjouterReponse = MakexoAjouterReponse(request.POST)
		formAjouterExo = MakexoAjouterExo(request.POST)
		formModifierExo = MakexoModifierExo(request.POST)
		if formMain.is_valid():
			print('ok')
			coreexo = CoreExo.objects.get(id=formMain.cleaned_data['idmainexo'])
			coreexo.question = formMain.cleaned_data['question']
			coreexo.corrige = formMain.cleaned_data['corrige']
			coreexo.type = formMain.cleaned_data['type']
			coreexo.save()
		elif formAjouterReponse.is_valid():
			reponse = CoreReponse(exo=coreexo,texte="Reponse",nom="v")
			reponse.save()
		elif formAjouterExo.is_valid():
			nouvelexo = CoreExo(banque=banque)
			nouvelexo.save()
		elif formModifierExo.is_valid():
			try:
				coreexo = CoreExo.objects.get(id=formModifierExo.cleaned_data['idexo'])
				request.session['makexo']=coreexo.id
			except:
				print('Exercice d\'id '+str(formModifierExo.cleaned_data['idexo'])+' inexistant')
			
	
	listeexos = list()
	for exo in banque.coreexo_set.all():
		formModifierExotemp = MakexoModifierExo()
		formModifierExotemp.setId(exo.id)
		listeexos.append({'question':exo.question,'reponses':'\n---\n'.join(x.texte for x in exo.corereponse_set.all()),'formModifierExo':formModifierExotemp})
		

	listereponses = list()
	for reponse in coreexo.corereponse_set.all():
		listereponses.append({'nom':reponse.nom,'texte':reponse.texte})
	formMain = MakexoMain()
	formMain.setFields(coreexo)
	formAjouterReponse = MakexoAjouterReponse()
	formAjouterExo = MakexoAjouterExo()
	

	return render(request, 'makexo.html', locals())

