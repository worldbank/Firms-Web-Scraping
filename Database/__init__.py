from utils import InputTable
#from utils import WebsiteRawTokensWithTaggedBizRegion
from utils import GooglePlacesAccess
from utils import JsonSink
import zipfile
import json
import os
from zipfile import ZipFile

class Stage1(object):
    """
    Simple implementation that fetches Businesses from a .csv file
    and for those businesses not already processed or in process
    it outputs two .zip files to be ingested by the next stage:
        one for website relevance and one for product extraction

    The follow on stages are responsible for appropriately processing
    this data; e.g. ExtractProducts should only operate on websites
    classified as relevant.
    """
    def __init__(self):
        self.stage1_output_intermediate_filename = 'sink.json.intermediate'
        self.stage1_output_final_filename = 'stage1.json'

        self.mygoogle = GooglePlacesAccess()
        self.mytable = InputTable(places_api = self.mygoogle)
        self.mysink = JsonSink(file_name = self.stage1_output_intermediate_filename)

    def run(self):
        """
        Implements basic ingest and output to follow on Biz, Owner Information stages
        Assumes an input.csv exists with columns for 'Business Name' and 'Region'
        """
        #import ipdb
        #ipdb.set_trace()
        self.mytable.push(getter=self.mytable.feature_getter,
                          sink=self.mysink)

        assert os.path.isfile(self.stage1_output_intermediate_filename), "Stage1 InputTable.push() did not produce an output file!"
        self.post_fix()

        myzipfile = ZipFile('database.output.relevance_data.zip', 'w')
        myzipfile.write(self.stage1_output_final_filename)
        myzipfile.close()

        # clean up
        os.remove(self.stage1_output_final_filename)
        os.remove(self.stage1_output_intermediate_filename)

    def post_fix(self):
        """
        The intermediate file was designed so that you could easily append json examples to it
        without having to worry about any outer containers or metadata

        So we then fix up the file so it's proper json that can be run by NextML.
        """
        def fix_up(row):
            ret = {'meta':{}}
            row = json.loads(row)

            ret['meta']['features'] = row['features']
            ret['target_id'] = hash(row['website'])
            ret['primary_description'] = "<a href=\"{}\" target=\"_blank\">{}</a>".format(row['website'], row['business_name'])
            ret['utc_timestamp'] = row['utc_timestamp']
            ret['website'] = row['website']
            ret['business_name'] = row['business_name']
            ret['region'] = row['region']

            return ret


        with open(self.stage1_output_intermediate_filename, 'r') as intermediate:
            final_output = [fix_up(row) for row in intermediate]

        with open(self.stage1_output_final_filename, 'w') as final:
            json.dump(final_output, final, ensure_ascii=False)
