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

import alignementDirect
from alignementDirect import SOURCE_NETWORK, TARGET_NETWORK
from alignementDirect import SOURCE_TRANSFERRED_VECTORS, TARGET_TRANSFERRED_VECTORS
from alignementDirect import read_json, normalizeTFIDF, normalizePMI, findCandidateTranslations
from alignementDirect import save_as_json, evaluate_against_gold, writeJsonGraph
from alignementDirect import SOURCE_NETWORK_FILE_INPUT, TARGET_NETWORK_FILE_INPUT
from alignementDirect import NORMALIZATION, TFIDF, PMI
from alignementDirect import SIMILARITY_FUNCTION
from alignementDirect import ESPILON as EPSILON
from alignementDirect import my_str

def alignAll(top=None):
    NETWORK = dict() #all entities
    global SOURCE_NETWORK
    global TARGET_NETWORK
    global SOURCE_TRANSFERRED_VECTORS
    global TARGET_TRANSFERRED_VECTORS
    global EPSILON
    EPSILON = 0.055
    print ">LOADING Pat candidates..."
    SOURCE_NETWORK = read_json(SOURCE_NETWORK_FILE_INPUT)
    #print SOURCE_NETWORK
    print ">LOADING Med candidates..."
    TARGET_NETWORK = read_json(TARGET_NETWORK_FILE_INPUT)
    #print TARGET_NETWORK

    NETWORK = SOURCE_NETWORK.copy()
    NETWORK.update(TARGET_NETWORK)
    
    start_time = time.time()
    
    print ">NORMALIZING ("+NORMALIZATION+") CONTEXT VECTORS..."
    if (NORMALIZATION == TFIDF) :
        normalizeTFIDF(NETWORK)
    elif (NORMALIZATION == PMI) :
        normalizePMI(NETWORK)

    PIVOT_WORDS = set()

    # We assume same language
    SOURCE_TRANSFERRED_VECTORS = SOURCE_NETWORK
    #TARGET_TRANSFERRED_VECTORS = TARGET_NETWORK
    print ">COMPUTING CANDIDATES RANKING ("+SIMILARITY_FUNCTION+")..."

    if not top : top = len(NETWORK)
    # DIRECT
    candidates = {} #Map< String, List<String> >
    unknownSourceWords = set()
    testset = NETWORK.keys()
    data = {}
    for word in testset :
        #print ">> DIRECT Candidates for '"+ word.encode(encoding='UTF-8',errors='strict')+"'"
        if word not in NETWORK :
            print my_str(word)+" not in source corpus"
            unknownSourceWords.add(word)
            #candidates[word] = []
        else :
            #transferedVector = transferedNetwork[word] #getTransferedVector(word)
            #Base
            word_target = NETWORK.copy()
            word_target.pop(word, None)
            candidates[word] = findCandidateTranslations(word, NETWORK[word], word_target, top, SIMILARITY_FUNCTION)
            data[word] = candidates[word][0:top]
        print my_str(word)
        print candidates[word][0:top]
        print "========"
        print "========"
    save_as_json(data, 'align-'+SIMILARITY_FUNCTION+'-'+NORMALIZATION+'.json')
    #evaluate_against_gold(data)
    writeJsonGraph(data, 'graph-'+SIMILARITY_FUNCTION+'-'+NORMALIZATION+'.json')
    elapsed_time = time.time() - start_time
    print str(elapsed_time)
    print EPSILON
    return data

if __name__ == "__main__":
    data = read_json('INCLUSTER/align-COSINE-PMI.json')
    print len(data)
    selected = []
    thres = 0.055
    for item in data :
        scores = [x['score'] for x in data[item]]
        #print scores
        if len(scores) == 0 or max(scores) < thres : print my_str(item) #data.pop(item, None)
        else : selected.append(item)
    print len(selected)
    #print data['nilou']

    N = len(selected)
    sim = numpy.zeros((N, N))
    for i in range(len(selected)) :
        for j in range(i+1, len(selected)) :
            #print i
            #print j
            #print '=='
            sim[i][j] = 0 #TODO
            
    #alignAll()
