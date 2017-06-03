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

# DB, walk through http://docs.sqlalchemy.org/en/latest/orm/tutorial.html
#   to get best practices
#
# also see: https://stackoverflow.com/questions/31394998/using-sqlalchemy-to-load-csv-file-into-a-database
# laste comment on best practices for larger files
#   catch is does COPY FROM support upsert type items
class InputTable(Base):
    """
    """
    def __init__(self, database_name="input"):
        # check if .db file exists if not create (does create_engine doethis?)
        # what type of database to back with?

        # bind to the engine, call sessionmaker, get DBSession
        pass




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


