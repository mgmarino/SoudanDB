from SoudanDB.management.soudan_database import RunTimeDict, DataFileClass, \
     AllReducedDataFilesClass, BaselineDict, QADataClass, TriggerDataClass,\
     NoiseCheckClass, MGDateTimeFieldClass, PulserDataClass, CutsDictClass,\
     SoudanServerClass, MGDocumentClass 
from views import view_all_accepted_runs, view_livetime_all_accepted_runs,\
                  view_files_of_accepted_runs, view_starttime_all_accepted_runs
from couchdb import schema
import os
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

class PPCTwoDB(SoudanServerClass):
    def __init__(self):
        SoudanServerClass.__init__(self, soudan_db_name, 
                              soudan_cuts_db_name,
                              RunDocumentClass)
    def check_and_update_run(self, run_number, check_only = False, force = False):
        """
          Checks to see if a run exists, and updates it if the modification time
          of the local files is more recent than the modification time of the 
          database document. 
        """
        run_doc = self.get_run(run_number)
        if not run_doc:
            if check_only: return True
            run_doc = self.run_doc_class.build_document(run_number)
            if run_doc:
                print "Run %i is not in database, inserting..." % run_number
                self.insert_rundoc(run_doc)
        else:
            if (force or 
                (run_doc.modification_time < 
                 run_doc.get_most_recent_modification_time())):
                if check_only: return True
                print "Run %i is modified, updating..." % run_number
                run_doc = run_doc.build_document(run_number, run_doc)
                self.insert_rundoc(run_doc) 
    
        return False
    def get_accepted_runs(self):
        view = view_all_accepted_runs.get_view_class()
        return view(self.get_database())

    def get_lfn_path(self):   
        return os.path.expanduser("~/Dropbox/SoudanData/PPC2")

    def get_starttime_of_runs(self):
        view = view_starttime_all_accepted_runs.get_view_class()
        return view(self.get_database())

    def get_livetime_of_runs(self):
        view = view_livetime_all_accepted_runs.get_view_class()
        return view(self.get_database())

    def get_files_of_runs(self):
        view = view_files_of_accepted_runs.get_view_class()
        return view(self.get_database())


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
    def build_document(cls, run_number, return_class=None):
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
            temp = glob.glob("%s/*%s%i%s" % 
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

        if not find_file_for_db(return_class.raw_data_file_tier_0, 
                         raw_data_file_directory, run_number,
                         raw_data_file_stem): return None
       
        if not find_file_for_db(return_class.root_data_file_tier_1, 
                         orcaroot_data_file_directory, run_number,
                         'run', '.root'): return None

        if not find_file_for_db(return_class.output_data_file_tier_2, 
                         output_data_file_directory, run_number,
                         'output', '.root'): return None
    
        for directory in reduced_file_dir_list:
            type_of_directory = os.path.basename(directory)
            if not hasattr(return_class.output_data_file_tier_3, 
              type_of_directory):
                print "Attribute: %s not found." % type_of_directory
                continue
            file_dictionary = return_class.output_data_file_tier_3.\
              __getattribute__(type_of_directory)

            if not find_file_for_db(file_dictionary, 
                         directory, run_number,
                         'output', 'reduce*.root'):
                return None
            file_dictionary.lfn = "%s/%s" % (type_of_directory, 
              os.path.basename(file_dictionary.pfn))

        return_class.modification_time = return_class.get_most_recent_modification_time()
        return_class.quality_assurance.qa_check_process_has_been_run = False
        return_class.quality_assurance.qa_accept_run = False
        return return_class
   
 
def update_database():
    #First get all the files together 
    def get_run_number_from_orcaroot_data_file(datafile_name):
        search_pattern = re.compile(".*?%s([1-9][0-9]*)" % orcaroot_data_file_stem)
        return int(search_pattern.search(datafile_name).group(1))

    ROOT.gROOT.SetBatch()
    temp = glob.glob("%s/*%s*" % 
      (orcaroot_data_file_directory, orcaroot_data_file_stem) ) 
    number_list = []
    for file in temp:
        number_list.append(get_run_number_from_orcaroot_data_file(file))

    number_list.sort()
    soudan_db = PPCTwoDB()
    cpuNUM = utilities.detectCPUs()
    scratch_list = number_list[:]
    for num in scratch_list:
        result = soudan_db.check_and_update_run(num, True)
        if not result:
            # Run does not need to be updated
            number_list.remove(num)

    def chunks(l, n):
        """ Yield successive n-sized chunks from l.
        """
        for i in xrange(0, len(l), n):
            yield l[i:i+n]
    cpu_list = list(chunks(number_list, len(number_list)/cpuNUM +1))
    wait_pids = []
    for cpu in cpu_list:
        pid = os.fork()
        if pid:
            #parent
            wait_pids.append(pid)
        else:
            new_db = SoudanServer()
            for num in cpu:
                print num
                new_db.check_and_update_run(num, False, True)
            sys.exit(0)
    for pid in wait_pids:
        os.waitpid(-1, 0)


