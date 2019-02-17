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

MAX_DISTANCE = 15000  # Maximum distance (meters) that a worker can cover in a day
MAX_VISIT_PER_DAY = 8  # Maximum number of various hotel a worker can cover within a day


def get_distances_matrix(hotels, workers):
    """Compute the distance matrix (distance between each hotels).
    Returns a triangular matrix and the labels of the hotels.

    Note:
        1) That the first address shall be the address of the depot.
        2) If the API doesn't returna a match for the address, we drop
            the point. This may not be the expected behavior. TODO


    Args: 
        hotels (list[dict]): list of address, each dict has the struct
            {'address': 'Avenue Winston Churchill', 'postcode': 27000}
        workers (dict(int: int))
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
    hotels_and_workers = workers + workers + hotels

    for hotel1 in hotels_and_workers:
        src_address = {
            "address": hotel1.get("address"),
            "postcode": hotel1.get("postcode"),
        }
        # point1 = map.point(src_address)
        point1 = hotel1["point"]
        src_dist = []
        if not point1:
            continue

        labels[index] = "{} {}".format(
            src_address.get("address"), src_address.get("postcode")
        )  # Store the address as labels for the node
        index = index + 1
        for hotel2 in hotels_and_workers:
            target_address = {
                "address": hotel2.get("address"),
                "postcode": hotel2.get("postcode"),
            }
            # point2 = map.point(target_address)
            point2 = hotel2["point"]

            if not point2:
                continue

            distance = map.distance(point1, point2)
            distance = int(np.round(distance * 1000))  # Distance expressed in meters
            src_dist.append(distance)

        if src_dist:
            distances.append(src_dist)

    return distances, labels


###########################
# Problem Data Definition #
###########################
def create_data_model(hotels, workers, from_raw_data):
    """Creates the data for the example.
    Args:
        hotels(list[dict])
        workers(dict(int: int): number of couple of Samu Social workers available
        from_raw_data(bool):
    """
    data = {}
    n_workers = len(workers)
    data["num_vehicles"] = n_workers

    # Precise start and end locations of the workers
    # The number_workers-th first line correspond to the start locations of the workers
    start_locations = [idx for idx in range(n_workers)]

    # The number_workers-th to the 2*number_workers-th line correspond to the end locations of the workers
    end_locations = [idx for idx in range(n_workers, 2 * n_workers)]
    data["start_locations"] = start_locations
    data["end_locations"] = end_locations

    # Matrix of distances between locations.
    if from_raw_data:
        hotels_data = parse_csv(hotels, "hotel", write=False)
    else:
        hotels_data = hotels
    _distances, labels = get_distances_matrix(hotels_data, workers)
    data["distances"] = _distances
    data["labels"] = labels
    num_locations = len(_distances)
    data["num_locations"] = num_locations

    # The problem is to find an assignment of routes to vehicles that has the shortest total distance
    # and such that the total amount a vehicle is carrying never exceeds its capacity. Capacities can be understood
    # as the max number of visits that a worker can do in a day
    demands = [1] * num_locations
    capacities = [MAX_VISIT_PER_DAY] * n_workers
    data["demands"] = demands
    data["vehicle_capacities"] = capacities

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


def create_demand_callback(data):
    """Creates callback to get demands at each location."""

    def demand_callback(from_node, to_node):
        return data["demands"][from_node]

    return demand_callback


def add_capacity_constraints(routing, data, demand_callback):
    """Adds capacity constraint"""
    capacity = "Capacity"
    routing.AddDimensionWithVehicleCapacity(
        demand_callback,
        0,  # null capacity slack
        data["vehicle_capacities"],  # vehicle maximum capacities
        True,  # start cumul to zero
        capacity,
    )


###########
# FORMATTER #
###########
def format_solution(data, routing, assignment):
    """Print routes on console."""
    plan_output = []
    for vehicle_id in range(data["num_vehicles"]):
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
        plan_output.append(route)
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
        data["num_locations"],
        data["num_vehicles"],
        data["start_locations"],
        data["end_locations"],
    )
    # Define weight of each edge
    distance_callback = create_distance_callback(data)
    routing.SetArcCostEvaluatorOfAllVehicles(distance_callback)

    # Add Capacity constraint
    demand_callback = create_demand_callback(data)
    add_capacity_constraints(routing, data, demand_callback)

    # Setting first solution heuristic (cheapest addition).
    search_parameters = pywrapcp.RoutingModel.DefaultSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

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
