class SolverStatus(object):
    """
    Define how to format the status ouput of the solver
    """
    OPTIMAL = 'OPTIMAL'
    FEASIBLE = 'FEASIBLE'
    INFEASIBLE = 'INFEASIBLE'
    MODEL_INVALID = 'MODEL_INVALID'
    UNKNOWN = 'UNKNOWN'

    @classmethod
    def fail(cls, status):
        """

        :param status: (str)
        :return: bool
        """
        return status in [cls.UNKNOWN, cls.INFEASIBLE, cls.MODEL_INVALID]

    @classmethod
    def success(cls, status):
        """

        :param status: (str)
        :return: bool
        """
        return status in [cls.OPTIMAL, cls.FEASIBLE]