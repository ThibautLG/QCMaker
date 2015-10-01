#-*- coding:utf-8 -*-

import pickle, os
from datetime import datetime

dossierbgjobs="prof/bgjobs/"
def intify(r):
	return int(''.join(x for x in r if x.isdigit()))

class BgJob():
    def __init__(self,fonction,arguments):
	listefichier = os.listdir(dossierbgjobs)
	listefichier.extend('1')
	n=max(map(intify,listefichier))+1
	print('what? bg job')
        with open(dossierbgjobs+"job"+str(n),'w') as f:
		pickle.dump([fonction,arguments], f)
