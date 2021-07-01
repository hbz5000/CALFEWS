from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize(['calfews_src/*.pyx', 'main_cy.pyx'], 
                                annotate=False,language_level=3, include_path=['./', 'calfews_src/'])
)
