import ROOT

class BaseVariables:
    
    def __init__(self, \
                 time_beginning,\
                 time_in_years,\
                 energy_threshold,\
                 energy_max):

        self.time = ROOT.RooRealVar("time", "Time",time_beginning,\
                    time_in_years, "years") 
 
        self.ee_energy = ROOT.RooRealVar("ee_energy", "ee_energy", \
                         energy_threshold, energy_max, "keV")

    def get_energy(self):
        return self.ee_energy

    def get_time(self):
        return self.time

class BaseModel:
    def __init__(self,
                 basevars):
        self.basevars = basevars
