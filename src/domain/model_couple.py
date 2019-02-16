from ortools.sat.python import cp_model

from src.domain.availability_model import read_employees_file
from src.domain.utils import SolverStatus

RESULTS_COUNT_LIMIT = 10


def create_model(persons, dispos_per_person):

    model = cp_model.CpModel()

    couples = {}
    dispos_per_couples = {}
    for p1 in persons:
        couples[p1] = {}
        dispos_per_couples[p1] = {}
        for p2 in persons:
            couples[p1][p2] = model.NewBoolVar('{}_coupled_with_{}'.format(p1, p2))
            dispos_p1 = dispos_per_person[p1]
            dispos_p2 = dispos_per_person[p2]
            dispos_per_couples[p1][p2] = [d_p1 for d_p1 in dispos_p1 for d_p2 in dispos_p2 if d_p1 == d_p2]

            # A person cannot be coupled with itself
            if p1 == p2:
                dispos_per_couples[p1][p2] = []
                model.Add(couples[p1][p2] == False)

    # Define couples: 1 person linked to one other exactly
    for p1 in persons:
        model.Add(sum(couples[p1][p2] for p2 in persons) == 1)

    # Define couples: person 1 linked to person 2 implies that person 2 is linked to person 1
    for p1 in persons:
        for p2 in persons:
            model.Add(couples[p1][p2] == couples[p2][p1])

    return model, couples, dispos_per_couples, dispos_per_couples


def exploration(persons, dispos_per_persons):
    model, couples, dispos_per_persons, dispos_per_couples = create_model(persons, dispos_per_persons)

    model.Maximize(sum(len(dispos_per_couples[p1][p2])*couples[p1][p2] for p1 in persons for p2 in persons))

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    status = solver.StatusName(status)

    if SolverStatus.success(status):
        return status, print_solutions(solver, persons, couples, dispos_per_couples), solver.ObjectiveValue()

    else:
        print('Cannot find couples :\'(')
        return status, 0, {}


class VarArrayAndObjectiveSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print and save solutions."""

    def __init__(self, variables, persons, dispos_per_couples):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__variables = variables
        self.__solution_count = 0
        self.__solution_limit = int(RESULTS_COUNT_LIMIT)
        self.solutions = []
        self.persons = persons
        self.dispos_per_couples = dispos_per_couples

    def save_solutions(self, solution):
        print('Solution {}'.format(self.__solution_count))
        assignments = print_solutions(self, self.persons, solution, self.dispos_per_couples)
        self.solutions.append(assignments)

    def NewSolution(self):
        self.__solution_count += 1
        self.save_solutions(self.__variables)
        if self.__solution_count >= self.__solution_limit:
            self.StopSearch()

    def solution_count(self):
        return self.__solution_count


def satisfaction(persons, dispos_per_persons, maximisation):
    model, couples, dispos_per_persons, dispos_per_couples = create_model(persons, dispos_per_persons)

    model.Add(sum(len(dispos_per_couples[p1][p2])*couples[p1][p2] for p1 in persons for p2 in persons) == int(maximisation))

    solution_printer = VarArrayAndObjectiveSolutionPrinter(couples, persons, dispos_per_couples)
    solver = cp_model.CpSolver()

    status = solver.SearchForAllSolutions(model, solution_printer)
    status = solver.StatusName(status)

    assignements = []
    if status not in ['INFEASIBLE', 'MODEL_INVALID', 'UNKNOWN']:
        assignements = solution_printer.solutions
    return status, assignements


def print_solutions(solver, persons, couples, dispos_per_couples):
    assigments = {}
    for p1 in persons:
        assigned_p2 = [p2 for p2 in persons if solver.Value(couples[p1][p2])][0]
        if set((p1,assigned_p2)) not in [set(k) for k in assigments.keys()]:
            assigments[(p1,assigned_p2)] = dispos_per_couples[p1][assigned_p2]
    for (p1, p2), dispos in assigments.items():
        print('{} assigned to {} with dispo {}'.format(p1,p2, dispos_per_couples[p1][p2]))
    return assigments


def main():
    # import ipdb; ipdb.set_trace()
    data = read_employees_file('/Users/emericbris/Downloads/55/fichier-salarie.csv')
    persons = [x['name'] for x in data]
    dispos_per_persons = {x['name']: x['availabilities'] for x in data}

    persons = ['Em', 'Pop', 'E', 'Palpal']
    dispos_per_persons = {'Em': [[1,4],[4,8],[12, 16]],
                          'Pop': [[1,4],[12,16],[16, 20]],
                          'E': [[4,8],[12,16],[16, 20]],
                          'Palpal': [[12,16],[16, 20]]}

    print('---- Exploration ----')
    exploration_status, exploration_assignments, maximisation = exploration(persons, dispos_per_persons)

    print('---- Satisfaction ----')
    satisfaction_status, satisfaction_assignments = satisfaction(persons, dispos_per_persons, maximisation)


if __name__ == "__main__":
    main()

