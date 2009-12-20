#!/usr/local/bin/python
import sys
from ROOT import TH1D, TF1, TFile, TGraph, TTree, TObject, TParameter, TCanvas
from management.soudan_database import SoudanServer
def analyze_channel_rates(outputfile='temp.root', force_overwrite=False):
    server = SoudanServer()
    file_list = server.get_accepted_runs()
    channel_to_analyze = { 0 : "Low-energy channel",\
                           1 : "Low-energy channel trigger",\
                           2 : "Muon veto",\
                           7 : "Pulser channel",\
                           8 : "High-energy channel",\
                           9 : "Reset inhibit"}

    
    #c1 = TCanvas()
    graph_list = {}
    time_list = []
    for channel in channel_to_analyze.keys(): graph_list[channel] = []
    for id in file_list:
        print id
        rundoc = server.get_run(id.id) 
        open_file = TFile(rundoc.output_data_file_tier_2.pfn)
        if len(time_list) == 0:
            first_time = rundoc.time_of_start_of_run
        time_list.append(rundoc.time_of_start_of_run - first_time)
        main_tree = open_file.Get("wf_analysis") 
        for channel in channel_to_analyze.keys():
            num_events = main_tree.Draw(">> eventList", "channel==%i" % channel, "goff")
            graph_list[channel].append(num_events/float(rundoc.livetime.run_seconds))
        open_file.Close()

    file_to_output = TFile(outputfile, 'recreate');
    objects_to_write = []
    # generate final plots
    last_time = time_list[len(time_list)-1]
    for channel, data_list in graph_list.items():
         
        file_to_output.cd()
        new_graph = TGraph(len(data_list))
        new_graph.SetNameTitle(channel_to_analyze[channel].replace(' ' , ''),\
                               channel_to_analyze[channel].replace(' ' , ''))
        new_hist = TH1D(channel_to_analyze[channel].replace(' ', '') + "hist",\
                        channel_to_analyze[channel], 100, 0, \
                        last_time.days + 1)
        new_hist.GetXaxis().SetTitle("Run start time (days)")
        new_hist.GetYaxis().SetTitle("Rate (Hz)")

        maximum = data_list[0]
        minimum = data_list[0]
        for i in range(len(data_list)):
            new_graph.SetPoint(i, time_list[i].days + time_list[i].seconds/(24*3600.),\
                               data_list[i])
            if minimum > data_list[i]: minimum = data_list[i]
            if maximum < data_list[i]: maximum = data_list[i]

        ten_percent = (maximum - minimum)*0.1
        new_hist.SetMaximum(maximum + ten_percent)
        new_hist.SetMinimum(minimum - ten_percent)
        #new_graph.SetHistogram(new_hist)
        objects_to_write.append(new_graph)
        objects_to_write.append(new_hist)

    file_to_output.cd()
    for object in objects_to_write:
        object.Write(object.GetName(), TObject.kOverwrite)
    file_to_output.Close()

if __name__ == '__main__':
    file_name = 'temp.root' 
    if (len(sys.argv) > 1): 
        file_name = sys.argv[1]
    print "Outputting to file: ", file_name
    analyze_channel_rates(file_name)
 
