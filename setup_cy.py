from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules = cythonize(['calfews_src/canal_cy.pyx','calfews_src/contract_cy.pyx',
                                'calfews_src/crop_cy.pyx', 'calfews_src/delta_cy.pyx',
                                'calfews_src/district_cy.pyx', 'calfews_src/inputter_cy.pyx',
                                'calfews_src/model_cy.pyx', 'calfews_src/private_cy.pyx',
                                'calfews_src/reservoir_cy.pyx', 'calfews_src/waterbank_cy.pyx',
                                'calfews_src/participant_cy.pyx', 'main_cy.pyx'], 
                                annotate=False,language_level=3, include_path=['./', 'calfews_src/'])
)
