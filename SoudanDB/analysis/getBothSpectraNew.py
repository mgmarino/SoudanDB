#!/usr/local/bin/python
import sys
from ROOT import TFile, TH1D, TTree, TObject, TEventList
from soudan_database import SoudanServer

def processSpectrum(pfn_dir, divide_by_number = 1, outputfile='temp.root', \
                    force_overwrite=False, hist_name='hist', \
		    energy_scale='*1', cuts='', use_baseline_cut=False, \
                    opposite_baseline_cut=False):
    tree_name = '%sTree' % hist_name
    server = SoudanServer()
    file_list = server.get_accepted_runs()
    
    number_of_sigma = 2
    mass_of_detector = 0.528 # in kg
    file_to_output = TFile("%s" % outputfile, 'UPDATE')
    tree_in_file = file_to_output.Get(tree_name)
    hist = TH1D(hist_name, hist_name, 8192, 0, eval("8192%s" % energy_scale))
    hist.Rebin(divide_by_number)
    hist.GetXaxis().SetTitle("Energy (keV)")
    hist.GetYaxis().SetTitle("Counts/keV/kg/day")

    total_time = 0
    for id in file_list:
        print id
        rundoc = server.get_run(id.id) 
        file_name = eval("rundoc.output_data_file_tier_3.%s.pfn" % pfn_dir)
        open_file = TFile(file_name)
        main_tree = open_file.Get("wf_analysis") 
        coinc_tree = open_file.Get("event_coincidence") 
        main_tree.AddFriend(coinc_tree)
        real_cuts = cuts
        main_tree.GetEntry(0)
        if use_baseline_cut:
            not_string = ""
            if opposite_baseline_cut:
                not_string = "!"
            additional_cuts = " && %s(abs(fitConstant-%f) <= 3*%f) " % (not_string, \
               rundoc.baseline_dict.average_fit_constant, \
               rundoc.baseline_dict.average_fit_rms)
            real_cuts += additional_cuts 
        file_to_output.cd()
        main_tree.Draw("-energy%s>> +%s" % (energy_scale, hist.GetName()),real_cuts, "goff")
        open_file.Close()
        total_time += rundoc.livetime.run_seconds


    total_time /= (3600.*24.)
    hist.Scale(1./(mass_of_detector*hist.GetBinWidth(1)*total_time))
    file_to_output.cd()
    hist.Write(hist.GetName(), TObject.kOverwrite)
    file_to_output.Close()

def getLowEnergySpectrum(outputfile='temp.root', force_overwrite=False):
    processSpectrum(pfn_dir='low_energy', divide_by_number=4, outputfile=outputfile, \
                    force_overwrite=force_overwrite, \
                    hist_name='LowEnergySpectrum', energy_scale='*0.0125749', \
                    cuts=' channel==0 && !(event_coincidence.coincidence & 0x280)  \
                    && lastInhibitTimeDif > 1e5 && (endRiseTime-startRiseTime)/100 < 0.6', \
                    use_baseline_cut = True)

def getLowEnergySpectrumNoBaseline(outputfile='temp.root', force_overwrite=False):
    processSpectrum(pfn_dir='low_energy', divide_by_number=4, outputfile=outputfile, \
                    force_overwrite=force_overwrite, \
                    hist_name='LowEnergySpectrumNoBaseline', energy_scale='*0.0125749', \
                    cuts=' channel==0 && !(event_coincidence.coincidence & 0x280)  \
                    && lastInhibitTimeDif > 1e5 && (endRiseTime-startRiseTime)/100 < 0.6', \
                    use_baseline_cut = True, opposite_baseline_cut=True)


def getLowEnergySpectrumNoCut(outputfile='temp.root', force_overwrite=False):
    processSpectrum(pfn_dir='low_energy', divide_by_number=4, outputfile=outputfile, \
                    force_overwrite=force_overwrite, \
                    hist_name='LowEnergySpectrumNoCut', energy_scale='*0.0125749', \
                    cuts=' channel==0 && !(event_coincidence.coincidence & 0x280)  \
                    && lastInhibitTimeDif > 1e5', use_baseline_cut=True)

def getLowEnergySpectrumNoCutNoBaseline(outputfile='temp.root', force_overwrite=False):
    processSpectrum(pfn_dir='low_energy', divide_by_number=4, outputfile=outputfile, \
                    force_overwrite=force_overwrite, \
                    hist_name='LowEnergySpectrumNoCutNoBaseline', energy_scale='*0.0125749', \
                    cuts=' channel==0 && !(event_coincidence.coincidence & 0x280)  \
                    && lastInhibitTimeDif > 1e5', use_baseline_cut=True, opposite_baseline_cut=True)


def getHighEnergySpectrum(outputfile='temp.root', force_overwrite=False):
    processSpectrum(pfn_dir='high_energy', divide_by_number=1, outputfile=outputfile, \
                    force_overwrite=force_overwrite, \
                    hist_name='HighEnergySpectrum', energy_scale='*0.602356 -0.303815 ', \
                    cuts=' channel==8 && !(event_coincidence.coincidence & 0x280)  \
                    && lastInhibitTimeDif > 1e5 && (endRiseTime-startRiseTime)/100 < 0.6')



if __name__ == '__main__':
    file_name = 'temp.root' 
    if (len(sys.argv) > 1): 
        file_name = sys.argv[1]
    print "Outputting to file: ", file_name
   #getLowEnergySpectrum(file_name)
   #getLowEnergySpectrumNoCutNoBaseline(file_name)
   #getLowEnergySpectrumNoCut(file_name)
   #getLowEnergySpectrumNoBaseline(file_name)
    getHighEnergySpectrum(file_name)
