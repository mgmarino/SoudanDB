from ..views import view_virgin_pulser_data
def update_rundoc(run_doc):
    import ROOT
    # check to see if we need to update
    if len(run_doc.pulser_run_characteristics.chan_0.sigma) ==\
       len(run_doc.pulser_on_set):
        return (run_doc, False)
    # following shuts off all messages from MINUIT.
    ROOT.RooMsgService.instance().setSilentMode(True)
    open_file = ROOT.TFile(run_doc.output_data_file_tier_2.pfn)
    tree = open_file.Get("energy_output_tree")
    if not tree: return (run_doc, False)
    energyRV = ROOT.RooRealVar ("energy", "energy", 0, 0.05)
    sigmaRV = ROOT.RooRealVar("sigma", "sigma", .01, 0.000, 0.05)
    meanRV = ROOT.RooRealVar("mean", "mean", .02, 0, 0.05)
    argset = ROOT.RooArgSet(energyRV)

    # clear any previous results
    for i in [0,1,2]:
        current_chan = eval("run_doc.pulser_run_characteristics.chan_%i" % i)
        current_chan.sigma_err = []
        current_chan.sigma = []
        current_chan.mean = []
        current_chan.mean_err = []

    for pulser in run_doc.pulser_on_set:
        for chan in [0, 1]:
            current_chan = eval("run_doc.pulser_run_characteristics.chan_%i" % chan)
            data = ROOT.RooDataSet("data", "data", argset)
            for i in range(pulser[0], pulser[1]+1):
                tree.GetEntry(i)
                energyRV.setVal(tree.channel_info.GetChannel(chan).maximum - \
                                tree.channel_info.GetChannel(chan).baseline)
                data.add(argset)
            gaussPeak = ROOT.RooGaussian("gauss", \
              "gauss(energy, mean, sigma)", energyRV, meanRV, sigmaRV)
            gaussPeak.fitTo(data, ROOT.RooFit.PrintEvalErrors(False))
            current_chan.mean.append(meanRV.getVal())
            current_chan.mean_err.append(meanRV.getError())
            current_chan.sigma.append(sigmaRV.getVal())
            current_chan.sigma_err.append(sigmaRV.getError())

    return (run_doc, True)

def get_view():
    return view_virgin_pulser_data.get_view_class()
