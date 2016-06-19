# coding: utf8

import urllib2
import json
import os
from pprint import pprint
#from codecs import open
#from io import open
#import io
import codecs
import requests
import time
import nltk
import re

RESULTS_FAMILIER = {}
RESULTS_ALL_FAMILIER = {}

def save_as_json(data, outputFile, directory="OUTPUT") :
    if not os.path.exists(directory):
        os.makedirs(directory)
    with codecs.open(os.path.join(directory, outputFile), 'w', encoding='utf-8') as outfile:
        json.dump(data, outfile, encoding='utf8') #, ensure_ascii=False)

def read_json(inputFile) :
    with codecs.open(inputFile, 'r', encoding='utf-8') as fIn:
        return json.loads(fIn.read(), encoding="utf8") #, ensure_ascii=False)

def getWiktPage(lang, pageTitle, directory="/home/monordi/releases/dkpro-jwktl/src/test/resources/articles-fr/api", write=True) :
    opener = urllib2.build_opener()
    url = "https://"+lang+".wiktionary.org/w/api.php?action=query&titles="+urllib2.quote(pageTitle)+"&prop=revisions&rvprop=content&rvgeneratexml=&format=json"
    #res = json.loads(opener.open(url).read())
    #print url
    res = json.loads(requests.get(url).text, encoding="utf-8")
    #print res
    if "-1" in res['query']['pages'] :
        print "======================-1:<"+pageTitle+"> does not exit"
        return None
    for pageid in res['query']['pages']:
        title = res['query']['pages'][pageid]['title']
        print title
        revs = res['query']['pages'][pageid]['revisions']
        if len(revs) == 1 :
            content = revs[0]['*']
            if write :
                with codecs.open(os.path.join(directory, title+".txt"), 'w',  encoding='utf-8') as fOut:
                    fOut.write(content)
            else:
                return content
        else:
            print "Oups len(revisions) != 1"

def writeWiktPages(lang, termList, directory="/home/monordi/releases/dkpro-jwktl/src/test/resources/articles-fr/api"):
    for term in termList:
        getWiktPage(lang, term, directory)

def getWiktLangContent(lang, wiktPage) :
    #l = re.compile("(?<!^)\s+(?=[A-Z])(?!.\s)").split(wiktPage)
    l = re.compile("(^|\n).*\\{\\{langue\|").split(wiktPage)
    for item in l :
        if item.startswith(lang) :
            print "***"
            #print item
            return item
    #wiktPage.split(
    print len(l)
    
def test(term='addiction', lang='fr', res=RESULTS_FAMILIER) :
    page = getWiktPage(lang, term, write=False)
    if page :
        #print page
        page = getWiktLangContent(lang, page)
        if page :
            lines = page.split('\n')
            for line in lines :
                if '{{familier' in line :
                    print line
                    # TODO Discard translations
                    m = re.search('\\[\\[(?P<abbr>(.+?))\\]\\]', line)
                    if m :
                        # TODO take all links
                        # Remove metadata
                        cand = m.group('abbr')
                        items = cand.split('|')
                        cand = items[len(items)-1]
                        print cand
                        # Save
                        candidates = res.get(term, [])
                        candidates.append(cand)
                        res[term] = candidates
                    #else : print m #None
    #else : print 'Not page'

    
def testAll(term='addiction', lang='fr', res=RESULTS_ALL_FAMILIER, targetList=None) :
    page = getWiktPage(lang, term, write=False)
    if page :
        #print page
        page = getWiktLangContent(lang, page)
        if page :
            lines = page.split('\n')
            for line in lines :
                if '{{familier' in line :
                    print line
                    # TODO Discard translations
                    lm = re.findall('\\[\\[(?P<abbr>(.+?))\\]\\]', line)
                    if lm :
                        for m in lm :
                            # Take all links
                            # Remove metadata
                            cand = m[1]
                            items = cand.split('|')
                            cand = items[len(items)-1]
                            print cand
                            # Save
                            candToSave = cand.lower().strip()
                            candidates = res.get(term, [])
                            if not targetList or (targetList and (candToSave in targetList)) :
                                candidates.append(candToSave)
                                res[term] = candidates
                    #else : print m #None
    #else : print 'Not page'

def initTargetList(filenamePath) :
    targetList = []
    with open(filenamePath, 'r') as fIn :
        for l in fIn:
            term = l.strip()
            if term : targetList.append(term)
    print targetList
    return targetList
            

if __name__ == '__main__' :
    DIR = '.'
    #test('estomac')
    #testAll('chimio')
    #inputFilename = 'inputINCa.csv'
    inputFilename = 'candidatesBioTex.txt'
    #outputFilename = 'familier_top250_PremiersPas.json'
    outputFilename = 'gold-Wiktionary-BioTex250-PremiersPas.json'
    #targetList = None
    targetTerms = initTargetList(os.path.join(DIR, 'inputINCa.csv'))
    
    with open(os.path.join(DIR, inputFilename), 'r') as fIn :
        for l in fIn :
            term = l.strip()
            if not term : continue
            testAll(term, targetList=targetTerms)
    #print RESULTS_FAMILIER
    save_as_json(RESULTS_ALL_FAMILIER, outputFilename, DIR)
