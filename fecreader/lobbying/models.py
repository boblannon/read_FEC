from django.db import models
from picklefield.fields import PickledObjectField

from datetime import timedelta

# Only update data on the base regstrant / client etc if it's more than 30 days out of date. 
# The original records will be kept in the pickled model field, so if we wanna do analysis on them we can peel them off, one at a time. 
registration_date_expiration = timedelta(30)

class Registrant(models.Model):
    
    # Data, as it appears    
    RegistrantPPBCountry = models.CharField(max_length=255, null=True, blank=True)
    RegistrantID = models.IntegerField(null=True, unique=True)
    RegistrantCountry = models.CharField(max_length=255, null=True, blank=True)
    RegistrantName = models.CharField(max_length=255, null=True, blank=True)
    GeneralDescription = models.CharField(max_length=255, null=True, blank=True)
    Address = models.CharField(max_length=255, null=True, blank=True)
    
    # add-ons
    display_name = models.CharField(max_length=255, null=True, blank=True)
    crp_name = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(unique=True, null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True, help_text="when was this record updated?")
    
    
    

class Client(models.Model):
    # Data, as it appears    
    ClientName = models.CharField(max_length=255, null=True, blank=True)
    ClientID = models.CharField(max_length=63, null=True, blank=True)
    GeneralDescription = models.CharField(max_length=255, null=True, blank=True)
    ContactFullname = models.CharField(max_length=255, null=True, blank=True)
    SelfFiler = models.NullBooleanField(null=True)
    ClientState = models.CharField(max_length=63, null=True, blank=True)
    ClientCountry = models.CharField(max_length=127, null=True, blank=True)
    ClientPPBState = models.CharField(max_length=63, null=True, blank=True)
    ClientPPBCountry = models.CharField(max_length=127, null=True, blank=True)
    IsStateOrLocalGov = models.NullBooleanField(null=True)
    
    # add-ons
    slug = models.SlugField(unique=True, null=True, blank=True)
    effective_date = models.DateField(null=True, blank=True, help_text="when was this record updated?")
    

# This is only used for U.S. Government entity
class GovernmentEntity(models.Model):
    GovEntityName = models.CharField(max_length=127, null=True, blank=True)
    
class Lobbyist(models.Model):
    
    LobbyistName = models.CharField(max_length=255, null=True, blank=True)    
    RegistrantID = models.IntegerField(null=True)
    
    class Meta:
        unique_together = (('LobbyistName', 'RegistrantID', ))
        
class Issue(models.Model):
    Issue = models.CharField(max_length=127, null=True, blank=True)
    SpecificIssue = models.TextField(null=True, blank=True)

class Org(models.Model):
    AffiliatedOrgName = models.CharField(max_length=127, null=True, blank=True)
    AffiliatedOrgCountry = models.CharField(max_length=127, null=True, blank=True)
    AffiliatedOrgPPBCcountry = models.CharField(max_length=127, null=True, blank=True)

class Entity(models.Model):
    #originals--numericalish fields are captured here as text. Not sure what's allowed in them.
    ForeignEntityName = models.CharField(max_length=127, null=True, blank=True)
    ForeignEntityCountry = models.CharField(max_length=127, null=True, blank=True)
    ForeignEntityStatus = models.CharField(max_length=127, null=True, blank=True)
    ForeignEntityOwnershipPercentage = models.CharField(max_length=7, null=True, blank=True)
    ForeignEntityContribution = models.CharField(max_length=15, null=True, blank=True)

class Filing(models.Model):
    # what report did this come from?
    source_file_name = models.CharField(max_length=127, null=True, blank=True)
    
    Received = models.CharField(max_length=127, null=True, blank=True)
    Period = models.CharField(max_length=255, null=True, blank=True)
    Amount = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    Year = models.IntegerField(null=True)
    Type = models.CharField(max_length=127, null=True, blank=True)
    ID = models.CharField(max_length=127, null=True, blank=True, unique=True)
    
    # foreign keys -- probably shouldn't allow null, but.. 
    Client = models.ForeignKey(Client, null=True)
    Registrant = models.ForeignKey(Registrant, null=True)
    Lobbyists = models.ManyToManyField(Lobbyist, null=True)
    Issues = models.ManyToManyField(Issue, null=True)
    Orgs = models.ManyToManyField(Org, null=True)
    ForeignEntities = models.ManyToManyField(Entity, null=True)
    GovernmentEntities = models.ManyToManyField(GovernmentEntity, null=True)
    
    #add-ons
    Received_formatted = models.DateTimeField(null=True, blank=True)
    period = models.CharField(max_length=2)
    is_amendment = models.BooleanField(default=False)
    is_termination = models.BooleanField(default=False)
    is_no_activity = models.BooleanField(default=False)
    # Has this been superseded by a later amendment?
    is_superseded = models.BooleanField(default=False)
    data_is_processed = models.BooleanField(default=False)
    
    # We need some representation of the whole object so we don't have to do a gazillion queries just to display it. It goes here as it is originally.
    flattened_filing = PickledObjectField()
    
    
"""


drop table lobbying_registrant cascade;
drop table lobbying_client cascade;
drop table lobbying_lobbyist cascade;
drop table lobbying_governmententity cascade;
drop table lobbying_org cascade;
drop table lobbying_entity cascade;
drop table lobbying_issues cascade;

drop table "lobbying_filing_GovernmentEntities" cascade;
drop table "lobbying_filing_Orgs" cascade;
drop table "lobbying_filing_Issues" cascade;
drop table "lobbying_filing_Lobbyists" cascade;
drop table "lobbying_filing_ForeignEntities" cascade;

drop table lobbying_filing cascade;



"""

