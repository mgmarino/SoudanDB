import couchdb
from couchdb import schema
from datetime import datetime
from dateutil import tz
import  views.view_all_accepted_runs as view_all_accepted_runs
import  views.view_all_rejected_runs as view_all_rejected_runs
import ROOT
import glob
import re

# Constants to access database
#majorana_db_server = 'http://majorana.npl.washington.edu:5984'
majorana_db_server = 'http://127.0.0.1:5984'
majorana_db_username = 'ewi'
majorana_db_password = 'darkma11er'
soudan_db_name = 'soudan_db'
soudan_cuts_db_name = 'soudan_cuts_db'
raw_data_file_directory='/mnt/auto/data3EWI/SoudanData'
raw_data_file_stem='LongRunCounting'
orcaroot_data_file_directory='/mnt/raid/data/Soudan/Data'
orcaroot_data_file_stem='greta_MarkIV_run'
output_data_file_directory='%s/tmp' % orcaroot_data_file_directory
reduced_size_data_file_high_energy_directory = '%s/high_energy' %\
  output_data_file_directory
reduced_size_data_file_low_energy_directory = '%s/low_energy' % \
  output_data_file_directory
reduced_size_data_file_pulser_directory = '%s/pulser' % \
  output_data_file_directory


def update_database():
    #First get all the files together 
    def get_run_number_from_orcaroot_data_file(datafile_name):
        search_pattern = re.compile(".*?%s([1-9][0-9]*)" % orcaroot_data_file_stem)
        return int(search_pattern.search(datafile_name).group(1))

    ROOT.gROOT.SetBatch()
    temp = glob.glob("%s/*%s*" % \
      (orcaroot_data_file_directory, orcaroot_data_file_stem) ) 
    number_list = []
    for file in temp:
        number_list.append(get_run_number_from_orcaroot_data_file(file))

    number_list.sort()
    soudan_db = SoudanServer()
    for num in number_list:
        soudan_db.check_and_update_run(num)

class RunTimeDict(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(\
          run_seconds = schema.FloatField(),\
          run_seconds_error = schema.FloatField()))

class BaselineDict(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(\
          average_fit_constant=schema.FloatField(),\
          average_fit_rms=schema.FloatField(),\
          chi_square=schema.FloatField(),\
          ndf=schema.FloatField(),\
          first_ten_percent_fit_constant=schema.FloatField(),\
          first_ten_percent_fit_constant_rms=schema.FloatField(),\
          last_ten_percent_fit_constant=schema.FloatField(),\
          last_ten_percent_fit_constant_rms=schema.FloatField()))

class CutsDictClass(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(\
          description_of_cut=schema.TextField(),\
          string_of_cut=schema.TextField(),\
          passes_cut=schema.BooleanField(),\
          version_of_cut=schema.TextField() ))

class TriggerDataClass(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(\
          scaling = schema.FloatField(),\
          scaling_err = schema.FloatField(),\
          offset = schema.FloatField(),\
          offset_err = schema.FloatField(),\
          erfc_function = schema.TextField() ))

class PulserDataClass(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(\
          sigma = schema.FloatField(),\
          sigma_err = schema.FloatField(),\
          mean = schema.FloatField(),\
          mean_err = schema.FloatField()  ))


class QADataClass(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(\
          qa_check_process_has_been_run = schema.BooleanField(),\
          qa_accept_run = schema.BooleanField()))

class NoiseCheckClass(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(\
          events_in_region_point6_to_10_keV=schema.IntegerField(),\
          events_in_region_10_to_70_keV=schema.IntegerField() ))

class DataFileClass(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(\
          pfn = schema.TextField(),\
          lfn = schema.TextField(),\
          md5hash = schema.TextField() ))

class AllReducedDataFilesClass(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(\
          pulser = DataFileClass(),\
          low_energy = DataFileClass(),\
          high_energy = DataFileClass() ))

class MGDateTimeFieldClass(schema.DateTimeField):
    """
    Assumes that we obtain a datetime object
    """   
    def _to_json(self, value):
        # Convert to UTC
        if value.tzinfo:
            value = value.astimezone(tz.tzutc()).replace(tzinfo=None)
        return schema.DateTimeField._to_json(self, value)
       

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
 

class RunDocumentClass(MGDocumentClass):
    raw_data_file_tier_0 = DataFileClass() 
    root_data_file_tier_1 = DataFileClass() 
    output_data_file_tier_2 =  DataFileClass()
    output_data_file_tier_3 = AllReducedDataFilesClass()
    baseline_dict = BaselineDict()
    livetime = RunTimeDict() 
    modification_time = schema.DateTimeField()
    quality_assurance = QADataClass() 
    trigger_efficiency = TriggerDataClass()
    noise_check = NoiseCheckClass()
    all_cuts = schema.ListField(CutsDictClass())
    time_of_start_of_run = MGDateTimeFieldClass()
    number_of_entries_in_tier1_root_tree = schema.LongField()
    pulser_data = PulserDataClass()

    def get_most_recent_modification_time(self):
        import os.path, datetime
        def check_dict_for_pfn(adict, list):
            try:
                dict_items = adict.items()
                for key, value in dict_items:
                    if key == 'pfn': 
                        list.append(value)
                    else:
                        check_dict_for_pfn(value, list)
            except AttributeError:
                pass
        files_to_check = []
        check_dict_for_pfn(self, files_to_check)
        most_recent_time = 0
        for file in files_to_check:
            if os.path.getmtime(file) > most_recent_time:
                most_recent_time = os.path.getmtime(file)
 
        return datetime.datetime.fromtimestamp(most_recent_time)

    @classmethod
    def build_runDocumentClass(cls, run_number, return_class=None):
        import os.path

        def get_hash_of_file(file, block_size=2**20):
            import hashlib
            md5 = hashlib.md5()
            open_file = open(file, 'rb')
            while True:
                data = open_file.read(block_size)
                if not data:
                    break
                md5.update(data)
            open_file.close()
            return md5.hexdigest()

        def find_file_for_db(db_entry, directory, run_number, first_stem, second_stem=''): 
            import glob
            temp = glob.glob("%s/*%s%i%s" % \
              (directory, first_stem, run_number, second_stem) ) 
            if len(temp) != 1:
                return None
            db_entry.pfn = temp[0]
            db_entry.md5hash = get_hash_of_file(temp[0])
            db_entry.lfn = os.path.basename(temp[0])
            return db_entry
 
        reduced_file_dir_list = []
        reduced_file_dir_list.append(reduced_size_data_file_high_energy_directory)
        reduced_file_dir_list.append(reduced_size_data_file_low_energy_directory)
        reduced_file_dir_list.append(reduced_size_data_file_pulser_directory)
    
        if not return_class:
            return_class = RunDocumentClass()
            return_class._set_id(str(run_number))

        if not find_file_for_db(return_class.raw_data_file_tier_0, \
                         raw_data_file_directory, run_number,\
                         raw_data_file_stem): return None
       
        if not find_file_for_db(return_class.root_data_file_tier_1, \
                         orcaroot_data_file_directory, run_number,\
                         'run', '.root'): return None

        if not find_file_for_db(return_class.output_data_file_tier_2, \
                         output_data_file_directory, run_number,\
                         'output', '.root'): return None
    
        for directory in reduced_file_dir_list:
            type_of_directory = os.path.basename(directory)
            if not hasattr(return_class.output_data_file_tier_3, \
              type_of_directory):
                print "Attribute: %s not found." % type_of_directory
                continue
            file_dictionary = return_class.output_data_file_tier_3.\
              __getattribute__(type_of_directory)

            if not find_file_for_db(file_dictionary, \
                         directory, run_number,\
                         'output', 'reduce*.root'):
                return None
            file_dictionary.lfn = "%s/%s" % (type_of_directory, \
              os.path.basename(file_dictionary.pfn))

        return_class.modification_time = return_class.get_most_recent_modification_time()
        return_class.quality_assurance.qa_check_process_has_been_run = False
        return_class.quality_assurance.qa_accept_run = False
        return return_class
   
 
class SoudanServer(couchdb.client.Server):
    def __init__(self):
        couchdb.client.Server.__init__(self, majorana_db_server)
        self.resource.http.add_credentials(majorana_db_username, majorana_db_password)
        if soudan_db_name not in self:
            self.soudan_db = self.create(soudan_db_name)
            print "Database created."
        else:
            self.soudan_db = self[soudan_db_name]
            print "Database found."

        if soudan_cuts_db_name not in self:
            self.soudan_cuts_db = self.create(soudan_cuts_db_name)
            print "Cuts database created."
        else:
            self.soudan_cuts_db = self[soudan_cuts_db_name]
            print "Cuts database found."
   
    def get_database(self):
        return self.soudan_db

    def get_cuts_database(self):
        return self.soudan_cuts_db

    def run_is_in_database(self, run_number):
        try:
            int_run_number = int(run_number)
        except ValueError:
            return False
        return (str(run_number) in self.get_database())

    def cut_is_in_database(self, cut):
        return (str(cut) in self.get_cuts_database())

    def get_cut(self, cut):
        if self.cut_is_in_database(cut): 
            return CutDocumentClass.load(self.get_cuts_database(), str(cut))
        else:
            return None

    def insert_cut(self, cut_doc):
        if cut_doc:
            cut_doc.store(self.get_cuts_database())

    def get_run(self, run_number):
        if self.run_is_in_database(run_number): 
            return RunDocumentClass.load(self.get_database(), str(run_number))
        else:
            return None

    def delete_run(self, run_number):
        if self.run_is_in_database(run_number): 
            self.get_database().__delitem__(str(run_number))
            
    def insert_rundoc(self, rundoc):
        if rundoc:
            rundoc.store(self.get_database())
    
    def get_rejected_runs(self):
        view = view_all_rejected_runs.get_view_class()
        return view(self.get_database())

    def get_accepted_runs(self):
        view = view_all_accepted_runs.get_view_class()
        return view(self.get_database())

    def check_and_update_run(self, run_number):
        """
          Checks to see if a run exists, and updates it if the modification time
          of the local files is more recent than the modification time of the 
          database document. 
        """
        run_doc = self.get_run(run_number)
        if not run_doc:
            run_doc = RunDocumentClass.build_runDocumentClass(run_number)
            if run_doc:
                print "Run %i is not in database, inserting..." % run_number
                self.insert_rundoc(run_doc)
        else:
            if run_doc.modification_time < run_doc.get_most_recent_modification_time():
                print "Run %i is modified, updating..." % run_number
                run_doc = self.build_runDocumentClass(run_number, run_doc)
                self.insert_rundoc(run_doc) 
    
