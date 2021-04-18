import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.rst")) as f:
    README = f.read()
with open(os.path.join(here, "CHANGES.txt")) as f:
    CHANGES = f.read()



setup(
    name="testscaffold",
    version="0.1",
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
    entry_points={
        "paste.app_factory": ["main = testscaffold:main"],
        "console_scripts": [
            "migrate_testscaffold_db = testscaffold.scripts.migratedb:main",
            "initialize_testscaffold_db = testscaffold.scripts.initializedb:main",
        ],
    },
)
