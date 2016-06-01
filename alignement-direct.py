#coding:utf-8

#-------------------------------
# Infers traductions based on two comparable corpora
# We perform the direct method using a dictionary of cognates
# and a bilingual dictionary
#-------------------------------

import re, sys, os #, nltk
import types
import time
import codecs
from math import sqrt, log, log10
from collections import Counter
from re import match

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

#-------------------------------------------------------------------------
# PARAMETERS
#-------------------------------------------------------------------------
##MIN_WORD_LENGTH=3
SIMILARITY_FUNCTION=measure.COSINE #JACCARD #
##METHOD=CHIAO
##STRATEGY_DICO="TO BE DEFINED"
##TOLERANCE_RATE=1 #1.5 #When there is several candidates with the same score, we accept
NORMALIZATION="none" #TFIDF #LO #
##STRATEGY_TRANSLATE=ALL_WEIGHTED #MOST_FREQ #SAME_WEIGHT #
# to process max. TOP*TOLERANCE_RATE candidates


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
        if score_c == -float("Inf") : continue
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

if __name__ == "__main__":
    print ">LOADING Pat candidates... TODO"
    SOURCE_NETWORK = read_json(SOURCE_NETWORK_FILE_INPUT)
    #print SOURCE_NETWORK
    print ">LOADING Med candidates... TODO"
    TARGET_NETWORK = read_json(TARGET_NETWORK_FILE_INPUT)
    #print TARGET_NETWORK
    
    print ">NORMALIZING ("+NORMALIZATION+") CONTEXT VECTORS... TODO"
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
