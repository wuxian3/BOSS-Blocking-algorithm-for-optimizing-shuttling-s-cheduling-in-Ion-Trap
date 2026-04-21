import math

import gate

ideal_setting = False

def _execution_time(shuttle_dis, aom_size, block_list, schedule, gate_model):
    total_time = 10 * 1000 + 50
    shuttle_time = 1
    total_time += shuttle_time * shuttle_dis

    total_time += 500

    qb_num = len(schedule[0][0])

    layout = schedule[0][0]
    head = schedule[0][1]
    tape = list(range(qb_num))
    for i in range(qb_num):
        tape[layout[i]] = i

    schedule_cnt = 1
    swap_cnt = 0
    block_idx = 0
    while 1:
        if block_idx >= len(block_list):
            break
        block = block_list[block_idx]
        flag = True
        for idx in block.index:
            phy_idx = tape.index(idx)
            if phy_idx < head or phy_idx >= head + aom_size:
                flag = False
                break

        if flag:
            total_time += _block_time(block, tape, gate_model)
            block_idx += 1
            continue

        layout = schedule[schedule_cnt][0]

        new_tape = list(range(qb_num))
        for i in range(qb_num):
            new_tape[layout[i]] = i

        max_dis_1 = 0
        max_dis_2 = 0
        for i in range(head, head + aom_size):
            if tape[i] != new_tape[i]:
                j = new_tape.index(tape[i])
                dis = abs(i - j)
                if dis > max_dis_1:
                    max_dis_1 = dis
                tem = tape[i]
                tape[i] = tape[j]
                tape[j] = tem
                swap_cnt += 1
                if tape[i] != new_tape[i]:
                    phy_j = new_tape[i]
                    j = tape.index(phy_j)
                    dis = abs(i - j)
                    if dis > max_dis_2:
                        max_dis_2 = dis
                    tem = tape[i]
                    tape[i] = tape[j]
                    tape[j] = tem
                    swap_cnt += 1

        assert tape == new_tape

        head = schedule[schedule_cnt][1]
        schedule_cnt += 1

        total_time += _gate_time(max_dis_1, gate_model) * 3 + _gate_time(max_dis_2, gate_model) * 3

        total_time += 40

    while 1:
        if schedule_cnt == len(schedule):
            break
        if schedule[schedule_cnt][1] == head:
            schedule_cnt += 1
        else:
            break
    assert schedule_cnt == len(schedule), f"schedule_cnt={schedule_cnt}, len(schedule) = {len(schedule) }"
    return total_time * (10 ** (-6))

def _gate_time(dis, model) -> int:
    if dis == 0 :
        return 0
    return gate_time(dis, model)

def gate_time(dis, model='Trout'):
    d_const = 1
    if model == "Duan":
        t = -22 + 100*dis
    elif model == "Trout":
        t = 10 + 38*dis

    elif model == "PM":
        t = 160 + 5*dis
    else:
        assert 0
    t = max(t, 1)
    return int(t)

def _block_time(block, tape, model):
    t = 0
    qb_num = len(tape)
    d_graph = gate.dependency_graph(qb_num)
    for g in block.gates:
        new_g = gate.Gate(g.gate_name, g.q1, g.q2)
        d_graph.add_gates(new_g)
    while len(d_graph.frontier):
        layer = []
        max_dis = 0
        while len(d_graph.frontier):
            g = d_graph.frontier.pop()
            layer.append(g)
            if g.is_single:
                continue
            x = tape.index(g.q1)
            y = tape.index(g.q2)
            dis = abs(x - y)
            if dis > max_dis:
                max_dis = dis
        t += _gate_time(max_dis, model)
        for g in layer:
            d_graph.execute_gate(g)
    return t

def _success_rate(shuttle_dis, aom_size, block_list, schedule):
    ret_success_rate = 1.0
    swap_num = 0

    qb_num = len(schedule[0][0])
    k = math.sqrt(qb_num)

    layout = schedule[0][0]
    head = schedule[0][1]
    tape = list(range(qb_num))
    for i in range(qb_num):
        tape[layout[i]] = i

    schedule_cnt = 1

    block_idx = 0
    shuttle_number = 0
    while 1:
        if block_idx >= len(block_list):
            break
        block = block_list[block_idx]
        flag = True
        for idx in block.index:
            phy_idx = tape.index(idx)
            if phy_idx < head or phy_idx >= head + aom_size:
                flag = False
                break

        if flag:
            block_success_rate = _new_block_rate(block, aom_size)
            ret_success_rate *= block_success_rate

            shuttle_fidelity = _shuttle_rate(shuttle_number)
            ret_success_rate *= shuttle_fidelity
            block_idx += 1
            continue

        layout = schedule[schedule_cnt][0]

        new_tape = list(range(qb_num))
        for i in range(qb_num):
            new_tape[layout[i]] = i

        for i in range(head, head + aom_size):
            if tape[i] != new_tape[i]:
                j = new_tape.index(tape[i])
                dis = abs(i - j)
                swap_success_rate = _new_gate_rate(aom_size)
                ret_success_rate *= swap_success_rate ** 3
                tem = tape[i]
                tape[i] = tape[j]
                tape[j] = tem
                swap_num += 1
                if tape[i] != new_tape[i]:
                    phy_j = new_tape[i]
                    j = tape.index(phy_j)

                    swap_success_rate = _new_gate_rate(aom_size)
                    ret_success_rate *= swap_success_rate ** 3

                    tem = tape[i]
                    tape[i] = tape[j]
                    tape[j] = tem
                    swap_num += 1

        assert tape == new_tape

        if head != schedule[schedule_cnt][1]:
            shuttle_number += 1
        head = schedule[schedule_cnt][1]

        schedule_cnt += 1

    while 1:
        if schedule_cnt == len(schedule):
            break
        if schedule[schedule_cnt][1] == head:
            schedule_cnt += 1
        else:
            break
    assert schedule_cnt == len(schedule)

    return ret_success_rate

def _new_block_rate(block, aom_size):
    ret = 1.0
    for g in block.gates:
        if g.is_single:
            continue
        rate = _new_gate_rate(aom_size, ideal_setting)
        ret *= rate
    return ret

def _gate_rate(time, move_time, k):
    rate = 1.0
    radial_heating_rate = 1.0
    two_qubit_gate_error = 10 ** (-3)
    rate -= radial_heating_rate * time * (10 ** (-6))
    rate += 1 - (1 + two_qubit_gate_error) ** (2 * move_time * k + 1)
    ret = max(rate, 0.0001)
    return ret

def _block_rate(block, tape, move_number):
    ret = 1.0
    qb_num = len(tape)
    k = math.sqrt(qb_num)
    for g in block.gates:
        if g.is_single:
            continue
        idx_a = tape.index(g.q1)
        idx_b = tape.index(g.q2)
        dis = abs(idx_a - idx_b)
        g_time = _gate_time(dis)
        rate = _gate_rate(time=g_time, move_time=move_number, k=k)
        ret *= rate
    return ret

def _new_gate_rate(block_size, ideal=False):
    if ideal:
        return 0.999
    eplision = (1e-3) / 256
    rate = max(0.00001, 1 - eplision * block_size ** 2)
    return rate

def _shuttle_rate(shuttle_cnt):

    eplision = 1e-3
    rate = max(0.00001, 1 - eplision * shuttle_cnt)
    return rate