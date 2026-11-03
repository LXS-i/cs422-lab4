import gurobipy as gp
from gurobipy import GRB
import networkx as nx
import numpy as np

nodes = 6
degree = 3
graph = nx.random_regular_graph(degree, nodes)

#Define capacities
capacity = {}
for i in range(nodes):
    for j in range(nodes):
        if (i,j) in graph.edges():
            capacity[(i, j)] = 1
        else:
            capacity[(i, j)] = 0

#Create demand matrix
demx = np.zeros((nodes, nodes))
for i in range(nodes):
    for j in range(nodes):
        if i != j:
            demx[i][j] = degree / (nodes - 1)

all_paths = {}
for i in graph.nodes():
    for j in graph.nodes():
        if i != j:
            all_paths[i,j] = [list(zip(path, path[1:])) for path in nx.all_simple_paths(graph, source=i, target=j)]

model = gp.Model("throughput")

flow_vars = {}
for (s,d), paths in all_paths.items():
    for i in range(len(paths)):
        flow_vars[s,d,i] = model.addVar(vtype=GRB.CONTINUOUS, name=f"flow_{s}_{d}_{i}", lb=0)

throughput = model.addVar(vtype=GRB.CONTINUOUS, name="throughput", lb=0, ub=1)

#Capacity constraints
for u, v in graph.edges():
    model.addConstr(gp.quicksum(flow_vars[i,j,p] for (i,j), paths in all_paths.items() for p in range(len(paths)) if (u,v) in paths[p]) <= capacity[(u,v)], name=f"cap_{u}_{v}")

#Demand constraints
for u in graph.nodes():
    for v in graph.nodes():
        if u != v:
            model.addConstr(gp.quicksum(flow_vars[u,v,p] for p in range(len(all_paths[u,v]))) >= throughput*demx[u][v], name=f"demand_{u}_{v}")

model.setObjective(throughput, GRB.MAXIMIZE)
print("Throughput for the given topology before optimization: ", throughput)
model.optimize()
print("Throughput for the given topology after optimization: ", throughput.X)