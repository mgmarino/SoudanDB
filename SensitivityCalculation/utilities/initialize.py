import ROOT
import os

def initialize():
    try: 
        temp = ROOT.MGMWimpTimeFunction
    except AttributeError:
        try_path = os.path.realpath( __file__ )
        try_path = os.path.dirname(os.path.dirname( try_path ))
        print "**************************************"
        print "Performing Initialization of module..."
        print "**************************************"
        print
        ROOT.gSystem.Load("%s/lib/libMGDOWIMPPdfs.so" % try_path);
        ROOT.gROOT.ProcessLine(".include \"%s/WIMPPdfs\"" % try_path);
