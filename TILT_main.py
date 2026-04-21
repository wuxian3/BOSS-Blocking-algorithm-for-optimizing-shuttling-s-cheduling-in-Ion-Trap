import random
import time
import functools

from benchmark import _random_graph, _get_graph_from_qasm
import benchmark

from gate import _is_in_execuation_zone, block
from evaluation import _execution_time, _success_rate
from utils import _my_cmp, _Block_merge, _Block_sort, get_expect_index, is_block_in_execution_zone

sabre_flag = True

def block_scheduling(block_list, qb_num: int, execuation_zone_size: int, initial_mapping=None, initial_head = 0):
    ret_scheduling = []
    ret_swap_list = []

    execuation_zone_head = initial_head

    logical_to_physical_mapping = list(range(qb_num))

    tape = list(range(qb_num))
    if initial_mapping is not None:
        logical_to_physical_mapping = initial_mapping.copy()
        for i in range(qb_num):
            tape[i] = initial_mapping.index(i)

    swap_number = 0
    current_head = initial_head

    ret_scheduling.append([logical_to_physical_mapping.copy(), execuation_zone_head])

    for block in block_list:
        tem_scheduling, tem_swap_number, tem_swap_list = (
            block_schedule_single_step(block, qb_num, execuation_zone_size=execuation_zone_size, current_head=current_head, current_mapping=logical_to_physical_mapping))

        ret_scheduling += tem_scheduling
        swap_number += tem_swap_number
        ret_swap_list += tem_swap_list

        if len(tem_scheduling):
            current_head = tem_scheduling[-1][1]

    return ret_scheduling, swap_number, ret_swap_list

def block_schedule_single_step(current_block, qb_num: int, execuation_zone_size: int, current_mapping=None, current_head=0, block_size=None):
    if block_size is None:
        block_size = current_block.size
    logical_to_physical_mapping = current_mapping
    block = current_block

    ret_scheduling = []
    ret_swap_list = []
    swap_number = 0

    swap_gate_list = []
    expect_index = get_expect_index(block, logical_to_physical_mapping)
    mid = int(block.size / 2)
    mid_pix = expect_index[mid][1]
    flag = is_block_in_execution_zone(block, logical_to_physical_mapping, current_head, execuation_zone_size)
    if flag:
        return ret_scheduling, swap_number, ret_swap_list
    execuation_zone_head = logical_to_physical_mapping[expect_index[0][0]]
    if execuation_zone_head >= qb_num - execuation_zone_size:
        execuation_zone_head = qb_num - execuation_zone_size

    ret_swap_list.append(swap_gate_list)
    swap_gate_list = []
    ret_scheduling.append([logical_to_physical_mapping.copy(), execuation_zone_head])

    tape = list(range(qb_num))
    for i in range(qb_num):
        tape[i] = current_mapping.index(i)

    while 1:
        rightmost = min(qb_num - 1, execuation_zone_head + execuation_zone_size - 1)
        rightmost = min(rightmost, mid_pix - 1)
        for i in range(block_size):
            idx_i = rightmost - i
            if idx_i < execuation_zone_head or i > block_size / 2:
                break
            log_i = logical_to_physical_mapping.index(idx_i)
            if log_i in block.index:
                continue
            for j in range(1, block_size):
                idx_j = idx_i - j
                if idx_j < execuation_zone_head:
                    break
                log_j = logical_to_physical_mapping.index(idx_j)
                if log_j in block.index:
                    logical_to_physical_mapping[log_i] = idx_j
                    logical_to_physical_mapping[log_j] = idx_i
                    swap_number += 1
                    swap_gate_list.append((idx_j, idx_i))
                    tape[idx_j] = log_i
                    tape[idx_i] = log_j
                    break
        flag = True
        for i in range(mid):
            log_i = expect_index[i][0]
            phy_i = logical_to_physical_mapping[log_i]
            if mid_pix - phy_i > mid:
                flag = False
                break
        if flag:
            break

        phy_leftmost = qb_num - execuation_zone_size
        for i in range(block.size):
            log_i = expect_index[i][0]
            if logical_to_physical_mapping[log_i] < phy_leftmost:
                phy_leftmost = logical_to_physical_mapping[log_i]

        execuation_zone_head = phy_leftmost

        ret_swap_list.append(swap_gate_list)
        swap_gate_list = []
        ret_scheduling.append([logical_to_physical_mapping.copy(), execuation_zone_head])

    flag = is_block_in_execution_zone(block, logical_to_physical_mapping, execuation_zone_head,
                                      execuation_zone_size)
    if flag:
        return ret_scheduling, swap_number, ret_swap_list
    execuation_zone_head = logical_to_physical_mapping[expect_index[-1][0]] - execuation_zone_size + 1
    if execuation_zone_head < 0:
        execuation_zone_head = 0

    ret_swap_list.append(swap_gate_list)
    swap_gate_list = []
    ret_scheduling.append([logical_to_physical_mapping.copy(), execuation_zone_head])

    while 1:
        leftmost = max(execuation_zone_head, mid_pix + 1)
        for i in range(block_size):
            idx_i = leftmost + i
            if idx_i >= execuation_zone_head + execuation_zone_size or i >= block_size / 2:
                break
            log_i = logical_to_physical_mapping.index(idx_i)
            if log_i in block.index:
                continue
            for j in range(1, block_size):
                idx_j = idx_i + j
                if idx_j >= qb_num:
                    break
                log_j = logical_to_physical_mapping.index(idx_j)
                if log_j in block.index:
                    logical_to_physical_mapping[log_i] = idx_j
                    logical_to_physical_mapping[log_j] = idx_i
                    swap_number += 1
                    swap_gate_list.append((idx_j, idx_i))
                    tape[idx_j] = log_i
                    tape[idx_i] = log_j
                    break

        flag = is_block_in_execution_zone(block, logical_to_physical_mapping, execuation_zone_head,
                                          execuation_zone_size)
        if flag:
            ret_swap_list.append(swap_gate_list)
            swap_gate_list = []
            ret_scheduling.append([logical_to_physical_mapping.copy(), execuation_zone_head])
            break

        phy_rightmost = 0

        for i in range(block.size):
            log_i = expect_index[i][0]
            if logical_to_physical_mapping[log_i] > phy_rightmost + execuation_zone_size - 1:
                phy_rightmost = logical_to_physical_mapping[log_i] - execuation_zone_size + 1

        execuation_zone_head = min(phy_rightmost, qb_num - execuation_zone_size)

        ret_swap_list.append(swap_gate_list)
        swap_gate_list = []
        ret_scheduling.append([logical_to_physical_mapping.copy(), execuation_zone_head])

    flag = is_block_in_execution_zone(block, logical_to_physical_mapping, execuation_zone_head,
                                      execuation_zone_size)
    assert flag
    return ret_scheduling, swap_number, ret_swap_list

def greedy_initial_mapping(block_list, qb_num:int):
    special_mapping = {}
    for i in range(qb_num):
        special_mapping[i] = -1
    cnt = 0
    for b in block_list:
        if cnt == qb_num:
            break
        for i in b.index:
            if cnt == qb_num:
                break
            if special_mapping[i] < 0:
                special_mapping[i] = cnt
                cnt += 1

    for i in range(qb_num):
        if special_mapping[i] < 0:
            special_mapping[i] = cnt
            cnt += 1
    tem_mapping = list(range(qb_num))
    for i in range(qb_num):
        tem_mapping[i] = special_mapping[i]

    return tem_mapping

def get_dgraph(app_name, qb_num, QASM_FILE):
    
    return _get_graph_from_qasm(QASM_FILE)

def cut_number(block_list, act_size):
    activate = []
    block_cnt = len(block_list)
    total_cut = 0
    for i in range(block_cnt - 1):
        current_block = block_list[i]
        next_block = block_list[i + 1]
        for idx in next_block.index:
            if idx not in current_block.index:
                total_cut += 1

    return total_cut

def TILT_main(Application, qb_num, block_size, gate_model, QASM_FILE, print_flag=False):
    d_graph = get_dgraph(Application, qb_num, QASM_FILE)

    gate_dis = 0
    for g in d_graph.frontier + d_graph.gates:
        gate_dis += abs(g.q1 - g. q2)
    gate_dis /= len(d_graph.frontier + d_graph.gates)
    start = time.time()
    block_list = d_graph.blocking(block_size)

    _Block_sort(block_list)
    _Block_merge(block_list, max_size=block_size)
    cut_number(block_list, block_size)

    for b in block_list:

        assert len(b.index) <= block_size
    greedy_map = greedy_initial_mapping(block_list, qb_num)
    schedule, swap_number, swap_gate_lists = block_scheduling(block_list, qb_num, block_size, initial_mapping=greedy_map)
    if sabre_flag:
        sabre_cnt = 1
        for _ in range(sabre_cnt):
            fin_mapping = schedule[-1][0]
            fin_head = schedule[-1][1]
            block_list.reverse()
            schedule, swap_number, swap_gate_lists = block_scheduling(block_list, qb_num, block_size,
                                                                      initial_mapping=fin_mapping, initial_head=fin_head)

            fin_mapping = schedule[-1][0]
            fin_head = schedule[-1][1]
            block_list.reverse()
            schedule, swap_number, swap_gate_lists = block_scheduling(block_list, qb_num, block_size,
                                                                      initial_mapping=fin_mapping,
                                                                      initial_head=fin_head)

    shuttle_time = 0
    shuttle_dis = 0
    last_head = 0

    assert len(schedule) == len(swap_gate_lists) + 1, f' but got {len(schedule)} and {len(swap_gate_lists)}'

    cnt = -1
    swap_cnt = 0
    for s in schedule:

        if cnt >= 0:
            swap_gate_list = swap_gate_lists[cnt]

            for l in swap_gate_list:
                swap_cnt += len(l) // 2

        cnt += 1
        layout = s[0]
        head = s[1]
        assert head >= 0
        assert head <= qb_num - block_size
        if head != last_head:
            shuttle_time += 1
        shuttle_dis += abs(head - last_head)
        physical_tape = list(range(qb_num))
        for i in range(qb_num):
            physical_tape[layout[i]] = i

        if print_flag:
            for i in range(qb_num):
                if i == head:
                    print('[', end='')
                print(f'{physical_tape[i]}', end=',')
                if i == head + block_size - 1:
                    print(']', end='')
            print()
        last_head = head

    end = time.time()
    t_exe = _execution_time(shuttle_dis, block_size, block_list, schedule, gate_model)
    rate = _success_rate(shuttle_dis, block_size, block_list, schedule)
    result = [shuttle_time, shuttle_dis, swap_number, end - start, t_exe, rate, gate_dis]
    return result

if __name__ == '__main__':
    QASM_FILE = 'qasm_file/ALT64.qasm'
    Application = 'QASM'
    gate_model = 'Trout'
    block_size = 16
    qb_num = 64

    results = []
    result = TILT_main(
        Application=Application,
        qb_num=qb_num,
        block_size=block_size,
        gate_model=gate_model,
        QASM_FILE=QASM_FILE,
    )
    results.append(result)

    shuttles = [results[i][0] for i in range(len(results))]
    print(f'{Application}_shuttles = {shuttles}')

    shuttle_dis = [results[i][1] for i in range(len(results))]
    print(f'{Application}_shuttle_dis = {shuttle_dis}')

    swap_number = [results[i][2] for i in range(len(results))]
    print(f'{Application}_swap_cnt = {swap_number}')

    times= [results[i][3] for i in range(len(results))]
    print(f'{Application}_complation_time = {times}')

    exe_time = [results[i][4] for i in range(len(results))]
    print(f'{Application}_execution_time = {exe_time}')

    rate = [results[i][5] for i in range(len(results))]
    print(f'{Application}_success_rate_true = {rate}')

    print(results[0][-1])
