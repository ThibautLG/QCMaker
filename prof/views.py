#-*- coding:utf-8 -*-

from django.shortcuts import render,redirect,HttpResponse
from prof.models import *
from prof.forms import *
import os
import mimetypes
from django.core.servers.basehttp import FileWrapper
from qcmaker import *
import pickle
from django.core.files import File
import random
from bgjob import BgJob
import prof.core as core
#from django_rq import job



def is_prof(nom):
	listeprof=['tle-gouic','jliandrat','cpouet','gchiavassa']
	if nom in listeprof:
		return True
	else:
		return False


def genererCSVnotes(qcm):
	dossier="media/ups/"+str(qcm.prof.id)+"/"+str(qcm.id)+"/"
	codes=range(100000)
	random.seed(float('0.'+str(qcm.id)))
	random.shuffle(codes)
	random.shuffle(codes)
	random.shuffle(codes)
	listecopies=[qcmpdf for qcmpdf in qcm.coreqcmpdf_set.all() if qcmpdf.reponses != ""]
	fichierCSV=io.FileIO(dossier+"notes.csv",'w')
	for qcmpdf in listecopies:
		fichierCSV.write(str(codes[qcmpdf.numero])+","+qcmpdf.corecopie_set.all()[0].eleve.nom.encode('ascii','replace')+","+str(qcmpdf.getnote()))
		fichierCSV.write("\n")
	fichierCSV.close()
	return str(dossier+"notes.csv")
	
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
   

def svg(request,id_svg, prefix):
	
	if not request.user.is_active:
		return redirect('django_cas.views.login')
	nom = str(request.user.username)
	if prefix == '1':
		prefix = "exo"
	elif prefix == '2':
		prefix = "qcm-prev"
	try:
		try:
			pr = Enseignant.objects.get(nom=nom)
			svg = "media/ups/"+str(pr.id)+"/"+prefix+"-"+str(id_svg)+".svg"
		except:
			try:
				el = Eleve.objects.get(nom=nom)
				exo = CoreExo.objects.get(id=int(id_svg))
				ok = False
				for copie in el.corecopie_set.all():
					if exo in copie.qcmpdf.exos.all():
						ok = True
				if ok:
					svg = "media/ups/"+str(exo.banque.prof.id)+"/"+prefix+"-"+str(id_svg)+".svg"
			except Exception,er:
				print('Erreur svg: '+str(er))
				return HttpResponse("Non disponible")
		return telecharger(request,svg)
	except Exception, er:
		print("Erreur : ",er)
		return HttpResponse("Non disponible")
	

def image(request,id_cc,page):
	
	if not request.user.is_active:
		return redirect('django_cas.views.login')
	nom=str(request.user.username)
	id_cc = int(id_cc)
	page = int(page)
	try:
		el=Eleve.objects.get(nom=nom)
		cc=CoreCopie.objects.get(id=id_cc)
		if el==cc.eleve:
			return telecharger(request,cc.getpage(page))
		else:
			raise Exception(el.nom,cc.eleve.nom)
	except:
		try:
			pr=Enseignant.objects.get(nom=nom)
			cc=CoreCopie.objects.get(id=id_cc)
			if pr==cc.qcmpdf.qcm.prof:
				return telecharger(request,cc.getpage(page))
		except Exception, er:
			print("Erreur : ",er)
			return HttpResponse("Non disponible")
	
	
def ehome(request):
	
	if not request.user.is_active:
		return redirect('django_cas.views.login')
	nom=str(request.user.username)
	el,nouveleleve=Eleve.objects.get_or_create(nom=nom)
	if request.method == 'POST':
		formAssign=AssignerCopie(request.POST)
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
				numcopie = codes.index(numcopie)
				qcm = CoreQcm.objects.get(id=qcmid)
				qcmpdf = CoreQcmPdf.objects.get(qcm=qcm,numero=numcopie)
			except:
				err='1'
			try:
				if not [cc for cc in el.corecopie_set.all() if cc.qcmpdf.qcm==qcm]:
					cp=CoreCopie.objects.get(qcmpdf=qcmpdf)
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

	#creation de la liste des copies de l'élève
	listecps  = list()
	for cp in [cc for cc in CoreCopie.objects.all() if cc.eleve == el]:
		tform = VoirCopie(initial={'idcopieavoir':cp.id})
		listecps.append({'id':cp.id,'note':cp.qcmpdf.getnote(),'nom':cp.qcmpdf.qcm.nomTeX,'formvoir':tform})
	formAssign=AssignerCopie()
	return render(request, 'ehome.html', locals())
	
def home(request):

	if not request.user.is_active:
		return redirect('django_cas.views.login')
	nom=str(request.user.username)
	print(nom)
	if not is_prof(nom):
		return redirect('prof.views.ehome')
	pr,nouveauprof = Enseignant.objects.get_or_create(nom=nom)
	if nouveauprof:
		try:
			os.mkdir('media/ups/'+str(pr.id))
		except:
			print('Erreur lors de la création du nouveau dossier prof')

	formNouvelleBanque = AjouterBanque(request.POST)
	formBanque = ChoixBanque(request.POST)
	listebanquestemp=pr.corebanque_set.all()
	listebanques=list()
	for banq in listebanquestemp:
		listebanques.append((banq.id,banq.nom))
	formBanque.setListe(listebanques)	
		
	if request.method == 'POST':
		if formBanque.is_valid():
			print('ok')
			request.session['banque'] = formBanque.cleaned_data['banque']
			return redirect('prof.views.banque')
		elif formNouvelleBanque.is_valid():
			print(pr)
			banque,creation = CoreBanque.objects.get_or_create(prof=pr,nom=formNouvelleBanque.cleaned_data['nouvellebanque'])
			banque.save()
			request.session['banque'] = banque.id
			return redirect('prof.views.banque')

	formNQCM = NouveauQCM()
	formBanque = ChoixBanque()
	formChoix = QCMChoix()
	formNouvelleBanque = AjouterBanque()

	listeqcms = sorted(pr.coreqcm_set.all(), key=lambda r: int(r.id),reverse=True)
	listeChoix = list()
	for lqcm in listeqcms:
		listeChoix.append((lqcm.id,lqcm.nom))
	formChoix.setListe(listeChoix)

	listebanquestemp=pr.corebanque_set.all()
	listebanques=list()
	for banq in listebanquestemp:
		listebanques.append((banq.id,banq.nom))
	formBanque.setListe(listebanques)	
		
	
	return render(request, 'home.html', locals())

def qcmaker(request):
	
	if not request.user.is_active:
		return redirect('django_cas.views.login')
	nom=str(request.user.username)
	if not is_prof(nom):
		return redirect('prof.views.ehome')
		

	
	pr=Enseignant.objects.get(nom=nom)
	dossier = 'media/ups/'+str(pr.id)

	#on charge tous les formulaires
	formGenerer = Generer(request.POST)
	formNQCM = NouveauQCM(request.POST) 
	formNEntete = Entete(request.POST)

	#on remplit la liste des QCMs (pour tester le formulaire de choix de QCM)
	listeqcms = sorted(pr.coreqcm_set.all(), key=lambda r: int(r.id),reverse=True)
	listeChoix = list()
	for lqcm in listeqcms:
		listeChoix.append((lqcm.id,lqcm.nom))
	formChoix = QCMChoix(request.POST)
	formChoix.setListe(listeChoix)
	formTelecharger = Telecharger(request.POST)
	formEffacer = Effacer(request.POST)
	
	#on remplit la liste des banques d'exos
	formAjoutBanque = ChoixBanqueQCM(request.POST)
	listebanquestemp=pr.corebanque_set.all()
	listebanques=list()
	for banq in listebanquestemp:
		listebanques.append((banq.id,banq.nom))
	formAjoutBanque.setListe(listebanques)

	formDel=EffacerBanque(request.POST)
	if request.method == 'POST':  # S'il s'agit d'une requête POST
	
		#si nouveau QCM
		if formNQCM.is_valid():
			qcm,creation=CoreQcm.objects.get_or_create(prof=pr,nom=formNQCM.cleaned_data["titre"])
			if creation:
				qcm.save()
			request.session['qcm']=qcm.id
			errtex = core.genererSvgQcm(qcm,dossier)
			if not errtex == 0:
				qcm.erreurtex = True
			else: 
				qcm.erreurtex = False
			qcm.save()
		
		#si QCM existant
		elif formChoix.is_valid():
			print('Formulaire de choix de QCM valide')
			try:
				qcm=CoreQcm.objects.get(prof=pr,id=int(formChoix.cleaned_data['qcm']))
				request.session['qcm']=qcm.id
			except Exception, er:
				print("Erreur : ",er)
				return redirect('prof.views.home')	

		#si suppression de banque d'exo du qcm
		elif formDel.is_valid():
			print('On efface un nbexos')
			td=CoreNbExos.objects.get(id=formDel.cleaned_data['banqueaeff'])
			td.delete()
			
		#si ajout de banque
		elif formAjoutBanque.is_valid():
			qcm=CoreQcm.objects.get(id=request.session['qcm'])
			nbanque=CoreBanque.objects.get(prof=pr,id=formAjoutBanque.cleaned_data['banque'])
			nbexos=formAjoutBanque.cleaned_data['nbexos']
			n=CoreNbExos(qcm=qcm,banque=nbanque,nb=nbexos,position=len(qcm.nbexos.all())+1)
			n.save()
		
		#si changement d'entete
		elif formNEntete.is_valid():
			qcm=CoreQcm.objects.get(id=request.session['qcm'])
			qcm.nomTeX = formNEntete.cleaned_data["nomTeX"]
			qcm.texteTeX = formNEntete.cleaned_data["texteTeX"]
			qcm.save()
			errtex = core.genererSvgQcm(qcm,dossier)
			if not errtex == 0:
				qcm.erreurtex = True
			else: 
				qcm.erreurtex = False
			qcm.save()
		
		#si génération des qcms
		elif formGenerer.is_valid():
			qcm=CoreQcm.objects.get(id=request.session['qcm'])
			#si aucun générateur n'est en cours
			if not qcm.erreurtex and qcm.generation == 0:
				print('ok, on lance le générateur')
				qcm.generation=1
				qcm.save()
				try:
					BgJob(core.genererQcm,(qcm,formGenerer.cleaned_data['nbpdfs']))
					BgJob(core.genererPdfs,(qcm.id,dossier+'/'+str(qcm.id)))
					BgJob(core.importOriginaux,qcm.id)
					return redirect('prof.views.qcmanage')
				except Exception, er:
					qcm.delete()
					print("Erreur generateur: ",er, Exception)
					return redirect('prof.views.home')
			elif qcm.generation>0:
				return redirect('prof.views.qcmanage')
				
				
	try:
		qcm=CoreQcm.objects.get(id=request.session['qcm'])
	except Exception,er:
		print('Erreur chargement du QCM: '+str(er))
		return redirect('prof.views.home')
	if qcm.generation>0:
		return redirect('prof.views.qcmanage')

	#on remplit la liste des banques d'exos
	formAjoutBanque = ChoixBanqueQCM()
	listebanquestemp=pr.corebanque_set.all()
	listebanques=list()
	for banq in listebanquestemp:
		listebanques.append((banq.id,banq.nom))
	formAjoutBanque.setListe(listebanques)

	#on remplit la liste des banques du qcm		
	listebanquesqcmtemp = sorted(CoreNbExos.objects.filter(qcm=qcm), key=lambda r: int(r.id))
	listebanquesqcm=list()
	for nb in listebanquesqcmtemp:
		tform=EffacerBanque(initial={'banqueaeff':nb.id})
		listebanquesqcm.append({'nom':nb.banque.nom,'nb':nb.nb,'formDel':tform})
	formNEntete = Entete()
	formNEntete.setFields(qcm)
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
		qcm=CoreQcm.objects.get(id=request.session['qcm'])
	except Exception,er:
		return redirect('prof.views.home')
	
	dossier = 'media/ups/'+str(pr.id)
	
	if request.method == 'POST':
		formTelecharger = Telecharger(request.POST)
		formAjoutCopies = AjoutCopies(request.POST,request.FILES)
		formGenNotes = TelechargerNotes(request.POST)
		#si téléchargement de qcmpdf
		if formTelecharger.is_valid():
			return telecharger(request,dossier+'/'+str(qcm.id)+'/originaux/'+formTelecharger.cleaned_data['fichieratel'])
		#si upload de copie
		elif formAjoutCopies.is_valid():
			cps=CoreCopies(qcm=qcm,fichier=formAjoutCopies.cleaned_data['fichiercp'],nom=str(formAjoutCopies.cleaned_data['fichiercp']))
			cps.save()
			try:
				BgJob(core.correctionCopies,(qcm.id,cps))
			except Exception, er:
				print("Erreur : ",er)
				cps.delete()
		#si téléchargement des notes au format CSV
		elif formGenNotes.is_valid():
			return telecharger(request,genererCSVnotes(qcm))
		#sinon bug?
		else:
			print('rien')
			
	#on remplit la liste des pdf du qcm
	try:
		listepdfqcmtemp = sorted([x for x in os.listdir(dossier+'/'+str(qcm.id)+'/originaux') if x.startswith('exos-') and x.endswith('.pdf')],key=lambda r: int(''.join(x for x in r if x.isdigit())))
	except:
		listepdfqcmtemp = list()
	listepdfqcm=list()
	for pdf in listepdfqcmtemp:
		pdform = Telecharger(initial={'fichieratel':pdf})
		listepdfqcm.append({'nom':pdf,'formTel':pdform})
		
	
	#creation de la liste des copies corrigées
	listecps=list()
	listecjpgtemp=list()
	codes=range(100000)
	random.seed(float('0.'+str(qcm.id)))
	random.shuffle(codes)
	random.shuffle(codes)
	random.shuffle(codes)

	for cp in [cc for cc in CoreCopie.objects.all() if cc.qcmpdf.qcm==qcm]:
		tform = VoirCopie(initial={'idcopieavoir':cp.id})
		listecps.append({'id':cp.id,'note':cp.qcmpdf.getnote(),'nom':cp.eleve.nom,'jpg':listecjpgtemp,'code':codes[cp.qcmpdf.numero],'formvoir':tform,'malcorrigee':cp.malcorrigee})
	nbcopiescorrigees=len(listecps)
		

	#on remplit la liste des copies
	listecopiestemp=CoreCopies.objects.filter(qcm=qcm)
	listecopies=list()
	for cp in listecopiestemp:
		#le worker marche encore, correction de copies
		if not cp.corrigees:
			correctionencours=True
		listecopies.append({'nom':cp.nom,'corrigee':cp.corrigees})

	#le worker marche encore, création des pdfs
	encours = qcm.generation<2
	#le worker marche encore, import des pdfs
	importpdfini = qcm.generation==3
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
	except Exception,er:
	#	return redirect('prof.views.home')
		pass

	banque,creation = CoreBanque.objects.get_or_create(prof=pr,id=request.session['banque'])
	dossier = 'media/ups/'+str(pr.id)

	if not request.session['makexo']:
		return redirect('prof.views.banque')
	
	try:
		coreexo = CoreExo.objects.get(id=request.session['makexo'])
	except:
		print('Exercice d\'id '+str(formModifierExo.cleaned_data['idexo'])+' inexistant')
		return redirect('prof.views.banque')

	if request.method == 'POST':
		formMain = MakexoMain(request.POST)
		formAjouterReponse = MakexoAjouterReponse(request.POST)
		if formMain.is_valid():
			print('ok')
			coreexo = CoreExo.objects.get(id=formMain.cleaned_data['idmainexo'])
			coreexo.question = formMain.cleaned_data['question']
			coreexo.corrige = formMain.cleaned_data['corrige']
			coreexo.type = formMain.cleaned_data['type']
			coreexo.save()
			errtex = core.genererSvg(coreexo,dossier)
			if not errtex == 0:
				coreexo.erreurtex = True
			else: 
				coreexo.erreurtex = False
			coreexo.save()
		elif formAjouterReponse.is_valid():
			reponse = CoreReponse(exo=coreexo,texte=formAjouterReponse.cleaned_data['reponse'],nom=formAjouterReponse.cleaned_data['nom'],position=len(coreexo.corereponse_set.all())+1)
			reponse.save()
			errtex = core.genererSvg(coreexo,dossier)
			if not errtex == 0:
				coreexo.erreurtex = True
			else: 
				coreexo.erreurtex = False

			coreexo.save()
	

	listereponses = list()
	for reponse in sorted(coreexo.corereponse_set.all(), key=lambda r: int(r.position)):
		listereponses.append({'nom':reponse.nom,'texte':reponse.texte})
	

	exosvg = str(coreexo.id)
	formMain = MakexoMain()
	formMain.setFields(coreexo)
	formAjouterReponse = MakexoAjouterReponse()

	return render(request, 'makexo.html', locals())

def banque(request):

	if not request.user.is_active:
		return redirect('django_cas.views.login')
	nom=str(request.user.username)
	if not is_prof(nom):
		return redirect('prof.views.ehome')
	try:
		pr=Enseignant.objects.get(nom=nom)
	except Exception,er:
	#	return redirect('prof.views.home')
		pass

	banque = CoreBanque.objects.get(id=request.session['banque'])
	dossier = 'media/ups/'+str(pr.id)
	request.session['makexo']=""

	if request.method == 'POST':
		formAjouterExo = MakexoAjouterExo(request.POST) 
		formModifierExo = MakexoModifierExo(request.POST)
		if formAjouterExo.is_valid():
			nouvelexo = CoreExo(banque=banque)
			nouvelexo.save()
			request.session['makexo']=nouvelexo.id
			core.genererSvg(nouvelexo,dossier)
			return redirect('prof.views.makexo')
		elif formModifierExo.is_valid():
			request.session['makexo']=formModifierExo.cleaned_data['idexo']
			return redirect('prof.views.makexo')
	
	listeexos = list()
	for exo in banque.coreexo_set.all():
		formModifierExo = MakexoModifierExo()
		formModifierExo.setId(exo.id)
		listeexos.append({'id':exo.id,'form':formModifierExo,'err':exo.erreurtex})
	nbexos = len(listeexos)

	formAjouterExo = MakexoAjouterExo()
	formModifierExo = MakexoModifierExo()
	return render(request, 'banque.html', locals())

def voircopie(request):

	if not request.user.is_active:
		return redirect('django_cas.views.login')
	nom=str(request.user.username)
	if not is_prof(nom):
		return redirect('prof.views.ehome')
	
	try:
		pr=Enseignant.objects.get(nom=nom)
		qcm=CoreQcm.objects.get(id=request.session['qcm'])
	except Exception,er:
		return redirect('prof.views.home')
	
	dossier = 'media/ups/'+str(pr.id)
	try:
		copie = CoreCopie.objects.get(id=request.session['idcopie'])
	except:
		pass

	if request.method == 'POST':
		formVoirCopie = VoirCopie(request.POST) 
		formChangerCases = ChangerCases(request.POST)
		if formVoirCopie.is_valid():
			idcopie = formVoirCopie.cleaned_data['idcopieavoir']
			try:
				copie = CoreCopie.objects.get(id=idcopie)
				request.session['idcopie'] = copie.id
			except:
				print('Copie d\'id '+str(idcopie)+' non trouvée')
				return redirect('prof.views.qcmanage')
		elif formChangerCases.is_valid():
			try:
				copie = CoreCopie.objects.get(id=formChangerCases.cleaned_data['idcopieachanger'])
				qcmpdf = copie.qcmpdf
				qcmpdf.setreponses(formChangerCases.cleaned_data['reponses'])
				copie.malcorrigee = False
				copie.save()
			except:
				pass

	infoscopie = {'id':copie.id,'nomeleve':copie.eleve.nom,'note':copie.qcmpdf.getnote(),'pages':[i+1 for i in range(copie.qcmpdf.pages)]}
	reponsescopie = copie.qcmpdf.getreponses()
	formChangerCases = ChangerCases({'idcopieachanger':copie.id,'reponses':copie.qcmpdf.reponses})
	return render(request, 'voircopie.html', locals())

def evoircopie(request):

	if not request.user.is_active:
		return redirect('django_cas.views.login')
	nom=str(request.user.username)
	
	try:
		el=Eleve.objects.get(nom=nom)
	except Exception,er:
		return redirect('prof.views.ehome')
	
	dossier = 'media/ups/'+str(el.id)
	try:
		copie = CoreCopie.objects.get(id=request.session['idecopie'])
	except:
		pass

	if request.method == 'POST':
		formVoirCopie = VoirCopie(request.POST) 
		formChangerCases = ChangerCases(request.POST)
		formSignalerErreur = SignalerErreur(request.POST)
		print(formSignalerErreur)
		if formVoirCopie.is_valid():
			idcopie = formVoirCopie.cleaned_data['idcopieavoir']
			try:
				copie = CoreCopie.objects.get(id=idcopie)
				request.session['idecopie'] = copie.id
			except:
				print('Copie d\'id '+str(idcopie)+' non trouvée')
				return redirect('prof.views.ehome')
		elif formSignalerErreur.is_valid():
			idcopie = formSignalerErreur.cleaned_data['idcopieerronee']
			print('ouhou')
			try:
				copie = CoreCopie.objects.get(id=idcopie)
				copie.malcorrigee = True
				copie.save()
				print('id:'+str(copie.id))
			except:
				print('Copie d\'id '+str(idcopie)+' non trouvée')
				
		elif not copie:
			return redirect('prof.views.ehome')

	infoscopie = {'id':copie.id,'nomcopie':copie.qcmpdf.qcm.nomTeX,'note':copie.qcmpdf.getnote(),'pages':[i+1 for i in range(copie.qcmpdf.pages)],'malcorrigee':copie.malcorrigee}
	exocopies = list()
	for exo in copie.qcmpdf.exos.all():
		exocopies.append(exo.id)	

	formSignalerErreur = SignalerErreur({'idcopieerronee':copie.id})
	return render(request, 'evoircopie.html', locals())
