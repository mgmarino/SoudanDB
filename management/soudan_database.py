import couchdb
from couchdb import schema
from datetime import datetime
from dateutil import tz
import ROOT
import glob
import re
import cPickle as pickle
import types
from ..utilities import utilities
import os
import sys
from . import ServerSingleton, CurrentDBSingleton
from ..views import view_database_updated_docs
from calendar import timegm
from time import strptime
from couchdb_extensions import MappingField

local_server = True
#local_server = False



def SoudanServer():
    return ServerSingleton.get_server()

def get_current_db_module():
    return CurrentDBSingleton.get_current_db_module()

majorana_db_server = 'http://127.0.0.1:5984'
if local_server:  
    majorana_db_username = ''
    majorana_db_password = ''
else:
    majorana_db_username = 'ewi'
    majorana_db_password = 'darkma11er'

"""
    Following are a set of fields set up primarily 
    for the soudan database.  They encapsulate a 
    certain type of data
"""

class RunTimeDict(schema.DictField):
    """
      Field to save the run time for a particular run
    """
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(
          run_seconds = schema.FloatField(),
          run_seconds_error = schema.FloatField()))

class BaselineDict(schema.DictField):
    """
      Field to save the the average baseline, and different
      fit parameters.
    """
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(
          average_fit_constant=schema.FloatField(),
          average_fit_rms=schema.FloatField(),
          chi_square=schema.FloatField(),
          ndf=schema.FloatField(),
          first_ten_percent_fit_constant=schema.FloatField(),
          first_ten_percent_fit_constant_rms=schema.FloatField(),
          last_ten_percent_fit_constant=schema.FloatField(),
          last_ten_percent_fit_constant_rms=schema.FloatField()))

class CutsDictClass(schema.DictField):
    """
      Depracated, will remove.  Serves to encapsulate a cut dictionary
      describing the cut and how to generate.  This is redundant with
      MapReduce functionality and so will not be used in the future.
    """
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(
          description_of_cut=schema.TextField(),
          string_of_cut=schema.TextField(),
          passes_cut=schema.BooleanField(),
          version_of_cut=schema.TextField() ))

class TriggerDataClass(schema.DictField):
    """
      This class keeps track of trigger efficiency data, in
      particular an erfc function that may be fit to the 
      efficiency data.  
    """
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(
          scaling = schema.FloatField(),
          scaling_err = schema.FloatField(),
          offset = schema.FloatField(),
          offset_err = schema.FloatField(),
          erfc_function = schema.TextField() ))

class PulserDataClass(schema.DictField):
    """
      Keep track of pulser width and mean information.  Can store 
      pulser parameters with this class.
    """
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(
          sigma = schema.FloatField(),
          sigma_err = schema.FloatField(),
          mean = schema.FloatField(),
          mean_err = schema.FloatField()  ))


class QADataClass(schema.DictField):
    """
      Quality assurance class, allowing flags to be set based
      upon whether or not QA has been run.
    """
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(
          qa_check_process_has_been_run = schema.BooleanField(),
          qa_accept_run = schema.BooleanField()))

class NoiseCheckClass(schema.DictField):
    """
      Encapsulates data for a run, saving how many events in 
      a particular region exists.  This is useful for cutting
      noisy runs.
    """
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(
          events_in_region_point6_to_10_keV=schema.IntegerField(),
          events_in_region_10_to_70_keV=schema.IntegerField() ))

class DataFileClass(schema.DictField):
    """
      Base class for all data files:
        lfn: logical file name, where the file exists in relation
          to a relative base
        pfn: physical file name, where the file exists.
        md5hash: a hash calculated to protect against file
          corruption
        last_mod_time: last modification time of the file.
    """
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(
          pfn = schema.TextField(),
          lfn = schema.TextField(),
          md5hash = schema.TextField(),
          last_mod_time = MGDateTimeFieldClass()  ))

class AllReducedDataFilesClass(schema.DictField):
    """
      Encapsulate reduced data file classes.  This class is 
      depracated.  Instead use MappingField in couchdb_extensions.
    """

    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(
          pulser = DataFileClass(),
          low_energy = DataFileClass(),
          high_energy = DataFileClass() ))

class MGPickleFieldClass(schema.Field):
    """
      Schema for pickled fields, allowing trivial storage of python
      objects within the database.
    """
    def _to_python(self, value):
        # Be smart, try to return a function if includes 'def' 
        temp = pickle.loads(str(value))
        if type(temp) is types.StringType: 
            match_it = re.search('def .*', temp, re.DOTALL) 
            if match_it:
                try:
                    code_obj = compile(temp, '<string>', 'exec') 
                    return types.FunctionType(code_obj.co_consts[0], globals())
                except (SyntaxError,TypeError): 
                    pass
        return temp

    def _to_json(self, value):
        return unicode(pickle.dumps(value,0))

class CutDataClass(schema.Schema):
    """
      This class encapsulates data for a cut, returning the efficiency
      of the cut.  Derived classes are in charge of defining the 
      actual cut values, this class defines the efficiency of the cut.  
      All pickled data members should be TF1s or at least objects
      that respond to 'Eval'.
    """
    efficiency_function = MGPickleFieldClass()


class RiseTimeDataClass(CutDataClass):
    """
      Rise-time data cut class.  
      high_energy_function: Class that responds to Eval (TGraph/TF1) to
        give an upper limit on rise-time in the high-energy range.
      low_energy_function: Class that responds to Eval (TGraph/TF1) to
        give an upper limit on rise-time in the low-energy range.
    """
    high_energy_function =  MGPickleFieldClass()
    low_energy_function =  MGPickleFieldClass() 

class MicrophonicsCutDataClass(CutDataClass):
    """
      Microphonics data cut class.  
      upper_cut: Class that responds to Eval (TGraph/TF1) to
        give an upper limit on ratios. 
      lower_cut: Class that responds to Eval (TGraph/TF1) to
        give an lower limit on chan0/chan1 ratio. 
    """
    upper_cut =  MGPickleFieldClass() 
    lower_cut =  MGPickleFieldClass() 



class MGDateTimeFieldClass(schema.DateTimeField):
    """
    Assumes that we obtain a datetime object
    Encapsulates a datatime object (i.e. one created using 
    datetime module to create)
    """   
    def _to_json(self, value):
        # Convert to UTC
        if value.tzinfo:
            value = value.astimezone(tz.tzutc()).replace(tzinfo=None)
        return schema.DateTimeField._to_json(self, value)
    def _to_python_localtime(self, value):
        if isinstance(value, basestring):
            try:
                value = value.split('.', 1)[0] # strip out microseconds
                value = value.rstrip('Z') # remove timezone separator
                timestamp = timegm(strptime(value, '%Y-%m-%dT%H:%M:%S'))
                value = datetime.utcfromtimestamp(timestamp)
            except ValueError, e:
                raise ValueError('Invalid ISO date/time %r' % value)
        return value
       

class MGDocumentClass(schema.Document):
    """ 
      Base class of all documents in the soudan database
      Includes utility function:

        update_schema 

      Use this to update a document held in the database to a new
      schema.  In other words, if the defined schema changes in the 
      code and the respective object in the database needs to 
      be updated, call the following like:

      >>> server = couchdb.Server('http://localhost:5984/'
      >>> db = server['list-tests']

      >>> class TestDoc(MGDocument):
      ...    title = schema.TextField()

      >>> class TestDocAlt(MGDocument):
      ...    title = schema.TextField()
      ...        test_list = schema.ListField(schema.TextField())

      >>> t1 = TestDoc()
      >>> t1.title = 'Test'
      >>> t1.store(db)

      >>> t2 = TestDocAlt.load(db, t1.id)
      >>> t2 = TestDocAlt.update_schema(t2)
      >>> t2.store(db) # persist back to db

    """ 

    @classmethod
    def update_schema(cls, old_doc):
        """
        Run this on an old document to generate the correct 
        schema and update to the correct rev and ids.
        """
        new_doc = cls()
        def update_field(field, old_field):
            try:
                for sub_field in field:
                    if sub_field in old_field:
                        try:
                            update_field(field[sub_field], old_field[sub_field])
                        except TypeError:
                            #print sub_field, type(sub_field)
                            field[sub_field] = old_field[sub_field]
            except TypeError: 
                # this field is non-iterable, return to the calling function 
                raise

        update_field(new_doc, old_doc)
        #for field in new_doc:
        #    if field in old_doc:
        #        new_doc[field] = old_doc[field]

        if '_rev' in old_doc:
            new_doc['_rev'] = old_doc['_rev']
        new_doc._set_id(old_doc._get_id())
        return new_doc

class PickleDocumentClass(MGDocumentClass):
    """
      Document class for a single pickle field, depracated.
    """
    pickle = MGPickleFieldClass() 

class TriggerEfficiencyDocumentClass(MGDocumentClass):
    """ 
      Class encapsulating trigger efficiency cuts
    """
    trigger_efficiency = MappingField( schema.DictField(CutDataClass ))

class MicrophonicsCutDocumentClass(MGDocumentClass):
    """ 
      Class encapsulating microphonics cuts
      Uses MappingField to allow dynamic update of key names in 
      all_rise_cuts.  That is, we can define a key naming different
      cuts.
    """
    all_micro_cuts = MappingField( schema.DictField(MicrophonicsCutDataClass ))


class RiseTimeCutDocumentClass(MGDocumentClass):
    """ 
      Class encapsulating rise-time cuts
      Uses MappingField to allow dynamic update of key names in 
      all_rise_cuts.  That is, we can define a key naming different
      cuts.
    """
    all_rise_cuts = MappingField( schema.DictField(RiseTimeDataClass ))


class UpdateDatabaseDocumentClass(MGDocumentClass):
    """
      Class saving when the database has been updated.
      This is useful to save information for external
      daemons so that they know when the last
      update has been run.  FixME, use changes feed of
      couchdb instead of this.
    """
    time_of_last_update = MGDateTimeFieldClass() 

class EnergyCalibrationDocumentClass(MGDocumentClass):
    """
      Class saving information regarding energy
      calibration.  For example, the energy_calibration
      field should store an object which can return
      an energy value.  In practice one could 
      decide that this is a ROOT object, like TF1
      or TGraph, but this is up to the implementation.
      
    """
    energy_calibration = MGPickleFieldClass()

class SoudanServerClass(couchdb.client.Server):
    
    """
      Workhorse class of the entire SoudanDB python package,
      this class encapsulates a database object.
      Generally, classes will derive from this class to instantiate
      their own database.

    """
    def __init__(self, db_name, cuts_db_name, run_doc_class, cut_doc_class=None):
        couchdb.client.Server.__init__(self, majorana_db_server)
        self.resource.http.add_credentials(majorana_db_username, majorana_db_password)
        if db_name not in self:
            self.soudan_db = self.create(db_name)
            print "Database created."
        else:
            self.soudan_db = self[db_name]

        if cuts_db_name:
            if cuts_db_name not in self:
                self.soudan_cuts_db = self.create(cuts_db_name)
                print "Cuts database created."
            else:
                self.soudan_cuts_db = self[cuts_db_name]
        
        """
        if not cut_doc_class:
            self.cut_doc_class = TriggerEfficiencyDocumentClass
        else:
            self.cut_doc_class = cut_doc_class
        """
        self.run_doc_class = run_doc_class
        
    def get_lfn_path(self):   
        return os.path.expanduser("~/Dropbox/SoudanData")

    def get_last_update_run(self):
        """
          Returns the last time the database was updated.
          Ret: datetime.datetime object
          Useful for caching when polling daemons last ran. 
        """
        view = view_database_updated_docs.get_view_class()
        all_docs = view(self.get_database()) 
        if not all_docs or len(all_docs) == 0:
            self.set_last_update_run(datetime.fromtimestamp(0))
            return self.get_last_update_run()
        for id in all_docs:
            doc = UpdateDatabaseDocumentClass.load(self.get_database(), 
                                                   str(id.id)) 
            return doc.time_of_last_update
        return 0

    def set_last_update_run(self, time):
        """
          Sets the time the database was updated.
          time: datetime.datetime object
          Useful for caching when polling daemons last ran. 
        """
        view = view_database_updated_docs.get_view_class()
        all_docs = view(self.get_database()) 
        update_doc = None
        if not all_docs or len(all_docs) == 0:
            update_doc = UpdateDatabaseDocumentClass()
            update_doc._set_id("update_doc")
        else:
            for id in all_docs:
                update_doc = UpdateDatabaseDocumentClass.load(
                             self.get_database(), str(id.id)) 
                break
        update_doc.time_of_last_update = time
        update_doc.store(self.get_database())


    def get_database(self):
        """
          Returns db primitive
        """
        return self.soudan_db

    def get_cuts_database(self):
        """
          Returns cut db primitive, deprecated
        """
        return self.soudan_cuts_db

    def run_is_in_database(self, run_number):
        try:
            int_run_number = int(run_number)
        except ValueError:
            return False
        return (str(run_number) in self.get_database())

    """
      Cut document access functions, these are
      deprecated and will be removed.
    """
    def cut_is_in_database(self, cut):
        return (str(cut) in self.get_cuts_database())

    def get_cut(self, cut):
        if self.cut_is_in_database(cut): 
            return self.cut_doc_class.load(self.get_cuts_database(), str(cut))
        return None

    def insert_cut(self, cut_doc):
        if cut_doc:
            cut_doc.store(self.get_cuts_database())


    """
      Pickle access functions.  Deprecated, these should
      exist in derived classes.
    """
    def pickle_is_in_database(self, pickle):
        """
          Checks for a pickle document in the 
          database.  This is assuming that the
          pickle has a string name.  Will be removed.
        """
        # Searches for a pickle in the database
        if self.run_is_in_database(pickle):
            # This means it's a run document
            return False
        return (str(pickle) in self.get_database())

    def get_pickle(self, pickle):
        if self.pickle_is_in_database(pickle): 
            return PickleDocumentClass.load(self.get_database(), str(pickle))
        return None

    def insert_pickle(self, pickle_doc, pickle_name=None):
        if pickle_name:
            try:
                temp = int(pickle_name)
                print "%i is an integer, please choose a string" % pickle_name
                return
            except ValueError:
                pickle_doc._set_id(str(pickle_name)) 
                pass
        pickle_doc.store(self.get_database())

    def get_doc(self, doc):
        return self.get_run(doc)

    def get_run(self, run_number):
        if self.run_is_in_database(run_number): 
            return self.run_doc_class.load(self.get_database(), str(run_number))
        return None

    def delete_run(self, run_number):
        if self.run_is_in_database(run_number): 
            self.get_database().__delitem__(str(run_number))
            
    def insert_rundoc(self, rundoc):
        if rundoc:
            rundoc.store(self.get_database())
    
    """
      Get Rise-time cut doc for the server
    """
    def get_rise_time_cut_doc(self):
        doc_name = "risetimedoc" 
        if doc_name not in self.get_database():  
            doc = RiseTimeCutDocumentClass()
            doc._set_id(doc_name)
            self.insert_rundoc(doc)
        return RiseTimeCutDocumentClass.load(
                     self.get_database(), doc_name)

    """
      Get microphonics cut doc for the server
    """
    def get_microphonics_cut_doc(self):
        doc_name = "microdoc" 
        if doc_name not in self.get_database():  
            doc = MicrophonicsCutDocumentClass()
            doc._set_id(doc_name)
            self.insert_rundoc(doc)
        return MicrophonicsCutDocumentClass.load(
                     self.get_database(), doc_name)

    """
      Get trigger efficiency for the server
    """
    def get_trigger_efficiency_doc(self):
        doc_name = "triggerdoc" 
        if doc_name not in self.get_database():  
            doc = TriggerEfficiencyDocumentClass()
            doc._set_id(doc_name)
            self.insert_rundoc(doc)
        return TriggerEfficiencyDocumentClass.load(
                     self.get_database(), doc_name)

    """
      Get energy calibration for the server 
    """
    def get_energy_calibration_doc(self):
        doc_name = "energy_calibration_doc" 
        if doc_name not in self.get_database():  
            doc = EnergyCalibrationDocumentClass()
            doc._set_id(doc_name)
            self.insert_rundoc(doc)
        return EnergyCalibrationDocumentClass.load(
                     self.get_database(), doc_name)


    def insert_doc(self, doc):
        doc.store(self.get_database())

    def check_and_update_run(self, run_number):
        """
          Checks to see if a run exists, and updates it if the modification time
          of the local files is more recent than the modification time of the 
          database document.  Deprecated, uses views and update database now. 
        """
        run_doc = self.get_run(run_number)
        if not run_doc:
            run_doc = self.run_doc_class.build_document(run_number)
            if run_doc:
                print "Run %i is not in database, inserting..." % int(run_number)
                self.insert_rundoc(run_doc)


