from management.soudan_database import RunDocumentClass
import ROOT

def update_trigger_efficiency_for_rundoc(run_doc):
    trigger_efficiency_file = '/mnt/raid/data/Soudan/Data/EfficiencyTests/all_out.root'
    open_file = ROOT.TFile(trigger_efficiency_file)
    efficiency_tree = open_file.Get('efficiency_tree')
    if not efficiency_tree:
         print 'Problem obtaining efficiency_tree'
         return (run_doc, False)

    el = ROOT.TEventList("el", "el")
    efficiency_tree.Draw(">>el", "run_number==%i" % int(run_doc.id))
    if el.GetN() != 1: return (run_doc, False)

    efficiency_tree.GetEntry(el.GetEntry(0))
    # check to see if something has already been loaded
    if len(run_doc.trigger_efficiency) == 0:
        # This means we need to update the schema:
        run_doc = RunDocumentClass.update_schema(run_doc)
    if run_doc.trigger_efficiency.scaling == efficiency_tree.scaling:
        # no update necessary
        return (run_doc, False)

    run_doc.trigger_efficiency.scaling = efficiency_tree.scaling
    run_doc.trigger_efficiency.scaling_err = efficiency_tree.scaling_err
    run_doc.trigger_efficiency.offset = efficiency_tree.offset
    run_doc.trigger_efficiency.offset_err = efficiency_tree.offset_err
    run_doc.trigger_efficiency.erfc_function = \
      efficiency_tree.erfc_function.GetExpFormula()

    return (run_doc, True)
