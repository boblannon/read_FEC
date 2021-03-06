# load both the house and senate ratings
# assumes the files have already been downloaded
from lxml import etree
from StringIO import StringIO

from django.core.management.base import BaseCommand, CommandError

from rothenberg.models import HouseRace, SenateRace


from django.conf import settings

ROTHENBERG_HOUSE_FILE  = settings.ROTHENBERG_HOUSE_FILE
ROTHENBERG_SENATE_FILE  = settings.ROTHENBERG_SENATE_FILE

# ROTHENBERG_HOUSE_FILE = "rothenberg/data/house.xml"
# ROTHENBERG_SENATE_FILE = "rothenberg/data/senate.xml"

def parse_senate_line(elt):
    result = {}
    result['state'] = elt.find('state').text
    result['seat_class'] = elt.find('class').text
    rating = elt.find('rating')
    result['rating_id'] = rating.find('id').text
    result['rating_segment'] = rating.find('segment').text
    result['rating_label'] = rating.find('label').text
    result['incumbent'] = elt.find('incumbent').text
    return result

def parse_house_line(elt):
    result = {}
    result['state'] = elt.find('state').text
    result['district'] = elt.find('district').text
    rating = elt.find('rating')
    result['rating_id'] = rating.find('id').text
    result['rating_label'] = rating.find('label').text
    result['incumbent'] = elt.find('incumbent').text
    return result
        
def load_house():
    xmldata = open(ROTHENBERG_HOUSE_FILE, 'r').read()
    tree = etree.parse(StringIO(xmldata))
    for elt in tree.getiterator('race'):
        result = parse_house_line(elt)
        print result
        try:
            thisrace = HouseRace.objects.get(state=result['state'],district=result['district'])
            thisrace.rating_id = result['rating_id']
            thisrace.rating_label = result['rating_label']
            thisrace.save()
            
        except HouseRace.DoesNotExist:
            HouseRace.objects.create(**result)
            

def load_senate():
    xmldata = open(ROTHENBERG_SENATE_FILE, 'r').read()
    tree = etree.parse(StringIO(xmldata))
    for elt in tree.getiterator('race'):
        result = parse_senate_line(elt)
        print result
        try:
            thisrace = SenateRace.objects.get(state=result['state'],seat_class=result['seat_class'])
            thisrace.rating_id = result['rating_id']
            thisrace.rating_label = result['rating_label']
            thisrace.save()

        except SenateRace.DoesNotExist:
            SenateRace.objects.create(**result)
        
        
        
class Command(BaseCommand):
    help = "load both the house and senate ratings"
    requires_model_validation = False

    def handle(self, *args, **options):
        print "loading house..."
        load_house()
        print "loading senate..."
        load_senate()