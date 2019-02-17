from ortools.sat.python import cp_model

from src.domain.utils import SolverStatus

RESULTS_COUNT_LIMIT = 10


def create_couples(persons):
    """
    Create a list of couples without duplicate

    Args:
        persons (list[str]):

    Returns:
        list[set(str)]
    """
    list_of_couples = []
    for p1 in persons:
        for p2 in persons:
            couple = {p1, p2}
            if couple not in list_of_couples:
                list_of_couples += [couple]
    return list_of_couples


def create_model(persons, list_of_couples, dispos_per_person, sector_per_person):
    """
    Build the model

    Args:
        persons (list[str]):
        list_of_couples (list[set(str)]):
        dispos_per_person (dict[str: list[int]):
        sector_per_person (dict[str: int]):

    Returns:
        model (CpModel),
        couples (dict[int: NewBoolVar]),
        dispos_per_couple (dict[int: list[int]]):
    """

    model = cp_model.CpModel()

    couples = {}
    dispos_per_couple = {}
    sector_per_couple = {}
    for i, couple in enumerate(list_of_couples):
        if len(couple) == 2:
            p1, p2 = couple
            couples[i] = model.NewBoolVar('{}_coupled_with_{}'.format(p1, p2))
            dispos_p1 = dispos_per_person[p1]
            dispos_p2 = dispos_per_person[p2]
            dispos_per_couple[i] = [d_p1 for d_p1 in dispos_p1 for d_p2 in dispos_p2 if d_p1 == d_p2]
            sector_per_couple[i] = ((sector_per_person[p1] & sector_per_person[p2]) != 0)

        # A person cannot be coupled with itself
        if len(couple) == 1:
            couples[i] = model.NewBoolVar('{}_coupled_alone'.format(couple))
            dispos_per_couple[i] = []
            model.Add(couples[i] == False)
            sector_per_couple[i] = False

    # Define couples: 1 person linked to one other exactly
    for p1 in persons:
        model.Add(sum(couples[i] for i, couple in enumerate(list_of_couples) if p1 in couple) <= 1)

    for i in range(len(list_of_couples)):
        # If no sector in common or no disponibility in common, the couple cannot happen
        if sector_per_couple[i] is False or len(dispos_per_couple[i]) == 0:
            model.Add(couples[i] == False)

    return model, couples, dispos_per_couple, sector_per_couple


def exploration(persons, dispos_per_person, sector_per_person):
    """
    First iteration of the solver, that find the cost of the best configuration possible

    Args:
        persons (list[str]):
        dispos_per_person (dict[str: list[int]):
        sector_per_person (dict[str: int]):

    Returns:
        status (str),
        assignments(dict[tuple(str,str): list[int]),
        maximisation (int):
    """
    list_of_couples = create_couples(persons)
    model, couples, dispos_per_couples, sector_per_couples = create_model(persons,
                                                                          list_of_couples,
                                                                          dispos_per_person,
                                                                          sector_per_person)

    # model.Maximize(sum(len(dispos_per_couples[i])*couples[i] for i, couple in enumerate(list_of_couples)))

    max_dispo = max(len(dispos_per_couples[i]) for i in range(len(list_of_couples)))
    model.Maximize(sum(max_dispo*couples[i] for i, couple in enumerate(list_of_couples))
                   + sum(len(dispos_per_couples[i])*couples[i] for i, couple in enumerate(list_of_couples)))

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    status = solver.StatusName(status)

    if SolverStatus.success(status):
        satisfaction_assignment = save_solutions(solver, list_of_couples, couples, dispos_per_couples, sector_per_person)
        return status, satisfaction_assignment, solver.ObjectiveValue()

    else:
        print('Cannot find couples :\'(')
        return status, {}, 0


class VarArrayAndObjectiveSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print and save solutions."""

    def __init__(self, variables, list_of_couples, dispos_per_couples, sector_per_person):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__variables = variables
        self.__solution_count = 0
        self.__solution_limit = int(RESULTS_COUNT_LIMIT)
        self.solutions = []
        self.list_of_couples = list_of_couples
        self.dispos_per_couples = dispos_per_couples
        self.sector_per_person = sector_per_person

    def save_solutions(self, solution):
        print('Solution {}'.format(self.__solution_count))
        assignments = save_solutions(self, self.list_of_couples, solution, self.dispos_per_couples, self.sector_per_person)
        self.solutions.append(assignments)

    def NewSolution(self):
        self.__solution_count += 1
        self.save_solutions(self.__variables)
        # if self.__solution_count >= self.__solution_limit:
        #     self.StopSearch() # TODO implemetn

    def solution_count(self):
        return self.__solution_count


def satisfaction(persons, dispos_per_person, sector_per_person, maximisation):
    """
    Second iteration of the solver, that finds all configurations of couple, respecting the given maximisation cost

    Args:
        persons (list[str]):
        dispos_per_person (dict[str: list[int]):
        sector_per_person (dict[str: int]):
        maximisation (int):

    Returns:
        status (str),
        assignments (list[dict[tuple(str,str): list[int]]]])
    """
    list_of_couples = create_couples(persons)
    model, couples, dispos_per_couples, sector_per_couples = create_model(persons, list_of_couples, dispos_per_person, sector_per_person)

    # model.Add(sum(len(dispos_per_couples[i])*couples[i] for i, couple in enumerate(list_of_couples)) == int(maximisation))

    max_dispo = max(len(dispos_per_couples[i]) for i in range(len(list_of_couples)))
    model.Add(sum(max_dispo*couples[i] for i, couple in enumerate(list_of_couples))
             + sum(len(dispos_per_couples[i])*couples[i] for i, couple in enumerate(list_of_couples)) == int(maximisation))

    solution_printer = VarArrayAndObjectiveSolutionPrinter(couples,
                                                           list_of_couples,
                                                           dispos_per_couples,
                                                           sector_per_person)
    solver = cp_model.CpSolver()

    status = solver.SearchForAllSolutions(model, solution_printer)
    status = solver.StatusName(status)

    assignements = []
    if status not in ['INFEASIBLE', 'MODEL_INVALID', 'UNKNOWN']:
        assignements = solution_printer.solutions
    return status, assignements


def save_solutions(solver, list_of_couples, couples, dispos_per_couples, sector_per_person):
    """
    Print and Save solutions

    Args:
        solver (CpModel):
        list_of_couples (list[set(str)]):
        couples (couples (dict[int: NewBoolVar])):
        dispos_per_person (dict[str: list[int]):
        sector_per_person

    Returns:
        assignments (list[dict[tuple(str,str): list[int]]]])
    """

    assigments = {}
    assigned_couples = [(i, couple) for i, couple in enumerate(list_of_couples) if solver.Value(couples[i])]

    for i, couple in assigned_couples:
        p1, p2 = couple
        sector = sector_per_person[p1] & sector_per_person[p2]
        assigments[tuple(couple)] = (dispos_per_couples[i], sector)
        print('{} assigned to {} with dispo {} and sector {}'.format(p1, p2, dispos_per_couples[i], sector))
    return assigments


def solve_couples(employees):
    persons = [p['name'] for p in employees]
    disponibility_per_person = {p['name']: p['availabilities'] for p in employees}
    sector_per_person = {p['name']: p['sector'] for p in employees}

    print('---- Exploration ----')
    exploration_status, exploration_assignments, maximisation = exploration(persons,
                                                                            disponibility_per_person,
                                                                            sector_per_person)

    print('---- Satisfaction ----')
    satisfaction_status, satisfaction_assignments = satisfaction(persons,
                                                                 disponibility_per_person,
                                                                 sector_per_person,
                                                                 maximisation)

    return satisfaction_assignments
