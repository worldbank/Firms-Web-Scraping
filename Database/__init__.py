from utils import InputTable
from utils import WebsiteBagOfKeyphrases
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
    def __init__(self, input_file=None):
        self.input_file = input_file
        if not input_file:
            self.input_file = 'input.csv'

        self.stage1_output_intermediate_filename = 'sink.json.intermediate'
        self.stage1_output_final_filename = 'stage1.json'

        self.product_stage1_output_intermediate_filename = 'product.sink.json.intermediate'
        self.product_stage1_output_final_filename = 'product.stage1.json'

        self.mygoogle = GooglePlacesAccess()
        self.bagofkeyphrases = WebsiteBagOfKeyphrases()

        self.mytable = InputTable(database_name=input_file,
                                  places_api = self.mygoogle)
        self.product_mytable = InputTable(database_name=input_file,
                                          places_api = self.mygoogle,
                                          featurizer= self.bagofkeyphrases)

        self.mysink = JsonSink(file_name = self.stage1_output_intermediate_filename)
        self.myproductsink = JsonSink(log_name = "Product Sink", file_name = self.product_stage1_output_intermediate_filename)

    def run(self):
        """
        Implements basic ingest and output to follow on Biz, Owner Information stages
        Assumes an input.csv exists with columns for 'Business Name' and 'Region'
        """

        # Generate features for the Website Relevance task, save as zip for Active Learning training
        # and follow on processing


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

         Generate features for the Product Classification task, save as zip for Active Learning training
         and follow on processing
        self.product_mytable.push(getter=self.product_mytable.feature_getter,
                                  sink=self.myproductsink)

        assert os.path.isfile(self.product_stage1_output_intermediate_filename), "Stage1 InputTable.push() did not produce an output file for products!"
        self.post_fix(intermediate=self.product_stage1_output_intermediate_filename,
                      final=self.product_stage1_output_final_filename,
                      for_products=True)

        myzipfile = ZipFile('database.output.product.zip', 'w')
        myzipfile.write(self.product_stage1_output_final_filename)
        myzipfile.close()

        # clean up
        os.remove(self.product_stage1_output_final_filename)
        os.remove(self.product_stage1_output_intermediate_filename)

    def post_fix(self,
                 intermediate=None,
                 final=None,
                 for_products=False):
        """
        The intermediate file was designed so that you could easily append json examples to it
        without having to worry about any outer containers or metadata

        So we then fix up the file so it's proper json that can be run by NextML.
        """
        if not intermediate:
            intermediate = self.stage1_output_intermediate_filename
        if not final:
            final = self.stage1_output_final_filename

        def feature_list_to_features(my_json):
            """
            For fixing up product lists, expand array of features into rows per element
            """
            max_feature_length = 100 # some keyphrases get crazy long

            ret = []
            for business in my_json:
                for feature in business['meta']['features']:
                    row = {'meta':{'features': feature[:max_feature_length]},
                           'business_name':business['business_name'],
                           'target_id':hash(business['business_name']+feature[:max_feature_length]),
                           'region': business['region'],
                           'primary_description':business['primary_description'],
                           'utc_timestamp': business['utc_timestamp'],
                           'website': business['website']}
                    ret.append(row)
            return ret

        def fix_up(row):
            ret = {'meta':{}}
            row = json.loads(row)

            ret['meta']['features'] = row['features']
            ret['target_id'] = hash(row['website'])
            ret['primary_description'] = row['business_name'] # note would be nice to capture business website title
            ret['utc_timestamp'] = row['utc_timestamp']
            ret['website'] = row['website']
            ret['business_name'] = row['business_name']
            ret['region'] = row['region']

            return ret

        with open(intermediate, 'r') as intermediate_obj:
            final_output = [fix_up(row) for row in intermediate_obj]

        if for_products:
            final_output = feature_list_to_features(final_output)

        with open(final, 'w') as final_obj:
            json.dump(final_output, final_obj, ensure_ascii=False)

class Stage5(object):
    """
    Implements Data Staging: Sink sub system, basically
    collects all the output files of other stages and generates a
    new .csv of business information.

    Businesses may be listed more than once but their product and/or ownership
    informatino may be different
    """
    def __init__(self):
        pass
