from ortools.graph import pywrapgraph
from ortools.sat.python import cp_model


def create_model(persons, hotels, distances):
    model = cp_model.CpModel()

    assignment = {}
    for person in persons:
        assignment[person] = {}
        for hotel in hotels:
            assignment[person][hotel] = model.NewBoolVar('{}_hotel_{}'.format(person, hotel))

    # Strictly assign one person to one hotel
    for person in persons:
        model.Add(sum([assignment[person][h] for h in hotels]) == 1)

    model.Minimize(sum(assignment[p][h]*distances[p][h] for p in persons for h in hotels))

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    status = solver.StatusName(status)

    for p in persons:
        print([solver.Value(assignment[p][h]) for h in hotels])
        for h in hotels:
            if solver.Value(assignment[p][h]):
                print('Person {} assigned to {} with distance {}'.format(p, h, distances[p][h]))

    return status, assignment


def create_model_assignment(persons, hotels, distances):
    """
    Model using assigment N - N
    :param persons:
    :param hotels:
    :param distances:
    :return:
    """
    assignment = pywrapgraph.LinearSumAssignment()

    for i, person in enumerate(persons):
        for j, hotel in enumerate(hotels):
            if distances[person][hotel]:
                assignment.AddArcWithCost(i, j, distances[person][hotel])

    solve_status = assignment.Solve()
    if solve_status == assignment.OPTIMAL:
        print('Total cost = ', assignment.OptimalCost())
        print()
        for i in range(0, assignment.NumNodes()):
            print('Person {} assigned to hotel {}. Distance = {}'
                  .format(i,
                          assignment.RightMate(i),
                          assignment.AssignmentCost(i)))
    elif solve_status == assignment.INFEASIBLE:
        print('No assignment is possible.')
    elif solve_status == assignment.POSSIBLE_OVERFLOW:
        print('Some input costs are too large and may cause an integer overflow.')


def main():
    persons = ['A', 'B', 'C']
    hotels = ['formule1', 'ibis', 'grand hotel', 'premiere classe', 'b&b']
    distances = {'A': {'formule1': 10, 'ibis': 5, 'grand hotel': 15, 'premiere classe': 12, 'b&b': 18},
                 'B': {'formule1': 2, 'ibis': 10, 'grand hotel': 5, 'premiere classe': 18, 'b&b': 8},
                 'C': {'formule1': 7, 'ibis': 7, 'grand hotel': 12, 'premiere classe': 6, 'b&b': 12}}

    create_model(persons, hotels, distances)


if __name__ == "__main__":
    main()
