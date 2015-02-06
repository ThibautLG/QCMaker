#-*- coding:utf-8 -*-

from django import forms

class BanqueToMakexo(forms.Form):
	
	def setListe(self,listeChoix):
		self.fields['banque'] = forms.ChoiceField(label="Liste de vos banques d'exercices",choices=listeChoix)
		
	banque = forms.ChoiceField(label="Liste de vos banques d'exercices")

class MakexoMain(forms.Form):

	def setFields(self,exo):
		self.fields['nom'] = forms.CharField(initial=exo.nom,label="")
		self.fields['question'] = forms.CharField(initial=exo.question,label="",widget=forms.Textarea)
		self.fields['corrige'] = forms.CharField(initial=exo.corrige,label="",widget=forms.Textarea,required=False)
		self.fields['question'].widget.attrs['cols']=u'90'
		self.fields['corrige'].widget.attrs['cols']=u'90'
		self.fields['idmainexo'] = forms.IntegerField(widget=forms.HiddenInput(),initial=exo.id)

	idmainexo =  forms.IntegerField()
	nom = forms.CharField(initial="Nom de l'exercice",label="")
	question = forms.CharField(initial="Question",label="",widget=forms.Textarea)
	corrige = forms.CharField(initial="Correction",label="",widget=forms.Textarea,required=False) 	
	type = forms.ChoiceField(label="Type de correction",choices=[('1','Une bonne réponse')])

class MakexoAjouterReponse(forms.Form):
	
	nouvellereponse = forms.BooleanField(widget=forms.HiddenInput(),initial=True)

class MakexoAjouterExo(forms.Form):
	
	nouvelexo = forms.BooleanField(widget=forms.HiddenInput(),initial=True)

class MakexoModifierExo(forms.Form):

	def setId(self,id):
		self.fields['idexo'] =  forms.IntegerField(widget=forms.HiddenInput(),initial=id)
	idexo = forms.IntegerField()

class MakexoReponse(forms.Form):

	nom = forms.CharField(max_length=3)
	texte = forms.CharField(max_length=2000,widget=forms.Textarea)
	position = forms.ChoiceField(label="Position",choices=[('1','1')])


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

class ExoChoix(forms.Form):
	
	def setListe(self,listeChoix):
		self.fields['exo'] = forms.ChoiceField(label=" exercices de ",choices=listeChoix)
		
		
	nbexos=forms.IntegerField(initial=1,min_value=1,label="Ajouter")
	exo=forms.ChoiceField(label="Liste de vos Exos")
	
class EffacerCopie(forms.Form):
	cpid = forms.IntegerField(widget=forms.HiddenInput())
	
class EffacerExo(forms.Form):
	exo = forms.IntegerField(widget=forms.HiddenInput())
	
class EffacerFExo(forms.Form):
	fexo = forms.IntegerField(widget=forms.HiddenInput())
	
class Effacer(forms.Form):
	fichieraeff = forms.CharField(label="Fichier",widget=forms.HiddenInput())
	
class TelechargerNotes(forms.Form):
	generernotes = forms.BooleanField(widget=forms.HiddenInput(),initial=True)

class AjoutTemplate(forms.Form):
	def setFields(self,qcm):
		self.fields['nomTeX'] = forms.CharField(max_length=100,label="Sujet",initial=qcm.nomTeX)
		self.fields['texteTeX'] = forms.CharField(label="Texte",widget=forms.Textarea,initial=qcm.texteTeX)
		self.fields['texteTeX'].widget.attrs['cols']=u'100'
	nomTeX = forms.CharField(max_length=100,label="Sujet")
	texteTeX = forms.CharField(label="Texte",widget=forms.Textarea)

class MontrerImage(forms.Form):
	montrerimage = forms.IntegerField(widget=forms.HiddenInput())

class AjoutCopies(forms.Form):
	fichiercp = forms.FileField(label="Copies")
	
class Telecharger(forms.Form):
	fichieratel = forms.CharField(label="Fichier",widget=forms.HiddenInput())
	
class QCMChoix(forms.Form):
	def setListe(self,listeChoix):
		self.fields['qcm'] = forms.ChoiceField(label="Liste de vos QCM",choices=listeChoix)
		
	qcm = forms.ChoiceField(label="Liste de vos QCM")

class Note(forms.Form):
	note = forms.FloatField(label="")
	copiecorrigeeid = forms.IntegerField(widget=forms.HiddenInput())

class NouveauQCM(forms.Form):
	titre = forms.CharField(max_length=100,label="Nouveau QCM")

class NouveauxExos(forms.Form):
	exos = forms.FileField(label="Charger un nouveau fichier .exos")

class AssignerCopie(forms.Form):
	numcopie = forms.CharField(max_length=100,label="Numero de copie")
