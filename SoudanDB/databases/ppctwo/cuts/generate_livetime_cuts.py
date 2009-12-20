from database_cuts import MGCut

class LiveTimeCut(MGCut):
    def get_description_of_cut(self):
        return "livetime_cut_for_runs"

    def get_verbose_description_of_cut(self):
        return """
Generates a livetime cut effectively removing runs when
the livetime is significantly different than 1 hour.  This
deals with runs that might span multiple files (which is
very irregular) and removes other errors such as power failures.
               """

    def get_string_of_cut(self):
        return """math.fabs(livetime.run_seconds - 3600)\
                  < 3*livetime.run_seconds_error"""

def get_cut_class():
    return LiveTimeCut()

