from ..views import view_numentries_virgin_docs
def update_rundoc(run_doc):
    """
    Determine how many entries are in the main root file
    """
    import ROOT
    open_file = ROOT.TFile(run_doc.root_data_file_tier_1.pfn)
    main_tree = open_file.Get("gretaDec") 
    run_doc.number_of_entries_in_tier1_root_tree = \
      main_tree.GetEntries()
    return (run_doc, True)

def get_view():
    return view_numentries_virgin_docs.get_view_class()
