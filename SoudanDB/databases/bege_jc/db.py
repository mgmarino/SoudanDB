#!/bin/env python
from SoudanDB.management.soudan_database import DataFileClass, \
     QADataClass, MGDateTimeFieldClass, CutsDictClass, MGDocumentClass,\
     SoudanServerClass 
from couchdb import schema
import os
import re
import glob

soudan_db_name = 'soudan_bege_db'
soudan_cuts_db_name = 'soudan_bege_cuts_db'
data_file_directories=[ '/mnt/raid/data/Soudan/Data/BeGe/tier0',\
                        '/mnt/raid/data/Soudan/Data/BeGe/tier1',\
                        '/mnt/raid/data/Soudan/Data/BeGe/tier2'] 
ln_fill_directory = '/mnt/raid/data/Soudan/Data/BeGe/transfer'

class BeGeJCDB(SoudanServerClass):
    def __init__(self):
        SoudanServerClass.__init__(self, soudan_db_name, 
                              soudan_cuts_db_name,
                              RunDocumentClass)
    def get_run_docs(self):
        temp_list = list(self.get_database())
        temp_list = [line for line in temp_list if not re.match(".*LN2", line)] 
        return temp_list

    def get_ln_docs(self):
        temp_list = list(self.get_database())
        temp_list = [line for line in temp_list if re.match(".*LN2", line)] 
        return temp_list

    def get_doc(self, doc):
        adoc = self.get_run(doc)
        if not adoc:
            adoc = self.get_ln(doc)
        return adoc

    def get_run(self, run_number):
        if str(run_number) in self.get_run_docs(): 
            return self.run_doc_class.load(self.get_database(), str(run_number))
        return None

    def get_ln(self, lnrun):
        if str(lnrun) in self.get_ln_docs(): 
            return LNFillClass.load(self.get_database(), str(lnrun))
        return None

    def check_and_update_lnfill(self, lnfilltime):
        """
          Checks to see if a ln fill exists, and updates it if the modification time
          of the local files is more recent than the modification time of the 
          database document. 
        """
        run_doc = self.get_run(lnfilltime)
        if not run_doc:
            run_doc = LNFillClass.build_lnDocumentClass(lnfilltime)
            if run_doc:
                print "LN %s is not in database, inserting..." % lnfilltime
                self.insert_rundoc(run_doc)

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

        
def update_database():
    #First get all the files together 
    import re
    def get_run_number_from_raw_data_file(datafile_name):
        temp_num = int("20" + datafile_name) 
        return temp_num

    print "Checking normal runs"
    temp = os.listdir(data_file_directories[0])
    temp = [line for line in temp if re.match("[0-9]*\Z", line)]
    number_list = []
    for file in temp:
        number_list.append(get_run_number_from_raw_data_file(file))

    number_list.sort()
    soudan_db = BeGeJCDB()
    for num in number_list:
        soudan_db.check_and_update_run(num)

    print "Checking ln runs"
    temp = os.listdir(ln_fill_directory)
    temp = ["20"+line for line in temp if not re.match(".*png", line)]
    for fill in temp:
        soudan_db.check_and_update_lnfill(fill)


if __name__ == '__main__':
    # Means we are called as a script
    update_database()
