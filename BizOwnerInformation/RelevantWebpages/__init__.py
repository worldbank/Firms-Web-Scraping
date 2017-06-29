from utils import vw_api
from zipfile import ZipFile
import os
import json

class ExtractRelevantWebpages(object):
    def __init__(self,
                 in_zip_file='database.output.relevance_data.zip',
                 out_zip_file='relevance.output.zip'):
        """
        RelevantWebpages accepts the output of a run of Stage 1
        and queries the WebsiteRelevance classifier for each
        website. Websites deemed as relevant are outputted to disk
        for follow on product extraction, business owner information
        extraction
        """

        with ZipFile(in_zip_file,'r') as zf:
            loads = zf.read(zf.namelist()[0])
            json_data = json.loads(loads.decode("utf-8"))

        api = vw_api.VWAPI(host='localhost') # Docker container is visible in the host OS

        features = [website['meta']['features'] for website in json_data]
        responses = api.get_bulk_responses(features)
        # something of a hack but we threshold the response as < 0 for relevant websites ... would be different if
        # we used logistic regression I believe
        relevant_webpages = [website for website, response in zip(json_data, responses) if response.prediction < 0]

        api.vw.close()
        del api

        with open('relevance.output.tmp' ,'w+') as tmp:
            json.dump(relevant_webpages, tmp)

        with ZipFile(out_zip_file,'w') as zf:
            zf.write('relevance.output.tmp')

        os.remove('relevance.output.tmp')
