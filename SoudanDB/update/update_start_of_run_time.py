def update_start_of_run_time_for_rundoc(run_doc):
    """
      Updates a rundoc with the calculation of the livetime 
      and an error on that livetime (in seconds)
      Can be used to popluate a RunTimeDict
    """
    import ROOT, plistlib
    import dateutil.parser as parse
    if run_doc.time_of_start_of_run:
        return (run_doc, False)
    open_file = ROOT.TFile(run_doc.root_data_file_tier_1.pfn)
    header_xml = open_file.Get("headerXML") 
    obj = plistlib.readPlistFromString(header_xml.String().Data())
    run_doc.time_of_start_of_run = parse.parse(obj['Document Info']['date'])
    return (run_doc, True)

