""" Computes the Fleiss' Kappa value as described in (Fleiss, 1971) """

DEBUG = True

def computeKappa(mat):
    """ Computes the Kappa value
        @param n Number of rating per subjects (number of human raters)
        @param mat Matrix[subjects][categories]
        @return The Kappa value """
    n = checkEachLineCount(mat)   # PRE : every line count must be equal to n
    N = len(mat)
    k = len(mat[0])
    
    if DEBUG:
        print n, "raters."
        print N, "subjects."
        print k, "categories."
    
    # Computing p[]
    p = [0.0] * k
    for j in xrange(k):
        p[j] = 0.0
        for i in xrange(N):
            p[j] += mat[i][j]
        p[j] /= N*n
    if DEBUG: print "p =", p
    
    # Computing P[]    
    P = [0.0] * N
    for i in xrange(N):
        P[i] = 0.0
        for j in xrange(k):
            P[i] += mat[i][j] * mat[i][j]
        P[i] = (P[i] - n) / (n * (n - 1))
    if DEBUG: print "P =", P
    
    # Computing Pbar
    Pbar = sum(P) / N
    if DEBUG: print "Pbar =", Pbar
    
    # Computing PbarE
    PbarE = 0.0
    for pj in p:
        PbarE += pj * pj
    if DEBUG: print "PbarE =", PbarE
    
    kappa = (Pbar - PbarE) / (1 - PbarE)
    if DEBUG: print "kappa =", kappa
    
    return kappa

def checkEachLineCount(mat):
    """ Assert that each line has a constant number of ratings
        @param mat The matrix checked
        @return The number of ratings
        @throws AssertionError If lines contain different number of ratings """
    n = sum(mat[0])
    
    assert all(sum(line) == n for line in mat[1:]), "Line count != %d (n value)." % n
    return n

def printKappaAlt(lFiles=['eval_Solene_AL.csv', 'eval_Solene_Lea.csv', 'eval_Solene_Solene.csv']):
    nSubj = 1000
    nCat = 2
    matAlt = [] #Cette liste contiendra ma map en 2D$
    for i in range(nSubj):
        matAlt.append([0] * nCat) #Ajoute nCat colonnes de nCat entiers(int) ayant pour valeurs 0
    for filename in lFiles : 
        with codecs.open(os.path.join(directory, filename), 'r', encoding='utf-8') as fIn:
            lines = fIn.readlines()[2:1001]
            for pairId in range(len(lines)) :
                l = lines[pairId]
                if not l.strip() : continue
                answers = l.strip().split(';')
                if filename == 'eval_Solene_Lea.csv' : 
                    answers = l.strip().split('\t')
                    #print answers
                    #print len(answers)
                    if len(answers) < 4 : answers.extend(['n', 'n'])
                #if len(answers) == 1 : answers = l.strip().split('\t')
                #print answers
                #print '====='
                #pat = pat | set([answers[0]])
                #current = res.get(answers[0], {})
                #rel = current.get('rel', [])
                #alt = current.get('alt', [])
                if answers[2].lower().strip() == 'o' :
                    matAlt[pairId][0] = matAlt[pairId][0] + 1
                    #alt.append(answers[1])
                    #current['alt'] = alt
                else : matAlt[pairId][1] = matAlt[pairId][1] + 1
                #if answers[3].lower().strip() == 'o' :
                    #rel.append(answers[1])
                    #current['rel'] = rel
                #res[answers[0]] = current
    #annot_AL = readEvalFile(lFiles[0])
    #annot_L = readEvalFile(lFiles[1])
    #annot_S = readEvalFile(lFiles[2])
    kappaFleiss.computeKappa(matAlt)
    
if __name__ == "__main__":
    printKappaAlt()
    
def wiki() : 
    """ Example on this Wikipedia article data set """
    
    mat = \
    [
        [0,0,0,0,14],
        [0,2,6,4,2],
        [0,0,3,5,6],
        [0,3,9,2,0],
        [2,2,8,1,1],
        [7,7,0,0,0],
        [3,2,6,3,0],
        [2,5,3,2,2],
        [6,5,2,1,0],
        [0,2,2,3,7]
    ]
    print mat[0][4]
    kappa = computeKappa(mat)
