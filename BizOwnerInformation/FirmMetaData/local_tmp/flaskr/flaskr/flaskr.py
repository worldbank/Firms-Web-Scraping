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

class MTurkInfo(db.Document):
    mturk_id = db.StringField(max_length=max_length)
    has_referred = db.BinaryField(False)
    has_submitted = db.BinaryField(False)
    verification_status = db.IntField(api_verification_status['NO VERIFICATION']) # interface with api_verification_status

class Referral(db.Document):
    referred = db.ReferenceField(MTurkInfo)
    referrees = db.ListField(db.ReferenceField(MTurkInfo)) # ordered list of referrees

class Submission(db.Document):
    mturk_id = db.ReferenceField(MTurkInfo)
    business_info = db.DictField() # all(key in api_submission_roles for key in business_info[:N])

def validate_submission(form_items):
    ret = False
    return ret

def validate_referral(form_items):
    ret = False
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
        # validate the input, upsert it and update any referall chains
        # as neccesary
        app.logger.info(request.form)
        if validate_referral(request.form):
            app.logger.info('Stuff is legit')

            for key, mturk_id in request.form.items():
                if not '' == mturk_id:
                    app.logger.info( (key, mturk_id) )
                    # see: https://stackoverflow.com/questions/24738617/mongoengine-update-oneupsert-vs-deprecated-get-or-create
                    MTurkInfo.objects(mturk_id=mturk_id).update_one(upsert=True,
                                                                    set__mturk_id=mturk_id)

            referrer = request.form['My MTurkID']

    business = {'name':'Bailey Park Thriftway', 'region':'Battle Creek, MI'}
    award = {'amt':4.56, 'max_referral_amt':2.13}

    app.logger.info('\t at HIT endpoint')

    return render_template('HIT.html', business=business, award=award)



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
