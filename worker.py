#-*- coding:utf-8 -*-

import pickle, os, time, io
from datetime import datetime
os.environ['LD_LIBRARY_PATH'] = "/usr/local/lib/gcc48"

from django.core.wsgi import get_wsgi_application
os.environ['DJANGO_SETTINGS_MODULE'] = 'qcm.settings'
application = get_wsgi_application()

dossierbgjobs="prof/bgjobs/"
if not os.path.exists(dossierbgjobs):
    os.mkdir(dossierbgjobs)

def log(texte):
    fichierlog="worker.log"
    f=io.FileIO(fichierlog,'a')
    f.write(str(datetime.now())+" >>> "+str(texte)+"\n")
    f.close()
    return

while True:
    listjobs = [job for job in os.listdir(dossierbgjobs) if job.startswith("job")]
    if listjobs:
        log("Job(s) trouvé(s): "+str(listjobs))
    for job in listjobs:
        try:
            with open(dossierbgjobs+job, 'r') as f:
                foncetarg=pickle.load(f)
                fonction=foncetarg[0]
                arg=foncetarg[1]
                log("Function: "+str(fonction)+", argument: "+str(arg))
                log('Sortie: '+str(fonction(arg)))
                os.remove(dossierbgjobs+job)
                log('Job '+str(job)+' fait')
        except Exception,er:
            log('Erreur: '+str(er))
            os.remove(dossierbgjobs+job)
    time.sleep(1)
    
