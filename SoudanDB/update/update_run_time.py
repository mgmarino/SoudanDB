def update_run_time_for_rundoc(run_doc):
    """
      Updates a rundoc with the calculation of the livetime 
      and an error on that livetime (in seconds)
      Can be used to popluate a RunTimeDict
    """
    import ROOT
    if run_doc.livetime.run_seconds:
        return (run_doc, False)
    output_dictionary = {}
    frequency_of_pulser = 1.0 # in seconds
    open_file = ROOT.TFile(run_doc.output_data_file_tier_3.pulser.pfn)
    main_tree = open_file.Get("wf_analysis") 
    main_tree.GetEntry(0)
    output_dictionary['run_seconds'] = \
      float(main_tree.GetEntries())/frequency_of_pulser
    output_dictionary['run_seconds_error'] = 1./frequency_of_pulser
    run_doc.livetime = output_dictionary
    return (run_doc, True)

