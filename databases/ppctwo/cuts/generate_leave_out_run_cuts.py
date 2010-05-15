from cuts.database_cuts import MGCut

class LeaveOutRunsCut(MGCut):
    def get_description_of_cut(self):
        return "leave_out_run_cuts_for_runs"

    def get_verbose_description_of_cut(self):
        return """
Leaves out specific runs which we sould like to 
cut by hand, e.g. a run that was taking
during a test.

Run 1933 has time rollover.
               """

    def get_string_of_cut(self):
        return """not _id == '1204' and not _id == '1933'"""

def get_cut_class():
    return LeaveOutRunsCut()

