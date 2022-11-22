#!/usr/bin/env python3.9.15 
import csv
import json
from collections import OrderedDict
from pathlib import Path
#import gcsfs
#from gcsfs import GCSFS


import joblib
import nltk
import numpy as np
import pandas as pd  # *************************************
from flask import Flask, render_template, request
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

nltk.download('stopwords')
nltk.download('punkt')
import re
import string

from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize
from sklearn.decomposition import NMF  # model is based on NMF
from sklearn.feature_extraction.text import \
    CountVectorizer  # Get count vectorizer

nltk.download('wordnet')
nltk.download('omw-1.4')
import nlp_project_final_3
from nlp_project_final_3 import convert, convert_raw, normalize_corpus_num

#class App:
app = Flask(__name__)
vectorizer = joblib.load("vectorizer.jbl")
nmf = joblib.load("nmf.jbl")
maxind_fixed=pd.DataFrame(data=np.array([1,2,0]), index=['Topic 1', 'Topic 2', 'Topic 3']).squeeze()
print ('maxind_fixed', maxind_fixed)
num_label_list = [0,1,2]                                      #list of manually added label types
text_label_list = ['test', 'procedure', 'note']                #list of descriptive label types
label_dict = dict(zip(num_label_list, text_label_list))



#print ('label+dict', label_dict)
#def load_joblib(fs, bucket_name, file_name):
#    with fs.open(f'{bucket_name}/{file_name}') as f:
#        return joblib.load(f)
#fs = gcsfs.GCSFileSystem(project='dsc590nlp-project')
#bucket_name = "dsc590nlp-project.appspot.com"
#print (fs.ls(bucket_name))
#vectorizer = load_joblib(fs, bucket_name, "vectorizer.jbl")
#nmf = load_joblib(fs, bucket_name, "nmf.jbl")
# def sort_docs(doc_dict): returns OrderedDict() of doc_dict in orderof tests, procedures, notes
def sort_docs(doc_dict):
    doc_ordered = OrderedDict()
    for key in doc_dict.keys():
        
        doc_list = list(doc_dict[key])
        if doc_list[0] == 'test':
            doc_ordered[key]=doc_dict[key]
    for key in doc_dict.keys():
        doc_list = list(doc_dict[key])
        if doc_list[0] == 'procedure':
            doc_ordered[key]=doc_dict[key] 
    for key in doc_dict.keys():
        doc_list = list(doc_dict[key])
        if doc_list[0] == 'note':
            doc_ordered[key]=doc_dict[key]
    return doc_ordered

@app.route('/')
def homepage():
    return render_template("main.html");
state=0
print ('state=', state)

@app.route("/get")
def get_bot_response():
    global state
    global doc_dict
    global file_of_docs
    global file_count, list_of_files
    userText = request.args.get('msg')
    if state == 1:
        file_of_docs = userText
        state = 2
        doc_dict={}
        if Path(file_of_docs).is_file():
            docs = open(file_of_docs,'r')
            print ("error1")
            try:
                doc_dict=json.load(docs)
                print ("error2")
                docs.close
                key_string=""
                for key in doc_dict.keys():
                    key_string+=key+"<br>"
                return str("File exists and name store documents is:" 
                    +file_of_docs+" state="+str(state)+" and contains: "
                        +"<br>"+key_string) 
            except ValueError:
                return str("File exists but contains no files")
        else:
            
            doc_dict={}
            docs = open(file_of_docs, 'w')
            json.dump(doc_dict, docs, indent="")
            docs.close()
            return str("File name of file to store documents:"+file_of_docs+" state="+str(state))   
    elif state == 3:
        doc = userText
        state = 2
        if Path(doc).is_file():     
            text_file = open(doc, "r")
            text = text_file.read()
            text_file.close
            docs = open(file_of_docs,'r')
            try:
                doc_dict=json.load(docs)
                
            except ValueError:
                doc_dict={}
            doc_dict[doc]=text
            docs = open(file_of_docs, 'w')
            json.dump(doc_dict, docs, indent="")
            docs.close()
            return str('Added '+doc+'<br>'+"text:"+"<br>"+text+ "state="+str(state))
        else:
            return str(doc+' not found')
    elif state == 4:
        docs_file = userText
        state = 2
        docs = open(file_of_docs,'r')
        doc_dict=json.load(docs)

        nonfile_list =[]
        file_list=[]
        if Path(docs_file).is_file():
            f = open(docs_file, 'r')
            files_list = f.read()
            files_list= files_list.split(',')
            for doc in files_list:
                doc=doc.strip()
                print (doc)
                if Path(doc).is_file():
                    file_list.append(doc)      
                    text_file = open(doc, "r")
                    text = text_file.read()
                    text_file.close
                    doc_dict[doc]=text
                   
                else:
                    
                    nonfile_list.append(doc)
            docs = open(file_of_docs, 'w')
            json.dump(doc_dict, docs, indent="")
            docs.close()
            return str("Files added: "+" ".join(file_list)+
                "Files not found: " +" ".join(nonfile_list)+" state="+str(state)) 
        else:                        
             return str(docs_file+' not found') 
    elif state == 5:
        state=2
        return str("The file holding your documents, "+str(Path(file_of_docs).absolute())+" has been closed."+" state="+str(state))
    elif state == 6:
        state=2
        if userText == 'label':
            docs = open(file_of_docs,'r')
            doc_dict=json.load(docs)
            docs.close()
            list_of_files = list(doc_dict.keys())
            key_string = "file         label    initial text"+"<br>"
            for key in doc_dict.keys():
                if isinstance(doc_dict[key], list):
                    pass
                    
                else:
                    pd_pred_raw = convert_raw([doc_dict[key]], nmf, vectorizer, maxind_fixed)
                    label = pd_pred_raw['pred_label'][0]
                    #print ("label=", label, 'type:', type(label))
                    doc_dict[key] = [label, doc_dict[key]]
            if len(list_of_files) > 0:
                doc_ordered = sort_docs(doc_dict)
                key_string = "file         label    initial text"+"<br>"
                for key in doc_ordered.keys():
                    key_string+=key+"  "+doc_dict[key][0]+"  "+ doc_dict[key][1][:60]+"<br>"
            docs = open(file_of_docs,'w')   
            json.dump(doc_ordered, docs, indent="")
            docs.close()    
            return str("Files with type and initial text" +"<br>"
                    +key_string)
            
        else:
            return str("Labeling of files was aborted, no files were labeled")
    elif state == 7 or state == 8:
        
        if state == 7:
            if userText == 'review':
                state = 8
                docs = open(file_of_docs,'r')
                doc_ordered = json.load(docs, object_pairs_hook=OrderedDict)
                docs.close()
                list_of_files = list(doc_ordered.keys())
                file_count = 0
        else:
            data_list = list(doc_dict[list_of_files[file_count]])
            data_list.append(userText)
            doc_dict[list_of_files[file_count]] = data_list
            
            file_count+=1
        if file_count>= len(list_of_files):
            state=2
            docs = open(file_of_docs,'w')
            doc_dict=json.dump(docs)
            docs.close()
               
            return str('No more files to review')

        key = list_of_files[file_count]    
        key_string = "File: "+ key + "Document type: "+doc_dict[key][0]+" Document:"+"<br>"
        return str(key_string+doc_dict[key][1]+"<br>"+"Enter notes")


    else:
        if userText == '1':
            state=1
            return str("Enter file name of file to store documents(.json)"+" state="+str(state))   
        if userText == '2':
            state=3
            return str("Enter file name of the document"+" state="+str(state))  
        if userText == '3':
            state=4
            return str("Enter csv file of documents(.csv)"+" state="+str(state))
        if userText == '4':
            state=5
            return str("The file of documents will be closed it can be reopened to add documents<br>"+
                "or it can be opened to sort and analyzed douments. It will be saved as:<br>"+
                file_of_docs+" in path: " +str(Path(file_of_docs).absolute())+" state="+str(state)+"<br>"
                +"Type <close> to close file, any other entry will abort closing file")
        if userText == '5':
            state=6
            return str("The documents in file of documents will be labelled with Note, test, or procedure.<br>"+
                "The file, label, and initial text will be displayed.<br>"+
                file_of_docs+" in path: " +str(Path(file_of_docs).absolute())+" state="+str(state)+"<br>"
                +"Type label to label files, any other entry will abort labelling transcripts")
        if userText == '6':
            state=7
            doc = 0
            return str("You can review each document in the file of documents and add a note"+"<br>"+
                "Type review to review files, any other entry will abort reviewing transcripts")
        else:
            state=2
            #chat = Chat_T()
            #return str(chat.chat(userText))+" state="+str(state)
            return str(userText+" is not a valid selection from above")+" state="+str(state)

if __name__ == "__main__":
    app.run()