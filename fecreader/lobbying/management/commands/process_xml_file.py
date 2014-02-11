# utils to ease the pain of reading soprs xml.


import re, os
import lxml.etree
from dateutil.parser import parse as dateparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from lobbying.models import Filing, Entity, Org, Issue, Lobbyist, GovernmentEntity, Client, Registrant
from lobbying.utils.read_entry import process_periodic_filing

# Probably need to add this to local settings example
LOBBYING_FILE_DIR = settings.LOBBYING_FILE_DIR


type_hash = {}

def simple_clean(string):
    return string.strip().upper()
    
def get_filing_description(filing_type):
    # this is probably unnecessary
    filing_type = filing_type.upper().strip()
    filing_description = {}
    
    # what period?
    if filing_type.find('FIRST QUARTER') >= 0:
        filing_description['period'] = 'Q1'
    elif filing_type.find('SECOND QUARTER') >= 0:
        filing_description['period'] = 'Q2'
    elif filing_type.find('THIRD QUARTER') >= 0:
        filing_description['period'] = 'Q3'
    elif filing_type.find('FOURTH QUARTER') >= 0:
        filing_description['period'] = 'Q4'
    elif filing_type.find('REGISTRATION') >= 0:
        filing_description['period'] = 'RG'
    elif filing_type.find('MID-YEAR') >= 0:
        filing_description['period'] = 'MY'
    elif filing_type.find('YEAR-END') >= 0:
        filing_description['period'] = 'YE'
        
    # Not sure what can be done with these miscellaneous filings
    elif filing_type.find('MISC. DOC') >= 0:
            filing_description['period'] = 'MD'

    elif filing_type.find('MISC TERM') >= 0:
            filing_description['period'] = 'MD'

    else:
        print "Couldn't find period in type: %s" % (filing_type)
        assert False
    
    # Is it a termination report?
    if filing_type.find('TERMINATION') >= 0:
        filing_description['is_termination'] = True
    else:
        filing_description['is_termination'] = False
    
    
    
    # Is it an amendment ? 
    if filing_type.find('AMENDMENT') >= 0:
        filing_description['is_amendment'] = True
    else:
        filing_description['is_amendment'] = False

    if filing_type.find('NO ACTIVITY') >= 0:
        filing_description['is_no_activity'] = True
    else:
        filing_description['is_no_activity'] = False
        
    return filing_description
    
    
def smart_unicode(s):
    # Could also try the below
    # but latin1 seems not to work
    # 'ascii', 'latin1', 'windows-1252',
    for enc in [ 'utf-8', 'utf-16']:
        try:
            s.decode(enc)
            return (enc)
        except UnicodeDecodeError:
            pass
    raise UnicodeDecodeError

# if it's just a mess, kill the bad characters        
def kill_ascii_unprintable(s):
    a = s.decode(smart_unicode(s))
    ascii_cleaned = ''
    for i in a:
        if ord(i)<128:
            ascii_cleaned += i
    return ascii_cleaned


def validate_numeric_fields(filing_dict):
    if not filing_dict['Amount']:
        filing_dict['Amount'] = None
    return filing_dict
    

## The get_or_creates below are plain vanilla for now--they could be replaced with django's native get_or_create. But we want to eventually do more with them to uniquefy or something.

### DOH! THE ORDER OF THE RETURN FROM GET_OR_CREATE IS REVERSED HERE. WHOOPS. THIS LEADS TO ANNOYING MISTAKES BECAUSE TRUE/FALSE ARE 0 AND 1 SO WILL ASSIGN BOGUS IDS IF FLIPPED.  
    
def get_or_create_client(client_dict):
    try:
        cli = Client.objects.get(ClientID = client_dict['ClientID'])
        return (False, cli)
    except Client.DoesNotExist:
        cli = Client(**client_dict)
        cli.save()
        return (True, cli)

def get_or_create_registrant(registrant_dict):
    
    try:
        reg = Registrant.objects.get(RegistrantID=registrant_dict['RegistrantID'])
        return (False, reg)
    except Registrant.DoesNotExist:
        reg = Registrant(**registrant_dict)
        reg.save()
        return (True, reg)
        
def get_or_create_lobbyist(lobbyist_dict_complete):
    # our lobbyist model is just a name and an employer--we have to sort the covered position stuff out separately.
    name_clean = simple_clean(lobbyist_dict_complete['LobbyistName'])
    lobbyist_dict = {
        'LobbyistName':name_clean,
        'RegistrantID':lobbyist_dict_complete['RegistrantID']
    }
    
    try:
        lob = Lobbyist.objects.get(LobbyistName=lobbyist_dict['LobbyistName'], RegistrantID=lobbyist_dict['RegistrantID'])
        return (False, lob)
    except Lobbyist.DoesNotExist:
        lob = Lobbyist(**lobbyist_dict)
        lob.save()
        print "Added lobbyist %s" % (lobbyist_dict)
        return (True, lob)
        
    

# this is foreign entity
def get_or_create_foreign_entities(entity_dict):
    tf, created = Entity.objects.get_or_create(ForeignEntityName=entity_dict['ForeignEntityName'], ForeignEntityCountry=entity_dict['ForeignEntityCountry'], defaults={'ForeignEntityStatus': entity_dict['ForeignEntityStatus'], 'ForeignEntityOwnershipPercentage':entity_dict['ForeignEntityOwnershipPercentage'], 'ForeignEntityContribution':entity_dict['ForeignEntityContribution']})
    return (created, tf)

def get_or_create_government_entity(goventity_dict):
    ge, created = GovernmentEntity.objects.get_or_create(GovEntityName=goventity_dict['GovEntityName'])
    return (created, ge)

def get_or_create_issue(issue_dict):
    issue, created =  Issue.objects.get_or_create(Issue=issue_dict['Code'], SpecificIssue=issue_dict['SpecificIssue'])
    return (created, issue)

def get_or_create_org(org_dict):
    org, created = Org.objects.get_or_create(AffiliatedOrgName=org_dict['AffiliatedOrgName'], AffiliatedOrgCountry=org_dict['AffiliatedOrgCountry'], AffiliatedOrgPPBCcountry=org_dict['AffiliatedOrgPPBCcountry'])
    return (created, org)

def read_xml(file_path):
    
    file_name = os.path.basename(file_path)
    print "file name is " + file_name
    return 0
    # SOPR limits the file size to about 4MB so we can just slurp whole files at once. 
    xml = open(file_path, 'r').read()
    
    encoding = smart_unicode(xml)
    print "Found encoding %s" % (encoding)
    filings = re.findall(r'<filing.*?<\/filing>', unicode(xml, encoding), re.I | re.S | re.U)
    for filing_xml in filings:
        try:
            filing = lxml.etree.fromstring(filing_xml)
        except lxml.etree.XMLSyntaxError:
            print "Found error! Continuing... "
            continue

        #data = {'xml': filing_xml, } # Store the raw XML
        
        filing_type = dict(filing.items())['Type']

        
        description = get_filing_description(filing_type)
        filing_structured = process_periodic_filing(filing)

        # Check if the filng already exists. 
        try:
            this_filing = Filing.objects.get(ID=filing_structured['Filing']['ID'])
            print "Already entered filing: %s" % (filing_structured['Filing']['ID'])
            continue
        except Filing.DoesNotExist:
            pass
                
        
        
        # walk through the related children of a filing, and see if we can find them one at a time.
        
        #client = get_or_create_client(filing_structured['Client'])
        effective_date = None
        try:
            effective_date_raw = filing_structured['Received']
            effective_date = dateparse(effective_date_raw)
        except KeyError:
            pass
    
            
        registrant_data = filing_structured['Registrant']
        registrantid = registrant_data['RegistrantID']
        if effective_date:
            registrant_data['effective_date'] = effective_date
        registrant_created, registrant = get_or_create_registrant(registrant_data)
        
        client_data = filing_structured['Client']
        client_created, client = get_or_create_client(client_data)
        
        #lobbyists = []
        #for lobbyist in filing_structured['Lobbyists']:
        #    lobbyists.append(get_or_create(lobbyist))
        
        if effective_date:
            filing_structured['Received_formatted'] = effective_date
            
        filing_dict = dict(description.items() + filing_structured['Filing'].items())
        filing_dict = validate_numeric_fields(filing_dict)
        filing_dict['Registrant'] = registrant
        filing_dict['Client'] = client
        filing_dict['source_file_name'] = file_name
        filing_dict['flattened_filing'] = filing_structured
        
        try:
            # This sometimes occurs -- not sure why, but erase it. 
            del filing_dict['AffiliatedOrgsURL']
        except KeyError:
            pass
        this_filing = Filing.objects.create(**filing_dict)
        
        # now add the many-to-many models
        
        lobbyists = filing_structured['Lobbyists']
        for lobbyist in lobbyists:
            lobbyist['RegistrantID']=registrantid
            created, lob = get_or_create_lobbyist(lobbyist)
            this_filing.Lobbyists.add(lob)
        
        issues = filing_structured['Issues']
        for issue in issues:
            created, issue = get_or_create_issue(issue)
            this_filing.Issues.add(issue)
        
        orgs = filing_structured['AffiliatedOrgs']
        for org in orgs:
            created, this_org = get_or_create_org(org)
            this_filing.Orgs.add(this_org)
            
            
        foreign_entities = filing_structured['ForeignEntities']
        for foreign_entity in foreign_entities:
            created, this_foreign_ent = get_or_create_foreign_entities(foreign_entity)
            this_filing.ForeignEntities.add(this_foreign_ent)
            
        gov_entities = filing_structured['GovernmentEntities']
        for gov_entity in gov_entities:
            created, this_gov_entity = get_or_create_government_entity(gov_entity)
            this_filing.GovernmentEntities.add(this_gov_entity)
            
        
        this_filing.save()



class Command(BaseCommand):
    help = "Load current and historic legislators from yaml files. This is not efficient, because it checks for the existence of each separate piece of data before loading, and quite slow, because it slurps and parses the whole historical file whole."
    requires_model_validation = False

    def handle(self, *args, **options):
        
        # this is just for testing--there will be structure by quarter like the retrieval command, probably.
        import os
    
        arraylist = []
        for d, _, files in os.walk(LOBBYING_FILE_DIR):
            for a in files:
                file_path = LOBBYING_FILE_DIR + a
                if file_path.find("2013") > 0:
                    print "Processing data from: %s" % (file_path)
                    read_xml(file_path)
    


    