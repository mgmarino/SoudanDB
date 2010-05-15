def processSpectrum(doc_list, input_directory='..', type='pulser',\
                    hist_name='hist', \
		    energy_scale='*1', cuts='', use_baseline_cut=False, opposite_baseline_cut=False):
    import re
    from array import array
    from ROOT import TFile, TH1D, TTree, TObject, TEventList, gROOT
    from soudan_database import SoudanServer
    
    number_of_sigma = 3
    hist = TH1D(hist_name, hist_name, 8192, 0, eval("8192%s" % energy_scale))
    hist.GetXaxis().SetTitle("Energy (keV)")
    hist.GetYaxis().SetTitle("Counts")

    server = SoudanServer()

    for run_number in doc_list:
        doc = server.get_run(run_number.id) 
        try:
            string_of_file_name = eval('doc.output_data_file_tier_3.%s.lfn' % type)
        except:
            print "Incorrect type"
            continue
        print doc._get_id()
        open_file = TFile("%s/%s" % (input_directory,string_of_file_name))
        main_tree = open_file.Get("wf_analysis") 
        coinc_tree = open_file.Get("event_coincidence") 
        main_tree.AddFriend(coinc_tree)
        real_cuts = cuts
        if use_baseline_cut:
            not_string = ""
            if opposite_baseline_cut:
                not_string = "!"
            additional_cuts = " && %s(abs(fitConstant-%f) <= %f*%f) " % \
                 (not_string, doc.baseline_dict.average_fit_constant,\
                   number_of_sigma, doc.baseline_dict.average_fit_rms)
            real_cuts += additional_cuts 
        gROOT.cd()
        main_tree.Draw("-energy%s>> +%s" % (energy_scale, hist.GetName()),real_cuts, "goff")
        open_file.Close()

    return hist

def getLowEnergySpectrum(file_list, input_directory='..'):
    return processSpectrum(file_list, input_directory=input_directory, type='low_energy',\
                    hist_name='LowEnergySpectrum', energy_scale='*0.0125749', \
                    cuts=' !(event_coincidence.coincidence & 0x280)  \
                    && lastInhibitTimeDif > 1e5', \
                    use_baseline_cut = True)


def getHighEnergySpectrum(file_list, input_directory='..'):
    return processSpectrum(file_list, input_directory=input_directory, type='high_energy', \
                    hist_name='HighEnergySpectrum', energy_scale='*0.602356 -0.303815 ', \
                    cuts=' !(event_coincidence.coincidence & 0x280)  \
                    && lastInhibitTimeDif > 1e5')



