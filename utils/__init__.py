from googleplaces import GooglePlaces, types, lang
from ApiKey import ApiKeys
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import (
        create_engine,
        Column,
        ForeignKey,
        Integer,
        String,
        )
from fuzzywuzzy import process
import textacy
import requests
import pandas as pd
import logging
import json
import re
import time, datetime
import itertools
import sys
import os
import errno

# DB, walk through http://docs.sqlalchemy.org/en/latest/orm/tutorial.html
#   to get best practices
#
# also see: https://stackoverflow.com/questions/31394998/using-sqlalchemy-to-load-csv-file-into-a-database
# laste comment on best practices for larger files
#   catch is does COPY FROM support upsert type items

# For now let's just use a Panads read from .csv
class InputTable(object):
    """
    Map an input.csv to the project database (helps to track
    businesses processed, input/outputs, etc.)

    WIP: For now we just do a straight read of the input.csv,
    deupe it but that's it.

    Todo: duplicate, upsert to a project
    local database to more easily capture statistics and
    manage input data flow.
    """
    def __init__(self,
                 database_name="input.csv",
                 pushed="pushed.csv",
                 output="output.csv",
                 data_root='./',
                 places_api=None,
                 featurizer=None,
                 sink_func=None):
        self.data_root = data_root
        self.places_api = places_api
        self.featurizer = featurizer
        self.sink_func = sink_func

        if not self.featurizer:
            self.featurizer = WebsiteRawTokensWithTaggedBizRegion() # WebsiteBagOfKeyphrases()

        if not self.sink_func:
            self.sink_func = JsonSink()

        if not os.path.isfile(output): # then create one, note this a basic output file, not production
            csv_output = pd.DataFrame(columns=['Business Name',
                                               'Region',
                                               'Overwrite',
                                               'Associated Agents',
                                               'Associated Products',
                                               'Source Urls',
                                               ])
            csv_output.to_csv(output, index=False, sep='\t')

        if not os.path.isfile(pushed): # then create one
            csv_pushed = pd.DataFrame(columns=['Business Name',
                                               'Region',
                                               'Overwrite'])
            csv_pushed.to_csv(pushed, index=False, sep='\t')

        file_path = os.path.join(self.data_root, database_name)
        if  os.path.isfile(file_path):
            self.table = pd.read_csv(file_path, sep='\t')
            # treat table as a LIFO queue, most recent copy of
            # bussiness name is kept
            self.table.drop_duplicates(subset=['Business Name',
                                               'Region',
                                               'Overwrite'],
                                       keep='last',
                                       inplace=True)
        else:
            raise FileNotFoundError(
                    errno.ENOENT, os.strerror(errno.ENOENT), file_path)

    def timing_getter(self, business):
        print(datetime.datetime.now()) # entered into call
        print(business['Business Name'], business['Region'])

    def default_getter(self, business):
        ret = None
        results = self.places_api.get_results(business_name=business['Business Name'],
                                              region=business['Region'],
                                              types=None)
        relevant_places = self.places_api.get_relevant_places(results)
        ret = self.places_api.get_place_websites(relevant_places)
        return ret

    def feature_getter(self, business, feature_func=None):
        """
        Gets website "features" (keyphrases, text, etc) as well as pulls website
        address. Gathers data for the rest of the system.

        `business` is a row from the input database.

        Extract website features, used for follow on human manual check, for
        active learning task training and, finally, for task prediction
        (both task training and prediction happen at the same time under the
        active learning paradigm)
        """
        if not feature_func:
            feature_func = self.featurizer

        # utility function for feature_getter
        def website_features(dict_results, feature_func=feature_func, key='websites'):
            ret = []
            for url in dict_results[key]:
                if url and url != 'None': # todo: fix dict_results from returning 'None'
                    # note this could be multi threaded for speed up; feature_func is kinda slow
                    ret.append( {'features': feature_func.\
                                                get_website_features(url=url,
                                                                     business_name=business['Business Name'],
                                                                     region=business['Region']),
                                 'website': url,
                                 'utc_timestamp': str(datetime.datetime.utcnow())} )
            return ret

        # get google place api results
        results = self.places_api.get_results(business_name=business['Business Name'],
                                              region=business['Region'],
                                              types=None)

        # get google place api website result (requires another api call, conver to dict w/ 'websites' key
        results = self.places_api.get_place_websites(results)
        dict_results = self.places_api.to_dict(results)

        # TODO: pass in google location results as features too
        # extract website fatures (ues feature_func, typically NLP or tokenize the website)
        return website_features(dict_results)

    def push(self,
             sink=None,
             getter=None,
             output='output.csv',
             pushed='pushed.csv'):
        """
        Push a given set of output as defined by getter over self.input to sink

        Can use custom `getter` if an alternative set of logic
        should be used.

        Checks for race conditions (pushing something twice because
        it hasn't completed between calls) by pollin against pushed, output tables
        """
        def pull(pushed=pushed,
                 output=output,
                 getter=getter,
                 sink=sink):
            """
            Pulls business related data, features, to supply to the sink function.
            Typically we just write out the business data aquired from Google Places to disk.

            Made this into an inner function to simplfy the driving logic of `push`
            """
            if not getter:
                getter = self.default_getter


            keys = ['Business Name', 'Region']

            for index, business in self.table.iterrows():
                # check that business does not exist in output or pushed by
                # checking keys.
                #
                # Note: There could be race conditions in here but I don't think
                # Firm Web Scraping runs fast enough for it really happen.
                # e.g., (~300/(30*24) business/hour vs. millsecond polling)
                pushed = pd.read_csv(os.path.join(self.data_root, pushed), sep='\t')
                output = pd.read_csv(os.path.join(self.data_root, output), sep='\t')

                # note: could use a real database, would elminate this problem
                if not all(any(output[key] == business[key]) for key in keys) and\
                   not all(any(pushed[key] == business[key]) for key in keys):
                    # degelate to getter
                    time.sleep(1)
                    yield business # yielding allows us to have relatively constant memory
                    #break #DEBUG

        if not sink:
            sink = self.sink_func

        for data in pull():
            for to_json in getter(data):
                import ipdb
                ipdb.set_trace()
                sink.write(to_json)

        return

class WebsiteRawTokensWithTaggedBizRegion(object):
    def __init__(self, url=None, business_name=None, region=None):
        self.url = url
        self.business_name = business_name
        self.region = region

    def get_text(self, html):
        """
        Copied from NLTK package.
        Modified to mark/tag HTML attributes

        see: https://stackoverflow.com/questions/26002076/python-nltk-clean-html-not-implemented
        for more details
        """

        # First we remove inline JavaScript/CSS:
        cleaned = re.sub(r"(?is)<(script|style).*?>.*?(</\1>)", " JAVASCRIPT_CSS ", html.strip())
        # Then we remove html comments. This has to be done before removing regular
        # tags since comments can contain '>' characters.
        cleaned = re.sub(r"(?s)<!--(.*?)-->[\n]?", " COMMENT ", cleaned)
        # Next we can remove the remaining tags:
        cleaned = re.sub(r"(?s)<.*?>", " TAG ", cleaned)
        # Finally, we deal with whitespace
        cleaned = re.sub(r"&nbsp;", " ", cleaned)
        cleaned = re.sub(r"\n", " ", cleaned) # added to strip newlines
        cleaned = re.sub(r"\t", " ", cleaned) # added to strip tabs
        cleaned = re.sub(r"  ", " ", cleaned)
        cleaned = re.sub(r"  ", " ", cleaned)
        return cleaned.strip()

    def ngram_iterator(self, text, n):
        for idx in range(len(text) - n + 1):
            yield ' '.join(text[idx:idx+n])

    def tag_item(self, text, item, tag_name):
        ngrams = self.ngram_iterator(text.split(), len(item.split()))
        # take top 3 fuzzy matches greater than 90%
        matches = process.extract(item, ngrams, limit=3)

        for match in matches:
            if match[1] >= 90:
                # note: `=` is a vw 'trick' where it's a categorical variable but since we're
                # doing >= 90 we only have 10. I can't assign a value (`:`) w/o post processing
                # in the NextML code, which woudl get way too messy
                text = text.replace(match[0], tag_name+'='+str(match[1]))

        return text.split()

    def get_website_features(self, url=None, business_name=None, region=None):
        if not url:
            url = self.url
        if not business_name:
            business_name = self.business_name
        if not region:
            region = self.region

        try:# note: some websites seems to block straight requets, might want to mimick a browswer using selenium
            html = requests.get(url).text
        except requests.exceptions.RequestException as e:
            html = 'REQUEST TIMED OUT ' + '(' + url + ')'
        text = self.get_text(html)

        # todo: optimze away redundant spliting, etc
        tagged = self.tag_item(text, item=business_name, tag_name="BIZ_OF_INTEREST")
        tagged = self.tag_item(' '.join(tagged), item=region, tag_name="REGION_OF_INTEREST")

        return tagged

class WebsiteBagOfKeyphrases(object):
    def __init__(self, n_keyterms=0.05, url=None):
        self.n_keyterms = n_keyterms
        self.url = url

    def reduce_keyphrases(list_keyphrases):
        return itertools.chain.from_iterable((element.split()\
                for element in list_keyphrases))

    def get_text(self, html):
        """
        Copied from NLTK package.
        Remove HTML markup from the given string.

        see: https://stackoverflow.com/questions/26002076/python-nltk-clean-html-not-implemented
        for more details
        """

        # First we remove inline JavaScript/CSS:
        cleaned = re.sub(r"(?is)<(script|style).*?>.*?(</\1>)", "", html.strip())
        # Then we remove html comments. This has to be done before removing regular
        # tags since comments can contain '>' characters.
        cleaned = re.sub(r"(?s)<!--(.*?)-->[\n]?", "", cleaned)
        # Next we can remove the remaining tags:
        cleaned = re.sub(r"(?s)<.*?>", " ", cleaned)
        # Finally, we deal with whitespace
        cleaned = re.sub(r"&nbsp;", " ", cleaned)
        cleaned = re.sub(r"\n", " ", cleaned) # added to strip newlines
        cleaned = re.sub(r"  ", " ", cleaned)
        cleaned = re.sub(r"  ", " ", cleaned)
        return cleaned.strip()

    def get_website_features(self, lang="en", url=None, n_keyterms=None):
        if not n_keyterms:
            n_keyterms = self.n_keyterms

        if not url:
            url = self.url

        html = requests.get(url).text
        text = self.get_text(html)

        processed_text = textacy.preprocess.preprocess_text(text,
                                                            lowercase=True,
                                                            no_urls=True,
                                                            no_emails=True,
                                                            no_phone_numbers=True,
                                                            no_currency_symbols=True,
                                                            no_punct=True)

        doc = textacy.Doc(processed_text, lang=lang)

        keyphrases = textacy.keyterms.singlerank(doc, n_keyterms=n_keyterms)

        return [element[0] for element in keyphrases] # use () for generator if desired

# initalize Google Places API
class GooglePlacesAccess(object):
    """
    A simple class to provide access to the GooglePlaces API.

    To rate limit the API calls to Google Places as one call per second
    we require that all users of this class be under the same process
    (as a child or parent thread). This rate limiting will not work under
    multi process processing, only multi threaded.

    todo: implement rate limiting

    Example:

    import utils
    from googleplaces import types

    myg = utils.GooglePlacesAccess()
    business_name = "Fish and Chips"
    region = "London, England"

    ret1 = myg.get_results(business_name=business_name,
                           region='London, England',
                           types=[types.TYPE_FOOD])
    ret2 = myg.get_relevant_places(ret1)
    ret3 = myg.get_place_websites(ret2)
    """
    def __init__(self, key=ApiKeys['Google Places']):
        self.places_api = GooglePlaces(ApiKeys['Google Places'])

    # todo: requires rate limiting
    def get_results(self,
                    business_name,
                    region,
                    radius=20000,
                    types=None):
        location = region
        keyword = business_name

        results = self.places_api.nearby_search(location=location,
                                                keyword=keyword,
                                                radius=radius,
                                                types=types)

        # return unique results only, note some businesses have different names but same url
        seen = set()
        seen_add = seen.add
        unique_results = [result for result in results.places if not (result.name in seen or seen_add(result.name))]

        return unique_results

    # todo: requires rate limiting on loop
    def get_place_websites(self, results):
        # return unique webistes only (irrespective of the business name)

        seen = set()
        seen.update([None, 'None'])# skip urls that are null
        seen_add = seen.add

        ret = []
        for place in results:
            time.sleep(1) # note: when rate limitating is implemented, no longer needed

            place.get_details() # side effect, calls Google API
            if not (place.website in seen or seen_add(place.website)):
                ret.append(place)

        return ret

    def to_dict(self, relevant_places):
        ret = {'websites':[], 'urls':[]}
        for place in relevant_places:
            ret['websites'].append(place.website)
            ret['urls'].append(place.url)

        return ret

class JsonSink(object):
    """
    A simple class for writing json data across multi threads safely
    to a single file. Basically an instance of logging.getLogger
    with defined constants.
    """
    def __init__(self, log_name="Feature Sink", file_name="sink.json.intermediate"):

        # Handle two side effects that occur when using logging:
        #   a) existing handlers and ...
        logger = logging.getLogger(log_name)
        if logger.handlers:
            logger.handlers = []

        # ... b) need an existing file to write to
        # There is some kind of side effect wherein the file_name has to exist for the
        # the logger to write to it and it won't create it.
        # We truncate/create the either case as this is new data.
        open(file_name, 'w').close()

        self.log_name = log_name
        self.file_name = file_name

        self.logger = logging.getLogger(self.log_name)
        self.logger.setLevel(logging.INFO)

        self.file_handler = logging.FileHandler(file_name)
        self.file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(message)s') # only take messages

        self.logger.addHandler(self.file_handler)

    def write(self, to_json):
        """
        Write one line of json
        """
        self.logger.info(json.dumps(to_json))

"""
Example usage:

    mygoogle = utils.GooglePlacesAccess()
    mytable = utils.InputTable(places_api=mygoogle)
    # returns per row associated websites to a given business in InputTable
    mytable.push(getter=mytable.feature_getter) # look at `sink.json.intermediate`

    # do something interesting with `sink.json.intermediate`, like feed it to NextML+MTurk
    # see WebsiteRelevance/__init__.py for a use of these functions
"""
