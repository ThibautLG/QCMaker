#-*- coding:utf-8 -*-

from django import forms

class AjouterBanque(forms.Form):

	nouvellebanque = forms.CharField(label="",initial="Nouvelle banque")

class ChoixBanque(forms.Form):
	
	def setListe(self,listeChoix):
		self.fields['banque'] = forms.ChoiceField(label="",choices=listeChoix)
		
	banque = forms.ChoiceField()

class MakexoMain(forms.Form):

	def setFields(self,exo):
		self.fields['question'] = forms.CharField(initial=exo.question,label="",widget=forms.Textarea)
		self.fields['corrige'] = forms.CharField(initial=exo.corrige,label="",widget=forms.Textarea,required=False)
		self.fields['question'].widget.attrs['cols']=u'100%'
		self.fields['corrige'].widget.attrs['cols']=u'100%'
		self.fields['idmainexo'] = forms.IntegerField(widget=forms.HiddenInput(),initial=exo.id)

	idmainexo =  forms.IntegerField()
	question = forms.CharField()
	corrige = forms.CharField(required=False)
	type = forms.ChoiceField(label="Type de correction",choices=[('1','Une seule réponse possible')])

class UploadExos(forms.Form):
	fichierexos = forms.FileField(label="Charger un fichier .exos")
	
class MakexoAjouterReponse(forms.Form):
	
	nouvellereponse = forms.BooleanField(widget=forms.HiddenInput(),initial=True)
	nom = forms.CharField(initial="v",max_length=1,label="",required=True)
	reponse = forms.CharField(initial="Réponse",label="",widget=forms.Textarea,required=True)

class MakexoAjouterExo(forms.Form):
	
	nouvelexo = forms.BooleanField(widget=forms.HiddenInput(),initial=True)

class MakexoModifierExo(forms.Form):

	def setId(self,id):
		self.fields['idexo'] =  forms.IntegerField(widget=forms.HiddenInput(),initial=id)
	idexo = forms.IntegerField()

class QCMChoix(forms.Form):
	def setListe(self,listeChoix):
		self.fields['qcm'] = forms.ChoiceField(label="",choices=listeChoix)
		
	qcm = forms.ChoiceField()

class ChoixBanqueQCM(forms.Form):
	
	def setListe(self,listeChoix):
		self.fields['banque'] = forms.ChoiceField(label=" exercices de ",choices=listeChoix)
		
		
	nbexos=forms.IntegerField(initial=1,min_value=1,label="Ajouter")
	banque=forms.ChoiceField(label="Liste de vos Exos")

class EffacerBanque(forms.Form):
	banqueaeff = forms.IntegerField(widget=forms.HiddenInput())

class EffacerExo(forms.Form):
	exoaeff = forms.IntegerField(widget=forms.HiddenInput())

class Entete(forms.Form):
	def setFields(self,qcm):
		self.fields['nomTeX'] = forms.CharField(max_length=100,label="",initial=qcm.nomTeX)
		self.fields['texteTeX'] = forms.CharField(label="",widget=forms.Textarea,initial=qcm.texteTeX)
		self.fields['texteTeX'].widget.attrs['cols']=u'100%'
	nomTeX = forms.CharField(max_length=100,label="Sujet")
	texteTeX = forms.CharField(label="Texte",widget=forms.Textarea)

class TelechargerNotes(forms.Form):
	generernotes = forms.BooleanField(widget=forms.HiddenInput(),initial=True)


class Generer(forms.Form):
	nbpdfs = forms.CharField(initial="30,30,30",label="Copies à générer")

	def clean_nbpdfs(self):
		nbpdfs = self.cleaned_data['nbpdfs']
		nbpdfs_test = nbpdfs.split(",")

		for nb in nbpdfs_test:
			try:
				int(nb)
			except:
				self.erreurici=True
				raise forms.ValidationError("Format incorrect, vous devez entrer chaque les nombres de copies de chaque fichier pdf que vous souhaitez, séparés par une virgule.")
			if int(nb) < 1 or int(nb)>50:
				self.erreurici=True
				raise forms.ValidationError("Chaque nombre doit être entre compris entre 1 et 50.")

		return nbpdfs

class AjoutCopies(forms.Form):
	fichiercp = forms.FileField(label="Copies")
	
class NouveauQCM(forms.Form):
	titre = forms.CharField(max_length=100,label="",initial="Nouveau QCM")

class VoirCopie(forms.Form):
	idcopieavoir = forms.IntegerField(widget=forms.HiddenInput())

class ChangerCases(forms.Form):
	
	idcopieachanger = forms.IntegerField(widget=forms.HiddenInput())
	reponses = forms.CharField(max_length=200,initial='')

class SignalerErreur(forms.Form):
	idcopieerronee = forms.IntegerField(widget=forms.HiddenInput())


################################################# OLD ################################################# 


	
class EffacerCopie(forms.Form):
	cpid = forms.IntegerField(widget=forms.HiddenInput())
	
class Effacer(forms.Form):
	fichieraeff = forms.CharField(label="Fichier",widget=forms.HiddenInput())


class Telecharger(forms.Form):
	fichieratel = forms.CharField(label="Fichier",widget=forms.HiddenInput())
	

#class Note(forms.Form):
#	note = forms.FloatField(label="")
#	copiecorrigeeid = forms.IntegerField(widget=forms.HiddenInput())
#class NouveauxExos(forms.Form):
#	exos = forms.FileField(label="Charger un nouveau fichier .exos")

class AssignerCopie(forms.Form):
	numcopie = forms.CharField(max_length=100,label="Numero de copie")
