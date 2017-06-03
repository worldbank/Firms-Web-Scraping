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
import time
import pandas as pd
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
class InputTable(Base):
    """
    Map an input.csv to the project database (helps to track
    businesses processed, input/outputs, etc.)

    WIP: For now we just do a straight read of the input.csv,
    deupe it but that's it.

    Todo: duplicate, upsert to a project
    local database to more easily capture statistics and
    manage input data flow.
    """
    def __init__(self, database_name="input.csv", pushed="pushed.csv"):
        if not os.path.isfile(pushed): # then create one
            open.(os.path.join('./', pushed), 'a').close()

        file_path = os.path.join('..', database_name)
        if  os.path.isfile(file_path):
            self.table = pd.read_csv(file_path)
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

        def push(self, pusher, output='output.csv', pushed='pushed.csv'):
            """
            Push a given set of output (if not string, then a dataframe)
            downstream in order to collect business information on the input.

            Can use custom `pusher` if an alternative set of logic
            should be used.

            Checks for race conditions (pushing something twice because
            it hasn't completed between calls) against a pushed table by polling
            """

            keys = ['Business Name', 'Region']

            for business in self.table.iterrows():
                # poll on pushed, output this is fast enough I believe
                pushed = pd.read_csv(os.path.join('./', pushed))
                output = pd.read_csv(os.path.join('../', output))

                # check that business does not exist in output or pushed by
                # checking keys
                if not all(
                        (any(output[key] == business[key]) for key in keys)) and
                   not all(
                        (any(pushed[key] == business[key]) for key in keys)):
                    # degelate to pusher
                    pusher(business) # should be an asynch call

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

        return results

    def get_relevant_places(self, results):
        ret = []
        for place in results.places:
            if True: # WIP: check if place is actually relevant, should only be 2 at max
                place.get_details() # side effect, calls Google API
                time.sleep(1) # note: when rate limitating is implemented, no longer needed
                ret.append(place)

        return ret

    def get_place_websites(self, relevant_places):
        ret = {'websites':[], 'urls':[]}
        for place in relevant_places:
            ret['websites'].append(place.website)
            ret['urls'].append(place.url)

        return ret


