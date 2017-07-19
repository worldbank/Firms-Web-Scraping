"""FirmMetaData/../flaskr

flaskr is the default name for the metadata verification app (it's called flaskr
beacuse some of the work was based off of the standard Flask tutorial)

This webapp can be installed by running ./setup.sh.
This webapp can be run by running ./run.sh. Ensure that the webapp binds
to your desired address and port.

Both shell scripts above have light documentation on where to access the
webapp.

The DW directory under FirmMetaData contains HTML files that provide the visual
GUI for the front end (essentially, the look of the website webapp). It may be
modified as needed.
"""

from setuptools import setup

setup(
    name='flaskr',
    packages=['flaskr'],
    include_package_data=True,
    install_requires=[
        'flask',
        'flask-mongoengine',
        'flask-wtf',
        'gunicorn',
        'pandas',
    ],
)
