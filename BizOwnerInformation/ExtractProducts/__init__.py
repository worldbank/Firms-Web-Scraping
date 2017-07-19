"""ExtractProducts/__init__.py

The ExtractProducts class leverages the products oracle to filter
a list of potential products. The list of potential products is output
by the Database class.

note: there is a github issue relating to verifying that the output file
is as expected, since this was an implementation item left aside to work
on more pressing aspects of the system at the time.
"""

from utils import vw_api
from zipfile import ZipFile
import pandas
import os
import json

class ExtractProducts(object):
    """
    Simply extracts products from valid websites.
    Run with
    from BizOwnerInformation.ExtractProducts import ExtractProducts

    myextractedproducts = ExtractProducts()
    """
    def __init__(self,
                 in_relevance_zip_file='relevance.output.zip',
                 in_product_zip_file='database.output.product.zip',
                 out_file='output.csv'):
        """
        ExtractProducts accepts the output of a run of ExtractRelevantWebsites
        and queries the Product classifier for each product in a valid website.
        """
        with ZipFile(in_product_zip_file,'r') as zf:
            loads = zf.read(zf.namelist()[0])
            product_json_data = json.loads(loads.decode("utf-8"))

        with ZipFile(in_relevance_zip_file,'r') as zf:
            loads = zf.read(zf.namelist()[0])
            relevance_json_data = json.loads(loads.decode("utf-8"))

        relevant_websites = set([website['website'] for website in relevance_json_data])
        features = [website['meta']['features'] for website in product_json_data if website['website'] in relevant_websites]

        api = vw_api.VWAPI(host='localhost', task='product classification') # Docker container is visible in the host OS

        responses = api.get_bulk_responses(features)
        # something of a hack but we threshold the response as < 0 for relevant websites ... would be different if
        # we used logistic regression I believe

        # should probably zip() product_json_data as well so that we can capture the
        # business_name, region, etc.
        products = [feature for feature, response in zip(features, responses) if response.prediction < 0]

        api.vw.close()
        del api

        # This is a temporary fix to output data for scraping as implemented
        csv_output.read_csv(output, sep='\t')

        assert len(relevance_json_data) == len(products), "Number of product sets do not match number of relevant websites!"

        # loop through relevant websites, with their products, add to data frame
        rows = []
        for website, product in zip(relevance_json_data, products):
            row_dict = {}
            row_dict.update("Business Name"=website['Business Name'],
                            "Region"=website['Region'],
                            "Associated Products"=product)

            rows.append()

        csv_output.append(pd.DataFrame(rows))

        csv_output.to_csv(output, sep='\t', index=False)

        # done



        #with open('relevance.output.tmp' ,'w+') as tmp:
        #    json.dump(products, tmp)

        # do something with pandas here

        #os.remove('relevance.output.tmp')
