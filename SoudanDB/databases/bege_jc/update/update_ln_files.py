#!/bin/env python
import os 
import datetime
import time
import ROOT


def update_all_files_in_ln_doc(rundoc):
    """
    Returns whether or not the rundoc has been updated.
    This list is composed with tuples of the following:
       file_dict,
       program_to_make_next_file
       dest_file
    """
    from SoudanDB.utilities.utilities import get_hash_of_file
    def make_png_for_ln_fills(infile, outfile):
        ROOT.gROOT.SetBatch()
        open_file = open(infile, 'r') 
        line = open_file.readline()
        basename = os.path.basename(infile) 
        year = int('20' + basename[0:2])
        month = int(basename[2:4])
        day = int(basename[4:6])
    
        list_of_data = []
        while line:
            (temp, timedat) = line.split()
            (hour, minute, second) = timedat.split(':')
            list_of_data.append( (float(temp), datetime.datetime(year, month, day, \
              int(hour), int(minute), int(second))))
            line = open_file.readline()
    
    
        temp, date_obj = list_of_data[0]
        first_time = time.mktime(date_obj.timetuple())
        graph = ROOT.TGraph(len(list_of_data))
        graph.SetTitle("LN Fill: %i-%i-%i %i:%i:%i" % (year, month, day, \
                                                       date_obj.hour, date_obj.minute, \
                                                       date_obj.second))
        c1 = ROOT.TCanvas()
        
        hist = ROOT.TH1F("hist", "LN Fill: %i-%i-%i %i:%i:%i" % (year, month, day, \
                                                       date_obj.hour, date_obj.minute, \
                                                       date_obj.second), \
                         len(list_of_data), 0, len(list_of_data)+10)
    
        hist.GetYaxis().SetTitle("Temperature (C)")
        hist.GetXaxis().SetTitle("Time since start (s)")
    
        minimum = temp
        maximum = temp
        for i in range(len(list_of_data)):
            (temp, date_obj) = list_of_data[i]
            if temp > maximum: maximum = temp
            if temp < minimum: minimum = temp
            this_time = time.mktime(date_obj.timetuple()) - first_time
            graph.SetPoint(i, this_time, float(temp))
    
        hist.SetMinimum(minimum-10)
        hist.SetMaximum(maximum+10)
        for i in range(hist.GetNbinsX()):
            hist.SetBinContent(i+1, minimum-50)
        hist.Draw()
        graph.Draw("P")
        c1.Update()
        c1.Print(outfile)
 
    rundoc_was_modified = False
    list_to_check = [ ( rundoc.ln_data_file,\
                        make_png_for_ln_fills,\
                        rundoc.ln_plot_file.pfn ), \
                      ( rundoc.ln_plot_file, None, "") ]

    for dict, program, dest in list_to_check:
        if not os.path.exists(dict.pfn): continue
        if not (dict.last_mod_time and \
          os.path.getmtime(dict.pfn) <= time.mktime(dict.last_mod_time.timetuple())):
            rundoc_was_modified = True
            dict.last_mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(dict.pfn))
            dict.md5hash = get_hash_of_file(dict.pfn)
        if program and not (os.path.exists(dest) \
          and os.path.getmtime(dest) >= os.path.getmtime(dict.pfn)):
            print "Running: %s %s" % (dict.pfn, dest)
            program(dict.pfn, dest)
            open_file = open(dict.pfn)
            rundoc.fill_duration = sum([1 for line in open_file]) 
            rundoc_was_modified = True

    return (rundoc, rundoc_was_modified)

