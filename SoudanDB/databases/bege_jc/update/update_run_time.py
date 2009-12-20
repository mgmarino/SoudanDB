def update_run_time_for_rundoc(run_doc):
    """
      Updates a rundoc with the calculation of the livetime 
      and an error on that livetime (in seconds)
      Can be used to popluate a RunTimeDict
    """
    import ROOT
    import os.path
    if not os.path.exists(run_doc.output_data_file_tier_2.pfn):
        return (run_doc, False)
    output_dictionary = {}
    open_file = ROOT.TFile(run_doc.output_data_file_tier_2.pfn)
    main_tree = open_file.Get("energy_output_tree") 
    main_tree.GetEntry(0)
    first_time = main_tree.time
    main_tree.GetEntry(main_tree.GetEntries()-2)
    last_time = main_tree.time
    output_time = last_time - first_time
    if output_time == run_doc.livetime.run_milliseconds:
        return (run_doc, False)
    output_dictionary['run_milliseconds'] = output_time 
    output_dictionary['run_milliseconds_error'] = 0 
    run_doc.livetime = output_dictionary
    return (run_doc, True)

