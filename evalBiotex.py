#coding:utf-8

#-------------------------------
# Infers traductions based on two comparable corpora
# We perform the direct method using a dictionary of cognates
# and a bilingual dictionary
#-------------------------------

from __future__ import division
import re, sys, os #, nltk
import types
import time
import codecs
from math import sqrt, log, log10
from collections import Counter
from re import match
#import numpy

import json
import measure
from measure import similarity
from measure import arithmeticMean, harmonicMean


def readEvalFileBioTex(filename, directory='Kappa'):
    res = {'o' : [], 'n':[]}
    pat = set()
    print filename
    with codecs.open(os.path.join(directory, filename), 'r', encoding='utf-8') as fIn:
        for l in fIn.readlines()[1:] :
            if not l.strip() : continue
            answers = l.strip().split(';')
            if len(answers) < 2 : answers.extend(['n', 'n'])
            #if len(answers) == 1 : answers = l.strip().split('\t')
            #print answers
            #print '====='
            pat = pat | set([answers[0]])
            ok = res.get('o', [])
            no = res.get('n', [])
            if answers[1].lower().strip() == 'n' :
                no.append(answers[0])
                res['n'] = no
            else :
                ok.append(answers[0])
                res['o'] = ok
    #print len(pat)
    #print pat
    return res


def kappaBioTex(lFiles=['test_Solene_AL.csv', 'test_Solene_L.csv', 'test_Solene_S.csv']) :
    dictPairs_S = {}
    dictPairs_AL = {}
    dictPairs_L = {}    
    candidates = set()
    res = []

    annot_AL = readEvalFileBioTex(lFiles[0])
    #print annot
    candidates = candidates | set(annot_AL.keys())

    annot_L = readEvalFileBioTex(lFiles[1])
    #print annot
    candidates = candidates | set(annot_L.keys())

    annot_S = readEvalFileBioTex(lFiles[2])
    #print annot
    candidates = candidates | set(annot_S.keys())
  
    allOk = set(annot_AL.get('o', [])) | set(annot_L.get('o', [])) | set(annot_S.get('o', []))
    allNo = set(annot_AL.get('n', [])) | set(annot_L.get('n', [])) | set(annot_S.get('n', []))

    consensusOk = set(annot_AL.get('o', [])) & set(annot_L.get('o', [])) & set(annot_S.get('o', []))
    consensusNo = set(annot_AL.get('n', [])) & set(annot_L.get('n', [])) & set(annot_S.get('rel', []))
    print 'consensus Ok; No'
    print len(consensusOk)
    print len(consensusNo)
    print 'desaccord All Ok; des Ok;  All No; des No'
    print len(allOk)
    desOk = allOk - consensusOk
    print len(desOk)
    desNo = allNo - consensusNo
    print len(allNo)
    print len(desNo)
    print '======'
    #for x in desRel :
    #     print x
    for x in consensusOk :
         print x
    res = {'o' : consensusOk, 'n' : consensusNo}
    return res


if __name__ == "__main__":
    #microEval()
    #successEval()
    #finalOutput(0.055)
    #testThres([ESPILON, 0.05, 0.055, 0.06, 0.07, 0.08, 0.09, 0.1])
    kappaBioTex()
