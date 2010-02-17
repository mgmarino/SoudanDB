import couchdb
from couchdb import schema
from datetime import datetime
from dateutil import tz
import ROOT
import glob
import re
import pickle
import types
from ..utilities import utilities
import os
import sys
from . import ServerSingleton, CurrentDBSingleton
from ..views import view_database_updated_docs
from calendar import timegm
from time import strptime

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

class RunTimeDict(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(
          run_seconds = schema.FloatField(),
          run_seconds_error = schema.FloatField()))

class BaselineDict(schema.DictField):
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
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(
          description_of_cut=schema.TextField(),
          string_of_cut=schema.TextField(),
          passes_cut=schema.BooleanField(),
          version_of_cut=schema.TextField() ))

class TriggerDataClass(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(
          scaling = schema.FloatField(),
          scaling_err = schema.FloatField(),
          offset = schema.FloatField(),
          offset_err = schema.FloatField(),
          erfc_function = schema.TextField() ))

class PulserDataClass(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(
          sigma = schema.FloatField(),
          sigma_err = schema.FloatField(),
          mean = schema.FloatField(),
          mean_err = schema.FloatField()  ))


class QADataClass(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(
          qa_check_process_has_been_run = schema.BooleanField(),
          qa_accept_run = schema.BooleanField()))

class NoiseCheckClass(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(
          events_in_region_point6_to_10_keV=schema.IntegerField(),
          events_in_region_10_to_70_keV=schema.IntegerField() ))

class DataFileClass(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(
          pfn = schema.TextField(),
          lfn = schema.TextField(),
          md5hash = schema.TextField(),
          last_mod_time = MGDateTimeFieldClass()  ))

class AllReducedDataFilesClass(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(
          pulser = DataFileClass(),
          low_energy = DataFileClass(),
          high_energy = DataFileClass() ))

class MGPickleFieldClass(schema.Field):
    """Schema for pickled fields."""
    def _to_python(self, value):
        # Be smart, try to return a function if includes 'def' 
        temp = pickle.loads(value)
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

class MGDateTimeFieldClass(schema.DateTimeField):
    """
    Assumes that we obtain a datetime object
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
                            print sub_field, type(sub_field)
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
    pickle = MGPickleFieldClass() 

class CutDocumentClass(MGDocumentClass):
    string_of_cut = schema.TextField()
    verbose_description_of_cut = schema.TextField()

    def generate_cut_for_run_doc(self, run_doc):
        # setting up the dynamic running later.
        import math
        import ROOT
        for item in run_doc:
            if hasattr(run_doc, item):
                exec("%s = run_doc.%s" % (str(item), str(item)))
        _id = run_doc._get_id()
        bool_of_cut = eval(self.string_of_cut)
        return bool_of_cut
 
class UpdateDatabaseDocumentClass(MGDocumentClass):
    time_of_last_update = MGDateTimeFieldClass() 

class SoudanServerClass(couchdb.client.Server):
    
    def __init__(self, db_name, cuts_db_name, run_doc_class, cut_doc_class=None):
        couchdb.client.Server.__init__(self, majorana_db_server)
        self.resource.http.add_credentials(majorana_db_username, majorana_db_password)
        if db_name not in self:
            self.soudan_db = self.create(db_name)
            print "Database created."
        else:
            self.soudan_db = self[db_name]
            print "Database found."

        if cuts_db_name:
            if cuts_db_name not in self:
                self.soudan_cuts_db = self.create(cuts_db_name)
                print "Cuts database created."
            else:
                self.soudan_cuts_db = self[cuts_db_name]
                print "Cuts database found."
        
        if not cut_doc_class:
            self.cut_doc_class = CutDocumentClass
        else:
            self.cut_doc_class = cut_doc_class
        self.run_doc_class = run_doc_class
        
    def get_lfn_path(self):   
        return os.path.expanduser("~/Dropbox/SoudanData")

    def get_last_update_run(self):
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
        return self.soudan_db

    def get_cuts_database(self):
        return self.soudan_cuts_db

    def pickle_is_in_database(self, pickle):
        # Searches for a pickle in the database
        if self.run_is_in_database(pickle):
            # This means it's a run document
            return False
        return (str(pickle) in self.get_database())

    def run_is_in_database(self, run_number):
        try:
            int_run_number = int(run_number)
        except ValueError:
            return False
        return (str(run_number) in self.get_database())

    def cut_is_in_database(self, cut):
        return (str(cut) in self.get_cuts_database())

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

    def get_cut(self, cut):
        if self.cut_is_in_database(cut): 
            return self.cut_doc_class.load(self.get_cuts_database(), str(cut))
        return None

    def insert_cut(self, cut_doc):
        if cut_doc:
            cut_doc.store(self.get_cuts_database())

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
    
    def check_and_update_run(self, run_number):
        """
          Checks to see if a run exists, and updates it if the modification time
          of the local files is more recent than the modification time of the 
          database document. 
        """
        run_doc = self.get_run(run_number)
        if not run_doc:
            run_doc = self.run_doc_class.build_document(run_number)
            if run_doc:
                print "Run %i is not in database, inserting..." % int(run_number)
                self.insert_rundoc(run_doc)


