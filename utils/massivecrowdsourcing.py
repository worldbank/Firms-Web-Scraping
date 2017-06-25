class MassiveCrowdSourcing(object):
    """
    An implementation of "Verification in Referral-Based Crowdsourcing,"
    Victor Naroditskiy, et al. PLOS One, (2012)

    This implementation assumes a social network of workers on a crowdsourced platform
    (e.g. MTurks on Amazona MTurK).
    """
    def __init__(self,
                 t=0.90,
                 f=0.10,
                 e=0.10,
                 c=0.30,
                 r=5,
                 sj_1=0.25,
                 calculate_min_values=True):
        self.t = t
        self.f = f
        self.e = e
        self.c = c
        self.r = r
        self.sj_1 = sj_1

    def max_verification_cost(self):
        return self.f


