import lxml.etree


def text_clean(this_string):
    # perform minimal text cleaning for certain fields. Not sure what this may need to entail.
    return ' '.join(this_string.upper().split())
    
def long_text_clean(this_string):
    this_string = this_string.replace("\r", " ")
    this_string = this_string.replace("\n", " ")
    return ' '.join(this_string.split())


def process_periodic_filing(xml):

    # first we grab all the data out of the filing, then we'll process it. 
    
    # Add the 
    this_filing_contents = {'Lobbyists':[], 'GovernmentEntities':[], 'Issues':[], 'ForeignEntities':[], 'AffiliatedOrgs':[]}
    for node in xml.iter():
        tag = node.tag
        
        if tag == 'Filing':
            this_filing_contents['Filing'] = node.attrib            
        elif tag == 'Registrant':
            this_filing_contents['Registrant'] = node.attrib
            this_filing_contents['Registrant']['GeneralDescription'] = long_text_clean(this_filing_contents['Registrant']['GeneralDescription'])
            this_filing_contents['Registrant']['Address'] = long_text_clean(this_filing_contents['Registrant']['Address'])
            
            
            
        elif tag =='Client':
            this_filing_contents['Client'] = node.attrib
        elif tag =='Lobbyists':
            # This is just a parent container for lobbyists
            pass
        elif tag == 'Lobbyist':
            this_filing_contents['Lobbyists'].append(node.attrib)
        elif tag == 'GovernmentEntities':
            # This is just a parent container for gov entities
            pass
        elif tag == 'GovernmentEntity':
            this_filing_contents['GovernmentEntities'].append(node.attrib)
            
        elif tag == 'Issues':
            # Just a container for issue
            pass
        elif tag == 'Issue':
            this_filing_contents['Issues'].append(node.attrib)
        elif tag == 'ForeignEntities':
            # container
            pass
        elif tag == 'Entity':
            this_filing_contents['ForeignEntities'].append(node.attrib)
            
        elif tag == 'AffiliatedOrgs':
            # container
            pass
        elif tag == 'Org':
            this_filing_contents['AffiliatedOrgs'].append(node.attrib)
        else:
            print "Illegal tag: " + tag
            assert False
        
    # 
    #print this_filing_contents
    return this_filing_contents
"""
<Entity xmlns="" ForeignEntityName="Rational Services" ForeignEntityCountry="UNITED KINGDOM" ForeignEntityPPBcountry="UNITED KINGDOM" ForeignEntityContribution="15000                         " ForeignEntityOwnershipPercentage="0" ForeignEntityStatus="ADDED" /></ForeignEntities><AffiliatedOrgs><Org xmlns="" AffiliatedOrgName="Rational Services" AffiliatedOrgCountry="UNITED KINGDOM" AffiliatedOrgPPBCcountry="UNITED KINGDOM" /></AffiliatedOrgs>
"""