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


DICO = {}
DICO_INV = {}

TARGET_SPACE = set()
SOURCE_SPACE = set()
PIVOT_WORDS = set()
TARGET_TRANSFERRED_VECTORS = {}
SOURCE_TRANSFERRED_VECTORS = {}
TARGET_NETWORK = {}
SOURCE_NETWORK = {}
TARGET_TRANSFERRED_VECTORS_FILE = "target_transferred_vectors.json"
SOURCE_TRANSFERRED_VECTORS_FILE = "source_transferred_vectors.json"
TARGET_NETWORK_FILE = "target_network.json"
SOURCE_NETWORK_FILE = "source_network.json"
TARGET_NETWORK_FILE_INPUT = "IN/med_context.json"
SOURCE_NETWORK_FILE_INPUT = "IN/pat_context.json"
CONTEXT_FREQ_FILE_INPUT = "IN/frequency_contextTerms.json"
ENTITY_FREQ_FILE_INPUT = "IN/frequency_lexicon.json"


#-------------------------------------------------------------------------
# PARAMETERS
#-------------------------------------------------------------------------
##MIN_WORD_LENGTH=3
SIMILARITY_FUNCTION=measure.COSINE #JACCARD_SET #JACCARD #
##METHOD=CHIAO
##STRATEGY_DICO="TO BE DEFINED"
##TOLERANCE_RATE=1 #1.5 #When there is several candidates with the same score, we accept
TFIDF="TFIDF"
PMI="PMI"
NORMALIZATION=PMI #LO #"none" #TFIDF #
##STRATEGY_TRANSLATE=ALL_WEIGHTED #MOST_FREQ #SAME_WEIGHT #
# to process max. TOP*TOLERANCE_RATE candidates
ESPILON=numpy.finfo(float).eps
_log2 = lambda x: log(x, 2.0)

def save_as_json(data, outputFile, directory="OUTPUT") :
    if not os.path.exists(directory):
        os.makedirs(directory)
    with codecs.open(os.path.join(directory, outputFile), 'w', encoding='utf-8') as outfile:
        json.dump(data, outfile, encoding='utf8') #, ensure_ascii=False)

def read_json(inputFile) :
    with codecs.open(inputFile, 'r', encoding='utf-8') as fIn:
        return json.loads(fIn.read(), encoding="utf8") #, ensure_ascii=False)
        
def addCandidateWithScore(result, candidate, score) :
    item = {}
    item["name"] = candidate
    item["score"] = score
    result.append(item)

    
def findCandidateTranslations(word, transferedVector, targetNetwork, nb, similarityFunction, f_filter_candidates=None) :
    #list of the nb best scores found  candidates = {}
    scores = []
    if f_filter_candidates is None :
        candidates = findCandidateScores(word, transferedVector, targetNetwork, nb, similarityFunction)
        scores = sorted(candidates.keys(), reverse=True)
    else :
        candidatesKeys = DICO.get(word, [])
        if len(candidatesKeys) == 0 :
            candidatesKeys = [k for k in targetNetwork.keys() if (len(DICO_INV.get(k, []))== 0)]
        filteredTargetNetwork = {k: v for k, v in targetNetwork.iteritems() if k in candidatesKeys}
        candidates = findCandidateScores(word, transferedVector, filteredTargetNetwork, nb, similarityFunction)
        scores = sorted(candidates.keys(), reverse=True)
    #print "========="
    #print scores

    result = [] #Concatenation of Strings from candidates, ordered by their rank; len(translations) <= TOP
    # Give an ordered list of the translation candidates
    for i in range(len(scores)) :
        for w in candidates[scores[i]] :
            #print w+"> "+str(s)
            addCandidateWithScore(result, w, scores[i])
            #result.append(w)

 #  i = 0
#  while (i<TOP) and (i<len(scores)) :
#    for w in candidates[scores[i]] : 
#      result.append(w)
#      print word+"> "+str(i)+" "+w
#    i=i+len(candidates[scores[i]])
    return result

def findCandidateScores(word, transferedVector, targetNetwork, nb, similarityFunction) :
    """ nb : number of candidates scores to find """
    #print"====="
    TOP = nb
    scores = [] #list<Double> ; invariant : len(scores) <= TOP
    candidates = {} #Map< Double, list<String> >
    result = [] #Concatenation of Strings from candidates, ordered by their rank; len(translations) <= TOP
    rank_results = [] #Concatenation of couple - rank
    current_min = 10000 #TODO initialize with max double
    for c in targetNetwork :
        score_c = similarity(transferedVector, targetNetwork[c], similarityFunction)
        if (score_c == -float("Inf")) or (score_c < ESPILON) : continue #or score_c < ESPILON
        if len(scores) < TOP :
            # add candidate
            #print "ADDING ("+c.encode(encoding='UTF-8',errors='strict')+", "+str(score_c)+")"
            if score_c not in candidates :
                scores.append(score_c)
                candidates[score_c] = []
            # score_c is already in scores and in candidates' keyset
            candidates[score_c].append(c)
            # update current_min
            if current_min > score_c : current_min = score_c 
        else :
            if score_c > current_min :
                # replace by the candidate c
                # pre : current_min is in candidates as key and in scores
                scores.remove(current_min)
                del candidates[current_min]
                # add candidate
                #print "ADDING ("+c.encode(encoding='UTF-8',errors='strict')+", "+str(score_c)+")"
                if score_c not in candidates :
                    scores.append(score_c)
                    candidates[score_c] = []
                #else score_c is already in scores and in candidates' keyset
                candidates[score_c].append(c)
                # update current_min
                current_min = min(scores)
    # rank the results
    return candidates

def my_str(c) :
    return c.encode(encoding='UTF-8',errors='strict')
def sum_cooc(context_i):
    return reduce(add, context_i.values(), 0)
def add(x,y): return x+y

def normalizeTFIDF(vectors):
    """ Normalize context vectors using the tf*idf measure described in Chiao """
    max_cooc = [reduce(max, vectors[i].values(), 0) for i in vectors]
    MAX_OCC = float(max(max_cooc))
    cooc_i = [sum_cooc(vectors[i]) for i in vectors]
    for i_index, i in enumerate(vectors) :
        if  not vectors[i] : continue
        #print i
        #print i_index
        #print cooc_i[i_index]
        idf = 1 + log(MAX_OCC/cooc_i[i_index])
        for j in vectors[i] :
            vectors[i][j] = ( float(vectors[i][j])/MAX_OCC ) * idf

def normalizePMI(vectors):
    """ Normalize context vectors using the PMI measure described in Manning et al. """
    freq_unigrams_context = read_json(CONTEXT_FREQ_FILE_INPUT)
    #print freq_unigrams_context
    total_contexts = reduce(add, freq_unigrams_context.values(), 0)
    
    freq_unigrams_entity = read_json(ENTITY_FREQ_FILE_INPUT)
    #print freq_unigrams_entity
    total_entities = reduce(add, freq_unigrams_entity.values(), 0)

    for entity in vectors :
        print "=============="+my_str(entity)
        if entity not in freq_unigrams_entity  : continue
        p_entity = freq_unigrams_entity[entity] / total_entities
        #print "p_entity"+str(p_entity)
        for context in vectors[entity] :
            p_entity_context = vectors[entity][context]
            #print "p_entity_context"+str(p_entity_context)
            p_context = freq_unigrams_context[context] / total_contexts
            #print "p_context"+str(p_context)
            vectors[entity][context] = _log2(p_entity_context) - _log2(p_entity * p_context)
            #print my_str(entity)+"__"+my_str(context)+" ="+str(vectors[entity][context])


if __name__ == "__main__":
    print ">LOADING Pat candidates... TODO"
    SOURCE_NETWORK = read_json(SOURCE_NETWORK_FILE_INPUT)
    #print SOURCE_NETWORK
    print ">LOADING Med candidates... TODO"
    TARGET_NETWORK = read_json(TARGET_NETWORK_FILE_INPUT)
    #print TARGET_NETWORK
    
    print ">NORMALIZING ("+NORMALIZATION+") CONTEXT VECTORS... TODO"
    if (NORMALIZATION == TFIDF) :
        normalizeTFIDF(SOURCE_NETWORK)
        normalizeTFIDF(TARGET_NETWORK)
    elif (NORMALIZATION == PMI) :
        normalizePMI(SOURCE_NETWORK)
        normalizePMI(TARGET_NETWORK)

    start_time = time.time()

    PIVOT_WORDS = set()

    # We assume same language
    SOURCE_TRANSFERRED_VECTORS = SOURCE_NETWORK
    print ">COMPUTING CANDIDATES RANKING... TODO"
    top_list = [10]
    candidates = {} #Map< String, List<String> >
    unknownSourceWords = set()
    testset = SOURCE_NETWORK.keys()

    data = {}
    for word in testset :
        print ">>Candidates for '"+ word.encode(encoding='UTF-8',errors='strict')+"'"
        if word not in SOURCE_NETWORK :
            print word+" not in source corpus"
            unknownSourceWords.add(word)
            candidates[word] = []
        else :
            #transferedVector = transferedNetwork[word] #getTransferedVector(word)
            #Base
            candidates[word] = findCandidateTranslations(word, SOURCE_TRANSFERRED_VECTORS[word], TARGET_NETWORK, max(top_list), SIMILARITY_FUNCTION)
        data[word] = candidates[word][0:max(top_list)]
        save_as_json(data, 'context-cosinus-none.json') 
        #print word.encode(encoding='UTF-8',errors='strict')
        #print candidates[word][0:max(top_list)]
        #print "========"
        #print "========"
    elapsed_time = time.time() - start_time
    print str(elapsed_time)

    # INVERSE
    start_time = time.time()
    TARGET_TRANSFERRED_VECTORS = TARGET_NETWORK
    candidates = {} #Map< String, List<String> >
    unknownSourceWords = set()
    testset = TARGET_NETWORK.keys()

    data = {}
    for word in testset :
        print ">>Candidates for '"+ word.encode(encoding='UTF-8',errors='strict')+"'"
        if word not in TARGET_NETWORK :
            print word+" not in source corpus"
            unknownSourceWords.add(word)
            candidates[word] = []
        else :
            #transferedVector = transferedNetwork[word] #getTransferedVector(word)
            #Base
            candidates[word] = findCandidateTranslations(word, TARGET_TRANSFERRED_VECTORS[word], SOURCE_NETWORK, 2*max(top_list), SIMILARITY_FUNCTION)
        data[word] = candidates[word][0:(2*max(top_list))]
        save_as_json(data, 'inv-context-cosinus-none.json') 
        #print word.encode(encoding='UTF-8',errors='strict')
        #print candidates[word][0:max(top_list)]
        #print "========"
        #print "========"
    elapsed_time = time.time() - start_time
    print str(elapsed_time)
