# all the imports
import os
import sqlite3
from bson.objectid import ObjectId # to handle ObjectId weirdness w MongoEngine
from flask import Flask, request, session, g, redirect, url_for, abort, \
             render_template, flash
from flask_mongoengine import MongoEngine

# import massivecrowdsourcing # how best to handle API style/side functions? See T's webapp?

app = Flask(__name__) # create the application instance :)
app.config.from_object(__name__) # load config from this file , flaskr.py

# Load default config and override config from an environment variable
#    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
app.config.update(dict(
    SECRET_KEY='development key',
    MONGODB_SETTINGS={'DB':'flaskr_db'},
    TESTING=True,
))

app.config.from_envvar('FLASKR_SETTINGS', silent=True)
app.config.from_envvar('HIT_MAX_AWARD', silent=True)

db = MongoEngine(app)

# Schema
max_length = 21
api_verification_status = {'NO VERIFICATION': 1,
                           'PENDING VERIFICATION':2,
                           'PASSED VERIFICATION':3,
                           'FAILED VERIFICATION':4}# use slots instead?
api_submission_roles = set(['CEO_Owner',
                            'Employee',
                            'Manager'])
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

class PartipicatedBusinessRegion(db.Document):
    businessregion = db.DictField() # 'business/region' dictionary into mturk ids

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
    ret = True
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

@app.route('/HIT', methods=['POST', 'GET'])
@app.route('/hit', methods=['POST', 'GET'])
def hit():
    error = None
    app.logger.info('\t request.method: '+request.method)

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

    # Other wise it's their first time here
    business = {'name':'Bailey Park Thriftway', 'region':'Battle Creek, MI'}
    award = {'amt':4.56, 'max_referral_amt':2.13}

    app.logger.info('\t at HIT endpoint')

    return render_template('HIT.html', business=business, award=award)

@app.route('/submit_info', methods=['POST'])
def submit_info():
    # When a MTurker submits info, yay!
    app.logger.info('\t User has some info to submit!')

    app.logger.info(request.form)

    if validate_submission(request.form):
        app.logger.info('Stuff is legit')
        app.logger.info(list(request.form.keys()))

        ceo = request.form['CEO_Owner']
        manager = request.form['Manager']
        employee = request.form['Employee']
        mturk_id = request.form['My MTurk ID']

        app.logger.info((ceo, manager, employee))

        mturk_obj = MTurkInfo.objects.get(mturk_id=mturk_id)
        app.logger.info((mturk_obj, mturk_obj.id))

        referral_path = list(breadthfirstsearch(mturk_obj))
        app.logger.info(referral_path) # verify, pay out too

    return render_template('thank_you.html')

@app.route('/thank_you', methods=['POST'])
def thank_you():
    app.logger.info('\t Thanks!')

    return render_template('thank_you.html')
