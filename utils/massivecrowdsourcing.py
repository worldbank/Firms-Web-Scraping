"""MassiveCrowdSourcing

This is an implementation of the paper below. This class would be used
if any MTurkers referred another MTurker and we needed to determine
the required pay out. It also provides payment amounts for a fixed budget.

This code is currently unused and isn't as required due to MTurkers being
mostly anonymous and unable to easily refer other MTurkers; most of the
crowdsourcing is done as direct firm metadata submissions and not referred ones.

However, it may be possible to change the requirement for a MTurk ID to just
providing a unique "handle" known to you and the other MTurker; this way they
would not have to share MTurk (Worker) IDs and can still referr others.
"""

class MassiveCrowdSourcing(object):
    """
    An implementation of "Verification in Referral-Based Crowdsourcing,"
    Victor Naroditskiy, et al. PLOS One, (2012)

    This implementation assumes a social network of workers on a crowdsourced platform
    (e.g. MTurks on Amazon MTurK). While the variable names are obtuse
    they follow those referenced in the paper above along with documentation.

    Essentially, given a penalty (with held bonus in terms of MTurk) `e` and a
    verification cost `e`, time a Turker has to spend verifying something and how much we pay them for it, we can
    calculate the minimum total reward you must be willing to spend to encourage a
    social network of depth `i` to particpate.

    The social network is paid out according to scheme in `reward_for_node_i`
    and follows the 1/2 split incentive contract that is shown to be optimal in the paper
    for spending the least amount of money.

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
                 t=1/3,
                 f=2/3,
                 sj=0.5,
                 c=None,
                 r=None,
                 e=None,
                 idx=3,
                 wage_per_min=0.18):

        self.t = t
        self.f = f
        self.sj = sj

        # variables we can set optimally given the paper above
        # ... requires one of them to be fixed
        if not e or not c:
            self.e = wage_per_min # assume 1 minute of time to verify
            self.c = self.c_min(e=self.e)
            self.total_reward = self.reward_min(i=idx)

    def reward_for_node_i(self, i=2, reward=None):
        """
        This calculates the payment given to a node_i, with i 0 indexed from the reporter.
        So, e.g., the parent of the report is i = 1, the parent of the parent of the reporter
        is i = 2, etc. all the way to the root.

        Note: This notation is different than the paper which 0 indexes from the root.
        Note: A feature of this optimal pricing is that the total reward actually paid out
        may not equal the total reward we are willing to pay and may be less.

        An example of this is: If we have a reward of $12 but only care about 2 level deep networks then we only pay
        out $6 to the reporter and $3 to their parent, who then verifies and sends the report to us.
        Only $9 is spent here.
        """
        # now we can caluculate the 1/2 split contract reward to node i
        if not reward:
            reward = self.total_reward
        reward = self.s_i(i) * reward
        print(reward, ' is the amount we pay to node {} to particpate'.format(i))
        return reward

    def reward_min(self, i=2):
        """
        i indicates the node index and we calculate the minimum total reward needed for incetativing
        up to node i = i particpation, including node_i verification of any child reports.
        """
        # now we can caluculate the minimum *total reward* to encourage a parent node i to particpate
        # under the payment distribution scheme node `reward_for_node_i`
        assert i > 0, "Can only calculate minimium rewards for networks involving at least 2 nodes on path"
        r_i_min = (1+(self.f/self.t)) * \
                     self.e/((1-self.s_i(i+1))*self.s_i(i))
        # we do s_i(i+1) because we're indexing from the reporter, not from the root
        # so s_i-1 = s_i+1 in this implementation

        print(r_i_min, ' is the minimum reward offered by the root'.format(i))
        return r_i_min

    def c_min(self, e):
        return (1 + self.t/self.f)*e

    def e_max(self, c):
        return c*self.f/(self.t + self.f)

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
