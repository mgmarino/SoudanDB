#!/usr/local/bin/python
from management.soudan_database import SoudanServer
from ROOT import TH2D, TFile, TObject
import sys
def analyze_peak_vs_max_min(outputfile='temp.root'):

    channels_to_analyze = {0 : ("*0.0125749", "low_energy", 80), \
                           8 : ("*0.602356 -0.303815", "high_energy", 2800)}
    histograms = {}

    server = SoudanServer()
    file_list = server.get_accepted_runs()
    
    hist_2d = None
    file_to_output = TFile(outputfile, 'recreate');
    objects_to_write = []

    for id in file_list:
        print id
        rundoc = server.get_run(id.id) 
        real_value = rundoc.baseline_dict.average_fit_constant 
        real_value_rms = rundoc.baseline_dict.average_fit_rms 
        for chan, tmp_tuple in channels_to_analyze.items():
            (energy_scaler, pfn_dir, max_energy) = tmp_tuple
            file_name = eval("rundoc.output_data_file_tier_3.%s.pfn" % pfn_dir)
            open_file = TFile(file_name)
            main_tree = open_file.Get("wf_analysis") 
            coinc_tree = open_file.Get("event_coincidence") 
            main_tree.AddFriend(coinc_tree)
            file_to_output.cd()
            hist_2d = histograms[chan]
            main_tree.Draw("(endRiseTime-startRiseTime)/100:(-energy%s)>> +%s" % \
               (energy_scaler,hist_2d.GetName()), \
               "channel==%i && !(event_coincidence.coincidence & 0x280) && \
                lastInhibitTimeDif > 1e5 && abs(fitConstant-%f) <= 3*%f" % \
               (chan, real_value, real_value_rms), "goff")
            open_file.Close()

    file_to_output.cd()
    for object in objects_to_write:
        object.Write(object.GetName(), TObject.kOverwrite)

    file_to_output.Close()

if __name__ == '__main__':
    file_name = 'temp.root' 
    if (len(sys.argv) > 1): 
        file_name = sys.argv[1]
    print "Outputting to file: ", file_name
    analyze_risetime_vs_energy(file_name)
