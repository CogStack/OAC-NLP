#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Jun 18 14:17:36 2019

@author: danielbean
"""

# demo the annotator class
import os
import pandas as pd
from DrugNLP import OACAnnotator

annr = OACAnnotator()

#this has to be tuned to your docs
#its the number of characters expected when a drug list is present but empty
annr.empty_list_size = 70 

doc_list = os.listdir('./demo/docs')
doc_list = [x for x in doc_list if x.endswith('.txt')]

all_results = {}
rows = []
for doc_fname in doc_list:
    fname = './demo/docs/%s' % doc_fname
    print "###########################"
    print doc_fname
    with open(fname,'r') as doc_input:
        doc = doc_input.read()
        #doc = doc.encode('utf8')
        result = annr.annotate(doc)
        result['status']['doc'] = int(doc_fname[:-4])
        rows.append(result['status'])
        all_results[doc_fname] = result

#create dataframe of results
df = pd.DataFrame(rows)
df = df.set_index('doc').sort_index()

#load expected annotations and reformat
expected = pd.read_csv('./demo/expected.csv')
del expected['notes']
expected.set_index('doc', inplace=True)

expected = expected.fillna(0).astype(bool)
expected = expected[df.columns]

#compare results to expected
correct = expected == df

print ""
print "All documents annotated as expected:"
print correct.all()


# check specific details

# prasugrel not detected in doc 3 because drug list found and only mentioned
# in body
assert all_results['3.txt']['pt_data']['prasugrel']['mentioned'] == False


# use fallback for doc 4
assert all_results['4.txt']['pt_data']['source'] == "NOT FOUND"

# in doc 5 warfarin is switched to rivaroxaban
assert all_results['5.txt']['pt_data']['warfarin']['mentioned'] == True
assert all_results['5.txt']['pt_data']['warfarin']['negated'] == True
assert all_results['5.txt']['pt_data']['rivaroxaban']['mentioned'] == True
