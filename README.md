# OAC-NLP

Detect prescription of oral anticoagulants (OAC) in clinical text using regular expressions. Developed and used in Bean et al. (2019 submitted) "Semantic Computational Analysis of Anticoagulation Use in Atrial Fibrillation from Real World Data".

Note many parameters in this code are specifically tuned to the text used in this project and are unlikely to generalise. 

This repository does not contain any patient data, the report text used in the demo is a generic structure. 

## Overview
The annotator tries to find a discharge medication list. If there isn't a list, or the list is found but empty, it falls back to checking the full body of the text. 

Most of the regular expressions are used to detect negations, or any other keyword that means the drug is not currently being taken. Cases considered are:

* Stopping, withholding, discontinuing
* Allergy
* Medication switching (A switched to B -> A is negated)
* Consider / consider restarting (e.g. after surgery)

## Usage
oac_nlp_demo.py loads some dummy reports and annotates them. The expected overall results as well as some specific details are checked e.g. that a drug was detected but negated, switching medications. 

DrugNLP.py contains the OACAnnotator class which does all the work, the only method used externally is .annotate()

## Funding
Dan Bean is funded by Health Data Research UK

## Contact
Developed by Dan Bean at King's College London - daniel.bean@kcl.ac.uk