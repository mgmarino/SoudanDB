#!/usr/local/bin/python
import sys
from ROOT import TH1F, TF1, TFile, TGraphErrors, TTree, TObject, TParameter, TCanvas
from management.soudan_database import SoudanServer
def analyze_pulser_data(outputfile='temp.root', force_overwrite=False):
    server = SoudanServer()
    file_list = server.get_accepted_runs()

    time_list = []
    mean_list = []
    sigma_list = []
    for id in file_list:
        print id
        rundoc = server.get_run(id.id) 
        if len(time_list) == 0:
            first_time = rundoc.time_of_start_of_run
        time_list.append(rundoc.time_of_start_of_run - first_time)
        pd = rundoc.pulser_data
        mean_list.append((pd.mean, \
                        pd.mean_err))
        sigma_list.append((pd.sigma, \
                       pd.sigma_err))

    file_to_output = TFile(outputfile, 'recreate');
    objects_to_write = []
    # generate final plots
    list_to_analyze = [ ("Mean of pulser signal", "Mean (keV)", mean_list),\
                        ("Sigma of pulser signal", "Sigma (keV)", sigma_list) ]
    for name, axis_name, data_list in list_to_analyze:
         
        file_to_output.cd()
        new_graph = TGraphErrors(len(data_list))
        new_graph.SetNameTitle(name.replace(' ' , ''),\
                               name.replace(' ' , ''))
        new_hist = TH1F(name.replace(' ', '') + "hist",\
                        name, 100, time_list[0].days, \
                        time_list[len(time_list)-1].days + 1)
        new_hist.GetXaxis().SetTitle("Run start time (days)")
        new_hist.GetYaxis().SetTitle(axis_name)
        new_hist.GetYaxis().SetTitleOffset(1.17)

        maximum = data_list[0][0]
        minimum = data_list[0][0]
        for i in range(len(data_list)):
            new_graph.SetPoint(i, time_list[i].days + time_list[i].seconds/(24*3600.),\
                               data_list[i][0])
            new_graph.SetPointError(i, 0,\
                               data_list[i][1])
            if minimum > data_list[i][0]: 
                minimum = data_list[i][0]
            if maximum < data_list[i][0]: maximum = data_list[i][0]
            

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
    analyze_pulser_data(file_name)
 
