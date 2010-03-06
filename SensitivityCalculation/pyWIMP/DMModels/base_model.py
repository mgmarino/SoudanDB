import ROOT

class BaseVariables:
    class_tag = 0 
    def __init__(self, \
                 time_beginning,\
                 time_in_years,\
                 energy_threshold,\
                 energy_max,
                 use_tag = True):

        tag = ""
        if use_tag: tag = str(self.get_tag())
        self.time = ROOT.RooRealVar("time%s" % tag, "Time",time_beginning,\
                    time_in_years, "years") 
 
        self.ee_energy = ROOT.RooRealVar("ee_energy%s" % tag, "ee_energy", \
                         energy_threshold, energy_max, "keV")

    @classmethod
    def get_tag(cls):
        cls.class_tag += 1
        return cls.class_tag

    def get_energy(self):
        return self.ee_energy

    def get_time(self):
        return self.time

    def set_energy(self, energy):
        self.ee_energy = energy

    def set_time(self, time):
        self.time = time

class BaseModel:
    class_tag = 0 
    def __init__(self,
                 basevars):
        self.basevars = basevars

    @classmethod
    def get_tag(cls):
        cls.class_tag += 1
        return cls.class_tag
