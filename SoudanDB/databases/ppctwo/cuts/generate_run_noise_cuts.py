from database_cuts import MGCut
from soudan_database import SoudanServer
import ROOT
import math

class PoissonClass:
    def __call__(self, x, par):
        res = 0.0
        xx = x[0]
        if xx > 0:
            try:
                res = par[0]*math.pow(par[1], xx)/\
                  (ROOT.TMath.Gamma(xx+1)*math.exp(par[1]))
            except ValueError:
                return 0.0 
        return res

    def get_appropriate_cut(self,given_mean, cut_percentage=0.9999):
        cut = 0
        counts = 0 
        while True:
            cut += math.exp(-given_mean)*math.pow(given_mean, counts)/\
              self.factorial(counts) 
            if cut >= cut_percentage: 
                break
            counts+=1
        return (counts, cut)

    def factorial(self, i):
        if i <= 0:
            return 1
        return_val = i
        i -= 1
        while i>0:
           return_val *= i 
           i -= 1
        return return_val


class RunNoiseCut(MGCut):
    def __init__(self):
        self.generate_run_noise_cuts(SoudanServer())

    def get_description_of_cut(self):
        return "run_noise_cuts_for_runs"

    def get_verbose_description_of_cut(self):
        return """
Generates a cut based upon a poisson analysis of the event
rates in regions between 0.6 and 10 keV and 10 and 70 keV.
The number of events in these energy regions for a set
of events is histogrammed and then fit with a poisson
distribution.  This fit then allows the calculation of a
cut parameter which keeps 99.99%% of the "good" runs.  

In this particular cut, %i runs were used, beginning at
run %i and ending at run %i.  

In the 0.6 to 10 keV Region:
Cuts: %i
Accept percentage: %f

In the 10 to 70 keV Region:
Cuts: %i
Accept percentage: %f
               """ % (len(self.runs_used), \
                      self.runs_used[0], \
                      self.runs_used[len(self.runs_used)-1],\
                      self.first_region_cut, \
                      self.first_region_accept_percentage,\
                      self.second_region_cut, \
                      self.second_region_accept_percentage)

    def get_string_of_cut(self):
        return """noise_check.events_in_region_point6_to_10_keV <= %i and\
                  noise_check.events_in_region_10_to_70_keV <= %i""" % \
                  (self.first_region_cut, self.second_region_cut)

    def generate_run_noise_cuts(self, server):
        print "Generating run noise cuts..."
        hist = ROOT.TH1D("hist", "hist", 100, 0, 100)
        hist1 = ROOT.TH1D("hist1", "hist1", 100, 0, 100)
        self.runs_used = []
        for id in server.get_database():
            run_doc = server.get_run(id)
            if not run_doc.noise_check.events_in_region_point6_to_10_keV:
                continue
            hist.Fill(run_doc.noise_check.events_in_region_point6_to_10_keV)
            hist1.Fill(run_doc.noise_check.events_in_region_10_to_70_keV)
            self.runs_used.append(int(id))
           
        pois = PoissonClass()
        f1 = ROOT.TF1('pyf1', pois, 0, 50, 2)
        f1.SetParameter(1, hist.GetMean())
        hist.Fit(f1, "N")
        (self.first_region_cut, self.first_region_accept_percentage) =\
          pois.get_appropriate_cut(f1.GetParameter(1))

        f1.SetParameter(1, hist1.GetMean())
        hist1.Fit(f1, "N")
        (self.second_region_cut, self.second_region_accept_percentage) = \
          pois.get_appropriate_cut(f1.GetParameter(1))

        self.runs_used.sort()
        print
        print "Used %i runs, from run %i-%i" % (len(self.runs_used), \
                                                self.runs_used[0], \
                                                self.runs_used[len(self.runs_used)-1])
        print
        print self.get_verbose_description_of_cut()


def get_cut_class():
    return RunNoiseCut()
