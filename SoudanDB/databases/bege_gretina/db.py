#!/bin/env python
from SoudanDB.management.soudan_database import RunTimeDict, DataFileClass, \
     QADataClass, MGDateTimeFieldClass, CutsDictClass, MGDocumentClass,\
     SoudanServerClass 
from couchdb import schema
import os
import re
import glob
from views import view_all_accepted_runs

# Constants to access database
soudan_db_name = 'soudan_bege_gretina_db'
soudan_cuts_db_name = 'soudan_bege_gretina_cuts_db'
data_file_directories=[ '/mnt/raid/data/Soudan/Data/BeGeGretina/tier0',\
                        '/mnt/raid/data/Soudan/Data/BeGeGretina/tier1',\
                        '/mnt/raid/data/Soudan/Data/BeGeGretina/tier2'] 

class BeGeGretinaDB(SoudanServerClass):
    def __init__(self):
        SoudanServerClass.__init__(self, soudan_db_name, 
                              soudan_cuts_db_name,
                              RunDocumentClass)
    def get_run_docs(self):
        temp_list = list(self.get_database())
        return temp_list

    def get_accepted_runs(self):
        view = view_all_accepted_runs.get_view_class()
        return view(self.get_database())


def update_database():
    #First get all the files together 
    import re
    def get_run_number_from_raw_data_file(datafile_name):
        return re.match(".*BegeFinal_Run([0-9]*)\Z", datafile_name).group(1)

    print "Checking normal runs"
    temp = os.listdir(data_file_directories[0])
    temp = [line for line in temp if re.match(".*BegeFinal_Run[0-9]*\Z", line)]
    number_list = []
    for file in temp:
        number_list.append(get_run_number_from_raw_data_file(file))

    number_list.sort()
    soudan_db = BeGeGretinaDB()
    for num in number_list:
        soudan_db.check_and_update_run(num)

class RunDocumentClass(MGDocumentClass):
    raw_data_file_tier_0 = DataFileClass() 
    root_data_file_tier_1 = DataFileClass() 
    output_data_file_tier_2 =  DataFileClass()
    livetime = RunTimeDict() 
    local_time_of_start_of_run = MGDateTimeFieldClass()
    modification_time = schema.DateTimeField()
    quality_assurance = QADataClass() 
    all_cuts = schema.ListField(CutsDictClass())
    number_of_entries_in_tier1_root_tree = schema.LongField()
    run_settings = schema.ListField(schema.TextField())

    @classmethod
    def build_document(cls, run_number):
        return_class = RunDocumentClass()
        return_class._set_id(str(run_number))

        run_number = str(run_number)
        # assigning file names
        # tier 0, raw data
        afile = glob.glob("%s/*BegeFinal_Run%s" % (data_file_directories[0], run_number))
        if len(afile) != 1: 
            print "Error: ", afile
            return
        return_class.raw_data_file_tier_0.pfn = \
          "%s/%s" % (data_file_directories[0], os.path.basename(afile[0]))
        return_class.raw_data_file_tier_0.lfn = \
          "%s/%s" % (os.path.basename(data_file_directories[0]),  
                     os.path.basename(return_class.raw_data_file_tier_0.pfn))

        # tier 1, rootified data
        return_class.root_data_file_tier_1.pfn = \
          "%s/greta_MarkIV_run%s.root" % (data_file_directories[1],  
           str(run_number) )
        return_class.root_data_file_tier_1.lfn = \
          "%s/%s" % (os.path.basename(data_file_directories[1]),  
                     os.path.basename(return_class.root_data_file_tier_1.pfn))

        # tier 2, processed data
        return_class.output_data_file_tier_2.pfn = \
          "%s/output_run%s.root" % (data_file_directories[2],  
           str(run_number) )
        return_class.output_data_file_tier_2.lfn = \
          "%s/%s" % (os.path.basename(data_file_directories[2]),  
                     os.path.basename(return_class.output_data_file_tier_2.pfn))

        return return_class


if __name__ == '__main__':
    # Means we are called as a script
    update_database()
