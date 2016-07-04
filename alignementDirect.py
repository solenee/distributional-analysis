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


DICO = {}
DICO_INV = {}

TARGET_SPACE = set()
SOURCE_SPACE = set()
PIVOT_WORDS = set()
TARGET_TRANSFERRED_VECTORS = {"HELLO" : 1}
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
NONE="NONE"
NORMALIZATION=PMI #LO #NONE #TFIDF #
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


def getRank(candidates, word, isScore=True) :
    rank = 0
    s_index = 0
    stop = False
    scores = sorted(candidates.keys(), reverse=isScore)
    while not stop :
        if word in candidates[scores[s_index]] :
            rank = rank + 1
            stop = True
        else : rank = rank + len(candidates[scores[s_index]])
        s_index = s_index + 1
        if s_index == len(scores) :
            rank = float('inf')
            stop = True
    return rank


def findCandidateTranslationsChiao(word, transferedVector, targetNetwork, nb, similarityFunction, f_transferTarget=None, f_filter_candidates=None) :
    #print "==========="
    #print word
    #list of the nb best scores found
    candidates = {}
    scores = []
    if f_filter_candidates is None :
        #print "f_filter_candidates is None"
        candidates = findCandidateScores(word, transferedVector, targetNetwork, nb, similarityFunction)
        scores = sorted(candidates.keys(), reverse=True)
    else :
        candidatesKeys = DICO.get(word, [])
        if len(candidatesKeys) == 0 :
            candidatesKeys = [k for k in targetNetwork.keys() if (len(DICO_INV.get(k, []))== 0)]
        filteredTargetNetwork = {k: v for k, v in targetNetwork.iteritems() if k in candidatesKeys}
        candidates = findCandidateScores(word, transferedVector, filteredTargetNetwork, nb, similarityFunction)
        scores = sorted(candidates.keys(), reverse=True)
    res1 = [] #Concatenation of Strings from candidates, ordered by their rank; len(translations) <= TOP
    for i in range(len(scores)) :
        #if len(res1) >= nb*TOLERANCE_RATE : break
        for w in candidates[scores[i]] :
            #print w+"> "+str(s)
            res1.append(w)
            #if len(res1) >= nb*TOLERANCE_RATE :
            #print "----early exit"
            #break
    #print res1 #

    d_rank = {}

    for cand in res1 :
        if not (f_filter_candidates is None) :
            #print "f_filter_candidates is not None"
            if cand not in targetNetwork :
                #print str(cand)+" rejected because not in target corpus"
                continue
            #else : print str(cand)
        #else : print "f_filter_candidates is not None"
        if cand in TARGET_TRANSFERRED_VECTORS :
            cand_transferedVector = TARGET_TRANSFERRED_VECTORS[cand]
        else :
            #print "transfer::"
            #print my_str(cand)
            #print TARGET_TRANSFERRED_VECTORS
            raise RuntimeError("f_transferTarget is not defined in findCandidateTranslationsChiao")
            cand_transferedVector = f_transferTarget(cand)
            TARGET_TRANSFERRED_VECTORS[cand] = cand_transferedVector
        cand_reverse = findCandidateScores(cand, cand_transferedVector, SOURCE_NETWORK, nb, similarityFunction)
        #print my_str(cand)
        #print 'cand_reverse : '
        #print cand_reverse
        cand_rank = harmonicMean(getRank(candidates, cand), getRank(cand_reverse, word))
        if cand_rank not in d_rank : d_rank[cand_rank] = []
        d_rank[cand_rank].append(cand)
    
    result = []
    ranks = sorted(d_rank.keys(), reverse=False)
    # Give an ordered list of the translation candidates
    for i in range(len(ranks)) :
        if (ranks[i] == float('inf')) : continue
        for w in d_rank[ranks[i]] :
            #print w+"> "+str(s)
            addCandidateWithScore(result, w, ranks[i])
    #print "---"
    #print result
    return result



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

    cooc_list = [sum_cooc(vectors[i]) for i in vectors]
    total_entities_contexts = reduce(add, cooc_list, 0)

    for entity in vectors :
        #print "=============="+my_str(entity)
        if entity not in freq_unigrams_entity  : continue
        p_entity = freq_unigrams_entity[entity] / total_entities
        #print "p_entity"+str(p_entity)
        for context in vectors[entity] :
            p_entity_context = vectors[entity][context] / total_entities_contexts
            #print "p_entity_context"+str(p_entity_context)
            p_context = freq_unigrams_context[context] / total_contexts
            #print "p_context"+str(p_context)
            vectors[entity][context] = _log2(p_entity_context) - _log2(p_entity * p_context)
            #print my_str(entity)+"__"+my_str(context)+" ="+str(vectors[entity][context])

def writeJsonGraphMin(data1, data2, output='graph.json') :
    """ TODO keygroup can be 'pat' or 'med' """
    # nodes
    keygroup_nodes = set()
    nodes = []
    source = {}
    n_id = 0
    target = {}
    # links
    links = []
    for key_node in data.keys() :
        if not data[key_node] : continue
        # add node
        if key_node not in source :
            source[key_node] = n_id
            nodes.append({"name":key_node, "group":"1"})
            n_id += 1
        source_id = source[key_node]     
        for relation in data[key_node][0:1] :
            cand = relation["name"]
            if cand not in target :
                target[cand] = n_id
                nodes.append({"name":cand, "group":"2"})
                n_id += 1
            target_id = target[cand]
            # Build edge
            my_link = {"source":source_id,
                       "target":target_id,
                       "value":(relation["score"]*100)
                       }
            links.append(my_link)
    graph = {}
    graph["nodes"] = nodes
    graph["links"] = links
    save_as_json(graph, 'graph.json')
    return graph

def writeJsonGraphChiao(data, output='chiao-graph.json') :
    """ keygroup can be 'pat' or 'med' """
    RANK_THRESHOLD = 2
    # nodes
    keygroup_nodes = set()
    nodes = []
    source = {}
    n_id = 0
    target = {}
    # links
    links = []
    for key_node in data.keys() :
        if not data[key_node] : continue
        # add node
        if key_node not in source :
            source[key_node] = n_id
            nodes.append({"name":key_node, "group":"1"})
            n_id += 1
        source_id = source[key_node]     
        for relation in data[key_node] :
            if relation["score"] > RANK_THRESHOLD : break
            cand = relation["name"]
            if cand not in target :
                target[cand] = n_id
                nodes.append({"name":cand, "group":"2"})
                n_id += 1
            target_id = target[cand]
            # Build edge
            my_link = {"source":source_id,
                       "target":target_id,
                       "value":( (1/relation["score"]) * 100)
                       }
            links.append(my_link)
    graph = {}
    graph["nodes"] = nodes
    graph["links"] = links
    save_as_json(graph, output)
    return graph

def writeJsonGraph(data, output='graph.json') :
    """ keygroup can be 'pat' or 'med' """
    # nodes
    keygroup_nodes = set()
    nodes = []
    source = {}
    n_id = 0
    target = {}
    # links
    links = []
    for key_node in data.keys() :
        if not data[key_node] : continue
        # add node
        if key_node not in source :
            source[key_node] = n_id
            nodes.append({"name":key_node, "group":"1"})
            n_id += 1
        source_id = source[key_node]     
        for relation in data[key_node][0:1] :
            cand = relation["name"]
            if cand not in target :
                target[cand] = n_id
                nodes.append({"name":cand, "group":"2"})
                n_id += 1
            target_id = target[cand]
            # Build edge
            my_link = {"source":source_id,
                       "target":target_id,
                       "value":(relation["score"]*100)
                       }
            links.append(my_link)
    graph = {}
    graph["nodes"] = nodes
    graph["links"] = links
    save_as_json(graph, output)
    return graph

def yy() :
#if __name__ == "__main__":
    data = read_json('OUTPUT/context-cosinus-none.json')
    #print data
    myGraph = writeJsonGraph(data)
    #print myGraph
    
    
def evaluate_against_gold(data, top=20) :
    tp = 0
    testsetSize = 0
    averageMAP = 0
    averageMAP_recall = 0
    averageMAP_best = 0
    GOLD_FILE_INPUT = 'gold-standard.json'
    testset = read_json(GOLD_FILE_INPUT)
    candidates = {}
    for word in testset :
        wordMAP = 0
        wordMAP_recall = 0
        wordMAP_best = 0
        found = 0
        mistake = False
        if word not in data : continue
        else :
            #print data[word]
            #for x in data[word] : print x
            candidates[word] = [x['name'] for x in data[word]]
            print candidates[word]
        for r in testset[word] :
            if r in TARGET_NETWORK : mistake = True
            if ( len(candidates[word]) > 0 ) and r in [ candidates[word][i] for i in range( min([top, len(candidates[word])]) ) ] :
                #print "===================" + r
                found = found+1
                wordMAP = wordMAP + ( 1.0 / (candidates[word].index(r)+1) )
                wordMAP_best = max(wordMAP_best, ( 1.0 / (candidates[word].index(r)+1) ))
        print my_str(word) + "\t"+ str(wordMAP_best)
        if found > 0 :
            wordMAP = float(wordMAP) / len(testset[word])
            wordMAP_recall = float(wordMAP) / found
            #wordMAP_best = wordMAP_best
            tp = tp+1
        #else :
        if mistake :
            testsetSize += 1
            averageMAP = averageMAP + wordMAP
            averageMAP_recall = averageMAP_recall + wordMAP_recall
            averageMAP_best = averageMAP_best + wordMAP_best
        else :
            print str(word) + " couldn't be found"
        #else :
            #print str(word)+" : "
            #print candidates[word]
      
    ###################################################
    # Print results' evaluation
    precision = float(tp) / len(testset)
    realPrecision = float(tp) / testsetSize
    averageMAP = float(averageMAP) / testsetSize
    averageMAP_recall = float(averageMAP_recall) / testsetSize
    averageMAP_best = float(averageMAP_best) / testsetSize
    print "tp = "+str(tp)+" /"+str(testsetSize)
    print "Precision = "+str(precision)
    print "Real precision = "+str(realPrecision)
    print "MAP (classic) = "+str(averageMAP)
    print "MAP (recall) = "+str(averageMAP_recall)
    print "MAP (best) = "+str(averageMAP_best)
    
    

def align(top=20):
    global SOURCE_NETWORK
    global TARGET_NETWORK
    global SOURCE_TRANSFERRED_VECTORS
    global TARGET_TRANSFERRED_VECTORS
    print ">LOADING Pat candidates..."
    SOURCE_NETWORK = read_json(SOURCE_NETWORK_FILE_INPUT)
    #print SOURCE_NETWORK
    print ">LOADING Med candidates..."
    TARGET_NETWORK = read_json(TARGET_NETWORK_FILE_INPUT)
    #print TARGET_NETWORK

    start_time = time.time()
    
    print ">NORMALIZING ("+NORMALIZATION+") CONTEXT VECTORS..."
    if (NORMALIZATION == TFIDF) :
        normalizeTFIDF(SOURCE_NETWORK)
        normalizeTFIDF(TARGET_NETWORK)
    elif (NORMALIZATION == PMI) :
        normalizePMI(SOURCE_NETWORK)
        normalizePMI(TARGET_NETWORK)    

    PIVOT_WORDS = set()

    # We assume same language
    SOURCE_TRANSFERRED_VECTORS = SOURCE_NETWORK
    TARGET_TRANSFERRED_VECTORS = TARGET_NETWORK
    print ">COMPUTING CANDIDATES RANKING ("+SIMILARITY_FUNCTION+")..."

    # DIRECT
    candidates = {} #Map< String, List<String> >
    unknownSourceWords = set()
    testset = SOURCE_NETWORK.keys()
    data = {}
    for word in testset :
        #print ">> DIRECT Candidates for '"+ word.encode(encoding='UTF-8',errors='strict')+"'"
        if word not in SOURCE_NETWORK :
            print my_str(word)+" not in source corpus"
            unknownSourceWords.add(word)
            candidates[word] = []
        else :
            #transferedVector = transferedNetwork[word] #getTransferedVector(word)
            #Base
            candidates[word] = findCandidateTranslations(word, SOURCE_TRANSFERRED_VECTORS[word], TARGET_NETWORK, top, SIMILARITY_FUNCTION)
            data[word] = candidates[word][0:top]
        #print word.encode(encoding='UTF-8',errors='strict')
        #print candidates[word][0:max(top_list)]
        #print "========"
        #print "========"
    save_as_json(data, 'align-'+SIMILARITY_FUNCTION+'-'+NORMALIZATION+'.json')
    evaluate_against_gold(data)
    writeJsonGraph(data, 'graph-'+SIMILARITY_FUNCTION+'-'+NORMALIZATION+'.json')
    elapsed_time = time.time() - start_time
    print str(elapsed_time)
    return data

##    # INVERSE
##    print TARGET_TRANSFERRED_VECTORS
##    start_time = time.time()
##    candidates = {} #Map< String, List<String> >
##    #unknownSourceWords = set()
##    testset = TARGET_NETWORK.keys()
##
##    data = {}
##    for word in testset :
##        print ">> INV Candidates for '"+ word.encode(encoding='UTF-8',errors='strict')+"'"
##        if word not in TARGET_NETWORK :
##            print word+" not in source corpus"
##            unknownSourceWords.add(word)
##            candidates[word] = []
##        else :
##            #transferedVector = transferedNetwork[word] #getTransferedVector(word)
##            #Base
##            candidates[word] = findCandidateTranslations(word, TARGET_TRANSFERRED_VECTORS[word], SOURCE_NETWORK, 2*max(top_list), SIMILARITY_FUNCTION)
##            data[word] = candidates[word][0:(2*max(top_list))]
##    save_as_json(data, 'inv-align-'+SIMILARITY_FUNCTION+'-'+NORMALIZATION+'.json')
##    writeJsonGraph(data, 'inv-graph-'+SIMILARITY_FUNCTION+'-'+NORMALIZATION+'.json')
##        #print word.encode(encoding='UTF-8',errors='strict')
##        #print candidates[word][0:max(top_list)]
##        #print "========"
##        #print "========"

##    # CHIAO
##    #print TARGET_TRANSFERRED_VECTORS
##    candidates = {}
##    testset = SOURCE_NETWORK.keys()
##
##    data = {}
##    for word in testset :
##        #print ">> CHIAO Candidates for '"+ word.encode(encoding='UTF-8',errors='strict')+"'"
##        if word not in SOURCE_NETWORK :
##            print word+" not in source corpus"
##            unknownSourceWords.add(word)
##            candidates[word] = []
##        else :
##            #transferedVector = transferedNetwork[word] #getTransferedVector(word)
##            #Base
##            candidates[word] = findCandidateTranslationsChiao(word, SOURCE_TRANSFERRED_VECTORS[word], TARGET_NETWORK, max(top_list)*2, SIMILARITY_FUNCTION)
##            data[word] = candidates[word][0:max(top_list)]
##        #print word.encode(encoding='UTF-8',errors='strict')
##        #print candidates[word][0:max(top_list)]
##        #print "========"
##        #print "========"
##    save_as_json(data, 'chiao-align-'+SIMILARITY_FUNCTION+'-'+NORMALIZATION+'.json')
##    evaluate_against_gold(data)
##    writeJsonGraphChiao(data, 'chiao-graph-'+SIMILARITY_FUNCTION+'-'+NORMALIZATION+'.json')
##    elapsed_time = time.time() - start_time
##    print str(elapsed_time)

def testGoldStandard():
    global NORMALIZATION
    global SIMILARITY_FUNCTION
    for n_choice in [NONE, TFIDF, PMI] :
        if n_choice == NONE : sim_choices = [measure.L1NORM, measure.COSINE, measure.JACCARD, measure.JACCARD_SET]
        else : sim_choices = [measure.L1NORM, measure.COSINE, measure.JACCARD]
        NORMALIZATION=n_choice
        for sim_choice in sim_choices :
            SIMILARITY_FUNCTION=sim_choice
            align()

def printEvalSheet(sim_choice=measure.COSINE, n_choice=PMI, outputFile="eval.csv", directory="OUTPUT"):
    global NORMALIZATION
    global SIMILARITY_FUNCTION
    NORMALIZATION=n_choice
    SIMILARITY_FUNCTION=sim_choice
    data = align()
    with codecs.open(os.path.join(directory, outputFile), 'w', encoding='utf-8') as fOut:
        fOut.write('PATIENT;MEDECIN;ALTERNATIVE;RELATED;PARADIGMATIC;SYNTAGMATIC\n')
        for pat in data :
            for item in data[pat][0:10]: 
                fOut.write(pat+';'+item['name']+';;;;\n')
    with codecs.open(os.path.join(directory, 'candidates.csv'), 'w', encoding='utf-8') as fOut:
        fOut.write('PATIENT;CHV\n')
        for pat in data :
            fOut.write(pat+';\n')

if __name__ == "__main__":
    #printEvalSheet()
    testGoldStandard()

