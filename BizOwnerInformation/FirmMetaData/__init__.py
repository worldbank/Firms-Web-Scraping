from zipfile import ZipFile
import os
import json
import pymongo
import pandas

class ExtractSubmittedMetadata(object):
    def __init__(self,
                 in_database='flaskr_db',
                 in_collection='submitted_business_region',
                 out_zip_file='metadata.verified.output.zip'):
        """
        Given a mongo database and collection of submitted business regions
        That need to be verified, this class will pull them down,
        pull down the website content and construct a set of features
        for a NextML Metadata relevance oracle.

        Note that the oracle itself does not 'filter' the submitted metadata,
        instead it provides the NextML platform to offer a link to MTurk
        for humans to do the submitted metadata filtering.

        The oracle training is just a conveience (right now) and provides consistency
        across each of the Firm Meta Data tasks (product, website and metadata oracles).
        If it turns out to be good enough it may be used tosave on MTurk verification costs.
        """

        # set up connection to the submitted metadata
        client = pymongo.MongoClient()
        db = client[in_database]

        collection = db[in_collection]

        # fetch verified submitted metadata
        verified = collection.find_many({'verified':'True'})

        # write out verified as .csv
