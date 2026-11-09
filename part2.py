import gurobipy as gp
from gurobipy import GRB
import networkx as nx
import numpy as np

nodes = 8
degree = 4
graph = nx.DiGraph()
for i in range(nodes):
    graph.add_node(i)
model = gp.Model("throughput")

#Define capacities
capacity = {}
for i in range(nodes):
    for j in range(nodes):
        if i != j:
            capacity[i, j] = model.addVar(vtype=GRB.BINARY, name=f"capacity_{i}_{j}")

#Create demand matrix
demx = np.random.rand(nodes, nodes)
np.fill_diagonal(demx, 0)
row_sums = demx.sum(axis=1)
for i in range(nodes):
    if row_sums[i] > degree:
        demx[i, :] *= degree / row_sums[i]
col_sums = demx.sum(axis=0)
for j in range(nodes):
    if col_sums[j] > degree:
        demx[:, j] *= degree / col_sums[j]


flow_vars={}
for s in range(nodes):
    for d in range(nodes):
        if s != d:
            for i in range(nodes):
                for j in range(nodes):
                    if i != j:
                        flow_vars[s, d, i, j] = model.addVar(vtype=GRB.CONTINUOUS, name=f"flow_{s}_{d}_{i}_{j}", lb=0)


throughput = model.addVar(vtype=GRB.CONTINUOUS, name="throughput", lb=0)

#Degree constraints
for (i) in range(nodes):
    #outgoing = degree
    model.addConstr(gp.quicksum(capacity[i,j] for j in range(nodes) if i!=j) == degree)
    #incoming = degree
    model.addConstr(gp.quicksum(capacity[j,i] for j in range(nodes) if i!=j) == degree)

#Capacity constraints
for i in range(nodes):
    for j in range(nodes):
        if (i!=j):
            model.addConstr(gp.quicksum(flow_vars[s,d,i,j] for s in range(nodes) for d in range(nodes) if s!=d) <= capacity[i,j], name=f"cap_{i}_{j}")

#Demand constraints
for s in range(nodes):
    for d in range(nodes):
        if s==d:
            continue

        for i in range(nodes):
            outgoing = gp.quicksum(flow_vars[s,d,i,j] for j in range(nodes) if j!=i)
            incoming = gp.quicksum(flow_vars[s,d,j,i] for j in range(nodes) if j!=i)

            if i==s:
                model.addConstr(outgoing-incoming == throughput*demx[s,d])
            elif i==d:
                model.addConstr(outgoing-incoming == -throughput*demx[s,d])
            else:
                model.addConstr(outgoing-incoming == 0)


model.setObjective(throughput, GRB.MAXIMIZE)
model.optimize()

print("Demand matrix:")
print(demx)

print("Throughput for the given topology after optimization: ", throughput.X)

for i in range(nodes):
    for j in range(nodes):
        if i!=j and capacity[i,j].X == 1:
            graph.add_edge(i,j)

print("Topology adjacency matrix:")
print(nx.to_numpy_array(graph))