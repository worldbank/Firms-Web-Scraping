class MassiveCrowdSourcing(object):
    """
    An implementation of "Verification in Referral-Based Crowdsourcing,"
    Victor Naroditskiy, et al. PLOS One, (2012)

    This implementation assumes a social network of workers on a crowdsourced platform
    (e.g. MTurks on Amazon MTurK). While the variable names are obtuse
    they follow those referenced in the paper above along with documentation.

    Essentially, given a penalty (with held bonus in terms of MTurk) `e` and a
    verification cost `e`, time a Turker has to spend verifying something, we can
    calculate the minium total reward you must be willing to spend to encourage a
    social network of depth `i` to particpate.

    In any case, the social network is paid out according to scheme in `reward_for_node_i`
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
                 c=0.75,
                 r=None,
                 e=0.50,
                 num_min_to_review=5,
                 wage_per_min=0.18,
                 calculate_optimal_values=True):

        self.t = t
        self.f = f
        self.sj = sj

        # variables we can set optimally given the paper above
        # ... requires one of them to be fixed
        self.c = c
        self.total_reward = r
        self.e = e

    def reward_for_node_i(self, i=2, reward=None):
        # now we can caluculate the minimum reward to encourage a node i to particpate
        # node i is the zero index node relative to/counting back from the node finding the firm data
        if not reward:
            reward = self.total_reward
        reward = self.s_i(i) * reward
        print(reward, ' is the amount we pay to node {} to particpate'.format(i))

    def reward_min(self, i=2):
        """
        i indicates the node index, where i+1 is the reporting node (node that found firm metadata).
        i-1 is the parent of i and here we calculate the minimum total reward required for node i
        to bother to verify the report and send it directly to the root (e.g., complete the HIT)
        """
        # now we can caluculate the minimum *total reward* to encourage a parent node i to particpate
        # under the payment distribution scheme node `reward_for_node_i`
        assert i > 0, "Can only calculate minimium rewards for networks involving at least 2 nodes on path"
        r_i_min = (1+self.f/self.t) * \
                     self.e/((1-self.s_i(i-1))*self.s_i(i))

        print(r_i_min, ' is the minimum reward offered by the root'.format(i))

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
