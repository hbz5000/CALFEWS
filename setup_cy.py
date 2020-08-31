from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize(['calfews_src_cy/canal_cy.pyx','calfews_src_cy/contract_cy.pyx',
                                'calfews_src_cy/crop_cy.pyx', 'calfews_src_cy/delta_cy.pyx',
                                'calfews_src_cy/district_cy.pyx', 'calfews_src_cy/inputter_cy.pyx',
                                'calfews_src_cy/model_cy.pyx', 'calfews_src_cy/private_cy.pyx',
                                'calfews_src_cy/reservoir_cy.pyx', 'calfews_src_cy/waterbank_cy.pyx',
                                'main_cy.pyx'], 
                                annotate=True,language_level=3, include_path=['./', 'calfews_src_cy/'])
)
