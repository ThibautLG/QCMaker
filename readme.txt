=== QCMaker ===
Contributors: thibaut
Tags: qcm, django

== Installation ==

Dans mon pip freeze j'ai:

Django==1.7
argparse==1.2.1
distribute==0.7.3
django-cas==2.1.1
matplotlib==1.4.2
mock==1.0.1
nose==1.3.4
numpy==1.9.1
pyparsing==2.0.3
python-dateutil==2.4.0
pytz==2014.10
six==1.9.0
wsgiref==0.1.2

En plus, la version d'open-cv installée est:
Rev: 4557

Dans le fichier qcm/settings.py:
- il faut mettre le bon gestionnaire de base de données 
DATABASES = {
}
- il faut probablement enlever les debug = True

Il faut aussi certainement préparer la base de données avec un:
python manage.py syncdb