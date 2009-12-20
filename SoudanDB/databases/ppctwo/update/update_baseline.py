def update_baseline_for_rundoc(run_doc):
    """
      Analyzes baseline for a run_doc and returns a dictionary
      which can be used to populate a BaselineDict object
    """
    import ROOT
    if run_doc.baseline_dict.chi_square:
        return (run_doc, False)

    return_dict = {} 
    open_file = ROOT.TFile(run_doc.output_data_file_tier_3.low_energy.pfn)
    main_tree = open_file.Get("wf_analysis") 

    hist = ROOT.TH1D("temphist", "temphist", 1000, -8000, 1000)
    gaus = ROOT.TF1("gaus", "gaus")
    num_events = main_tree.Draw("fitConstant >> temphist", \
      "channel==0", "goff")
    gaus.SetParameter(0, hist.GetEntries())
    gaus.SetParameter(2, hist.GetRMS())
    gaus.SetParameter(1, hist.GetMean())
    hist.Fit(gaus, "Q N", "", hist.GetMean()-hist.GetRMS(), \
      hist.GetMean()+hist.GetRMS())

    return_dict['average_fit_constant'] = gaus.GetParameter(1)
    return_dict['average_fit_rms'] = gaus.GetParameter(2)
    return_dict['chi_square'] = gaus.GetChisquare()
    return_dict['ndf'] = gaus.GetNDF()

    entry_cuts_list = []
    entry_cuts_list.append(('first_ten_percent_fit_constant', \
      0, int(0.1*main_tree.GetEntries())))
    entry_cuts_list.append(('last_ten_percent_fit_constant', \
      main_tree.GetEntries() - 1 - int(0.1*main_tree.GetEntries()),\
       main_tree.GetEntries()-1))

    for (name_of_event, init_event, end_event) in entry_cuts_list:
        main_tree.Draw("fitConstant >> temphist", \
          "channel==0 && Entry$ >= %i && Entry$ <= %i" % \
          (init_event, end_event), "goff")
        gaus.SetParameter(0, hist.GetEntries())
        gaus.SetParameter(2, hist.GetRMS())
        gaus.SetParameter(1, hist.GetMean())
        hist.Fit(gaus, "Q N", "", hist.GetMean()-hist.GetRMS(), \
          hist.GetMean()+hist.GetRMS())
        return_dict[name_of_event] = gaus.GetParameter(1)
        return_dict["%s_rms" % name_of_event] = gaus.GetParameter(2)

    run_doc.baseline_dict = return_dict
    return (run_doc, True)
       

