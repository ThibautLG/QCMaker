QCMaker
=======
Contributors: ThibautLG

Tags: qcm, django

Présentation
============

Site de génération et correction de QCM papier.

Features
========

+ enregistre des banques d'exerices en format LaTeX
+ génère des QCMs au format pdf à partir des banques d'exercices
+ corrige et note les QCMs à partir des scans des copies
+ interface pour que les élèves puissent accéder à leurs copies corrigées et à leur note
+ possibilité d'enregistrer une correction pour chaque exerice, pour les élèves


Installation
===========

Dépendances
-----------

Dans pip freeze:

    Django==1.7
    argparse==1.2.1
    distribute==0.7.3
    django-cas==2.1.1
    mock==1.0.1
    nose==1.3.4
    numpy==1.9.1
    pyparsing==2.0.3
    python-dateutil==2.4.0
    pytz==2014.10
    six==1.9.0
    wsgiref==0.1.2

+ la librairie open-cv Rev: 4557

Et les logicels:

    pdfunite version 0.18.4
    pdfTeX 3.1415926-2.4-1.40.13 (TeX Live 2012/Debian)
    ImageMagick 6.7.7-10 2014-03-08 Q16
    pdf2svg

Pour trouver le bon django-cas:

    pip install https://bitbucket.org/cpcc/django-cas/get/47d19f3a871f.zip

Configuration
-------------

Dans le fichier qcm/settings.py:
- il faut mettre le bon gestionnaire de base de données
DATABASES = {
}
- il faut probablement enlever les debug = True
- remplacer STATICFILES_DIRS par STATIC_ROOT


Il faut aussi certainement préparer la base de données avec un:

    python manage.py syncdb

Y'a aussi a lancer pour la mise en prod:

    mkdir static;
    python manage.py collectstatic

Sous Windows :
-------------

1) Télécharger Anaconda :

Windows64 https://3230d63b5fc54e62148e-c95ac804525aac4b6dba79b00b39d1d3.ssl.cf1.rackcdn.com/Anaconda2-2.4.1-Windows-x86_64.exe

Windows32 https://3230d63b5fc54e62148e-c95ac804525aac4b6dba79b00b39d1d3.ssl.cf1.rackcdn.com/Anaconda2-2.4.1-Windows-x86.exe

2) Importer le dossier QCMaker dans GitBash :
    
    git clone https://github.com/ThibautLG/QCMaker.git
    
3) Ajouter le fichier manage.py dans le dossier QCMaker

    https://www.dropbox.com/s/5dbn82vzaksd50w/manage.py?dl=0
    
4) Installer cv2 :

-Télécharger et extraire Opencv
    
    http://downloads.sourceforge.net/project/opencvlibrary/opencv-win/3.1.0/opencv-3.1.0.exe?r=http%3A%2F%2Fopencv.org%2F&ts=1453856522&use_mirror=netix
    
-Mettre le fichier opencv\build\python\2.7\x64\cv2.pyd dans le dossier anaconda2\Lib\site-packages

-Installer le module

    pip install cv2
    
5) Mettre la bonne version de django

    pip install django==1.7
    
6) Aller dans QCMaker\qcm\settings.py et régler ALLOWED_HOSTS = ['*']

7) Installer Django-cas :

    pip install https://bitbucket.org/cpcc/django-cas/get/47d19f3a871f.zip
    
8) Créer dans QCMaker un dossier media\ups\1

9) Etablir la base de données

    python manage.py syncdb
    
10) Lancer le serveur
    
![myimage-alt-tag](http://img15.hostingpics.net/pics/501201runserver.jpg)

Lancement
========

Au demarrage, il faut aussi lancer le worker:

    python worker.py

et pour un bug du serveur, s'assurer que:

    export LD_LIBRARY_PATH=/usr/local/lib/gcc48
    
    

