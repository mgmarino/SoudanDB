import ROOT
from base_model import BaseModel

class OscillationModel(BaseModel):
    def __init__(self, \
                 basevars):
        BaseModel.__init__(self, basevars)

        self.simple_oscillation_model = ROOT.RooGenericPdf(\
                                  "simple_osc", \
                                  "Simple Oscillation Model",\
                                  "1+sin(TMath::TwoPi()*@0)",\
                                  ROOT.RooArgList(basevars.get_time()))
 
    def get_model(self):
        return self.simple_oscillation_model
