#-*- coding:utf-8 -*-

import pickle
from datetime import datetime

dossierbgjobs="prof/bgjobs/"

class BgJob():
    def __init__(self,fonction,arguments):
        with open(dossierbgjobs+"job"+str(datetime.now().microsecond),'w') as f:
            pickle.dump([fonction,arguments], f)

#	with open(conf.pickle, 'w') as f:
#			originaux += pickle.load(f)	
