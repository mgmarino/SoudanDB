from database_cuts import MGCut

class BaselineCut(MGCut):
    def get_description_of_cut(self):
        return "baseline_cut_for_runs"

    def get_verbose_description_of_cut(self):
        return """
Generates a baseline cut effectively removing runs when
the baseline shifts significantly.  This affects runs
during cooling cycles when the FET is changing temperature
quickly.  It also removes runs that occur when the FET is 
very warm, corresponding to a baseline of below -1000 ADC
units.
               """

    def get_string_of_cut(self):
        return """not (math.fabs(baseline_dict.first_ten_percent_fit_constant -\
                  baseline_dict.last_ten_percent_fit_constant) >\
                  (baseline_dict.first_ten_percent_fit_constant_rms +\
                  baseline_dict.last_ten_percent_fit_constant_rms)\
                  or baseline_dict.average_fit_constant < -1000)"""

def get_cut_class():
    return BaselineCut()
