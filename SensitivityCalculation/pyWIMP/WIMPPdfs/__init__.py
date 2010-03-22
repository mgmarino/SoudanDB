import ROOT
import os
import glob
import re
import exceptions

delineate = '*************************************'
for i in range(len(__name__)):
    delineate += '*'
print
print delineate
print "Performing Initialization of module: %s" % __name__

directory = os.path.dirname( os.path.realpath( __file__ ) )
if not hasattr(ROOT, "MGMWimpTimeFunction"):
    if not ROOT.gSystem.Load("%s/../lib/libMGDOWIMPPdfs" % directory) == 0:
        raise exceptions.ImportError, """

libMGDOWIMPPdfs does not exist, please run './configure && make' in the base 
directory of SensitivityCalculation

                                      """
    ROOT.gROOT.ProcessLine(".include \"%s\"" % directory)

#now export the items
all_object_files = glob.glob("%s/*.hh" % directory)
all_object_files = [os.path.basename(file) for file in all_object_files]
all_object_files = [re.match("(.*)\.hh", file).group(1) for file in all_object_files]

module_dict =  globals()
for export_obj in all_object_files:
    module_dict[export_obj] = getattr(ROOT, export_obj)
print 'Done.'
print delineate
print
