from soudan_database import SoudanServer
import ROOT
import array

def look_at_number_of_entries_in_file():

    server = SoudanServer()
    tree = ROOT.TTree("temp", "temp")
    num_entries = array.array('d', [0])
    tree.Branch("entries", num_entries, "num_entries/D")
    for id in server.get_database():
        print id
        rundoc = server.get_run(id) 
        if not rundoc: continue
        num_entries[0] = rundoc.number_of_entries_in_tier1_root_tree/\
                         float(rundoc.livetime.run_seconds)
        tree.Fill()

    open_file = ROOT.TFile("temp.root", "recreate")
    hist = ROOT.TH1D("hist", "hist", 1000, 0, 1000)
    tree.Draw("entries >> hist")
    raw_input("enter")
    hist.Write()

if __name__ == '__main__':
    look_at_number_of_entries_in_file()
 
