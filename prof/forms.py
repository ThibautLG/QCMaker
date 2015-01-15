#-*- coding:utf-8 -*-

from django import forms

class Generer(forms.Form):
	nbpdfs = forms.CharField(initial="30,30,30",label="Copies à générer")

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
