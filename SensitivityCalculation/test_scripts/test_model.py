import pyWIMP.DMModels.wimp_model as wimp_model
import pyWIMP.DMModels.base_model as base_model
import ROOT
import sys

#ROOT.gROOT.SetBatch()
basevars = base_model.BaseVariables(0,1./365., 0, 100)
time = basevars.get_time()
energy = basevars.get_energy()
time.setVal(0)
time.setConstant(True)
model_normal = ROOT.RooRealVar("model_normal", \
                               "model_normal", \
                               1, 0, 100000)
print model_normal.getVal()
wm = wimp_model.WIMPModel(basevars, mass_of_wimp=10, kilograms=1)
wm2 = wimp_model.WIMPModel(basevars, mass_of_wimp=7, kilograms=1)

c1 = ROOT.TCanvas()
model = wm.get_model()
model_extend = wm.get_simple_model() 
model_extend2 = wm2.get_simple_model() 
model_extend = wm.get_model() 
model_extend2 = wm2.get_model() 

print model_extend.getNorm(0)
print "Model extend: ", model_extend.expectedEvents(ROOT.RooArgSet(energy))
print "Model extend, ratio: ", model_extend.expectedEvents(ROOT.RooArgSet(energy))*(0.751/0.561)
print "Model extend: ", model_extend2.expectedEvents(ROOT.RooArgSet(energy))
print "Model extend, ratio: ", model_extend2.expectedEvents(ROOT.RooArgSet(energy))*(0.751/0.561)

frame = energy.frame()
model_extend.plotOn(frame)
model_extend2.plotOn(frame)
frame.Draw()
c1.Update()
raw_input("E")
norm_value = wm.get_normalization().getVal()
model_normal.setVal(1e-4/norm_value)



print 1e-4/norm_value
for i in range(50):
  energy.setVal(i*0.1)
  print i*0.1, model_extend.getVal()
norm_value = wm2.get_normalization().getVal()
model_normal.setVal(1e-4/norm_value)
for i in range(50):
  energy.setVal(i*0.1)
  print i*0.1, model_extend2.getVal()
print norm_value

integral = model_extend.createIntegral(ROOT.RooArgSet(energy))
value = integral.getVal()
number_of_counts = 0 
integral = model.createIntegral(ROOT.RooArgSet(energy))
print integral.getVal()
data = model.generate(ROOT.RooArgSet(energy), 1000)
model_extend.fitTo(data)
data.plotOn(frame)
model_extend.plotOn(frame)
frame.Draw()
c1.Update()
print wm.get_normalization().getVal()
print integral.getVal()*model_normal.getVal()
raw_input("E")
