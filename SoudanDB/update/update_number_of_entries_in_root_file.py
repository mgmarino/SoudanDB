def update_number_of_entries_in_root_file_for_rundoc(run_doc):
    """
    Determine how many entries are in the main root file
    """
    import ROOT
    if run_doc.number_of_entries_in_tier1_root_tree:
        return (run_doc, False)
    open_file = ROOT.TFile(run_doc.root_data_file_tier_1.pfn)
    main_tree = open_file.Get("gretaDec") 
    run_doc.number_of_entries_in_tier1_root_tree = \
      main_tree.GetEntries()
    return (run_doc, True)

