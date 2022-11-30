#!/usr/bin/env python3.8.10
import os
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
import re
import string
import psycopg2
nltk.download('stopwords')
nltk.download('punkt')

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
app = Flask(__name__)        #, template_folder='templates'
#set to enter data form files

vectorizer = joblib.load("vectorizer.jbl")
nmf = joblib.load("nmf.jbl")
maxind_fixed=pd.DataFrame(data=np.array([1,2,0]), index=['Topic 1', 'Topic 2', 'Topic 3']).squeeze()
#print ('maxind_fixed', maxind_fixed)
num_label_list = [0,1,2]                                      #list of manually added label types
text_label_list = ['test', 'procedure', 'note']                #list of descriptive label types
label_dict = dict(zip(num_label_list, text_label_list))


# global list_of_docs
# global state, File
# global doc_dict, doc_ordered
# global file_of_docs, list_name, list_of_docs
# global file_count# , list_of_files
# global conn_dict
state=-1
print ('state=', state, "test0")
list_of_docs=[]
Local = False
File = False
state = 0
global conn_dict #, local_dict, heroku_dict    
local_dict = {"user":"postgres",
"password":"Mm033062!",
"host":"127.0.0.1",
"port":"5432",
"database":"postgres"}

heroku_dict = {"user":"tdxakwnpoqnwuc",
"password":"bcc66bdba6ede864c3306448b595a5bcfa852941bba973e578518149de8bf76b",
"host":"ec2-3-211-221-185.compute-1.amazonaws.com",
"port":"5432",
"database":"d3n8eqim2b6sc9"}

if Local:
    conn_dict = local_dict
else:
    conn_dict = heroku_dict
#print ('label+dict', label_dict)
#def load_joblib(fs, bucket_name, file_name):
#    with fs.open(f'{bucket_name}/{file_name}') as f:
#        return joblib.load(f)
#fs = gcsfs.GCSFileSystem(project='dsc590nlp-project')
#bucket_name = "dsc590nlp-project.appspot.com"
#print (fs.ls(bucket_name))
#vectorizer = load_joblib(fs, bucket_name, "vectorizer.jbl")
#nmf = load_joblib(fs, bucket_name, "nmf.jbl")
if Local:
    conn_dict = local_dict
else:
    conn_dict = heroku_dict
def get_data_sql(table, index, column, select_column):
    global conn_dict
    try:
        connection = psycopg2.connect(
            user=conn_dict["user"],
            password=conn_dict["password"],
            host=conn_dict["host"],
            port=conn_dict["port"],
            database=conn_dict["database"])
        cursor = connection.cursor()  
        #print("Using Python variable in PostgreSQL select Query")
        postgreSQL_select_Query = "select "+column+" from "+table\
         +" where "+select_column+" = "+ str(index)
        #print (postgreSQL_select_Query)
        cursor.execute(postgreSQL_select_Query)
        data = cursor.fetchall()
        #print ("data", type(data), data, "\n"*2)
        data = data[0][0]
        #print ("testsql",index, type(data), data, "\n"*2)
    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
        data = -1
    finally:
        # closing database connection.
        if connection:
            cursor.close()
            connection.close()
            #print("PostgreSQL connection is closed")
    #print ("testsql",index, type(label), label, "\n"*2)
    return data

def set_data_sql(index, column, data):
    
    try:
        connection = psycopg2.connect(
            user=conn_dict["user"],
            password=conn_dict["password"],
            host=conn_dict["host"],
            port=conn_dict["port"],
            database=conn_dict["database"])
        cursor = connection.cursor()
        
        #print("Using Python variable in PostgreSQL select Query")
        postgreSQL_select_Query = "UPDATE mts SET "+column+" = " + "'"+data+"'" + " WHERE index = " + str(index)
        #print (postgreSQL_select_Query)
        cursor.execute(postgreSQL_select_Query)
        connection.commit()
        postgreSQL_select_Query = "SELECT "+column+" FROM mts WHERE index = " + str(index)
        cursor.execute(postgreSQL_select_Query)
        #print (postgreSQL_select_Query)
        data = cursor.fetchall()
        #print ("query label", label)
        data = data[0][0]
        #print ("last label", label)
    except (Exception, psycopg2.Error) as error:
        print("Error while fetching data from PostgreSQL", error)
        data = -1
    finally:
        # closing database connection.
        if connection:
            cursor.close()
            connection.close()
            #print("PostgreSQL connection is closed")
    return data
def get_note_sql(index):
    column = "note"
    select_column = "index"
    index = index
    table = "mts"
    return get_data_sql(table, index, column, select_column)


#def get_label_sql(index): return label from postgresql
def get_label_sql(index):
    column = "type"
    select_column = "index"
    index = index
    table = "mts"
    return get_data_sql(table, index, column, select_column)

# get_index(filename): retruns index in postgresql corresponding to transcription
def get_index(filename):
    index = filename[-4:]
    index = re.sub("[a-zA-Z]","", index)
    pattern = r'[' + string.punctuation + ']'
    index = int(re.sub(pattern,"", index))
    return index

#def add_type_sql(filename, label): adds type to type column in postgreql
def add_type_sql(index, label):
    column = "type"
    return set_data_sql(index, column, label)

# ef add_note_sql(filename, note): adds note to transcription in postgres
def add_note_sql(index, note):
    column = "note"
    return set_data_sql(index, column, note)    
 
#    def transcript_from_sql(index): returns transcript from postgresql table mts at index
def transcript_from_sql(index):
    column = "transcription"
    select_column = "index"
    index = index
    table = "mts"
    return get_data_sql(table, index, column, select_column)

# returns transcript form file named filename, from postgres table mts row with index if filename as transcript N, where N is 0-4999
def get_transcript(filename, file=True):
    doc=filename
    if File:
        if Path(doc).is_file():     
            text_file = open(doc, "r")
            text = text_file.read()
            text_file.close
        else:
            text=-1     #-1 indicates no text/file
        return text

    else:
        index = get_index(doc)
        print (doc, index)
        text = transcript_from_sql(index)
        return text

# def sort_list(doc_list): returns sorted list of doc names in orderof tests, procedures, notes
def sort_list(doc_list):
    list_ordered = []
    for doc in doc_list:
        index = get_index(doc)
        label = get_label_sql(index)
        if label == 'test':
            list_ordered.append(doc)
    for doc in doc_list:
        index = get_index(doc)
        label = get_label_sql(index)
        if label == 'procedure':
            list_ordered.append(doc)
    for doc in doc_list:
        index = get_index(doc)
        label = get_label_sql(index)
        if label == 'note':
            list_ordered.append(doc)
    return list_ordered

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

@app.route("/")
def homepage():
    return render_template("main.html");

File = False
state = 0


@app.route("/get" )
def get_bot_response():
    userText = request.args.get('msg')
    global doc_dict, doc_ordered
    global file_of_docs, list_name, list_of_docs
    global file_count# , list_of_files
    global  File, state
    # Local = True
    # local_dict = {"user":"postgres",
    # "password":"Mm033062!",
    # "host":"127.0.0.1",
    # "port":"5432",
    # "database":"postgres"}

    # heroku_dict = {"user":"tdxakwnpoqnwuc",
    # "password":"bcc66bdba6ede864c3306448b595a5bcfa852941bba973e578518149de8bf76b",
    # "host":"ec2-3-211-221-185.compute-1.amazonaws.com",
    # "port":"5432",
    # "database":"d3n8eqim2b6sc9"}
    # global local_dict, heroku_dict
    # if Local:
    #     conn_dict = local_dict
    # else:
    #     conn_dict = heroku_dict

    
    print ('state1=', state, "userText=", userText)
    if state == 1:      #enter storage name for doc names
        state = 2
        if File:        #will work with file system
            file_of_docs = userText
            doc_dict={}
            if Path(file_of_docs).is_file():
                docs = open(file_of_docs,'r')
                #print ("error1")
                try:
                    doc_dict=json.load(docs)
                    #print ("error2")
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
                return str("File name of file to store documents:"+file_of_docs)   
        else:  #will work with postgresql
            list_name = userText
            try:
                if len(list_of_docs) == 0:
                    globals()[list_name] = list_of_docs
                    return str("List "+list_name+" exists but contains no transcripts"
                    +"<br>"+"Enter item from menu above")   
                key_string = ""
                for key in list_of_docs:
                        key_string+=key+"<br>"
                globals()[list_name] = list_of_docs
                return str("List exists and is named:" 
                    +list_name+" and contains transcripts: "
                        +"<br>"+key_string) 
            except NameError:
                list_of_docs = []
                globals()[list_name] = list_of_docs
                return str("File list to save transcript names: "+list_name
                    +"<br>"+"Enter item from menu above")
    elif state == 3:       #enter single file name save doc
        filename = userText
        filename = filename.strip()
        state = 2
        text = get_transcript(filename, file=File)
        if text == -1:
            return str(filename + ' not found')
        if File:    # save text if file, otherwise testin postgresql table
            try:
                docs = open(file_of_docs,'r')
            except FileNotFoundError:
                return str("No file to store transcripts found, return to step 1"
                    +"<br>"+"Enter item from menu above")
            try:
                doc_dict=json.load(docs)    
            except ValueError:
                doc_dict={}
            doc_dict[filename]=text
            docs = open(file_of_docs, 'w')
            json.dump(doc_dict, docs, indent="")
            docs.close()
        else:
            list_of_docs.append(filename) 
        return str('Added '+filename+'<br>'+"text:"+"<br>"+text
            +"<br>"+"Enter item from menu above")
    
    
    elif state == 4: #enter list of files
        print ("entered list of files")
        docs_file = userText
        state = 2
        nonfile_list =[]
        file_list=[]
        if File:
            f = open(docs_file, 'r')
            files_list = f.read()
            files_list= files_list.split(',')
            f.close()
            docs = open(file_of_docs,'r')
            doc_dict=json.load(docs)
           
            if Path(docs_file).is_file():
                f = open(docs_file, 'r')
                files_list = f.read()
                files_list= files_list.split(',')
                for doc in files_list:
                    doc=doc.strip()
                    #print (doc)
                    text = get_transcript(doc, file=File)
                    if text ==-1:
                        nonfile_list.append(doc)
                    else:
                        file_list.append(doc)
                        doc_dict[doc]=text        
                docs = open(file_of_docs, 'w')
                json.dump(doc_dict, docs, indent="")
                docs.close()
                #return str("Files added: "+" ".join(file_list)+
                #    "Files not found: " +" ".join(nonfile_list)) 
            else:                        
                return str(docs_file+' not found'
                    +"<br>"+"Enter item from menu above")
        else:
            table = "tran_list"
            column = "t_list"
            select_column = "list_name"
            index = "'transcription_list'"
            files_list = get_data_sql(table, index, column, select_column)
            print ("files list=", files_list)
            if files_list == -1: 
                return str("Files list could not be read"
                 +"<br>"+"Enter item from menu above")    
            files_list= files_list.split(',')

            for doc in files_list:
                doc=doc.strip()
                #print ("doc: ", doc, "files list=", files_list)
                text = get_transcript(doc, file=File)
                if text ==-1:
                    nonfile_list.append(doc)
                else:
                    file_list.append(doc)
                    list_of_docs.append(doc)  
        return str("Files added: "+" ".join(file_list)+"<br>"
                    "Files not found: " +" ".join(nonfile_list)+"<br>"\
                    +"Enter item from menu above")                   
            
    elif state == 5:
        state=2
        if File:
            return str("The file holding your documents, "+str(Path(file_of_docs).absolute())+" has been closed."
                +"<br>"+"Enter item from menu above")
        else:
            return str("The list of transcripts, "+list_name+" has been closed."
                +"<br>"+"Enter item from menu above")
    elif state == 6:
        print ("File=", File)
        state=2
        if userText == 'label':
            if File:
                docs = open(file_of_docs,'r')
                doc_dict=json.load(docs)
                docs.close()
                list_of_files = list(doc_dict.keys())
            else:
                list_of_files = list_of_docs
            key_string = "file         label    initial text"+"<br>"
            maxlen_key=0
            #print ("len(list_of_files)", len(list_of_files))
            for key in list_of_files:
                if len(key) > maxlen_key: maxlen_key = len(key)
                if File:
                    if isinstance(doc_dict[key], list):
                        pass                        
                    else:
                        pd_pred_raw = convert_raw([doc_dict[key]], nmf, vectorizer, maxind_fixed)
                        label = pd_pred_raw['pred_label'][0]
                        #print ("label=", label, 'type:', type(label))
                        doc_dict[key] = [label, doc_dict[key]]
                else:
                    filename = key
                    text = get_transcript(filename, File)
                    pd_pred_raw = convert_raw([text], nmf, vectorizer, maxind_fixed)
                    label = pd_pred_raw['pred_label'][0]
                    print ("label=", label, 'type:', type(label),text[:40])
                    index=get_index(filename)
                    label1 = add_type_sql(index, label)
                    print ("index=", index,"type =",label1,"label=",label )
                
            if len(list_of_files) > 0:
                space = maxlen_key - 4
                key_string = "file "+"&nbsp"*space+" label "+"&nbsp"*3+" initial text"+"<br>"
                if File:
                    doc_ordered = sort_docs(doc_dict)
                    for key in doc_ordered.keys():
                        space=maxlen_key+2-len(key)
                        space2=10-len(doc_dict[key][0])
                        key_string+=key+" "+"&nbsp"*space+doc_dict[key][0]+"&nbsp"*space2+ doc_dict[key][1][:60]+"<br>"
                    docs = open(file_of_docs,'w')   
                    json.dump(doc_ordered, docs, indent="")
                    docs.close()
                else:
                    list_of_docs = sort_list(list_of_files)
                    for key in list_of_docs:
                        filename = key
                        index=get_index(filename)
                        label = get_label_sql(index)
                        text = get_transcript(filename, File)
                        space=maxlen_key+1-len(key)
                        space2=10-len(label)
                        key_string+=key+" "+"&nbsp"*space+label+"&nbsp"*space2+ text[:60]+"<br>"
                        print ("filename:",filename,"index:",index,"label:",label,"\n")
                        #print ("test: ", text)
                    
            
                return str("Files with type and initial text" +"<br>"
                    +key_string+"<br>"
                    +"Enter item from menu above") 
            else:   
                return str("Labeling of files was aborted, no list of files to label found"
                    +"<br>"+"Enter item from menu above")
            
        else:
            return str("Labeling of files was aborted, no files were labeled"
                +"<br>"+"Enter item from menu above")
    elif state == 7 or state == 8:
        print ("File=", File)
        if state == 7:
            if userText == 'review':
                state = 8
                file_count = 0
                if File:
                    docs = open(file_of_docs,'r')
                    doc_ordered = json.load(docs, object_pairs_hook=OrderedDict)
                    docs.close()
                    list_of_docs = list(doc_ordered.keys())
                #print (file_count, len(list_of_files), 1)
                #print (doc_ordered)
            else:
                state = 2
                return str("Review aborted"
                    +"<br>"+"Enter item from menu above")
        else:
            note = userText
            if File:
                data_list = list(doc_ordered[list_of_files[file_count]])
                data_list.append(note)
            else:
                filename = list_of_docs[file_count]
                index = get_index(filename)
                note = add_note_sql(index, note)
                #print ("index=",index,"note=",note)       
            file_count+=1
            #print (file_count, len(list_of_files), 3)
            if file_count>= len(list_of_docs):
                state=2
                if File:
                    docs = open(file_of_docs,'w')
                    json.dump(doc_ordered, docs, indent="")
                    docs.close()
                
                return str('No more files to review'
                    +"<br>"+"Enter item from menu above")
        key = list_of_docs[file_count]
        if File:
            label = doc_dict[key][0]
            text = doc_dict[key][1]
        else:
            #print ("key=", key, "list_of_files: ", list_of_files, "file_count=",file_count )
            index = get_index(key)
            label = get_label_sql(index)
            text =  get_transcript(key, file=File)   
        key_string = "File: "+ key + "  Document type: "+label+" Document: "+"<br>"
        return str(key_string+text+"<br>"+"Enter notes")

    elif state == 9:
        if userText == 'q':
            list_of_docs = []
            return str("work list is cleared, you may restart or leave"+"<br>"\
                +"Choose item from menu above or exit site")
        else:
            state =2
            return str("Continue, enter item from menu above")


    else:
        if userText == '1':
            state=1
            print ('state2=', state, "userText=", userText)
            if File:
                return str("Enter file name of file to store documents(.json)")   
            else:
                return str("Enter name of list to store transcription names")
        if userText == '2':
            state=3
            print ('state2=', state, "userText=", userText)
            return str("Enter file name of the document")  
        if userText == '3':
            state=4
            print ('state2=', state, "userText=", userText)
            return str("Enter csv file of documents(.csv)")
        if userText == '4':
            state=5
            print ('state2=', state, "userText=", userText)
            return str("The file of documents will be closed it can be reopened to add documents<br>"+
                "or it can be opened to sort and analyzed douments. It will be saved as:<br>"+
                file_of_docs+" in path: " +str(Path(file_of_docs).absolute())+"<br>"
                +"Type <close> to close file, any other entry will abort closing file")
        if userText == '5':
            state=6
            print ('state2=', state, "userText=", userText)
            if File:
                return str("The documents in file of documents will be labelled with Note, test, or procedure.<br>"+
                "The file, label, and initial text will be displayed.<br>"+
                "files are in: "+transcripts+" in path: " +str(Path(file_of_docs).absolute())+"<br>"
                +"Type label to label files, any other entry will abort labelling transcripts")
            else:
                return str("The documents in file of documents will be labelled with Note, test, or procedure.<br>"+
                "The file, label, and initial text will be displayed.<br>"+
                "data is in: postgrew table mts"+"<br>"
                +"Type label to label files, any other entry will abort labelling transcripts")
        if userText == '6':
            state=7
            print ('state2=', state, "userText=", userText)
            doc = 0
            return str("You can review each document in the file of documents and add a note"+"<br>"+
                "Type review to review files, any other entry will abort reviewing transcripts")
        if userText == '7':
            state=9
            print ('state2=', state, "userText=", userText)
            if File:
                doc = 0
                docs = open(file_of_docs,'r')
                doc_ordered = json.load(docs, object_pairs_hook=OrderedDict)
                docs.close()
                list_of_files = list(doc_ordered.keys())
            
                file_string = "Your files are as follows:"+"<br>"+ \
                        "file '|' label '|' initial text'"+"&nbsp"*17+ "'|' notation"+"<br>"
                for key in doc_ordered.keys():
                    file_string += key 
                    for item in doc_ordered[key]:
                        file_string += " | " + item[:30]
                    file_string += "<br>" 
                file_string += "Type q to quit; otherwise continue"
            else:
                try:
                    maxlen_key = len(max(list_of_docs, key=len))
                    space=maxlen_key-4
                    file_string = "Your files are as follows:"+"<br>"+ \
                        "file "+"&nbsp"*space+" label "+"&nbsp"*3+" initial text"\
                        +"&nbsp"*36+"notation"+"<br>"
                        #"file '|' label '|' initial text'"+"&nbsp"*17+ "'|' notation"+"<br>"
                except ValueError:
                    print ("list_of_docs: ",list_of_docs)
                    file_string = "File list is empty, please select files if desired"+"<br>"
                for doc in list_of_docs:
                    index = get_index(doc)
                    label = get_label_sql(index)
                    note = get_note_sql(index)
                    text = transcript_from_sql(index)
                    space=maxlen_key+1-len(doc)
                    space2=10-len(label)
                    space3=49-len(text[:45])
                    file_string+=doc+" "+"&nbsp"*space+label+"&nbsp"*space2+ \
                        text[:45]+"&nbsp"*space3+note[:30]+"<br>"
                    #file_string += doc+" | "+label[:10]+" | "+text[:30]+" | "+note[:40]
                    file_string += "<br>" 
                file_string += "Type q to quit and clear list; any other entry will continue"
            return str(file_string)

        else:
            state=2
            print ('state2=', state, "userText=", userText)
            print ('invalid userText=', userText)
            return str(userText+" is not a valid selection from above")


if __name__ == "__main__":
    app.run()
    #port = int(os.environ.get("PORT", 5000)) - suggested port changes from online
    #app.run(host="0.0.0.0", port=port)
    # - original