import os
import re

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.rst")) as f:
    README = f.read()
with open(os.path.join(here, "CHANGES.txt")) as f:
    CHANGES = f.read()

REQUIREMENTS = [
    "repoze.sendmail==4.3",
    "sqlalchemy>=1.0.12",
    "ziggurat_foundations>=0.8.2",
    "celery>=4.0",
    "redis>=2.10.3",
    "psycopg2-binary>=2.6",
    "paginate>=0.5.6",
    "paginate_sqlalchemy>=0.3.1",
    "email-validator>=1.0"
    "pyramid>=1.7",
    "pyramid_jinja2>=2.6.2",
    "pyramid_debugtoolbar",
    "pyramid_tm>=0.12.1",
    "pyramid_mailer>=0.14.1",
    "pyramid_redis_sessions>=1.0.1",
    "transaction>=1.6.1",
    "zope.sqlalchemy>=0.7.7",
    "waitress>=1.0a1",
    "dogpile.cache>=0.6.1",
    "marshmallow>=2.8.0",
    "wtforms>=2.1",
    "alembic>=0.8.6",
    "authomatic==0.1.0.post1",
    "six>=1.10.0",
    "cryptography>=1.4",
    "webhelpers2_grid>=0.1",
    "requests>=2.10.0",
    "pyramid_apispec>=0.3.2",
]


REQUIREMENTS_DEV = [
    "black",
    "pytest<5.0.0",
    "pytest-cov",
    "webtest",
    "mock",
    "babel",
    "lingua",
    "tox",
    "pyramid_ipython",
    "ipython",
]

setup(
    name="testscaffold",
    version="0.0",
    description="testscaffold",
    long_description=README + "\n\n" + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author="",
    author_email="",
    url="",
    keywords="web wsgi bfg pylons pyramid",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    extras_require={"dev": REQUIREMENTS_DEV, "lint": ["black"]},
    install_requires=REQUIREMENTS,
    entry_points={
        "paste.app_factory": ["main = testscaffold:main"],
        "console_scripts": [
            "migrate_testscaffold_db = testscaffold.scripts.migratedb:main",
            "initialize_testscaffold_db = testscaffold.scripts.initializedb:main",
        ],
    },
)
