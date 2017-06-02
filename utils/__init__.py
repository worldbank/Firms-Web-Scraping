from googleplaces import GooglePlaces, types, lang
from ApiKey import ApiKeys

# initalize Google Places API
# basically need a rate limited singleton
GooglePlacesAccess(object):
    def __init__(self, key=ApiKeys['Google Places']):
        self.places_api = GooglePlaces(ApiKeys['Google Places'])

    def get_results(self,
                    business_name,
                    region,
                    radius=20000,
                    types=None):
        location = region
        keyword = business_name

        results = self.places.nearby_search(location=location,
                                           keyword=keyword,
                                           radius=radius,
                                           types=types)

        return results

    def get_relevant_places(self, results):
        ret = []
        for place in results.places:
            if True: # WIP: check if place is actually relevant, should only be 2 at max
                place.get_details() # side effect, calls Google API
                ret.append(place)

        return ret

    def get_place_websites(self, relevant_places):
        ret = {'websites':[], 'urls':[]}
        for place in relevant_place:
            ret['websites'].append(place.website)
            ret['urls'].append(place.url)

        return ret

##
#loc = 'London, England'
#business_name='Fish and Chips'
#radius=20000
#result = google_places.nearby_search(
#                location='London, England', keyword='Fish and Chips',
#                        radius=20000, types=[types.TYPE_FOOD])
#result = places.nearby_search(
#                location='London, England', keyword='Fish and Chips',
#                        radius=20000, types=[types.TYPE_FOOD])
#result
#result.html_attributions
#result.raw_response
#result.has_attributions
#result.places
#result.places[0]
#result.places[0].website
#result.places[0].get_details()
#result.places[0].website
#
