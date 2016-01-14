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


Lancement
========

Au demarrage, il faut aussi lancer le worker:

    python worker.py

et pour un bug du serveur, s'assurer que:

    export LD_LIBRARY_PATH=/usr/local/lib/gcc48
