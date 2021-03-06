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
from math import sqrt, log, log10, fabs
from collections import Counter
from re import match



JACCARD="JACCARD"
JACCARD_SET="JACCARD_SET"
COSINE="COSINE"
TFIDF="TFIDF"
L1NORM="L1NORM"


def sum_cooc(context_i):
  def add(x,y): return x+y
  return reduce(add, context_i.values(), 0)

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


def arithmeticMean(x, y) :
  if x == float('inf') : return 2*y
  if y == float('inf') : return 2*x
  return float(x+y)/2

def geometricMean(x, y) :
  if x == float('inf') : return 2*y
  if y == float('inf') : return 2*x
  return sqrt(x*y)

def harmonicMean(x, y) :
  if x == float('inf') : return 2*y
  if y == float('inf') : return 2*x
  if (x+y) < 0.00000001 : return 0
  return float(2*x*y) / (x+y)

def jaccard_set_similarity(x, y) :
  x_set = set(x.keys())
  y_set = set(y.keys())
  if (len(x_set)== 0) or (len(x_set) == 0) : return 0 # not similar
  else :
    union = x_set | y_set
    inter = x_set & y_set
  return len(inter) / len(union)

def l1norm_similarity(x, y) :
  x_set = set(x.keys())
  y_set = set(y.keys())
  union = x_set | y_set
  l1norm = 0
  if (len(x_set)== 0) or (len(x_set) == 0) : return 0 # not similar
  else :
    for i in union : 
      l1norm = l1norm + fabs(float(x.get(i, 0) - y.get(i, 0)))
  return 1 - l1norm

def similarity(x, y, choice) :
  """ Cosine similarity : sigma_XiYi/ (sqrt_sigma_Xi2 * sqrt_sigma_Yi2) """
  result = 0
  try :
    if choice == JACCARD_SET :
      result = jaccard_set_similarity(x, y)
    elif choice == L1NORM : 
      result = l1norm_similarity(x, y)
    else : 
      
      Xi = [] # words
      sigma_XiYi = 0

      sigma_Xi2 = 0
      for w in x : 
        x_w = x[w]
        sigma_Xi2 = sigma_Xi2 + x_w *x_w

      sigma_Yi2 = 0
      for w in y : 
        y_w = y[w]
        sigma_Yi2 = sigma_Yi2 + y_w*y_w
        if w in x : sigma_XiYi = sigma_XiYi + x[w]*y_w
      
        if choice == COSINE : result = sigma_XiYi / ( sqrt(sigma_Xi2) * sqrt(sigma_Yi2) )
        if choice == JACCARD : result = sigma_XiYi / ( sigma_Xi2 + sigma_Yi2 - sigma_XiYi ) #CF Chiao et al.
        else : result = 0.5 * ((sigma_XiYi / ( sqrt(sigma_Xi2) * sqrt(sigma_Yi2) )) + (sigma_XiYi / ( sigma_Xi2 + sigma_Yi2 - sigma_XiYi )))
        #print "similarity :"+str(result)
  except ZeroDivisionError :
    #print 'ZeroDivisionError'
    result = -float('inf')
    
  return result

