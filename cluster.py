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
from alignementDirect import ENTITY_FREQ_FILE_INPUT

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
    freq_unigrams_entity = read_json(ENTITY_FREQ_FILE_INPUT)
    print len(NETWORK)
    for x in NETWORK.keys() :
        if freq_unigrams_entity.get(x, 0) < 5 : del NETWORK[x]
        
    
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
    #alignAll()
    
    data = read_json('INCLUSTER/align-COSINE-PMI.json')
    print len(data)
    selected = []
    thres = 0.055
    for item in sorted(data.keys()) :
        scores = [x['score'] for x in data[item]]
        #print scores
        #if len(scores) == 0 or max(scores) < thres : print my_str(item) #data.pop(item, None)
        #else : selected.append(item)
        if len(scores) > 0 : selected.append(item)
        else : print my_str(item)
    print len(selected)
    #print data['nilou']
    print 'O o o'
    exit

    N = len(selected)
    Sim = numpy.zeros((N, N))
    inds = {}
    for i in range(len(selected)) :
        inds[selected[i]] = i
        data_i = {cand['name']:cand['score'] for cand in data[selected[i]]}
        for j in range(i+1, len(selected)) :
            #print i
            #print j
            #print '=='
            #print data_i
            Sim[i][j] = data_i.get(selected[j], 0) #TODO            
    print Sim[min([inds['cancer'], inds['crabe']])][max([inds['cancer'], inds['crabe']])]

    clusters = dict() #id:[list of items]
    cptId = 0
    dendoIt = {}
    indToCluster = {}

    nbIter = 0
    UpdateSim = Sim.copy()
    # Init clusters
    for i in range(len(selected)) :
        clusters[i] = set([i])
        indToCluster[i] = i
    dendoIt[nbIter] = clusters

    # Iterate
    while True:#for n in range(100) : 
        maxInd = UpdateSim.argmax()
        #print maxInd
        #maxVal = Sim(maxInd)
        #print maxVal
        maxInds = numpy.unravel_index(maxInd, (N,N))
        #print maxInds
        print Sim[maxInds[0]][maxInds[1]]
        print UpdateSim[maxInds[0]][maxInds[1]]
        print my_str(selected[maxInds[0]])
        print my_str(selected[maxInds[1]])
        print "------"

        if UpdateSim[maxInds[0]][maxInds[1]] < 0.05 :#numpy.finfo(float).eps : #0.050 :#:5 : #
            print 'END'
            #exit
            break
        if len(dendoIt[nbIter]) == 2 :
            print '2 CLUSTERS'
            #exit
            break

        # Update matrix
##        UpdateSim[maxInds[0]][maxInds[1]] = 0
##        for i in range(len(selected)) :
##            val = min(
##                    UpdateSim[min(maxInds[0], i)][max(maxInds[0], i)],
##                    UpdateSim[min(maxInds[1], i)][max(maxInds[1], i)]
##                    )
##            UpdateSim[min(maxInds[0], i)][max(maxInds[0], i)] = val
##            UpdateSim[min(maxInds[1], i)][max(maxInds[1], i)] = val

        # Build cluster
        clId_i = indToCluster.get(maxInds[0])
        clId_j = indToCluster.get(maxInds[1])
        currentCl = clusters.get(clId_i)
        #print currentCl
        clusterToAbsorb = clusters.get(clId_j)
        #print clusterToAbsorb
        currentCl.update(clusterToAbsorb)
        clusters[clId_i] = currentCl
        # Update indToCluster
        for x in clusterToAbsorb :
            indToCluster[x] = clId_i
            # Update matrix 1/2
            for y in currentCl :
                UpdateSim[min(x,y)][max(x,y)] = 0
        del clusters[clId_j]
        # Update matrix 2/2
        for x in currentCl :
            for y in range(len(selected)) :
                UpdateSim[min(x,y)][max(x,y)] = min(
                    [UpdateSim[min(item,y)][max(item,y)] for item in currentCl]
                    )
##                min(
##                    [UpdateSim[min(item,y)][max(item,y)] for item in currentCl]
##                    )
##                 max(
##                    [UpdateSim[min(item,y)][max(item,y)] for item in currentCl]
##                    ) 
##                sum(
##                    [UpdateSim[min(item,y)][max(item,y)] for item in currentCl]
##                    ) / len(currentCl)
        
        
##        if clId_i == -1 and clId_j == -1 : 
##            currentCl = clusters.get(cptId, set())
##            currentCl.update([selected[maxInds[0]], selected[maxInds[1]]])
##            clusters[cptId] = currentCl
##            indToCluster[maxInds[0]] = cptId
##            indToCluster[maxInds[1]] = cptId
##            cptId = cptId + 1
##        else :
##            print 'already in clusters'

        nbIter = nbIter + 1
        dendoIt[nbIter] = clusters.copy()
##        cl = dendoIt[nbIter]
##        print "*********"+str(nbIter)
##        for x in cl :
##            print x
##            for i in cl[x]:
##                print my_str(selected[i])
##            print "========="
##        print "*********"+str(nbIter)
        print "======"
    #print clusters
    cl = dendoIt[nbIter]
    print "*********"+str(nbIter)
    for x in cl :
        print x
        for i in cl[x]:
            print my_str(selected[i])
        print "========="
    print "*********"+str(nbIter)
    print "======"
    print len(clusters)

    # Select pat terms
    clItems = {}
    selectedPat = []
    TARGET_NETWORK = read_json(TARGET_NETWORK_FILE_INPUT)
    SOURCE_NETWORK = read_json(SOURCE_NETWORK_FILE_INPUT)
    #print TARGET_NETWORK
    for x in cl :
        clItems[x] = [selected[i] for i in cl[x]]
        if len(set(clItems[x]) & set(TARGET_NETWORK.keys())) > 0 :
            for item in set(clItems[x]) & set(SOURCE_NETWORK.keys()) :
                selectedPat.append(item)
    #print clItems
    #selectedPat = [item for item in clItems[x] for x in clItems]
                   #if len(set(clItems[x]) & set(TARGET_NETWORK.keys())) > 0
                   #]
    print "************"
    print [my_str(t) for t in selectedPat]
    print len(selectedPat)
    print len(set(selectedPat) - set(SOURCE_NETWORK.keys()))
##    for pat in SOURCE_NETWORK :
##        if pat in 
    
