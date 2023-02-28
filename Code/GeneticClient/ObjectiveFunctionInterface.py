from pyharmonysearch import ObjectiveFunctionInterface as OFI

class ObjectiveFunction(OFI):
    """
    This defines the objective function HS optimizes.
    This MUST be present for 
    """

    def __init__(self):
        # TODO setup algorithm to HARMONYSEARCH over
        # PLACEHOLDER
        self._lower_bounds = [-1000, -1000]
        self._upper_bounds = [1000, 1000]
        self._variable = [False, True]

        # define all input parameters
        # PLACEHOLDER
        self._maximize = True  # do we maximize or minimize?
        self._max_imp = 50000  # maximum number of improvisations
        self._hms = 100  # harmony memory size
        self._hmcr = 0.75  # harmony memory considering rate
        self._par = 0.5  # pitch adjusting rate
        self._mpap = 0.25  # maximum pitch adjustment proportion (new parameter defined in pitch_adjustment()) - used for continuous variables only
        self._mpai = 2  # maximum pitch adjustment index (also defined in pitch_adjustment()) - used for discrete variables only

    def get_fitness(self, vector):
        """
            Return the objective function value given a solution vector containing each decision variable. In practice,
            vector should be a list of parameters.
            For example, suppose the objective function is (-(x^2 + (y+1)^2) + 4). A possible call to fitness may look like this:
            >>> print obj_fun.fitness([4, 7])
            -76
        """
        
        pass

    def get_value(self, i, j=None):
        """
            Get a valid value of parameter i. You can return values any way you like - uniformly at random, according to some
            distribution, etc.
            For example, suppose the x parameter in fitness() varies uniformly at random in the range [-1000, 1000]:
            >>> print obj_fun.get_value(0)
            763.406542555
            >>> print obj_fun.get_value(0)
            -80.8100680841
            j is used only for discrete parameters in the pitch adjustment step. j maps to some value the discrete
            parameter can take on. If parameter i is continuous, j should be ignored.
            For example, suppose that a variable z is discrete and can take on the values [-3, -1, 0, 3, 4.5, 6.3, 8, 9, 12]. Also
            suppose that z is the 3rd parameter in the objective function (i.e., i = 2).
            >>> print obj_fun.get_value(2, 1)
            -1
            >>> print obj_fun.get_value(2, 3)
            3
        """
        
        pass

    def get_index(self, i, v):
        """
            Get the index of the value v of the specified parameter.
            As an example, consider the variable z from get_value() above:
            >>> print obj_fun.get_index(2, 6.3)
            5
            This will only be called for discrete variables in the pitch adjustment step. The behavior here isn't well-defined in the case
            where the possible values for a variable contain non-unique elements.
            For best performance, store discrete values in a sorted list that can be binary searched. Additionally, this list should not
            contain any duplicate values.
        """
        
        pass

    def get_num_discrete_values(self, i):
        """
            Get the number of values possible for the discrete parameter i.
            As an example, consider the variables z and x from get_value() above:
            >>> print get_num_discrete_values(2)
            9
            >>> print get_num_discrete_values(0)
            inf
            This will only be called for discrete variables in the pitch adjustment step. If i is a continuous variable, +inf
            can be returned, but this function might not be implemented for continuous variables, so this shouldn't be
            counted on.
        """
        
        pass

    def get_lower_bound(self, i):
        """
            Return the lower bound of parameter i. Using the example for fitness(), the lower bound for y may be -1000.
            Seeing as y is the 2nd parameter (index 1 in a 0-indexed system), this call may look like the following:
            >>> print obj_fun.lower_bound(1)
            -1000
            This will only be called for continuous variables in the pitch adjustment step.
        """
        
        pass

    def get_upper_bound(self, i):
        """
            Return the upper bound of parameter i.
            This will only be called for continuous variables in the pitch adjustment step.
        """
        
        pass

    def is_variable(self, i):
        """
            Return whether or not the parameter at the specified index should be varied by HS. It may be the case that HS should
            only vary certain parameters while others should remain fixed. In the fitness() example, perhaps HS should only vary x.
            This call may look like:
            >>> print obj_fun.is_variable(0)
            True
            >>> print obj_fun.is_variable(1)
            False
            Note that if a parameter is not variable, it should still return a valid value in get_value(). This value can be constant,
            but a valid value must be returned.
        """
        
        pass

    def is_discrete(self, i):
        """
            Return whether or not the parameter at the specified index is a discrete parameter. Not all parameters may be continuous.
            This only really matters in the pitch adjustment step of HS. Suppose that x is continuous (e.g., x varies in [-1000, 1000]),
            and y is discrete (e.g., y is only allowed to take on values [-5, 3, 6, 9, 12, 45]):
            >>> print obj_fun.is_discrete(0)
            False
            >>> print obj_fun.is_discrete(1)
            True
        """
        
        pass

    def get_num_parameters(self):
        """
            Return the number of parameters used by the objective function. Using the example in fitness(), this will be 2.
            A sample call may look like the following:
            >>> print obj_fun.get_num_parameters()
            2
        """
        
        pass

    def use_random_seed(self):
        """
            Return whether or not a random seed should be used. If a random seed is used, the same result will be generated each time (i.e., multiple
            HS iterations will return the same best solution).
        """
        
        pass

    def get_random_seed(self):
        """
            Return an optional random seed. If use_random_seed() == False, this won't be called.
        """
        
        pass

    def get_max_imp(self):
        """
            Return the maximum number of improvisations. This represents the stopping criterion (i.e., the number of fitness evaluations HS
            performs until search stops).
        """
        
        pass

    def get_hmcr(self):
        """
            Return the harmony memory considering rate. This represents the proportion of memory consideration calls vs. random selection calls.
        """
        
        pass

    def get_par(self):
        """
            Return the pitch adjusting rate. This represents how often pitch adjustment will occur if memory consideration has already been done.
        """
        
        pass

    def get_hms(self):
        """
            Return the harmony memory size. This represents the size of the vector that stores previously best harmonies.
        """
        
        pass

    def get_mpai(self):
        """
            Return the maximum pitch adjustment index. This determines the range from which pitch adjustment may occur for discrete variables. Also known as
            discrete bandwidth.
        """
        
        pass

    def get_mpap(self):
        """
            Return the maximum pitch adjustment proportion. This determines the range from which pitch adjustment may occur for continuous variables. Also known as
            continuous bandwidth.
        """
        
        pass

    def maximize(self):
        """
            Return True if this is a maximization problem, False if minimization problem.
        """
        
        pass