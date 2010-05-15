#!/bin/env python
import os
import time
import subprocess
import datetime
import re
import imp
from ..views import view_virgin_docs
#from ..views import view_all_runs_modification

environment_vars={'LD_LIBRARY_PATH' : "/home/mgmarino/software/OrcaRoot/lib:/home/mgmarino/software/MaGe/lib:/home/mgmarino/software/MGDO/lib:/home/mgmarino/software/root/root_v5.26.00/lib:/home/mgmarino/software/geant4/geant4.9.1.p02/lib/Linux-g++:/home/mgmarino/software/CLHEP/2.0.3.2/lib",\
                  'PYTHONPATH' : "/home/mgmarino/software/root/root_v5.26.00/lib",\
                  'MGDODIR' : "/home/mgmarino/software/MGDO"}

make_tier1_from_tier0 = "/home/mgmarino/Dropbox/BeGeGretina/rootify_BeGe/rootify_BeGe.py"
make_tier2_from_tier1 = "/home/mgmarino/software/waveformAnalysis/analyzeWFs"

def update_rundoc(rundoc):
    """
    Returns whether or not the rundoc has been updated.
    This list is composed with tuples of the following:
       file_dict,
       program_to_make_next_file
       dest_file
    """
    from SoudanDB.utilities.utilities import get_hash_of_file
    rundoc_was_modified = False
    list_to_check = [ ( rundoc.raw_data_file_tier_0,
                        make_tier1_from_tier0,
                        rundoc.root_data_file_tier_1.pfn ), 
                      ( rundoc.root_data_file_tier_1, 
                        make_tier2_from_tier1,
                        rundoc.output_data_file_tier_2.pfn ), 
                      ( rundoc.output_data_file_tier_2,"", "")]

    FNULL = None#open("/dev/null",'w')
    for dict, program, dest in list_to_check:
        if not os.path.exists(dict.pfn): continue
        if not (dict.last_mod_time and \
          os.path.getmtime(dict.pfn) <= time.mktime(dict.last_mod_time.timetuple())):
            rundoc_was_modified = True
            dict.last_mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(dict.pfn))
            dict.md5hash = get_hash_of_file(dict.pfn)
        if program and (rundoc_was_modified and not os.path.exists(dest)):
            # Only run this if the file doesn't exist.
            # Check to see if is a py script, if so load the module
            basename = os.path.basename(program)
            if re.match(".*\.py\Z", basename):
                print "Using python module %s, executing main(%s, %s) from module" % \
                  (program, dict.pfn, dest) 
                new_module = imp.load_source(basename[0:-3], program)
                if not hasattr(new_module, 'main'):
                    print "Imported module not well constructed, exiting"
                    break
                #new_module.main(dict.pfn, dest)
           
            else:
                print "Running: %s %s %s" % (program, dict.pfn, dest)
                return_value = 0
                #return_value = subprocess.call([program, dict.pfn, dest], \
                #  stdout=FNULL, stderr=FNULL, env=environment_vars) 
                if return_value < 0:
                    # interrupt was called, delete the processed file.
                    print "Interrupted on file %s, removing processed file: %s" % (dict.pfn, dest) 
                    if os.path.exists(dest):
                        os.unlink(dest)
                    break
            rundoc_was_modified = True


    return (rundoc, rundoc_was_modified)

def get_view():
    #return view_all_runs_modification.get_view_class()
    return view_virgin_docs.get_view_class()
