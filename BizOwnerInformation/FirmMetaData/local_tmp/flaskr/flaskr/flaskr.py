# all the imports
import os
import sqlite3
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
api_submission_roles = set(['CEO/Owner',
                            'Employee'])
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

def validate_submission(form_items):
    ret = False
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
                # ... then we add the mturker id's that she refers too while aslo updating thier
                # referred_by lists with her
                for text_id in text_id_referred_to:
                    # upsert the id and add/create it's referred_by list; note .id, critical for constructing
                    # a reference
                    MTurkInfo.objects(mturk_id=text_id).update_one(upsert=True,
                                                                        set__mturk_id=text_id,
                                                                        push__referred_by = mturk_id_referred_by.id)

                    mturk_id_referred_to = MTurkInfo.objects.get(mturk_id=text_id)
                    # update the mturker's referred_to list too
                    MTurkInfo.objects(mturk_id=my_mturk_id).update_one(upsert=True,
                                                                            push__referred_to = mturk_id_referred_to.id)



            # ... so now we've updated the social network and everyboyd has references and refers to others
            # we will use this information when someone finds business information and pay out to their
            # social network

    business = {'name':'Bailey Park Thriftway', 'region':'Battle Creek, MI'}
    award = {'amt':4.56, 'max_referral_amt':2.13}

    app.logger.info('\t at HIT endpoint')

    return render_template('HIT.html', business=business, award=award)

@app.route('/info', methods=['POST'])
def info():
    # When a MTurker submits info, yay!
    return


# tutorial route code; remove when done
@app.route('/')
def show_entries():
    #db = get_db()
    #cur = db.execute('select title, text from entries order by id desc')
    #entries = cur.fetchall()
    #entries = ['My Title', 'Some text here', 1]


    app.logger.info('\t in Show Entries')

    business = {'name':'Bailey Park Thriftway', 'region':'Battle Creek, MI'}
    award = {'amt':4.56, 'max_referral_amt':2.13}

    return render_template('show_entries.html', business=business, award=award)

# re work to post on submit for referral endpoint
# dupe, do for firm meta data submission
@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    flash('New entry was successfully posted, yar!')
    return redirect(url_for('show_entries'))

# on data submission, kick off long running process of mturk verification (or just accept?)
# on accept set some kind of flag, write out something?

# Get users MTurk ID (they paste it)
# if already exist, then tell them no thanks
# else give screen
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))
