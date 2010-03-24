import os
import math


def rescale_frame(canvas, frame, scale, title):
    """
    HACK
    Takes a frame and rescales it to arbitrary coordinates. 
    This is helpful when dealing with RooPlot to get the axes
    correct.  Returns axis in case anything else needs to be done.
    """
    import ROOT
    yaxis = frame.GetYaxis()
    yaxis.SetTickLength(0)
    yaxis.SetNdivisions(0)
    yaxis.SetLabelSize(0)
    yaxis.SetTitle("")
    yaxis.SetLabelColor(10)
    yaxis.SetAxisColor(10)
    frame.Draw()
    canvas.Update()
    max = frame.GetMaximum()
    min = frame.GetMinimum()
    new_max = max*scale
    new_min = min*scale
    
    axis = ROOT.TGaxis(canvas.GetUxmin(), canvas.GetUymin(),
                       canvas.GetUxmin(), canvas.GetUymax(),
                       new_min,new_max,510,"")
    axis.SetTitle(title)
    axis.Draw()
    canvas.Update()
    return axis


def detectCPUs():
     """
     Detects the number of CPUs on a system. Cribbed from pp.
     """
     # Linux, Unix and MacOS:
     if hasattr(os, "sysconf"):
         if os.sysconf_names.has_key("SC_NPROCESSORS_ONLN"):
             # Linux & Unix:
             ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
             if isinstance(ncpus, int) and ncpus > 0:
                 return ncpus
         else: # OSX:
             return int(os.popen2("sysctl -n hw.ncpu")[1].read())
     # Windows:
     if os.environ.has_key("NUMBER_OF_PROCESSORS"):
             ncpus = int(os.environ["NUMBER_OF_PROCESSORS"]);
             if ncpus > 0:
                 return ncpus
     return 1 # Default


"""
  SignalHandler handles signals being sent to and from a process.
"""
class SignalHandler:
    exit_requested = False
    #@classmethod
    def exit_handler(self, signum, frame):
        print "Process %i: Exit (%i) has been requested..." % \
            (os.getpid(), signum)
        self.exit_requested = True

    #@classmethod
    def is_exit_requested(self):
        return self.exit_requested
    exit_handler = classmethod(exit_handler)
    is_exit_requested = classmethod(is_exit_requested)





def unroll_RooAbsPdf(apdf, scale = 1, scale_error = 0):
    """
      Unrolls a RooAbsPdf, allowing us to understand the components
      in the context of what the absolute value of each component.
    """
    temp_dict = {}
    try:
        coeflist = apdf.coefList()
        var =  coeflist[0]
        # If we get here we're a RooAbsPdf
        pdflist = apdf.pdfList()
        error = scale*var.getVal()*math.sqrt(math.pow(scale_error/scale, 2) + 
            math.pow(var.getError()/var.getVal(), 2))

        temp_dict.update(unroll_RooAbsPdf(pdflist[0], var.getVal()*scale, error))
        scale_error = scale*(1. - var.getVal())*math.sqrt(math.pow(scale_error/scale, 2) 
                              + math.pow(var.getError()/(1-var.getVal()), 2))
        scale *= (1 - var.getVal())
        temp_dict.update(unroll_RooAbsPdf(pdflist[1], scale, scale_error))
    except AttributeError: 
        #print "PDF: %s, amplitude: %f, error: %f" % (apdf.GetName(), 
        #                                        scale, 
        #                                        scale_error)
        try:
            pdflist = apdf.pdfList()
            #print "Printing out components of %s:" % apdf.GetName()
            for i in range(pdflist.getSize()): temp_dict.update(unroll_RooAbsPdf(pdflist[i], scale, scale_error))
        except AttributeError: pass 

        temp_dict[apdf.GetName()] = (scale, scale_error)
        pass
    return temp_dict
