import math

import qiskit, time
from qiskit import transpile
from qiskit.circuit.random import random_circuit

from gate import dependency_graph, _is_in_execuation_zone, Gate, nw_graph, gate_node


def _random_graph(qb_num=64, max_depth=20, idx=0):
    d_graph = dependency_graph(qb_num)
    circ = random_circuit(qb_num, max_depth, measure=False)
    circ = qiskit.transpile(circ, basis_gates=['id', 'rz', 'u3', 'u2', 'cx'])
    qasm = circ.qasm()

    lines = qasm.split('\n')[3:]

    new_qasm = ''
    for l in qasm.split('\n')[0:3]:
        new_qasm += l +'\n'

    cnt = 0
    for l in lines:
        tem = l.split(' ')
        if len(tem) < 2:
            continue
        gate_name = tem[0]
        if gate_name == 'cx':
            cnt += 1
            new_qasm += l + '\n'

        qubits = tem[1].split(',')
        if len(qubits) == 1:
            continue
        tem_l = qubits[0].index('[')
        tem_r = qubits[0].index(']')
        q1 = int(qubits[0][tem_l + 1: tem_r])

        tem_l = qubits[1].index('[')
        tem_r = qubits[1].index(']')
        q2 = int(qubits[1][tem_l + 1: tem_r])
        g = Gate(gate_name=gate_name, q1=q1, q2=q2)
        d_graph.add_gates(g)

    fout = open(f'random64_{idx}.qasm', 'w')
    fout.write(new_qasm)

    print(cnt)
    return d_graph

def baseline(d_graph: dependency_graph, execution_head: int, execution_zone_size: int):
    shuttle_number = 0
    qb_num = d_graph.qb_num
    right_most = qb_num - execution_zone_size
    gate_list = []
    logical_to_physical = list(range(qb_num))

    wait_list = []
    flag = True
    while len(d_graph.frontier):
        g = d_graph.frontier.pop()
        q1 = g.q1
        if g.is_single:
            if _is_in_execuation_zone(logical_to_physical[q1], exe_zone_head=execution_head, exe_zone_size=execution_zone_size):
                d_graph.execute_gate(g)
                gate_list.append(g)
                flag = True
            elif flag:
                wait_list.append(g)
            else:
                execution_head = q1
                d_graph.execute_gate(g)
                shuttle_number += 1
                shuttle = Gate('shuttle', q1)
                gate_list.append(shuttle)
                gate_list.append(g)
        else:
            q2 = g.q2
            phy_2 = logical_to_physical[q2]
            phy_1 = logical_to_physical[q1]
            if _is_in_execuation_zone(phy_1, execution_head, execution_zone_size) and\
                _is_in_execuation_zone(phy_2, execution_head, execution_zone_size):
                d_graph.execute_gate(g)
                gate_list.append(g)
                flag = True
            elif flag:
                wait_list.append(g)
            else:
                if not _is_in_execuation_zone(phy_1, execution_head, execution_zone_size) and\
                        not _is_in_execuation_zone(phy_2, execution_head, execution_zone_size):
                    if phy_1 < phy_2:
                        execution_head = min(phy_1, right_most)
                    else:
                        execution_head = min(phy_2, right_most)
                    shuttle_number += 1
                    shuttle = Gate('shuttle', execution_head)
                    gate_list.append(shuttle)
                if _is_in_execuation_zone(phy_2, execution_head, execution_zone_size):
                    tem = phy_1
                    phy_1 = phy_2
                    phy_2 = tem
                if _is_in_execuation_zone(phy_1, execution_head, execution_zone_size):
                    if _is_in_execuation_zone(phy_2, execution_head, execution_zone_size):
                        d_graph.execute_gate(g)
                        gate_list.append(g)
                    else:
                        direction = 1
                        if phy_1 > phy_2:
                            direction = -1
                        while not _is_in_execuation_zone(phy_2, execution_head, execution_zone_size):
                            if direction > 0:
                                rightest = min(execution_head + execution_zone_size - 1, qb_num - 1)
                                idx_i = logical_to_physical.index(rightest)
                                logical_i = logical_to_physical.index(phy_1)

                                tem = logical_to_physical[idx_i]
                                logical_to_physical[idx_i] = logical_to_physical[logical_i]
                                logical_to_physical[logical_i] = tem

                                execution_head = min(rightest, right_most)
                                shuttle_number += 1
                                shuttle = Gate('shuttle', execution_head)
                                gate_list.append(shuttle)
                            else:
                                idx_i = logical_to_physical.index(execution_head)
                                logical_i = logical_to_physical.index(phy_1)

                                tem = logical_to_physical[idx_i]
                                logical_to_physical[idx_i] = logical_to_physical[logical_i]
                                logical_to_physical[logical_i] = tem

                                leftmost = max(0, execution_head - execution_zone_size + 1)
                                execution_head = leftmost
                                shuttle_number += 1
                                shuttle = Gate('shuttle', execution_head)
                                gate_list.append(shuttle)
                        d_graph.execute_gate(g)
                        gate_list.append(g)
        if len(d_graph.frontier) == 0:
            if len(wait_list):
                flag = False
                while len(wait_list):
                    g = wait_list.pop()
                    d_graph.frontier.append(g)

    return gate_list, shuttle_number

def _qiskit_qasm(qasm_file_name):
    import qiskit
    fin = open(qasm_file_name, 'r')
    qasm = fin.read()
    cir = qiskit.QuantumCircuit.from_qasm_str(qasm)

    cirt = qiskit.transpile(cir, basis_gates=['u1', 'u2', 'u3', 'cx'], optimization_level=0)

    fout = open('qasm_file/wash.qasm', 'w')
    fout.write(cirt.qasm())

def _get_graph_from_qasm(qasm_file, nw_flag=False):
    fin = open(qasm_file, 'r')
    input_qasm = fin.read()

    cnt = 0
    offset = {}
    qb_num = 0
    lines = input_qasm.split('\n')[2:]

    for l in lines:
        tem = l.strip(';\n').split(' ')
        if tem[0] == 'qreg':
            reg = tem[1][:tem[1].find('[')]
            num = int(tem[1][tem[1].find('[') + 1: - 1])
            offset[reg] = qb_num
            qb_num += num
        else:
            break

    print(qb_num)
    if nw_flag:
        d_graph = nw_graph(qb_num)
    else:
        d_graph = dependency_graph(qb_num)

    for l in lines:
        tem = l.strip(';\n').split(' ')
        if tem[0] not in [ 'cx', 'cz']:
            continue
        regs = tem[1].split(',')
        tem1 = regs[0].find('[')
        reg1 = regs[0][:tem1]
        idx1 = int(regs[0][tem1 + 1: -1])
        q1 = idx1 + offset[reg1]

        tem2 = regs[1].find('[')
        reg2 = regs[1][:tem2]
        idx2 = int(regs[1][tem2 + 1: -1])
        q2 = idx2 + offset[reg2]
        if nw_flag:
            g = gate_node(gate_name='cx', q1=q1, q2=q2)
        else:
            g = Gate(gate_name='cx', q1=q1, q2=q2)
        d_graph.add_gates(g)
        cnt += 1

    print(cnt)

    return d_graph

if __name__ == '__main__':

    for i in range(10):
        _random_graph(idx=i)
