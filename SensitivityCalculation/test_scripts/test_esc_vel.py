import pyWIMP.DMModels.wimp_model as wimp_model
import pyWIMP.DMModels.base_model as base_model
import ROOT
#ROOT.gROOT.SetBatch()
basevars = base_model.BaseVariables(0,2, 4, 50)
wm = wimp_model.WIMPModel(basevars, mass_of_wimp=20)

test3 = wm.get_WIMP_model_with_escape_vel()
test2 = wm.get_WIMP_model()
energy = basevars.get_energy()
time = basevars.get_time()

precision = ROOT.RooNumIntConfig.defaultConfig()
new_config = precision#ROOT.RooNumIntConfig(precision)

new_config.setEpsRel(1e-9)
new_config.setEpsAbs(1e-9)
new_config.method2D().setLabel("RooIntegrator2D")
#test3.setIntegratorConfig(new_config)
new_config.Print('v')
integral = test3.createIntegral(ROOT.RooArgSet(time, energy))
print integral.getVal()
integral = test3.createIntegral(ROOT.RooArgSet(time, energy))
print integral.getVal()
integral = test3.createIntegral(ROOT.RooArgSet(energy))
print integral.getVal()
integral = test3.createIntegral(ROOT.RooArgSet(time))
print integral.getVal()
