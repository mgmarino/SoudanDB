import ROOT
from base_model import BaseModel

class FlatModel(BaseModel):
    def __init__(self, \
                 basevars):
        BaseModel.__init__(self, basevars)

        # Flat pdf
        self.time_pdf = ROOT.RooPolynomial("time_pdf", \
                                           "time_pdf", \
                                           basevars.get_time())
        self.energy_pdf = ROOT.RooPolynomial("energy_pdf", \
                                             "energy_pdf", \
                                             basevars.get_energy())
        self.flat_pdf = ROOT.RooProdPdf("time_and_energy_pdf", \
                                        "time_and_energy_pdf", \
                                        self.time_pdf, \
                                        self.energy_pdf)

    def get_flat_model(self):
        return self.flat_pdf
