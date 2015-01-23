#-*- coding:utf-8 -*-

import pickle, os, time
from datetime import datetime

from django.core.wsgi import get_wsgi_application
os.environ['DJANGO_SETTINGS_MODULE'] = 'qcm.settings'
application = get_wsgi_application()

dossierbgjobs="prof/bgjobs/"
if not os.path.exists(dossierbgjobs):
    os.mkdir(dossierbgjobs)

while True:
    listjobs = [job for job in os.listdir(dossierbgjobs) if job.startswith("job")]
    if listjobs:
        print("Job(s) trouvé(s): "+str(listjobs))
    for job in listjobs:
        try:
            with open(dossierbgjobs+job, 'r') as f:
                foncetarg=pickle.load(f)
                fonction=foncetarg[0]
                arg=foncetarg[1]
                print(fonction,arg)
                fonction(arg)
                os.remove(dossierbgjobs+job)
                print('Job '+str(job)+' fait')
        except Exception,er:
            print('Erreur: '+str(er))
    time.sleep(1)
    
