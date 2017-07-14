# all the imports
import os
import string
import pandas as pd
from urllib.parse import urlparse
from bson.objectid import ObjectId # to handle ObjectId weirdness w MongoEngine
from flask import session, Response
from flask import Flask, request, session, g, redirect, url_for, abort, \
             render_template, flash
from flask_mongoengine import MongoEngine

# import massivecrowdsourcing # how best to handle API style/side functions?

app = Flask(__name__) # create the application instance :)
app.config.from_object(__name__) # load config from this file , flaskr.py

# Load default config and override config from an environment variable
#    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
app.config.update(dict(
    SECRET_KEY='SECRET KEY 123',
    MONGODB_SETTINGS={'DB':'flaskr_db'},
    TESTING=True,
))

app.config.from_envvar('FLASKR_SETTINGS', silent=True)
app.config['HIT_MAX_AWARD'] = float(os.environ['HIT_MAX_AWARD'])
app.config['INPUT_FILE'] = os.environ['INPUT_FILE']

db = MongoEngine(app)

# Schema
max_length = 21
api_verification_status = {'NO VERIFICATION': 1,
                           'PENDING VERIFICATION':2,
                           'PASSED VERIFICATION':3,
                           'FAILED VERIFICATION':4}# use slots instead?
api_submission_roles = set(['My MTurk ID',
                            'CEO_Owner',
                            'Employee',
                            'Manager',
                            'URL_CEO_Owner',
                            'URL_Employee',
                            'URL_Manager'])# not techincally a role but whatever
api_referral_items = set(['My MTurkID',
                          'MTurk ID 1',
                          'MTurk ID 2',
                          'MTurk ID 3'])
api_collection_names = {'MTurkInfo':'m_turk_info',
                        'Referral':'referral'}

class MTurk(db.Document):
    mturk_id = db.StringField(max_length=max_length)
    has_referred = db.BinaryField(False)
    has_submitted = db.BinaryField(False)
    verification_status = db.IntField(api_verification_status['NO VERIFICATION']) # interface with api_verification_status

class MTurkInfo(db.Document):
    mturk_id = db.StringField(max_length=max_length)

    referred_by = db.ListField(db.ReferenceField(MTurk)) # ordered list of referrees, extended atomically by other mturkers
    referred_to = db.ListField(db.ReferenceField(MTurk)) # ordered list of referrers, set once

    has_submitted = db.BinaryField(False)
    verification_status = db.IntField(api_verification_status['NO VERIFICATION']) # interface with api_verification_status

class SubmittedBusinessRegion(db.Document):
    """
    This is a dynamic collection of business names and their regions, populated by
    the input file given by the path environment variable INPUT_FILE

    It's a dynamic collection because an outside process monitors the collection periodically,
    pushing unverified businesses to MTurk for verification. Businesses with verified good information
    are removed from the collection.

    Those businesses that are verified to have incorrect information are left as is, potentially
    being selected again at random.

    This class assumes only one submission per turker (a MTurker can not submit for multiple HITs)
    """
    submitter_object_id = db.ReferenceField(MTurkInfo) # can calculate referral chain from this

    information = db.DictField() # stores form submission
    business_name = db.StringField()
    region = db.StringField()

class NewBusinessRegion(db.Document):
    """
    A collection of Business, regions, ingested from the input file.
    Acted on by an outside process to remove submited businesses that are verified to be good.
    """
    business_name = db.StringField()
    region = db.StringField()

def url_check(url):
    """
    Adopted from https://stackoverflow.com/questions/7160737/python-how-to-validate-a-url-in-python-malformed-or-not

    This function is kind of weak in that it'll return True for 'http://www.google' (notice no tld)
    url validation can get tricky, i recomend exploring Django url validators or finding a more robust library.

    However, for what it's worth, we do url validation client side, by the HTML5 standard, which is pretty robust
    and this is just a final check. Will not defend against malicious useres submiting urls like `http://www.google`
    but they won't get a bonus anyway because the crowd will validate their submission as bogus.
    """

    min_attr = ('scheme' , 'netloc')
    result = urlparse(url)
    if all([result.scheme, result.netloc]):
        return True
    else:
        return False

def get_doc(obj):
    return MTurkInfo.objects.with_id(ObjectId(obj.id))# don't know why original OId isn't same type?

def breadthfirstsearch(root):
    """
    Adopted after last post of
    http://code.activestate.com/recipes/231503-breadth-first-traversal-of-tree/

    Essentially, we do breadth first search on the social network root provided.
    This constructs the referral chain that we need to pay out to.
    """
    queue = []

    visited = set()

    if not root in visited:
        visited.add(root)
        queue.append(root)

    while len(queue) > 0:
        node = queue.pop(0)
        mturk_id = get_doc(node).mturk_id
        yield mturk_id

        children = get_doc(node)
        if len(children.referred_by) != 0:
            for child in children.referred_by:
                if not child in visited:
                    visited.add(child)
                    queue.append(child)
            yield 'LEVEL'
    return

def validate_submission(form_items):
    ret = False

    # check that keys are as expected
    ret = all(key in api_submission_roles for key in form_items.keys())
    if ret: # ... great, now check that names/urls are as expected


        ret = False
        for label, name in form_items.items():
            if name:
                name = ' '.join(name.split()).strip().split()
                if 'URL_' in label: # is a URL
                    # kinda ugly but we split above, but urls won't any spaces
                    # so we set to first element
                    name = name[0]

                    ret = url_check(name)
                    if not ret:
                        break
                else:
                    # Otherwise we have a human name, want to verify that
                    # get rid of extra spaces w/o regexes wheewww
                    ret = all([token.isalpha() or token in string.punctuation for token in ''.join(name)])
                    if not ret:
                        break

    return ret

def validate_referral(form_items):
    ret = False

    if True: # check that user has not participated in this Business/Regiona
        # look into PartipicatedBusinessRegion
        pass
    # check that keys are as expected
    ret = all(key in api_referral_items for key in form_items.keys())
    if ret: # ... great, check that mturk_ids are all alphanumeric
        ret = all(mturk_id.isalnum() for mturk_id in form_items.values() if not mturk_id == '')
    return ret


# pre populate the business, regions, only adding if new
def push_biz_regions():
    df = pd.read_csv(app.config['INPUT_FILE'], sep='\t')
    # todo: push .csv to NewBusinessRegion collection
    for cols in df.itertuples():
        business_name = cols[1].strip()
        region = cols[2].strip()
        NewBusinessRegion.objects(business_name=business_name).update_one(upsert=True,
                                                                                 business_name=business_name,
                                                                                 region=region)
push_biz_regions()

@app.route('/HIT', methods=['POST', 'GET'])
@app.route('/hit', methods=['POST', 'GET'])
def hit():
    error = None
    app.logger.info('\t request.method: '+request.method)

    # prevent user from visiting more than once (backed by cookie; user could clear cookie)
    if 'visit count' in session:
        session['visit count'] += 1
    else:
        session['visit count'] = 1

    if session['visit count'] > 1:
        # redirect to thank you page, can only do this hit once!
        return render_template('thank_you.html')

    # If POST, then they're submitting referral information, which we handle ...
    if request.method == 'POST':
        app.logger.info(request.form)

        if validate_referral(request.form):
            app.logger.info('Stuff is legit')

            # So, in referral based crowdsourcing, we can view HITs as adding to the
            # social network people directly or indirectly (by referring others) searching for business information
            #
            # Once a node finds business information we need to pay out to its sub network of MTurkers
            # according to the referal scheme.

            # The first then we need to do is some housekeeping: we need to ensure that *every*
            # node referred exists within the network so that we can modify its properities as needed


            # ... first we add the mturker's id so she's in the network
            my_mturk_id = request.form['My MTurkID']
            MTurkInfo.objects(mturk_id=my_mturk_id).update_one(upsert=True,
                                                               set__mturk_id=my_mturk_id)
            mturk_id_referred_by = MTurkInfo.objects.get(mturk_id=my_mturk_id)

            text_id_referred_to = [mturk_id for key, mturk_id in request.form.items() if not mturk_id == my_mturk_id]

            app.logger.info((my_mturk_id, text_id_referred_to))

            # (it is possible that a malicious user could refer to their self, check against that)
            if text_id_referred_to:
                for text_id in text_id_referred_to:
                    if text_id == '':
                        continue

                    # upsert the id and add/create it's referred_by list; note .id, critical for constructing
                    # a reference
                    MTurkInfo.objects(mturk_id=text_id).update_one(upsert=True,
                                                                   set__mturk_id=text_id,
                                                                   push__referred_by = mturk_id_referred_by.id)
                    # then add her referred to list
                    mturk_id_referred_to = MTurkInfo.objects.get(mturk_id=text_id)
                    MTurkInfo.objects(mturk_id=my_mturk_id).update_one(upsert=True,
                                                                       push__referred_to = mturk_id_referred_to.id)

            # ... so now we've updated the social network and everyboyd has references and refers to others
            # we will use this information when someone finds business information and pay out to their
            # social network
        return render_template('thank_you.html')

    # todo: pull from MAX AWARD env variable
    #award = {'amt':0.50, 'max_referral_amt':0.25}
    award = {'amt': app.config['HIT_MAX_AWARD'], 'max_referral_amt':app.config['HIT_MAX_AWARD']/2}


    # Todo: randomly sample from businessregion database
    # Other wise it's their first time here
    random_business = next(NewBusinessRegion._get_collection().aggregate([{'$sample':{'size':1}}]))
    business = {'name': random_business['business_name'],
                'region': random_business['region']}

    # save off what random business, region this turker recieved
    #
    # Cyber security note:
    # note: https://blog.miguelgrinberg.com/post/how-secure-is-the-flask-user-session
    # Impact:
    # The session object can be easily reverse engineered; but this would defintely require a malcious user;
    # such a user would be able to insert any value into the mongodb database for business name/region,
    # allowing them to submit information on easily found businesses and get max payout for minimal effort

    # Risk:
    # This hit is limited to one per MTurker by AWS so the impact could only happen once per hit.
    # What this means is that they could spend the time reverse engineering the hit but is it really worth it
    # for a measly 50 cents? MTurkers only have one MTurk ID.
    #
    # So, for prototype purposes this is okay. The alternative is to use Flask-Session and a server in production
    session['business name'] = business['name']
    session['region'] = business['region']

    # add to session object so that when user submits


    app.logger.info('\t at HIT endpoint')

    return render_template('HIT.html', business=business, award=award)

@app.route('/submit_info', methods=['POST'])
def submit_info():
    # When a MTurker submits info, yay!
    app.logger.info('\t User has some info to submit!')

    app.logger.info(request.form)

    if validate_submission(request.form):
        app.logger.info('Passed Verification!')
        app.logger.info(list(request.form.items()))

        ceo = request.form['CEO_Owner']
        url_ceo = request.form['URL_CEO_Owner']
        manager = request.form['Manager']
        employee = request.form['Employee']
        mturk_id = request.form['My MTurk ID']

        # insert mturk id (upsert so we skip if already exists)
        MTurkInfo.objects(mturk_id=mturk_id).update_one(upsert=True,
                                                        set__mturk_id=mturk_id)
        mturk_obj = MTurkInfo.objects.get(mturk_id=mturk_id)
        app.logger.info((mturk_obj, mturk_obj.id))


        app.logger.info((ceo, manager, employee, url_ceo))

        # generating the referral path could be a time consuming operation
        # defer for now, outside verification process can run this
        # outside process will also intake massivecrowdsourcing too
        #referral_path = list(breadthfirstsearch(mturk_obj))
        #app.logger.info(referral_path) # verify, pay out too

        # Add submission to BizRegion database
        SubmittedBusinessRegion.objects(submitter_object_id=mturk_obj).update_one(upsert=True,
                                                                                  set__submitter_object_id=mturk_obj,
                                                                                  set__information=request.form,
                                                                                  set__business_name=session['business name'],
                                                                                  set__region=session['region'])

        app.logger.info(' after attempt to submit info to SubmittedBusinessRegion collection')

    return render_template('thank_you.html')

@app.route('/thank_you', methods=['POST'])
def thank_you():
    app.logger.info('\t Thanks!')

    return render_template('thank_you.html')
