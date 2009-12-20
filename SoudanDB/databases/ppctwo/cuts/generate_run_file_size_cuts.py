from database_cuts import MGCut
from soudan_database import SoudanServer
import ROOT

class RunFileSizeCut(MGCut):
    def __init__(self):
        self.generate_run_file_size_cuts(SoudanServer())

    def get_description_of_cut(self):
        return "run_file_size_cut_for_runs"

    def get_verbose_description_of_cut(self):
        return """
Generates a cut based upon looking at the number
of entries in a file divided by the livetime. It
histograms this value and then makes a cut at 
<= mean + 2*RMS of the histogram (acceptance).

In this particular cut, %i runs were used, beginning at
run %i and ending at run %i.  

Cut was at: %f (entries/livetime)

               """ % (len(self.runs_used), \
                      self.runs_used[0], \
                      self.runs_used[len(self.runs_used)-1],\
                      self.cut_ratio)

    def get_string_of_cut(self):
        return """number_of_entries_in_tier1_root_tree/\
                  float(livetime.run_seconds) <= %f""" % \
                  (self.cut_ratio)

    def generate_run_file_size_cuts(self, server):
        print "Generating run file size cuts..."
        hist = ROOT.TH1D("hist", "hist", 1000, 0, 1000)
        self.runs_used = []
        for id in server.get_database():
            run_doc = server.get_run(id)
            try:
                bool_to_check = (run_doc.livetime.run_seconds or \
                        run_doc.number_of_entries_in_tier1_root_tree)
            except AttributeError: continue
            if not bool_to_check: continue
            hist.Fill(run_doc.number_of_entries_in_tier1_root_tree/\
                      float(run_doc.livetime.run_seconds))
            self.runs_used.append(int(id))
           
        self.cut_ratio = hist.GetMean() + 2*hist.GetRMS()
        self.runs_used.sort()
        print
        print "Used %i runs, from run %i-%i" % (len(self.runs_used), \
                                                self.runs_used[0], \
                                                self.runs_used[len(self.runs_used)-1])
        print
        print self.get_verbose_description_of_cut()


def get_cut_class():
    return RunFileSizeCut()
