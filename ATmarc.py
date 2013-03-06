#!/usr/bin/python

import re
from xml.dom.minidom import parseString
import pymarc
from pymarc.field import Field
import difflib

filename = raw_input("Enter the full filename (include the .mrc extension): ")
print "Processing file '"+filename+"' ..."
# write validation code that makes sure the filename entered matches the correct pattern of a .mrc filename

#folder = filename[:-4]  	# remove the .mrc extension from the filename; the primary folder name created on the local directory should match the filename
folder = filename[:-17]		# remove the "_all_3_python.mrc" extension from the filename
marcRecsIn = pymarc.MARCReader(file(folder+'/input_files/'+filename), to_unicode=True, force_utf8=True)
marcRecsOut_rejects = pymarc.MARCWriter(file(folder+'/output_files/'+folder+'_rejects.mrc', 'w'))
marcRecsOut_good = pymarc.MARCWriter(file(folder+'/output_files/'+folder+'_good.mrc', 'w'))

######################################################################
## Method - no008dates
## Find records without any value set for the 008 Date1 (bytes 07-10) and write to file
######################################################################
open(folder+'/output_files/'+folder+'_no008dates.txt', 'w').close()	# creates and/or clears the file no008dates.txt
no008datesCount = 0
def no008dates(rec=None):
	global no008datesCount
	no008datesFile = open(folder+'/output_files/'+folder+'_no008dates.txt', 'a')
	if rec:
		for field008 in rec.get_fields('008'):
			field008data = field008.value()
			field008date1 = field008data[7:11]		# capture bytes 07-10 of the 008 field for Date1
			if field008date1 == '    ':
				if no008datesCount == 0:
					no008datesFile.write("RECORDS LACKING INCLUSIVE BEGIN/END DATES\n------------------------------------------------------------\n\n")
				a = rec['245']['a']
				if rec['245']['f']: f = rec['245']['f']
				else: f = ''
				if rec['245']['g']: g = rec['245']['g']
				else: g = ''
				no008datesFile.write("%s\n" % (rec['099']['a']))
				no008datesFile.write("%s %s %s\n\n" % (a, f, g))
				no008datesCount += 1
				return True
			else: return False
	else:
		no008datesFile.write("\n------------------------------------------------------------\nTotal Count of records lacking the Inclusive Begin/End dates: %s records\n" % (no008datesCount))
		return False
	no008datesFile.close()

######################################################################
## Method - lgAbstracts
## Write to file any 520 abstracts that are greater than 1900 characters
######################################################################
open(folder+'/output_files/'+folder+'_lgAbstracts.txt', 'w').close()	# creates and/or clears the file lgAbstractsFile.txt
lgAbstractsCount = 0
def lgAbstracts(rec=None, text=None):
	global lgAbstractsCount
	lgAbstractsFile = open(folder+'/output_files/'+folder+'_lgAbstracts.txt', 'a')
	if rec:
		if lgAbstractsCount == 0:
			lgAbstractsFile.write("RECORDS HAVING AN ABSTRACT GREATER THAN 1900 CHARACTERS\n------------------------------------------------------------\n\n")
		lgAbstractsFile.write("%s - length of 520 is: %s\n" % (rec['099']['a'], len(text)))
		lgAbstractsFile.write("%s\n\n" % (text[0:500]))
		lgAbstractsCount += 1
		return True
	else:
		lgAbstractsFile.write("\n------------------------------------------------------------\nTotal Count of abstracts > 1900 is: %s\n" % (lgAbstractsCount))
		return False
	lgAbstractsFile.close()

######################################################################
## Method - noAbstracts
## Write to file records having no abstract
######################################################################
open(folder+'/output_files/'+folder+'_noAbstracts.txt', 'w').close()	# creates and/or clears the file noAbstractsFile.txt 
noAbstractsCount = 0
noScopesCount = 0
def noAbstracts(rec=None, hasScope=None):
	global noAbstractsCount
	global noScopesCount
	noAbstractsFile = open(folder+'/output_files/'+folder+'_noAbstracts.txt', 'a')
	if rec:
		if noAbstractsCount == 0:
			noAbstractsFile.write("RECORDS LACKING AN ABSTRACT\n------------------------------------------------------------\n\n")
		a = rec['245']['a']
		if rec['245']['f']: f = rec['245']['f']
		else: f = ''
		if rec['245']['g']: g = rec['245']['g']
		else: g = ''
		noAbstractsFile.write("%s - " % (rec['099']['a']))
		if hasScope:
			noAbstractsFile.write("Has Scope Note\n")
		else:
			noAbstractsFile.write("NO SCOPE NOTE\n")
			noScopesCount += 1
		noAbstractsFile.write("%s %s %s\n\n" % (a, f, g))
		noAbstractsCount += 1
		return True
	else:
		noAbstractsFile.write("\n------------------------------------------------------------\nTotal Count of records lacking an abstract is: %s\n" % (noAbstractsCount))
		noAbstractsFile.write("\nCount of these records also lacking a scope note is: %s\n" % (noScopesCount))
		return False
	noAbstractsFile.close()

######################################################################
## Method - noMatch520s
## Write to file records having 520s that don't match either the Abstract or the Scope notes
######################################################################
open(folder+'/output_files/'+folder+'_noMatch520s.txt', 'w').close()  # creates and/or clears the file noMatch520s.txt
noMatch520sCount = 0
def noMatch520s(rec=None, eadData=None, alt520=None, diffAbstract=None, diffScope=None):
	global noMatch520sCount
	noMatch520sFile = open(folder+'/output_files/'+folder+'_noMatch520s.txt', 'a')
	if rec:
		if noMatch520sCount == 0:
			noMatch520sFile.write("RECORDS HAVING A 520 THAT DOES NOT MATCH ABSTRACT OR SCOPE\n------------------------------------------------------------\n\n")
		noMatch520sFile.write("\n-------------------------%s-------------------------" % (rec['099']['a']))
		if not eadData['abstract'] == '':
			noMatch520sFile.write("\nEAD abstract:\n%s\n" % (eadData['abstract']))
		if not eadData['scope'] == '':
			noMatch520sFile.write("\nEAD scope:\n%s\n" % (eadData['scope']))
		noMatch520sFile.write("\nMARC 520:\n%s\n" % (alt520))
		noMatch520sFile.write("- NOT a Match\n")
		noMatch520sFile.write("- Abstract similarity: %s\n" % (diffAbstract))
		noMatch520sFile.write("- Scope similarity: %s\n" % (diffScope))
		noMatch520sCount += 1
		return True
	else:
		noMatch520sFile.write("\n------------------------------------------------------------\nTotal Count of 520s that don't match is: %s\n" % (noMatch520sCount))
		return False
	noMatch520sFile.close()

######################################################################
## Method - normalizeText
## Strip and normalize text, removing extra white space, html codes, etc.
######################################################################
def normalizeText(text):
	headTag = re.compile(r'<head>[^<]*</head>')
	htmlTags = re.compile(r'<[^>]+>')
	htmlAmpCodes = re.compile(r'&[^;]+;')
	nonAlphaNum = re.compile(r'[^\sa-zA-Z0-9]')
	newLineChar = re.compile(r'\n')
	whiteSpace = re.compile(r'\s+')
	
	text = headTag.sub('', text)			# delete any <head> tags
	text = htmlTags.sub('', text)			# delete any html <> tags
	text = htmlAmpCodes.sub('', text)		# delete any html Amp codes, enclosed in &...;
	text = nonAlphaNum.sub(' ', text)		# replace any characters that are not whitespace or alpha-numeric with a single space
	text = newLineChar.sub(' ', text)		# replace any new line characters with a single space
	text = whiteSpace.sub(' ', text)		# substitute a single space for any whitespace that is longer than a single character
	text = text.strip()						# strip off any whitespace from the beginning and end of the string
	text = text.encode('ascii', 'ignore')	# change the string encoding to ascii
	
	return text

######################################################################
## Method - getEADdata
## Get resource ID <num>, scopecontent & abstract from EAD XML file
######################################################################
def getEADdata(resID):
	eadData = {}
	eadFilename = folder+'/input_files/'+folder+'_eadxml/'+resID+'-ead.xml'
	eadFile = open(eadFilename, 'r')
	eadStr = eadFile.read()
	eadFile.close()
	
	xmlDOM = parseString(eadStr)
	if xmlDOM.getElementsByTagName('num'):
		numTag = xmlDOM.getElementsByTagName('num')[0].toxml()
		numData = numTag.replace('<num>', '').replace('</num>', '')
		numData = numData.encode('ascii', 'ignore')
	else: numData = ''
	
	if xmlDOM.getElementsByTagName('scopecontent'):
		scopeTag = xmlDOM.getElementsByTagName('scopecontent')[0].toxml()
		scopeData = normalizeText(scopeTag)
	else: scopeData = ''
	
	if xmlDOM.getElementsByTagName('abstract'):
		abstractTag = xmlDOM.getElementsByTagName('abstract')[0].toxml()
		abstractData = normalizeText(abstractTag)
	else: abstractData = ''
	
	eadData['id'] = numData
	eadData['scope'] = scopeData
	eadData['abstract'] = abstractData
	
	return eadData

######################################################################
## Method - no7XXs
## Find records without any name headings and write to file
######################################################################
open(folder+'/output_files/'+folder+'_no7XXs.txt', 'w').close()		# creates and/or clears the file no7XXs.txt
no7XXsCount = 0
def no7XXs(rec=None):
	global no7XXsCount
	no7XXsFile = open(folder+'/output_files/'+folder+'_no7XXs.txt', 'a')
	if rec:
		if not rec['700'] and not rec['710']:
			if no7XXsCount == 0:
				no7XXsFile.write("RECORDS LACKING ANY NAME HEADING\n------------------------------------------------------------\n\n")
			a = rec['245']['a']
			if rec['245']['f']: f = rec['245']['f']
			else: f = ''
			if rec['245']['g']: g = rec['245']['g']
			else: g = ''
			no7XXsFile.write("%s\n" % (rec['099']['a']))
			no7XXsFile.write("%s %s %s\n\n" % (a, f, g))
			no7XXsCount += 1
	else:
		no7XXsFile.write("\n------------------------------------------------------------\nTotal Count of records lacking a name heading: %s records\n" % (no7XXsCount))
	no7XXsFile.close()

######################################################################
## Method - deDup7XXs
## Find duplicate 700 or 710 fields and combine variant roles onto a single field
######################################################################
def deDup7XXs(rec=None):
	add7XXs = []
	del7XXs = []
	for field700_1 in rec.get_fields('700'):
		this700 = field700_1
		this700done = False
		this700new = False
		for i in add7XXs:
			if this700.get_subfields('a', 'b', 'c', 'q', 'd') == i.get_subfields('a', 'b', 'c', 'q', 'd'):
				this700done = True
		if not this700done:
			for field700_2 in rec.get_fields('700'):
				if field700_1.get_subfields('a', 'b', 'c', 'q', 'd') == field700_2.get_subfields('a', 'b', 'c', 'q', 'd'):
					if field700_1.value() != field700_2.value():
						field700_2_e = field700_2.get_subfields('e')
						this700.add_subfield('e', field700_2_e[0])
						del7XXs.append(field700_2)
						this700new = True
		if this700new:
			add7XXs.append(this700)
			del7XXs.append(field700_1)
	
	for del7XX in del7XXs:
		rec.remove_field(del7XX)
	for add7XX in add7XXs:
		rec.add_field(add7XX)
	return rec

######################################################################
##  MAIN SCRIPT
######################################################################
recCount = 0

for record in marcRecsIn:	# Iterate through all records in marcRecsIn
	resID = record['099']['a']
	noAbstract = False
	abstractTooLg = False
	noMatch520 = False
	new520abstract = None
	new520scope = None
	
	no008date = no008dates(rec=record)	# if record lacks an 008 Date 1, write to file and return True, else return False
	
	eadDataDict = getEADdata(resID)
	
	if eadDataDict['abstract'] == '':
		if eadDataDict['scope'] == '':
			hasScope = False
		else: hasScope = True
		noAbstract = noAbstracts(rec=record, hasScope=hasScope)   # write this record to the noAbstracts.txt file, and return True
	
	########## Compare EAD scopecontent and abstract to 520 MARC fields
	for field520 in record.get_fields('520'):
		field520a = field520.get_subfields('a')[0]		# get the first item in the list of all subfields $a (there should be only 1 in list)
		altField520a = field520a						# capture a copy of the 520 text that will be altered for comparison
		altField520a = normalizeText(altField520a)		# strip and normalize the 520 text for comparison
		
		diffRatioAbstract = difflib.SequenceMatcher(None, altField520a, eadDataDict['abstract']).ratio()   # returns a value of the similarity ratio between the 2 strings
		diffRatioScope = difflib.SequenceMatcher(None, altField520a, eadDataDict['scope']).ratio()   # returns a value of the similarity ratio between the 2 strings
		
		if diffRatioAbstract >= 0.9:	# this 520 matches the abstract
			if len(altField520a) <= 1900:		# this 520 is within 1900 characters
				new520abstract = Field(tag='520', indicators=['3',' '], subfields=['a', field520a])	# create a new 520 field for the abstract with 1st indicator=3
			else:
				abstractTooLg = lgAbstracts(rec=record, text=altField520a)		# write to file when abstract is greater than 1900 characters, and return True
		elif diffRatioScope >= 0.9:		# this 520 matches the scope
			if len(altField520a) <= 1900:		# this 520 is within 1900 characters
				new520scope = Field(tag='520', indicators=['2',' '], subfields=['a', field520a])	# create a new 520 field for the scope note with 1st indicator=2
		else:
			noMatch520 = noMatch520s(rec=record, eadData=eadDataDict, alt520=altField520a, diffAbstract=diffRatioAbstract, diffScope=diffRatioScope)
		
		record.remove_field(field520)	# remove the old 520 field that has blank indicators
	
	if new520abstract:
		record.add_field(new520abstract)
	if new520scope:
		record.add_field(new520scope)
	
	for field545 in record.get_fields('545'):
		if len(field545) > 1900:
			record.remove_field(field545)
	
	no7XXs(rec=record)	# if record lacks any 700 or 710 fields, write to file
	
	record = deDup7XXs(rec=record)
			
	if no008date or noAbstract or abstractTooLg or noMatch520:
		marcRecsOut_rejects.write(record)
	else:
		marcRecsOut_good.write(record)
	
	recCount +=1


no7XXs()		# write the final count of records with no 7XXs to the file
no008dates()	# write the final count of records with no 008 Date1 to the file
lgAbstracts()	# write the final count of records with a large abstract to the file
noAbstracts()	# write the final count of records with no abstract to the file
noMatch520s()	# write the final count of records with a 520 that doesn't match to the file

print str(recCount)+" records were processed in file '"+filename+"'"
marcRecsOut_rejects.close()
marcRecsOut_good.close()
