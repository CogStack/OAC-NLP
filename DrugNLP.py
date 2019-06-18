#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 19 16:36:35 2018

@author: danielbean
"""

import regex

class OACAnnotator:
    def __init__(self):
        #used to check size of detectied drug lists
        #these values are specifically tuned to our records
        self.empty_list_size = 550 #this is tuned specifically to our records
        self.multicomp_aid = 300
        
        #build regex
        self.edge_cases = ["DRUGS ON XXXXXXXXX", "XXXXX ON DISCHARGE", "DRUGS XXXXXXXXXXXX", "DRUGS ON X"]
        self.oac = ['apixaban','rivaroxaban','dabigatran','edoxaban','warfarin']
        self.ap = ['aspirin', 'clopidogrel', 'dipyridamole', 'ticagrelor', 'prasugrel']
        self.all_drugs = self.oac + self.ap
        self.positive_regex = {}
        for i in xrange(len(self.all_drugs)):
            dr = self.all_drugs[i]
            term = dr.upper()
            pattern = "(?:"+term+"){s<=1}"
            self.positive_regex[dr] = [regex.compile(pattern)]
            
        self.negative_regex = {}
        for i in xrange(len(self.all_drugs)):
            dr = self.all_drugs[i]
            term = dr.upper()
            pattern = term + r" (?:STOP|WITHH|WAS WITHH|DISCONTINUE|TO BE STOPPED|HAS BEEN STOPPED|WAS STOPPED|CHANGED TO|SWITCHED TO)"
            self.negative_regex[dr] = [regex.compile(pattern)]
            pattern = r"(?:STOP|STOPPED|STOPPED HIS|STOPPED HER|WITHHOLD|WITHHELD|DISCONTINUE|DISCONTINUED|NOT ON|NOT CURRENTLY ON|CONSIDER|CONSIDER RESTARTING) " + term
            self.negative_regex[dr].append(regex.compile(pattern))
            #allergies - considered negation as not a positive mention
            pattern = r"(?:ALELRGIC|ALLERGIC TO|ALLERGIES) " + term
            self.negative_regex[dr].append(regex.compile(pattern))
        
        def find_all(a_str, sub):
            start = 0
            positions = []
            while True:
                start = a_str.find(sub, start)
                if start == -1:
                    return positions
                else:
                    positions.append(start)
                    start += len(sub) # use start += 1 to find overlapping matches
        
        #allow 2 substitutions here for S and D
        self.drugs_on_disch_regex = regex.compile('(?:DRUGS ON DISCHARGE){s<=2}')
        self.discharge_medication_regex = regex.compile('(?:DISCHARGE MEDICATION){s<=2}')
        self.drug_list_end_regex = []
        #self.drug_list_end_regex.append(regex.compile('(?:DRUG LIST COMPLETED){s<=2}'))
        #self.drug_list_end_regex.append(regex.compile('(?:TTA COMPLETED){s<=2}'))
        self.drug_list_end_regex.append(regex.compile('(?:FINAL TTA ASSEMBLY){s<=2}'))
        #expression for a specific negation possible in discharge drug list
        self.drug_stopped_regex = regex.compile('(?:\\. \\. STOP)') 
        
    def annotate(self, doc):
        doc = doc.upper().replace('\r\n','\n')

        section = self.find_druglist(doc)
        doc = section['doc']
        
        #negation detection works better with newlines removed
        doc = doc.replace('\n','')
        doc = doc.replace('\r','')
        
        pt_data = {}
        status = {}
        if section['druglist_ok']:
            pt_data['source'] = section['matched_phrase']
            pt_data['source_matches'] = section['n_matched']
            
            for dr in self.all_drugs:
                pt_data[dr] = {'mentioned':False, 'negated':False, 'status': False}
                for reg in self.positive_regex[dr]:
                    if len(reg.findall(doc)) > 0:
                        pt_data[dr]['mentioned'] = True
                        pt_data[dr]['status'] = True
                        break
                #although rare, drugs can be negated in the discharge meds list
                #only check for negation if mentioned
                if pt_data[dr]['status'] == True:
                    #test standard negation patterns
                    for reg in self.negative_regex[dr]:
                        if len(reg.findall(doc)) > 0:
                            pt_data[dr]['negated'] = True
                            pt_data[dr]['status'] = False
                    #test a specific " . . Stop" pattern
                    drugs_stopped = self.druglist_negation(doc) 
                    if dr in drugs_stopped:
                        pt_data[dr]['negated'] = True
                        pt_data[dr]['status'] = False
                status[dr] = pt_data[dr]['status']
            

        else:
            #no drug list found, check the whole doc for mentions and negations
            print "using fallback method"
            pt_data['source'] = "NOT FOUND"
            pt_data['source_matches'] = 0
            for dr in self.all_drugs:
                pt_data[dr] = {'mentioned':False, 'negated':False, 'status': False}   
                if dr.upper() in doc:
                    pt_data[dr]['mentioned'] = True
                    pt_data[dr]['status'] = True
                    for reg in self.negative_regex[dr]:
                        match_phrase = reg.findall(doc)
                        if len(match_phrase) > 0:
                            pt_data[dr]['negated'] = True
                            pt_data[dr]['status'] = False
                status[dr] = pt_data[dr]['status']
        result = {'pt_data': pt_data, 'status': status}
        return result
    
    def find_druglist(self, doc):
        empty_list_size = self.empty_list_size 
        multicomp_aid = self.multicomp_aid
        druglist_match = self.drugs_on_disch_regex.findall(doc)
        output = {'matched_phrase': None, 'n_matched': 0}
        output['druglist_found'] = False
        drug_start = 0
        
        if len(druglist_match) == 1:
            #find the start index of the druglist
            drug_start = doc.index(druglist_match[0])
            output['druglist_found'] = True
        if len(druglist_match) == 0:
            #try edge cases
            for opt in self.edge_cases:
                if opt in doc:
                    drug_start = doc.index(opt)
                    output['druglist_found'] = True
                    druglist_match = [opt]
                    break
        if len(druglist_match) > 1:
            print "multiple options found, using last"
            matches = self.find_all(doc, druglist_match[0])
            drug_start = matches[-1]
            output['druglist_found'] = True
        
        ##if not found using drugs on discharge, try discharge medication
        if not output['druglist_found']:
            druglist_match = self.discharge_medication_regex.findall(doc)
            if len(druglist_match) == 1:
                #find the start index of the druglist
                drug_start = doc.index(druglist_match[0])
                output['druglist_found'] = True
            if len(druglist_match) > 1:
                #try an exact match with newlines
                all_exact = self.find_all(doc,'DISCHARGE MEDICATION\n')
                if len(all_exact) == 1:
                    drug_start = all_exact[-1]
                    output['druglist_found'] = True
                else:
                    print "multiple discharge medication lists found"
                    print doc
                    #handling this is not implemented because never encountered yet
                    #presumably need to take either first or last match
        doc_cut = doc[drug_start:]
        
        #now find end of drug list
        if output['druglist_found']:
            drug_end = -1
            for pattern in self.drug_list_end_regex:
                end_match = pattern.findall(doc_cut)
                if len(end_match) == 1:
                    drug_end = doc_cut.index(end_match[0])
                    break
                elif len(end_match) > 1:
                    print "more than one END match for doc, using last"
                    print doc_cut
                    drug_end = doc_cut.index(end_match[-1])
            if drug_end == -1:
                print "no END found"
                print doc_cut
            doc_cut = doc_cut[:drug_end]
                
        #check for empty drug list
        list_size = len(doc_cut)
        if "PATIENT USES A MULTI-COMPARTMENT AID" in doc_cut:
            list_size = list_size - multicomp_aid
        if list_size <= empty_list_size:
            output['doc'] = doc
            print "Empty drug list detected"
            output['druglist_ok'] = False
        else:
            output['doc'] = doc_cut
            output['druglist_ok'] = True
        output['n_matched'] = len(druglist_match)
        if len(druglist_match) > 0:
            output['matched_phrase'] = druglist_match[0]
        return output
    
    def find_all(self, a_str, sub):
        start = 0
        positions = []
        while True:
            start = a_str.find(sub, start)
            if start == -1:
                return positions
            else:
                positions.append(start)
                start += len(sub) # use start += 1 to find overlapping matches
                
    def druglist_negation(self, doc):
        #returns a list of all drugs negated in druglist
        #for a specific pattern
        width = 100
        negation_matches = self.drug_stopped_regex.findall(doc)
        negation_strings = set(negation_matches)
        negated_drugs = set()
        for match in negation_strings:
            ends = self.find_all(doc, match)
            for end in ends:
                start = max(0, end-width) #don't loop back around
                big_chunk = doc[start:end]
                #taking chunk -5 is brittle, based on test docs
                #seems stable for these patients but won't generalise
                small_chunks = big_chunk.split(',')
                drug_name_chunk = small_chunks[-5]
                n_drugs_in_chunk = 0
                for dr in self.positive_regex:
                    for reg in self.positive_regex[dr]:
                        if len(reg.findall(drug_name_chunk)) > 0:
                            negated_drugs.add(dr)
                            n_drugs_in_chunk += 1
                if n_drugs_in_chunk > 1:
                    print "WARNING: multiple drugs in negation chunk, reduce chunk width"
        return negated_drugs
        
