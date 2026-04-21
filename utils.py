import time
import functools

import torch
from os.path import join, dirname

from gate import dependency_graph, _is_in_execuation_zone, Gate

def _my_cmp(a, b):
    pass
    value_a = a[1]
    value_b = b[1]
    if value_a > value_b:
        return 1
    elif value_a < value_b:
        return -1
    return 0

def _Block_sort(block_list):
    b = len(block_list)
    for i in range(b):
        for j in range(0, b - i - 1):
            bj = block_list[j]
            bj1 = block_list[j + 1]

            flag = True
            for idx in bj.index:
                if idx in bj1.index:
                    flag = False
                    break

            if not flag:
                continue
            if bj.index[0] > bj1.index[0]:
                tem = block_list[j]
                block_list[j] = block_list[j + 1]
                block_list[j + 1] = tem

    return

def _Block_merge(block_list, max_size):
    while 1:
        b = len(block_list)
        flag = True
        for i in range(b - 1):
            bi = block_list[i]
            bj = block_list[i + 1]
            if bi.size + bj.size <= max_size:
                bi.merge(bj)
                block_list.remove(bj)
                flag = False
                break
        if flag:
            break
    return block_list

def get_expect_index(block, mapping):
    index_and_physical = []
    for i in block.index:
        index_and_physical.append([i, mapping[i]])
    index_and_physical.sort(key=functools.cmp_to_key(_my_cmp))
    mid = int(block.size / 2)
    expect_index = index_and_physical.copy()
    for i in range(block.size):
        expect_index[i][1] = expect_index[mid][1] - mid + i
    return expect_index

def inset_swap_score(new_mapping, front_layer, second_layer):
    ret = 0
    alpha = 0.5
    for g in front_layer:
        if g.is_single:
            continue
        dis = abs(new_mapping[g.q1] - new_mapping[g.q2])
        ret += dis

    return ret

def is_block_in_execution_zone(block, mapping, head, size):
    for i in block.index:
        phy_i = mapping[i]
        if phy_i < head or phy_i >= head + size:
            return False
    return True

def dag_swap_insert(d_graph: dependency_graph, execution_zone_size: int):
    qb_num = d_graph.qb_num
    gate_list = []
    logical_to_physical = list(range(qb_num))

    while len(d_graph.frontier):
        g = d_graph.frontier[0]
        if g.is_single:
            new_g = Gate(g.gate_name, logical_to_physical[g.q1])
            gate_list.append(new_g)
            d_graph.execute_gate(g)
            continue
        dis = logical_to_physical[g.q1] - logical_to_physical[g.q2]
        dis = abs(dis)
        if dis < execution_zone_size:
            new_g = Gate(g.gate_name, logical_to_physical[g.q1], logical_to_physical[g.q2])
            gate_list.append(new_g)
            d_graph.execute_gate(g)
            continue

        front_layer = d_graph.frontier.copy()
        second_layer = []
        for tem_g in front_layer:
            for tem in tem_g.next_gates:
                second_layer.append(tem)
        a = logical_to_physical[g.q1]
        b = logical_to_physical[g.q2]
        if a > b:
            tem = a
            a = b
            b = tem
        swap_candidate = []
        for i in range(a + 1, b):
            if i - a < execution_zone_size:
                swap_candidate.append((a, i))
            if b - i < execution_zone_size:
                swap_candidate.append((i, b))
        physical_front = []
        for g in front_layer:
            physical_front.append(logical_to_physical[g.q1])
            physical_front.append(logical_to_physical[g.q2])
        min_score = 1000000000
        min_swap = None
        for a, b in swap_candidate:
            new_mapping = logical_to_physical.copy()
            log_a = new_mapping.index(a)
            log_b = new_mapping.index(b)
            new_mapping[log_a] = b
            new_mapping[log_b] = a
            score = inset_swap_score(new_mapping, front_layer, second_layer)

            if score < min_score:
                min_score = score
                min_swap = Gate(gate_name='custom_swap', q1=a, q2=b)
        gate_list.append(min_swap)
        log_q1 = logical_to_physical.index(min_swap.q1)
        log_q2 = logical_to_physical.index(min_swap.q2)

        logical_to_physical[log_q1] = min_swap.q2
        logical_to_physical[log_q2] = min_swap.q1

    new_d_graph = dependency_graph(qb_num)
    for g in gate_list:
        dis = abs(g.q1 - g.q2)
        assert dis <= execution_zone_size, f'it should be small than {execution_zone_size}, but got {dis}'
        new_d_graph.add_gates(g.__copy__())
    return new_d_graph

if __name__ == '__main__':
    simulation_data = torch.load(join(dirname(__file__), 'contraction_scheme.pt'))
    print(simulation_data['slicing_indices_dict'])
    print(simulation_data['slicing_edges_loop'])
    tensors = simulation_data['tensors']

    shapes = []
    shape_idx = []
    for t in tensors:
        shapes.append(len((t.shape)))

    for i in range(len(shapes)):
        if shapes[i] == 3:
            shape_idx.append(i)

    print(shape_idx)

