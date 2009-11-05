import ROOT
import os
import glob
import re

delineate = '*************************************'
for i in range(len(__name__)):
    delineate += '*'
print
print delineate
print "Performing Initialization of module: %s" % __name__
print delineate
print

directory = os.path.dirname( os.path.realpath( __file__ ) )
try: 
    temp = ROOT.MGMWimpTimeFunction
except AttributeError:
    ROOT.gSystem.Load("%s/libMGDOWIMPPdfs.so" % directory);
    ROOT.gROOT.ProcessLine(".include \"%s\"" % directory);

#now export the items
all_object_files = glob.glob("%s/*.hh" % directory)
all_object_files = [os.path.basename(file) for file in all_object_files]
all_object_files = [re.match("(.*)\.hh", file).group(1) for file in all_object_files]
for export_obj in all_object_files:
    exec "%s = ROOT.%s" % (export_obj, export_obj)
