"""
Determine an optimal list of hotel to visit.
"""

from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2

from src.services.map import Map


def get_distances_matrix(addresses):
    """Compute the distance matrix (distance between each hotels).
    Returns a triangular matrix.

    Args: 
        addresses(list[dict]): list of address, each dict has the struct
            {'address': 'Avenue Winston Churchill', 'postcode': 27000}
    Returns:
        distances(list[list[int]]): matrix of distances

    """
    map = Map()
    distances = []

    for address1 in addresses:
        src_address = {'address': address1.get('address'), 'postcode': address1.get('postcode')}
        src_dist = [] 
        for address2 in addresses:
            target_address = {'address': address2.get('address'), 'postcode': address2.get('postcode')}
            point1 = map.point(src_address)
            point2 = map.point(target_address)

            distance = map.distance(point1, point2)
            src_dist.append(distance)
        distances.append(src_dist)
    return distances

###########################
# Problem Data Definition #
###########################
def create_data_model():
  """Creates the data for the example."""
  data = {}
  # Array of distances between locations.
  _distances = get_distances_matrix(addresses)
  data["distances"] = _distances
  data["num_locations"] = len(_distances)
  data["num_vehicles"] = 4
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
  distance = 'Distance'
  maximum_distance = 3000  # Maximum distance per vehicle.
  routing.AddDimension(
      distance_callback,
      0,  # null slack
      maximum_distance,
      True,  # start cumul to zero
      distance)
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
    plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
    route_dist = 0
    while not routing.IsEnd(index):
      node_index = routing.IndexToNode(index)
      next_node_index = routing.IndexToNode(
        assignment.Value(routing.NextVar(index)))
      route_dist += routing.GetArcCostForVehicle(node_index, next_node_index, vehicle_id)
      plan_output += ' {0} ->'.format(node_index)
      index = assignment.Value(routing.NextVar(index))
    plan_output += ' {}\n'.format(routing.IndexToNode(index))
    plan_output += 'Distance of route: {}m\n'.format(route_dist)
    print(plan_output)
    total_distance += route_dist
  print('Total distance of all routes: {}m'.format(total_distance))
########
# Main #
########
def main():
  """Entry point of the program"""
  # Instantiate the data problem.
  data = create_data_model()
  # Create Routing Model
  routing = pywrapcp.RoutingModel(
      data["num_locations"],
      data["num_vehicles"],
      data["depot"])
  # Define weight of each edge
  distance_callback = create_distance_callback(data)
  routing.SetArcCostEvaluatorOfAllVehicles(distance_callback)
  add_distance_dimension(routing, distance_callback)
  # Setting first solution heuristic (cheapest addition).
  search_parameters = pywrapcp.RoutingModel.DefaultSearchParameters()
  search_parameters.first_solution_strategy = (
      routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC) # pylint: disable=no-member
  # Solve the problem.
  assignment = routing.SolveWithParameters(search_parameters)
  if assignment:
    print_solution(data, routing, assignment)
if __name__ == '__main__':
  main()