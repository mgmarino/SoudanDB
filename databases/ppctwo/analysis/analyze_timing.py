#!/usr/bin/env python
import sys
import ROOT
from SoudanDB.management.soudan_database import SoudanServer, PickleDocumentClass
import time
import types

#def dynamic_function(run_number, event_time):  
#   if run_number >= 1934:
#       return 1247631811.696431 + event_time*1e-8 
#   elif run_number >= 1205:
#       return 1244817068.198428 + event_time*1e-8
#   elif run_number >= 712:
#       return 1242946557.416290 + event_time*1e-8
#   elif run_number >= 293:
#       return 1240544960.676191 + event_time*1e-8
#   return 0 

def analyze_timing(outputfile='temp.root', force_overwrite=False):
    
    force_overwrite = True
    timing_list_name = "timing_list"
    time_run_list_name = "time_of_run_list"
    server = SoudanServer()
    file_to_output = ROOT.TFile(outputfile, 'recreate');
    objects_to_write = []
    apickle = None
    if server.pickle_is_in_database(timing_list_name):
        print "Already exists"
        apickle = server.get_pickle(timing_list_name)
        time_list = apickle.pickle
        timing_list_name = None
    else:
        apickle = PickleDocumentClass()
        force_overwrite = True
    if force_overwrite:
        time_list = []
        file_list = server.get_accepted_runs()
        
        # generate final plots
        start_time = None
        for id in file_list:
            print id
            rundoc = server.get_run(id.id) 
            if not start_time:
                start_time = rundoc.time_of_start_of_run
            timeofstart = rundoc.time_of_start_of_run
            file_name = rundoc.output_data_file_tier_2.pfn
            open_file = ROOT.TFile(file_name)
            main_tree = open_file.Get("wf_analysis") 
            coinc_tree = open_file.Get("event_coincidence") 
            main_tree.AddFriend(coinc_tree)
            main_tree.GetEntry(0)
            first_time = main_tree.eventTime 
            main_tree.GetEntry(main_tree.GetEntries()-1)
            last_time = main_tree.eventTime 
            time_list.append((time.mktime(timeofstart.timetuple()), \
                              first_time, last_time, \
                              main_tree.runNumber))
            
            open_file.Close()
        apickle.pickle = time_list
        server.insert_pickle(apickle, timing_list_name) 


    conversion_code = "convert_gretina_time_to_real_time"
    dynamic_function = None
    pickle = None
    if server.pickle_is_in_database(conversion_code):
        pickle = server.get_pickle(conversion_code)
        if not force_overwrite:
            dynamic_function = pickle.pickle
        conversion_code = None
    if not pickle:
        pickle = PickleDocumentClass()
    if not dynamic_function:
        start_run_number = time_list[0][3]
        start_time = time_list[0][0]
        last_time = time_list[0][0]
        
        scrap_list = []
        
        def find_offset(scrap_list):    
            agraph = ROOT.TGraph(len(scrap_list))
            for i in range(len(scrap_list)):
                agraph.SetPoint(i, scrap_list[i][1], scrap_list[i][0])
            pol1 = ROOT.TF1("pol1", "pol1")
            agraph.Fit(pol1)
            return pol1.GetParameter(0)
        
        
        run_dict = {}
        for start, event, last, runN in time_list:
            if event < last_time: 
                # We have cycled, do the fitting
                run_dict[start_run_number] = find_offset(scrap_list)
                del scrap_list[:]
                start_run_number = runN
            last_time = event
            scrap_list.append((start, event*1e-8, runN))
        run_dict[start_run_number] = find_offset(scrap_list)
        # Now make some dynamic code
        
        run_numbers = run_dict.keys()
        run_numbers.sort()
        run_numbers.reverse()
        code = """
def dynamic_function(run_number, event_time):  
    if run_number >= %i:
        return %f + event_time*1e-8 """ % (run_numbers[0], run_dict[run_numbers[0]]) 
        for i in range(1, len(run_numbers)):
            code += """
    elif run_number >= %i:
        return %f + event_time*1e-8""" % (run_numbers[i], run_dict[run_numbers[i]]) 
        code += """
    return 0 """

        pickle.pickle = code
        server.insert_pickle(pickle, conversion_code) 
        code_obj = compile(code,'<string>', 'exec')
  
        dynamic_function = types.FunctionType(code_obj.co_consts[0], globals())

    apickle = None
    mydict = None
    if not server.pickle_is_in_database(time_run_list_name):
        apickle = PickleDocumentClass() 
    else:
        apickle = server.get_pickle(time_run_list_name)
        time_run_list_name = None
        mydict = apickle.pickle
    if force_overwrite:
        scratch_list = {} 
        start_time = 0
        for start, event, last, runN in time_list:
            if runN == 1933: print "Yes"
            print runN
            if start_time == 0: start_time = dynamic_function(runN, event)
            scratch_list[runN] = (dynamic_function( runN, event ) - start_time,
                                 dynamic_function( runN, last ) - start_time)
        apickle.pickle = scratch_list
        server.insert_pickle(apickle, time_run_list_name)
        mydict = scratch_list
       
    keys = mydict.keys()
    new_graph = ROOT.TGraph(len(keys))
    keys.sort() 
    for i in range(len(keys)):
        first, last = mydict[keys[i]]
        new_graph.SetPoint(i, keys[i], last - first)
    
    c1 = ROOT.TCanvas()
    new_graph.Draw("APL")

    c1.Update()
    raw_input("E")
    #c1.Print("temp.eps")
    file_to_output.cd()
    for object in objects_to_write:
        object.Write(object.GetName(), TObject.kOverwrite)
    file_to_output.Close()

if __name__ == '__main__':
    file_name = 'temp.root' 
    if (len(sys.argv) > 1): 
        file_name = sys.argv[1]
    print "Outputting to file: ", file_name
    analyze_timing(file_name)
 
