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
import numpy

import json
import measure
from measure import similarity
from measure import arithmeticMean, harmonicMean

#import matplotlib.pyplot as plt
import kappaFleiss

import matplotlib.pyplot as plt


def readAnnotFile(filename="eval_S.csv", directory="Kappa1207-025cum-premiersPas"):
    res = []
    pat = set()
    print filename
    with codecs.open(os.path.join(directory, filename), 'r', encoding='utf-8') as fIn:
        lines = fIn.readlines()
        for l in lines[1:len(lines)] :
            if not l.strip() : continue
            answers = l.strip().split(';')
            if len(answers) < 4 : answers.extend(['', ''])
            res.append(answers)
            pat = pat | set([answers[0]])
    return res

def printConfrontationFile(files=['eval_S.csv', 'eval_AL.csv', 'eval_L.csv'], directory="Kappa1207-025cum-premiersPas", outputFile="confrontation.csv"):
    filesRead = []
    for f in ['eval_S.csv', 'eval_AL.csv', 'eval_L.csv']:
        filesRead.append(readAnnotFile(f))
    if not filesRead or (len(filesRead) == 0) :
        print 'Arg should be a non-empty list of files'
        exit
    lens = map(len, filesRead)
    print lens
    if len(set(lens)) > 1 :
        print 'Files should have the same length'
        exit
    nbPairs = lens[0]
    res = []
    f0 = filesRead[0]
    f1 = filesRead[1]
    f2 = filesRead[2]
    nbCons = 0
    nbDiff = 0
    for i in range(nbPairs) :
        #Check that all pairs are the same
        for x in [0, 1] :
            if not (f0[i][x].strip() == f1[i][x].strip() and f0[i][x].strip() == f2[i][x].strip() and f1[i][x].strip() == f2[i][x].strip()) :
                print 'All pairs should be in the same order : '+str(i)
                exit
        line = [f0[i][0], f0[i][1]]
        
        for x in [2, 3] : 
            if f0[i][x].strip(' ?') == f1[i][x].strip(' ?') and f0[i][x].strip(' ?') == f2[i][x].strip(' ?') and f1[i][x].strip(' ?') == f2[i][x].strip(' ?')  :
                line.append(f0[i][x].strip(' ?'))
                nbCons = nbCons + 1
            else :
                line.append('%'.join([f0[i][x].strip(), f1[i][x].strip(), f2[i][x].strip()]))
                nbDiff = nbDiff + 1

        res.append(';'.join(line))

    print 'nbCons = '+str(nbCons)
    print 'nbDiff = '+str(nbDiff)
    
    with codecs.open(os.path.join(directory, outputFile), 'w', encoding='utf-8') as fOut:
        fOut.write('PATIENT;MEDECIN;ALTERNATIVE;RELATED(M,G,P)\n')
        nbPairs = 0
        fOut.write('\n'.join(res))

def printConsensusRes(filename="consensus.csv", directory="Kappa1207-025cum-premiersPas", nbAnnot=3):
    cf = readAnnotFile(filename=filename, directory=directory) # consensus file
    
    #nbPairs = len(cf)
    ltops = sorted(set(range(50, len(cf), 50)) | set([len(cf)]))
    lprecisions = {'1':[], 'CGP':[], 'all':[]}
    for nbPairs in ltops :
        print '============='+str(nbPairs)+'======'
        nbCons = 0
        nbDiff = 0
        results = {}
        for i in range(nbPairs) :
            for x in [2, 3] :
                line = cf[i]
                if not line[x].strip() :
                    nbCons = nbCons + 1
                    continue
                ans = line[x].split('%')
                if len(ans) == 1 :
                    nbCons = nbCons + 1
                    alt = results.get(line[x], [])
                    alt.append(line[0]+'|'+line[1])
                    results[line[x]] = alt
                else :
                    nbDiff = nbDiff + 1
                    # take the majority vote

        total = 0
        for cat in results :
            nb = len(results[cat])
            total = total + nb
            print cat+' : '+str(nb)

        
        print 'nbCons = '+str(nbCons)
        print 'nbDiff = '+str(nbDiff)
        print 'nb relations cons = '+str(total)
        print 'Precision relations = '+str(total/nbPairs)
        print 'Precision alternative = '+str(len(results['1'])/nbPairs)
        lprecisions['1'].append(len(results['1'])/nbPairs)
        lprecisions['CGP'].append( (len(results['C'])+len(results['G'])+len(results['P'])) / nbPairs)
        lprecisions['all'].append(total/nbPairs)
        #print results['1']
    x = numpy.array(ltops)
    y1 = numpy.array(lprecisions['1'])
    yAll = numpy.array(lprecisions['all'])
    plt.plot(x,y1, "b:o", label="alternatives")
    plt.plot(x,yAll, "r:o", label="alternatives+CGP")
    plt.xlim(min(ltops), max(ltops))
    plt.ylim(0, 0.8)
    plt.title("Variation de la precision")# selon le nombre de paires retenu")
    plt.ylabel("Precision")
    plt.xlabel("nombre de paires retenues")
    plt.show()
    
if __name__ == "__main__":
    #printConfrontationFile(files=['eval_S.csv', 'eval_AL.csv', 'eval_L.csv'], outputFile="confrontation1.csv")
    printConsensusRes(filename="consensus.csv", directory="Kappa1207-025cum-premiersPas", nbAnnot=3)
    
            

