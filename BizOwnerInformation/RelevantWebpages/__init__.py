from utils import InputTable
#from utils import WebsiteRawTokensWithTaggedBizRegion
from utils import GooglePlacesAccess
from utils import JsonSink
import os

class Stage1(object):
    def __init__(self):
        self.stage1_output_filename = 'sink.json.intermediate'

        self.mygoogle = GooglePlacesAccess()
        self.mytable = InputTable(places_api = self.mygoogle)
        self.mysink = JsonSink(file_name = self.stage1_output_filename)

    def run(self):
        """
        Implements basic ingest and output to follow on Biz, Owner Information stages
        Assumes an input.csv exists with columns for 'Business Name' and 'Region'
        """
        self.mytable.push(getter=self.mytable.feature_getter,
                          sink=self.mysink)

        assert os.path.isfile(self.stage1_output_filename), "Stage1 did not produce an output file!"

        return True
