import pyWIMP.DMModels.wimp_model as wimp_model
import ROOT
import re
#ROOT.gROOT.SetBatch()
mass_of_wimp = 20
energy_max = 20
threshold = 1
wm_constant_quench = wimp_model.AllWIMPModels(energy_max=energy_max, energy_threshold=threshold, mass_of_wimp=mass_of_wimp, time_in_years=1, constant_quenching=True)

wm_variable_quench = wimp_model.AllWIMPModels(energy_max=energy_max, energy_threshold=threshold, mass_of_wimp=mass_of_wimp, time_in_years=1, constant_quenching=False)

constant_vars = ROOT.RooArgSet(wm_constant_quench.get_energy(), wm_constant_quench.get_time())
variable_vars = ROOT.RooArgSet(wm_variable_quench.get_energy(), wm_variable_quench.get_time())
print "variable", wm_variable_quench.get_WIMP_model().expectedEvents(variable_vars)
print "constant", wm_constant_quench.get_WIMP_model().expectedEvents(constant_vars)

