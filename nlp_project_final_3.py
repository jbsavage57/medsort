#!/usr/bin/env python3.8
# -*- coding: utf-8 -*-


import pandas as pd                               #*************************************
import numpy as np
import contractions
#from pycontractions import Contractions
#cont = Contractions(api_key="glove-twitter-100")
import nltk
import joblib

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
nltk.download('stopwords')
nltk.download('punkt')
import re
from nltk.tokenize import sent_tokenize
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
import string
from sklearn.feature_extraction.text import CountVectorizer #Get count vectorizer
from sklearn.decomposition import NMF                       #model is based on NMF
nltk.download('wordnet')
nltk.download('omw-1.4')

"""Normalization"""

'''   def normalize_corpus(corpus, text_lower_case=True, numeric=False,#*********************************************
                     text_lemmatization=True, text_stemmer=False, text_punct=True,
                     stopword_removal=True, hyphen_space=True, fix_contractions=True):
   
     arguments:
        corpus: list of documents
        text_lower_case, logical: True = make all lower case
        numeric, logical: True = encode various nuermical formats to code words
        text_lemmatization, logical: True = lemmatize text
        text_stemmer, logical: True = stemmerize text
        text_punct, logical: True = remove punctiation
        stopword_removal, logical: True = remove stop words
        hyphen_space, logical: True = replace hyphen with space
        fix_contractions, logical True = expand contractions
      References:
        WordNetLemmatizer (from nltk.stem)
        word_tokenize (from nltk)
        re
        stopwords (from nltk.corpus for this exercise)
        PorterStemmer (from nltk.stem)
      returns: list of text of docs in corpus with:
         carriage returns and new lines replaced with space
         extra whitespace repalced with single space
         processed according to arguments
'''
def normalize_corpus_num(corpus, text_lower_case=True, numeric=False,
                     text_lemmatization=True, text_stemmer=False, text_punct=True,
                     stopword_removal=True, hyphen_space=True, fix_contractions=True):

    lemmatizer = WordNetLemmatizer()
    stop_words = stopwords.words('english')
    normalized_corpus = []
    # normalize each document in the corpus
    i=0
    for doc in corpus:                      # iterate over docs incorpus list
        
        # lowercase the text if True
        i+=1
        #print (doc, i)
        if text_lower_case:
            doc = doc.lower()
        # remove extra newlines
        doc = re.sub(r'[\r|\n|\r\n]+', ' ',doc)
        #address hyphens

        #change numeric to code for num: 'num'
        #print (1, doc)
        if numeric:
          doc = re.sub( r'\d+-\d+\s', ' numdash ', doc)         #indicates likley proceduer, e.g., 3-0 vicryl
          doc = re.sub( r'\d+.\d+\s', ' numdec ', doc)          #indicates likley tes, e.g. includes numbers
          doc = re.sub( r"\d+\.\s", " numl ", doc)              #indicates liekly note, e.g., numbered list

          doc = re.sub( r"\d+\s", " num ", doc)                 #plain number, could be any, e.g., 30 yo'''

        if hyphen_space:
          doc = re.sub(r'-+', ' ', doc)
         # remove punctuation
        #print (2,doc)
        if text_punct:                      # remove punctuation if True
            doc = re.sub(r'[^a-zA-Z0-9\s]', ' ', doc, re.I|re.A) 
            #tokens = word_tokenize(doc)
            #print (tokens)
            #tokens = [token.lower() for token in tokens if token.isalpha()]
            #doc = ' '.join(tokens)
        #print (3,doc)
        # remove contractions
        if fix_contractions:
          word_list =word_tokenize(doc)
          #doc = ' '.join(cont.expand_texts(word_list))
          doc = ' '.join([contractions.fix(w) for w in word_list])
        # lemmatize text
        if text_lemmatization:              # lemmatize if True
            word_list = word_tokenize(doc)
            doc = ' '.join([lemmatizer.lemmatize(w) for w in word_list])       
        # remove extra whitespace
        doc = re.sub(' +', ' ', doc)
        # remove stopwords if True
        if stopword_removal:
            tokens = word_tokenize(doc)
            tokens = [token.strip() for token in tokens]
            filtered_tokens = [token for token in tokens if token.lower() not in stop_words]
            doc = ' '.join(filtered_tokens)
        # stemmeraize if True 
        if text_stemmer:
            ps = nltk.porter.PorterStemmer()
            doc = ' '.join([ps.stem(word) for word in doc.split()])
        #word_list =word_tokenize(doc)
        #if len(word_list) >30:
        normalized_corpus.append(doc)     #append normalized text to corpus list
    return normalized_corpus

"""# 3. Feature extraction

define vectorizer
vectorizer hyperparamters were optimized in separate code

# 4. Main functionality

Define Model
Hyperparamaters were optimized inseparate code, regularization was add because the model was prone to mild overfitting

Load Model
"""

#vectorizer = joblib.load("vectorizer.jbl")
#nmf = joblib.load("nmf.jbl")

"""Evaluate Model

During validation will match topics to labels (dcouemnt type)
"""

maxind_fixed=pd.DataFrame(data=np.array([1,2,0]), index=['Topic 1', 'Topic 2', 'Topic 3']).squeeze()
num_label_list = [0,1,2]                                      #list of manually added label types
text_label_list = ['test', 'procedure', 'note']                #list of descriptive label types
label_dict = dict(zip(num_label_list, text_label_list))

"""Convert normalized data"""

'''def convert(model, vectorizer, data_norm, maxValueIndex, label_dict=label_dict, n_topics=3, Print=False):
   
     arguments:
        model: trained model that transforms vectorized data
        vectorizer: vectorizer acting on norm_data
        norm_data: list of normalized data to be vectorized and transformed
        maxValueIndex: translation index for topics to labels
        n_topics: number of topics to be grouped
        label_dict = dictionary of nuemric lables to test labels
        Print: logical: True = print debugging lines
      References:
        pandas as pd
      returns: dataframe with column of predicted labels 'pred_labels and column of normalized data 'normalized_data'
         '''
def convert(model, vectorizer, data_norm, maxValueIndex, label_dict=label_dict, n_topics=3, Print=False):
  print ("convert1")
  topic_labels = ['Topic {}'.format(i) for i in range(1, n_topics+1)]
  if Print: print (data_norm[:5])
  data_dtm = vectorizer.transform(data_norm) #train on train docs articles
  if Print: print (data_dtm)
  doc_topics = model.transform(data_dtm)
  if Print: print (doc_topics)
  data_result = pd.DataFrame(data=doc_topics, columns=topic_labels)
  if Print: print (data_result)
  data_result['pred_label'] = np.argmax(data_result[list(maxValueIndex.sort_values().index.values)].to_numpy(), axis=1)  #sort columns in order of topic
  data_result['pred_label'] = data_result['pred_label'].map(label_dict)
  if Print: print (data_result)
  data_result['normalized_data']=data_norm
  if Print: print (data_result)
  print ("convert2")
  return data_result[['pred_label', 'normalized_data']]

"""Convert raw data

"""

'''def convert_raw(raw_data):
   
     arguments:
        raw_data: text, intended to be medical transciption to be classified as test result, preocedure note, or note
      References:
        normalize_corpus_num
        convert
      returns: dataframe with column of predicted labels 'pred_labels and column of raw data 'raw_data'
         '''
def convert_raw(raw_data, nmf, vectorizer, maxind_fixed):
  print ("convert_raw1")
  norm_data = normalize_corpus_num(raw_data, text_lower_case=True, numeric=True,
                     text_lemmatization=True, text_stemmer=False, text_punct=True,
                     stopword_removal=True)
#  raw_df = pd.DataFrame([convert(nmf, vectorizer,norm_data, maxind_fixed, n_topics=3, Print=False)['pred_label'],raw_data]).T
  label = convert(nmf, vectorizer,norm_data, maxind_fixed, n_topics=3, Print=False)
  print ("convert_raw2") 
  return label
#  return raw_df

#mt_dataset = pd.read_csv('/content/drive/MyDrive/NLP/NLP_Project/mtsamples.csv')    #load file

#for i in range (10):
#  print (raw_test[i])
#convert_raw(raw_test)