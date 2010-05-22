from SoudanDB.management.soudan_database import DataFileClass, \
     QADataClass, MGDateTimeFieldClass, CutsDictClass, MGDocumentClass,\
     SoudanServerClass, MGPickleFieldClass 
from couchdb import schema
from views import view_all_accepted_runs
from views import view_all_rejected_runs
from views import view_all_accepted_runs_ln_fills
from views import view_all_LN_fills
from views import view_all_runs
from views import view_all_runs_modification
from views import view_first_efficiency_runs
from views import view_scanning_pulser_runs
import os
import re
import glob
from datetime import datetime
from SoudanDB.management.soudan_database import MGDateTimeFieldClass
import time

soudan_db_name = 'soudan_bege_db'
soudan_cuts_db_name = 'soudan_bege_cuts_db'
data_file_directories=[ '/mnt/raid/data/Soudan/Data/BeGe/tier0',\
                        '/mnt/raid/data/Soudan/Data/BeGe/tier1',\
                        '/mnt/raid/data/Soudan/Data/BeGe/tier2'] 
ln_fill_directory = '/mnt/raid/data/Soudan/Data/BeGe/transfer'

class BeGeJCDB(SoudanServerClass):
    def __init__(self):
        SoudanServerClass.__init__(self, soudan_db_name, 
                              None,
                              RunDocumentClass)
    def get_run_docs(self):
        view = view_all_runs.get_view_class()
        return view(self.get_database())

    def get_accepted_runs(self):
        view = view_all_accepted_runs.get_view_class()
        return view(self.get_database())

    def get_accepted_runs_ln_fills(self):
        view = view_all_accepted_runs_ln_fills.get_view_class()
        return view(self.get_database())

    def get_efficiency_runs(self):
        view = view_first_efficiency_runs.get_view_class()
        return view(self.get_database())

    def get_rejected_runs(self):
        view = view_all_rejected_runs.get_view_class()
        return view(self.get_database())

    def get_scanning_pulser_runs(self):
        view = view_scanning_pulser_runs.get_view_class()
        return view(self.get_database())

    def get_ln_docs(self):
        view = view_all_LN_fills.get_view_class()
        return view(self.get_database())

    def get_doc(self, doc):
        adoc = self.get_run(doc)
        if not adoc:
            adoc = self.get_ln(doc)
        return adoc

    """
      Get pulse cut for the server 
    """
    def get_pulse_cut_doc(self):
        doc_name = "pulse_cut_doc" 
        if doc_name not in self.get_database():  
            doc = PulseCutClass()
            doc._set_id(doc_name)
            self.insert_rundoc(doc)
        return PulseCutClass.load(
                     self.get_database(), doc_name)


    def get_run(self, run_number):
        temp_list = [id.id for id in self.get_run_docs()]
        if str(run_number) in temp_list: 
            return self.run_doc_class.load(self.get_database(), str(run_number))
        return None

    def get_ln(self, lnrun):
        temp_list = [id.id for id in self.get_ln_docs()]
        if str(lnrun) in temp_list: 
            return LNFillClass.load(self.get_database(), str(lnrun))
        return None

    def check_and_update_lnfill(self, lnfilltime):
        """
          Checks to see if a ln fill exists, and updates it if the modification time
          of the local files is more recent than the modification time of the 
          database document. 
        """
        run_doc = self.get_ln(lnfilltime)
        if not run_doc:
            run_doc = LNFillClass.build_document(lnfilltime)
            if run_doc:
                print "LN %s is not in database, inserting..." % lnfilltime
                self.insert_rundoc(run_doc)

    def get_lfn_path(self):   
        return os.path.expanduser("~/Dropbox/SoudanData/BeGe")


def update_database():
    #First get all the files together 
    import re
    def get_run_number_from_raw_data_file(datafile_name):
        temp_num = int("20" + datafile_name) 
        return temp_num

    soudan_db = BeGeJCDB()
    start_run_time = datetime.now() 
    last_run_time = soudan_db.get_last_update_run() 
    print "Starting:", start_run_time
    print "Checking for new docs from last run time:",  last_run_time
    print "Checking normal runs"
    temp = os.listdir(data_file_directories[0])
    temp = [line for line in temp if re.match("[0-9]*\Z", line)]
    temp = [line for line in temp 
             if (datetime.fromtimestamp(os.path.getmtime("%s/%s" % 
                   (data_file_directories[0], line))) >= last_run_time or
                 datetime.fromtimestamp(os.path.getctime("%s/%s" % 
                   (data_file_directories[0], line))) >= last_run_time)]                   
    number_list = []
    for file in temp:
        number_list.append(get_run_number_from_raw_data_file(file))

    number_list.sort()
    for num in number_list:
        soudan_db.check_and_update_run(num)

    # Now check the other documents to make sure they are updated
    # This is kinda dirty and it shouldn't generally happen.
    view = view_all_runs_modification.get_view_class()
    list = view(soudan_db.get_database())

    field = MGDateTimeFieldClass()
    number_list = []
    for i in list:
        allfiles = i.value
        for afile, timestamp in allfiles:
            if not afile or not timestamp: continue
            this_mod_time = os.path.getmtime(afile)
            timestamp = time.mktime(field._to_python(timestamp).timetuple())
            if this_mod_time != timestamp:
                print afile, this_mod_time, timestamp
                number_list.append(i.id)
                break
    for num in number_list:
        soudan_db.delete_run(num)
        soudan_db.check_and_update_run(num)

    print "Checking ln runs"
    temp = os.listdir(ln_fill_directory)
    temp = [line for line in temp if not re.match(".*png", line)]
    temp = [line for line in temp 
             if (datetime.fromtimestamp(os.path.getmtime("%s/%s" % 
                   (ln_fill_directory, line))) >= last_run_time or
                 datetime.fromtimestamp(os.path.getctime("%s/%s" % 
                   (ln_fill_directory, line))) >= last_run_time)]                   
    temp = ["20"+line for line in temp]
    for fill in temp:
        soudan_db.check_and_update_lnfill(fill)
    soudan_db.set_last_update_run(start_run_time)

class RunTimeDict(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(\
          run_milliseconds = schema.FloatField(),\
          run_milliseconds_error = schema.FloatField()))

class PulserDataClass(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(\
          sigma = schema.ListField(schema.FloatField()),\
          sigma_err = schema.ListField(schema.FloatField()),\
          mean = schema.ListField(schema.FloatField()),\
          mean_err = schema.ListField(schema.FloatField())  ))

class AllPulserDataClass(schema.DictField):
    def __init__(self):
        schema.DictField.__init__(self, schema.Schema.build(\
          chan_0 = PulserDataClass(),\
          chan_1 = PulserDataClass(),\
          chan_2 = PulserDataClass() ))


class RunDocumentClass(MGDocumentClass):
    raw_data_file_tier_0 = DataFileClass() 
    root_data_file_tier_1 = DataFileClass() 
    output_data_file_tier_2 =  DataFileClass()
    settings_data_file =  DataFileClass()
    livetime = RunTimeDict() 
    local_time_of_start_of_run = MGDateTimeFieldClass()
    modification_time = schema.DateTimeField()
    quality_assurance = QADataClass() 
    all_cuts = schema.ListField(CutsDictClass())
    number_of_entries_in_tier1_root_tree = schema.LongField()
    run_settings = schema.ListField(schema.TextField())
    pulser_on_set = schema.ListField( schema.ListField( \
      schema.IntegerField() ))
    pulser_off_set = schema.ListField( schema.ListField( \
      schema.IntegerField() ))
    pulser_run_characteristics = AllPulserDataClass() 

    @classmethod
    def build_document(cls, run_number):
        return_class = RunDocumentClass()
        return_class._set_id(str(run_number))

        run_number = str(run_number)
        run_number = run_number[2:]
        # assigning file names
        # tier 0, raw data
        return_class.raw_data_file_tier_0.pfn = \
          "%s/%s" % (data_file_directories[0], str(run_number))
        return_class.raw_data_file_tier_0.lfn = \
          "%s/%s" % (os.path.basename(data_file_directories[0]), \
                     os.path.basename(return_class.raw_data_file_tier_0.pfn))

        return_class.settings_data_file.pfn = \
          return_class.raw_data_file_tier_0.pfn + "_settings" 
        return_class.settings_data_file.lfn = \
          return_class.raw_data_file_tier_0.lfn + "_settings" 

        # tier 1, rootified data
        return_class.root_data_file_tier_1.pfn = \
          "%s/%s" % (data_file_directories[1], \
           str(run_number) + "_rootified.root")
        return_class.root_data_file_tier_1.lfn = \
          "%s/%s" % (os.path.basename(data_file_directories[1]), \
                     os.path.basename(return_class.root_data_file_tier_1.pfn))

        # tier 2, processed data
        return_class.output_data_file_tier_2.pfn = \
          "%s/%s" % (data_file_directories[2], \
           str(run_number) + "_output.root")
        return_class.output_data_file_tier_2.lfn = \
          "%s/%s" % (os.path.basename(data_file_directories[2]), \
                     os.path.basename(return_class.output_data_file_tier_2.pfn))

        return return_class

class LNFillClass(MGDocumentClass):
    ln_data_file = DataFileClass() 
    ln_plot_file = DataFileClass() 
    time_of_start_of_fill = MGDateTimeFieldClass()
    fill_duration = schema.IntegerField() 

    @classmethod
    def build_document(cls, time_of_fill):
        return_class = LNFillClass()
        return_class._set_id(str(time_of_fill))

        return_class.time_of_start_of_fill = datetime(\
          int(time_of_fill[0:4]), int(time_of_fill[4:6]), \
          int(time_of_fill[6:8]), int(time_of_fill[8:10]),\
          int(time_of_fill[10:12]), int(time_of_fill[12:14]))

        time_of_fill = str(time_of_fill)[2:]
        # assigning file names
        # tier 0, ln_data_file
        return_class.ln_data_file.pfn = \
          "%s/%s" % (ln_fill_directory, time_of_fill)
        return_class.ln_data_file.lfn = \
          "%s/%s" % (os.path.basename(ln_fill_directory), \
                     os.path.basename(return_class.ln_data_file.pfn))

        # tier 1, png file 
        return_class.ln_plot_file.pfn = \
          "%s/%s" % (ln_fill_directory, \
           time_of_fill + ".png")
        return_class.ln_plot_file.lfn = \
          "%s/%s" % (os.path.basename(ln_fill_directory), \
                     os.path.basename(return_class.ln_plot_file.pfn))

        return return_class

        

class PulseCutClass(MGDocumentClass):
    """
      Class which encapsulates the information of generating
      a cut on aspects of the pulse.
    """
    pulse_cut = MGPickleFieldClass()
