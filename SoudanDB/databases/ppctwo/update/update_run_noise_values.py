import ROOT
from ..views import view_virgin_run_noise
def update_run_noise_values_for_rundoc(run_doc):

    open_file = ROOT.TFile(run_doc.output_data_file_tier_3.low_energy.pfn)
    main_tree = open_file.Get("wf_analysis")
    coincidence_tree = open_file.Get("event_coincidence")
    main_tree.AddFriend(coincidence_tree)
    
    run_doc.noise_check.events_in_region_point6_to_10_keV = \
      main_tree.Draw("","!(event_coincidence.coincidence & 0x280) && \
      lastInhibitTimeDif > 1e5 && -energy*0.0125749 <= 10 && \
      -energy*0.0125749 >= 0.6", "goff")

    run_doc.noise_check.events_in_region_10_to_70_keV = \
      main_tree.Draw("","!(event_coincidence.coincidence & 0x280) && \
      lastInhibitTimeDif > 1e5 && -energy*0.0125749 <= 70 && \
      -energy*0.0125749 >= 10", "goff")

    open_file.Close()
    return (run_doc, True)
        
def get_view():
    return view_virgin_run_noise.get_view_class()
