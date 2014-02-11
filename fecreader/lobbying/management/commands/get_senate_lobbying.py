# routines to get the actual files.

from optparse import make_option
import re
from urllib2 import Request, urlopen
from os import system
from time import sleep

from django.core.management.base import BaseCommand
from django.conf import settings

LOBBYING_ZIP_DIR = settings.LOBBYING_ZIP_DIR
LOBBYING_FILE_DIR = settings.LOBBYING_FILE_DIR
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:24.0) Gecko/20100101 Firefox/24.0"

def download_with_headers(url):
    """ Sign our requests with a user agent set in the settings file"""
    headers = { 'User-Agent' : USER_AGENT }    
    req = Request(url, None, headers)
    return urlopen(req).read()
    
def get_zipfile_urls():
    url = 'http://www.senate.gov/legislative/Public_Disclosure/database_download.htm'
    page = download_with_headers(url)
    zipfiles = re.findall(r'(\d\d\d\d\_\d\.zip)', page)
    base_url = 'http://soprweb.senate.gov/downloads/%s'
    return [base_url % filename for filename in zipfiles]

                
# typical usage-for current quarter: python manage.py get_senate_lobbying --years=2013
# get everything since 2011: python manage.py get_senate_lobbying --years=2013,2012,2011
                
class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
            make_option('--all_quarters',
                        action='store_true',
                        dest='all_quarters',
                        default=False,
                        help="Import all data for the given years"),
            make_option('--years',
                        action='store',
                        dest='years',
                        default='2013',
                        help="Years for which to import data. If multiple years are entered, all data for those years will be imported."),
            make_option('--filename',
                        action='store',
                        dest='filename',
                        default=None,
                        help="Override default behavior of downloading data from Senate website and use given file."),
            )

    def handle(self, *args, **options):
        filename = options['filename']
        all_quarters = options['all_quarters']
        years = options['years'].split(',')
        
        # reverse it so that the first result of each year is the most recent quarter.
        zipfile_urls = get_zipfile_urls()
        #zipfile_urls = []
        #zipfile_urls.reverse()
        #print "Got urls: %s" % (zipfile_urls)
        urls_to_download = []
        year_re = re.compile('(\d\d\d\d)_(\d)')
        
        
        if len(years) > 1 or all_quarters:        
            for zipfile_url in zipfile_urls:
                year_quarter = year_re.search(zipfile_url)                
                if year_quarter:
                    this_year = year_quarter.group(1)
                    this_quarter = year_quarter.group(2)
                    if this_year in years:
                        urls_to_download.append(zipfile_url)
        else:
            urls_to_download.append(zipfile_urls[0])
        
        for file_url in urls_to_download:
            
            # use old school system command, instead of annoying newer flavor
            zipfile_local_path = LOBBYING_ZIP_DIR
            year_quarter = year_re.search(file_url)
            # where will it end up?
            local_path = "%s%s_%s.zip" % (LOBBYING_ZIP_DIR, year_quarter.group(1), year_quarter.group(2))                
            
            download_cmd = "curl %s > %s" % (file_url, local_path)
            print "Executing: %s" % download_cmd
            sleep(1)
            system(download_cmd)
            
            # unzip with the -u update flag, so we only expand files that are new / modified. 
            unzip_cmd = "unzip -u %s -d %s" % (local_path, LOBBYING_FILE_DIR)
            print "Executing: %s" % unzip_cmd
            system(unzip_cmd)
            
            # SOPR format is: YYYY_Q_M_N.xml -- where YYYY is year, Q is quarter M is month (either one or two digits) and N
            # is file number for that month, so 2012_4_10_9.xml is the 9th file for Oct. 2012 (which is in the 4th quarter)