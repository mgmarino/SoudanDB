#!/usr/bin/env python
from SoudanDB.management.soudan_database import SoudanServer
import ROOT
class outputWFs:
    def __init__(self, nameOfPSFile, numberX=4, numberY=4, pages = 0):
        from ROOT import gStyle, TPostScript, TCanvas, gROOT
        gROOT.SetBatch()
        gStyle.SetHistFillColor(0)
        gStyle.SetOptStat(0)
        gStyle.SetOptTitle(1)
        self.number_x = numberX
        self.number_y = numberY
        self.pages = pages
        self.c1 = TCanvas("c1", "c1", int(8.5*300), int(11*300))
        self.c1.Divide(self.number_x, self.number_y)
        self.c1.SetBorderMode(0)
        self.c1.SetFillColor(0)
        self.c1.SetBorderSize(0)
        self.c1.SetFrameBorderMode(0)
        self.c1.SetFrameBorderSize(0)
        self.number_of_pages = 0
        
        self.ps = TPostScript(nameOfPSFile, 111)
        for i in range(self.number_y*self.number_x):
            pad = self.c1.cd(i+1)
            pad.SetFillColor(0)
            pad.SetFrameFillColor(0)
            pad.SetFrameBorderSize(0)
            pad.SetFrameBorderMode(0)
            pad.SetBorderMode(0)
            pad.SetBorderSize(0)
        self.current_pad_number = 0
           
    def get_current_pad_number(self):
        self.current_pad_number = (self.current_pad_number % (self.number_x*self.number_y)) + 1
        return self.current_pad_number
        
    def loopOverRecords(self, cuts, energyScaler, 
                        use_baseline_cut = True, 
                        opposite_baseline_cut = False):
        server = SoudanServer()
        file_list = server.get_accepted_runs()
        for id in file_list:
            print id
            rundoc = server.get_run(id.id) 
            file_name = rundoc.output_data_file_tier_2.pfn 
            wf_file_name = rundoc.root_data_file_tier_1.pfn 
            open_file = ROOT.TFile(file_name)
            main_tree = open_file.Get("wf_analysis") 
            coinc_tree = open_file.Get("event_coincidence") 
            wf_open_file = ROOT.TFile(wf_file_name)
            wf_tree = wf_open_file.Get("gretaDec")
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
            if not self.printWaveformToPS(main_tree, wf_tree, real_cuts, energyScaler): break

    def printWaveformToPS( self, main_tree, wf_tree, cuts = "", \
                           energyScaler="", number = 0):
        from ROOT import TEventList
        eventList = TEventList("eventList", "eventList")
        main_tree.Draw(">>eventList", cuts)
        if (number == 0 or number > eventList.GetN()):
            number = eventList.GetN()
        print "Total Entries: %i" % eventList.GetN()
        sg = ROOT.MGWFSavitzkyGolaySmoother(20, 0, 2)
        rt = ROOT.MGWFRisetimeCalculation()
        base = ROOT.MGWFBaselineRemover()
        base.SetBaselineTime(2500)
        rt.SetInitialThresholdPercentage(0.1)
        rt.SetFinalThresholdPercentage(0.9)
        for i in range(number):
            main_tree.GetEntry(eventList.GetEntry(i))
            wf_tree.GetEntry(eventList.GetEntry(i))
            rise_time = (main_tree.endRiseTime - main_tree.startRiseTime)/100.
            energy = main_tree.energy
            wf = wf_tree.MGTWaveformBranch
            padNumber = self.get_current_pad_number() 
            if (padNumber == 1):
                self.number_of_pages += 1
                self.ps.NewPage()
                if self.pages > 0 and self.number_of_pages > self.pages:
                    return False
                
            self.c1.cd(padNumber)
            sg.Transform(wf)
            rt.SetPulsePeakHeight(main_tree.energy)
            base.Transform(wf)
            rt.Transform(wf)
            riset = rt.GetFinalThresholdCrossing()
            riset -= rt.GetInitialThresholdCrossing()
            riset /= 100.
            hist = wf.GimmeHist()
            hist.SetFillColor(0)
            hist.SetTitle("Energy: %f (keV), Max: %f, Min: %f, rt: %f, new: %f" % (eval("%d%s" % (energy, energyScaler)),\
               main_tree.maximum, main_tree.minimum, rise_time, riset))
            hist.DrawCopy("HIST")
            if (padNumber == self.number_x*self.number_y): 
                self.c1.Update()
        return True
    
    def close_file(self):
        self.ps.Close()
        #gSystem->Exec(Form("gs %s", nameOfPSFile.c_str()))


output_WFs = outputWFs(nameOfPSFile="test_peaks.ps", numberX=1, numberY=1, pages=200)

dict = { "energyScaler" : "*-0.0125749",\
   "cuts" : " channel==0 && !(event_coincidence.coincidence & 0x280)  \
   && lastInhibitTimeDif > 1e5 && -energy*0.0125749 >= 0.6\
   && -energy*0.0125749 <= 2 " }

dict = { "energyScaler" : "*-0.602356 - 0.303", \
   "cuts" : " channel==8 && !(event_coincidence.coincidence & 0x3)  \
   && lastInhibitTimeDif > 1e5 " }

#dict = { "energyScaler" : "*-0.393364 -0.877544", \
#   "cuts" : " channel==8 && !(event_coincidence.coincidence & 0x280)  \
#   && lastInhibitTimeDif > 1e5 \
#   && energy*-0.393364 -0.877544 > 1730"} 
#dict = { "energyScaler" : "*-8.21888888888888842e-03", \
#   "cuts" : " channel==0 && !(event_coincidence.coincidence & 0x280)  && (event_coincidence.coincidence & 0x100)\
#   && lastInhibitTimeDif > 1e5 \
#   && energy*-8.21888888888888842e-03 > 30 && energy*-8.21888888888888842e-03 < 40"} 

output_WFs.loopOverRecords(dict['cuts'], dict['energyScaler'])

print "Closing File"
output_WFs.close_file()
