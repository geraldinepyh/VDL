'''Build a Dash app showing a patient's medical records, and that of a comparative/similar
population, with filters that can be applied to shrink/grow the population.

This module builds a Dash app using some Mindlinc data to show a patient's CGI and 
medication records over time, of all visits related to a specific disease. This patient's
records are also used to generate a 'comparative population' of patients, who also
suffer from the same disease. Some filters can be applied, such as Age, Sex, Race, Comorbidities, 
that will filter out patients from this 'comparative population' and adjust the metrics accordingly.
It shows the CGI response of this population over time, as well as their general reaction 
(CGI levels/improvement) to frequently prescribed medications. 
This is based on the VisualDecisionLinc paper, which was also based on the Mindlinc data. 
It may be used to aid in Clinical Decision Support and advise clinicians on what drugs could be
prescribed to patients based on how other patients like them have responded to the same drug.

Before you Begin
================

Ensure that you have the ``db.json`` file set up to connect to the Mindlinc database.

Details of Operation
====================

Data Source: Mindlinc database (mindlincnew, version rwe_version1_1). See ``getData.json`` 
under ``config/modules`` for the exact configurations. 

The VDl module has three main python files:
-  ``getData.py`` extracts the data from Mindlinc to the local data folder. 
    Speficically, extracts visits related to a specified disease category.
- ``utils.py`` has some helper functions to generate plots, extract and process 
    data from the raw_data that has been extracted locally.
-  ``app.py`` runs the Dash app. It contains layout specicifcations and callback functions.

There are also some notebooks in the ``src`` folder which have been used in the testing phase:
-  ``Queries.ipynb`` was used to generate the queries used in the ``utils.py``folder.
    It also contains some code used to clean the data extracted from ``getData``. (optional) 
-  ``PatientSampler.ipynb`` was used to try and reduce the number of patients being 
    processed, and thus speed up the app. This would create another set of the local data files,
    containing the data of patients which might be more interesting to look at on the dashboard.
- ``Filtering.ipynb`` was used to test the ``add_filter()`` logic in the ``app.py`` ``patientQ`` class.


Results
=======

After running the ``getData.py`` module, you should check that the data has been saved into the
``data`` folder under ``/raw_data`` or ``/intermediate``. 
After running the ``app.py``, you can open up a browser window to the port that the app is 
running on and view/interact with it there. If you were to make changes to the py file, 
you would need to reload the app again in order for the changes to take effect. 

Specifications:
===============

Specifications for running the module is described below. Note that all the json files
unless otherwise specified will be placed in the folder ``config`` in the main project
folder.


Specifications for ``modules.json``
-----------------------------------

Make sure that the ``execute`` statement within the modules file is set to True. 
This should apply for ``getData`` the first time you are running it to extract the data, 
and for all subsequent times of running the app on ``app.py``.

.. code-block:: python
    :emphasize-lines: 3

    "moduleName" : "getData",
    "path"       : "modules/VDL/getData.py",
    "execute"    : true,
    "description": "",
    "owner"      : ""


'''