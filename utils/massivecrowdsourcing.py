class MassiveCrowdSourcing(object):
    """
    An implementation of "Verification in Referral-Based Crowdsourcing,"
    Victor Naroditskiy, et al. PLOS One, (2012)

    This implementation assumes a social network of workers on a crowdsourced platform
    (e.g. MTurks on Amazon MTurK). While the variable names are obtuse
    they follow those referenced in the paper above along with documentation.

    This implementation is unique in that it is parameterized upon MTurk, national min wage
    and how long we expect it to take to *verify* a report of firm meta data. From these values
    an optimal reward amount is derived.

    t: Probabilty that a node has the answer
    f: Probabilty of a node is irrational and also generates a false answer (disjoint with t)
    e: Verification cost, price we pay to verifier to verify a report
    c: Penalty for submitting false report. This is the removal of an extra bonus to the parent
    r: Reward offered by the root node. This shuld be r >= min(r_i) for all nodes i
    s_j_1: Percentage of reward that node j must pay to its parent. This is the recursive payment propagated.
            The paper shows that s_j is optimal (see Optimal Split Contract) when set to 1/2 (0.5) and
                s_j_1 = (1-s_j)*s_j
                s_j_1 = (1-1/2)(1/2) = 1/4

            for j = 2
    """
    def __init__(self,
                 t=0.80,
                 f=0.20,
                 sj=0.25,
                 c=None,
                 r=None,
                 e=None,
                 num_min_to_review=5,
                 wage_per_min=0.18,
                 calculate_optimal_values=True):

        self.t = t
        self.f = f
        self.sj = sj

        # variables we can set optimally given the paper above
        # ... requires one of them to be fixed
        self.c = c
        self.r = r
        self.e = e

        # On the MTurk platform we can assume a fixed e by taking an
        # assumed average time required to verify a report multipled by a fair wage
        self.e = num_min_to_review * wage_per_min
        self.c = self.e * (1+self.t/self.f)

        # now we can caluculate the minimum reward to encourage a node i to particpate
        # node i is the zero index node relative to/counting back from the node finding the firm data
        i = 2 # let's say
        r_i_min = (1+self.f/self.t) * \
                     self.e/((1-self.s_i(i-1))*self.s_i(i))

        print(r_i_min, ' is the amount we expect to pay for node 2 to particpate')

    def s_i(self, node_i):
        """
        Calculate percentage s_i of the reward given that is given to node_i
        node_i value is an index that is 0 indexed from the first person to report
        (the finder) along the referral path.

        This implements Table 1 calculations.

        e.g., s_i(0) = 1/2 of the reward is given to the first node along any path form the finder/reporter
        e.g., s_i(2) = 1/8 of the reward is given to the third node along any path from the finder/reporter
        """
        assert node_i >= 0, "node i 0 based index is less than 0!"

        return (self.sj)**(1 + node_i)
