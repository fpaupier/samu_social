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


def get_distances_matrix(hotels):
    """Compute the distance matrix (distance between each hotels).
    Returns a triangular matrix and the labels of the hotels.

    Note:
        1) That the first address shall be the address of the depot.
        2) If the API doesn't returna a match for the address, we drop
            the point. This may not be the expected behavior. TODO


    Args: 
        hotels(list[dict]): list of address, each dict has the struct
            {'address': 'Avenue Winston Churchill', 'postcode': 27000}
    Returns:
        distances(list[list[int]]): matrix of distances
        labels(dict[int, string]): the index of the address and it's name

    Warnings:
        Function seems to break if size of input hotels is too big ? Returns empty distances
        that leads to a segmentation fault down the processing pipeline.

    """
    map = Map()
    distances = []
    labels = dict()

    index = 0
    for hotel1 in hotels:
        src_address = {
            "address": hotel1.get("address"),
            "postcode": hotel1.get("postcode"),
        }
        # point1 = map.point(src_address)
        point1 = hotel1['point']
        src_dist = []
        if not point1:
            continue

        labels[index] = "{} {}".format(
            src_address.get("address"), src_address.get("postcode")
        )  # Store the address as labels for the node
        index = index + 1
        for hotel2 in hotels:
            target_address = {
                "address": hotel2.get("address"),
                "postcode": hotel2.get("postcode"),
            }
            # point2 = map.point(target_address)
            point2 = hotel2['point']

            if not point2:
                continue

            distance = map.distance(point1, point2)
            distance = int(np.round(distance * 1000))  # Distance expressed in meters
            src_dist.append(distance)

        if (point1 is not None) and (point2 is not None):
            distances.append(src_dist)
    
    return distances, labels


###########################
# Problem Data Definition #
###########################
def create_data_model(hotels, number_workers, from_raw_data):
    """Creates the data for the example.
    Args:
        hotels(list[dict])
        number_workers(int): number of Samu Social worker available
        from_raw_data(bool):
    """
    data = {}
    # Array of distances between locations.
    if from_raw_data:
        hotels_data = parse_csv(hotels, "hotel", write=False)
    else:
        hotels_data = hotels
    _distances, labels = get_distances_matrix(hotels_data)
    data["distances"] = _distances
    data["num_locations"] = len(_distances)
    data["num_vehicles"] = number_workers
    data["depot"] = 0
    data["labels"] = labels
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
# FORMATTER #
###########
def format_solution(data, routing, assignment):
    """Print routes on console."""
    plan_output = dict()
    for vehicle_id in range(data["num_vehicles"]):
        plan_output[vehicle_id] = []
        route = []
        index = routing.Start(vehicle_id)
        route_dist = 0
        while not routing.IsEnd(index):
            node_index = routing.IndexToNode(index)
            next_node_index = routing.IndexToNode(
                assignment.Value(routing.NextVar(index))
            )
            route_dist += routing.GetArcCostForVehicle(
                node_index, next_node_index, vehicle_id
            )
            route.append(("{0}".format(data["labels"].get(node_index))))
            index = assignment.Value(routing.NextVar(index))
        # Add return address to the route
        route.append((data["labels"].get(routing.IndexToNode(index))))
        plan_output[vehicle_id] = route
    return plan_output


########
# Main #
########
def solve_routes(hotels, number_workers, from_raw_data=False):
    """
    Entry point of the program

    Args:
        hotels:
        number_workers:
        from_raw_data (bool): should we consider the raw csv file or not

    Returns:


    """
    # Instantiate the data problem.
    data = create_data_model(hotels, number_workers, from_raw_data)
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
        itinerary = format_solution(data, routing, assignment)
        return itinerary
    else:
        return None


if __name__ == "__main__":
    """
    Solve a Vehicle Routing Problem

    Note:
        The first record should be the address of the starting point (let's say the HQ of the Samu Social)

    """
    parser = argparse.ArgumentParser(description="Solve a Vehicle Routing Problem")
    parser.add_argument(
        "-s", "--source", help="path to the source address csv file", type=str
    )
    parser.add_argument(
        "-n",
        "--number_workers",
        help="Number of workers available to perform the visit",
        type=int,
        default=4,
    )

    args = parser.parse_args()
    solve_routes(args.source, args.number_workers, from_raw_data=True)
