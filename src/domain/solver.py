"""
Determine an optimal list of hotel to visit.
    ```
    $ python src/domain/solver.py \
        -s "/Users/fpaupier/projects/samu_social/data/hotels_subset.csv
    ```
    Note that the first record should be the adress of the starting point (let's say the HQ of the Samu Social)
"""
import argparse
import numpy as np


from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2

from src.services.map import Map
from src.services.csv_reader import parse_csv


def get_distances_matrix(addresses):
    """Compute the distance matrix (distance between each hotels).
    Returns a triangular matrix.
    
    Note:
        That the first address shall be the address of the depot.

    Args: 
        addresses(list[dict]): list of address, each dict has the struct
            {'address': 'Avenue Winston Churchill', 'postcode': 27000}
    Returns:
        distances(list[list[int]]): matrix of distances

    """
    map = Map()
    distances = []

    for address1 in addresses:
        src_address = {
            "address": address1.get("address"),
            "postcode": address1.get("postcode"),
        }
        src_dist = []
        for address2 in addresses:
            target_address = {
                "address": address2.get("address"),
                "postcode": address2.get("postcode"),
            }
            point1 = map.point(src_address)
            point2 = map.point(target_address)

            distance = map.distance(point1, point2)
            distance = int(np.round(distance * 1000))  # Work with distance expressed in meters
            src_dist.append(distance)
        distances.append(src_dist)
    return distances


###########################
# Problem Data Definition #
###########################
def create_data_model(addresses_source, number_workers):
    """Creates the data for the example.
    Args:
        addresses_source(list[dict])
    """
    data = {}
    # Array of distances between locations.
    addresses = parse_csv(addresses_source, "hotel", write=False)
    _distances = get_distances_matrix(addresses)
    data["distances"] = _distances
    data["num_locations"] = len(_distances)
    data["num_vehicles"] = number_workers  # FIXME: Do not hardcode number of vehicles - dynamic arg
    data["depot"] = 0
    return data


#######################
# Problem Constraints #
#######################
def create_distance_callback(data):
    """Creates callback to return distance between points."""
    distances = data["distances"]

    def distance_callback(from_node, to_node):
        """Returns the manhattan distance between the two nodes"""
        return distances[from_node][to_node]

    return distance_callback


def add_distance_dimension(routing, distance_callback):
    """Add Global Span constraint"""
    distance = "Distance"
    maximum_distance = 300000  # Maximum distance per vehicle expressed in meters
    routing.AddDimension(
        distance_callback,
        0,  # null slack
        maximum_distance,
        True,  # start cumul to zero
        distance,
    )
    distance_dimension = routing.GetDimensionOrDie(distance)
    # Try to minimize the max distance among vehicles.
    distance_dimension.SetGlobalSpanCostCoefficient(100)


###########
# Printer #
###########
def print_solution(data, routing, assignment):
    """Print routes on console."""
    total_distance = 0
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        plan_output = "Route for vehicle {}:\n".format(vehicle_id)
        route_dist = 0
        while not routing.IsEnd(index):
            node_index = routing.IndexToNode(index)
            next_node_index = routing.IndexToNode(
                assignment.Value(routing.NextVar(index))
            )
            route_dist += routing.GetArcCostForVehicle(
                node_index, next_node_index, vehicle_id
            )
            plan_output += " {0} ->".format(node_index)
            index = assignment.Value(routing.NextVar(index))
        plan_output += " {}\n".format(routing.IndexToNode(index))
        plan_output += "Distance of route: {}m\n".format(route_dist)
        print(plan_output)
        total_distance += route_dist
    print("Total distance of all routes: {}m".format(total_distance))


########
# Main #
########
def main(addresses_source, number_workers):
    """Entry point of the program"""
    # Instantiate the data problem.
    data = create_data_model(addresses_source, number_workers)
    # Create Routing Model
    routing = pywrapcp.RoutingModel(
        data["num_locations"], data["num_vehicles"], data["depot"]
    )
    # Define weight of each edge
    distance_callback = create_distance_callback(data)
    routing.SetArcCostEvaluatorOfAllVehicles(distance_callback)
    add_distance_dimension(routing, distance_callback)
    # Setting first solution heuristic (cheapest addition).
    search_parameters = pywrapcp.RoutingModel.DefaultSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )  # pylint: disable=no-member
    # Solve the problem.
    assignment = routing.SolveWithParameters(search_parameters)
    if assignment:
        print_solution(data, routing, assignment)


if __name__ == "__main__":
    """
    Solve a Vehicle Routing Problem

    Note:
        The first record should be the adress of the starting point (let's say the HQ of the Samu Social)

    """
    parser = argparse.ArgumentParser(
        description="Solve a Vehicle Routing Problem"
    )
    parser.add_argument("-s", "--source", help="path to the source address csv file", type=str)
    parser.add_argument("-n", "--number_workers", help="Number of workers available to perform the visit", type=int, default=4)


    args = parser.parse_args()
    main(args.source, args.number_workers)
