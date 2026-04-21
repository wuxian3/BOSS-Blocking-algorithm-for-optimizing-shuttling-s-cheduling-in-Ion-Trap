import time
import functools, random

# import paddle_quantum as pq

# from paddle_quantum import Circuit

class block:
    def __init__(self, gates):
        self.gates = gates
        self.index = []
        for g in gates:
            q1 = g.q1
            if q1 not in self.index:
                self.index.append(q1)
            if not g.is_single:
                q2 = g.q2
                if q2 not in self.index:
                    self.index.append(q2)
        self.index.sort()
        self.size = len(self.index)

    def merge(self, block_alt):
        for g in block_alt.gates:
            self.gates.append(g)

        for i in block_alt.index:
            if i not in self.index:
                self.index.append(i)

        self.index.sort()
        self.size = len(self.index)

    def __str__(self):
        return f"Block:{self.index}"

class Gate:
    def __init__(self, gate_name, q1, q2=None):
        pass
        self.q1 = q1
        self.q2 = q2
        self.gate_name = gate_name

        self.is_single = False
        if self.q2 is None:
            self.is_single = True

        self.next_gates = []
        self.q1_pre_gates = None
        self.q2_pre_gates = None

        self.execute = -1

    def __str__(self):
        ret_str = f'{self.gate_name} q[{self.q1}]'
        if not self.q2 is None:
            ret_str += f',q[{self.q2}]'
        ret_str += ';'

        return ret_str

    def exe(self):
        if self.execute != 0:
            return False
        self.execute = 1
        for g in self.next_gates:
            flag = 0
            if g.q1_pre_gates.execute < 1:
                flag = -1
            elif not g.is_single and g.q2_pre_gates.execute < 1:
                flag = -1
            g.execute = flag

    def update_execute(self):
        flag = 0
        if self.q1_pre_gates.execute != 1:
            flag = -1

        if not self.is_single and self.q2_pre_gates.execute != 1:
            flag = -1
        self.execute = flag
        return

    def past_execute(self):
        self.execute = 2
        return

    def __copy__(self):
        new_gate = Gate(self.gate_name, self.q1, self.q2)
        return new_gate

class gate_node(Gate):
    def __init__(self, gate_name, q1, q2=None):
        super().__init__(gate_name=gate_name, q1=q1, q2=q2)
        self.idx = None

    def is_neighbor(self, g):
        if g in self.next_gates or self in g.next_gates:
            return True
        return False

def _is_in_execuation_zone(index, exe_zone_head, exe_zone_size):
    if exe_zone_head <= index < exe_zone_size + exe_zone_head:
        return True
    return False

class dependency_graph():
    def __init__(self, qb_num):
        self.qb_num = qb_num
        self.qubits = []
        self.frontier = []
        self.gates = []
        self.tail = []

        for i in range(self.qb_num):
            gi = Gate('qubits', i)
            gi.execute = 1
            self.qubits.append(gi)
            self.tail.append(gi)

    def all_gates(self):
        return self.frontier + self.gates

    def add_gates(self, gate: Gate):
        pre1 = self.tail[gate.q1]
        gate.q1_pre_gates = pre1
        pre1.next_gates.append(gate)

        self.tail[gate.q1] = gate
        if not gate.is_single:
            pre2 = self.tail[gate.q2]
            if pre1 != pre2:
                pre2.next_gates.append(gate)
            gate.q2_pre_gates = pre2
            self.tail[gate.q2] = gate

        gate.update_execute()

        if gate.execute == 0:
            self.frontier.append(gate)
        else:
            self.gates.append(gate)

    def update_frontier(self):
        for g in self.gates:
            if g.execute == 0:
                self.frontier.append(g)
                self.gates.remove(g)

    def execute_gate(self, g: Gate):
        g.exe()
        if g in self.frontier:
            self.frontier.remove(g)
        g_next_gates = g.next_gates
        for tg in g_next_gates:
            if tg.execute == 0:
                self.frontier.append(tg)
                self.gates.remove(tg)

    def _my_heuristic_function(self, g: Gate):
        return 1

    def pick_a_gate(self):
        pass
        max_score = 0
        max_index = 0
        for i in range(len(self.frontier)):
            g = self.frontier[i]
            score = self._my_heuristic_function(g)
            if score > max_score:
                max_index = i
                max_score = score

        return self.frontier.pop(max_index)

    def blocking(self, block_size, max_dis=None):
        if max_dis is None:
            max_dis = 99999999999999999999999999
        block_list = []
        union_set = list(range(self.qb_num))
        waiting_gate_list = []
        index_to_gates = {}
        for i in range(self.qb_num):
            index_to_gates[i] = []

        while len(self.frontier):

            g = self.pick_a_gate()
            if g.q1_pre_gates.execute == 1:
                q1_idx = union_set[g.q1_pre_gates.q1]
            else:
                q1_idx = union_set[g.q1]
            if g.is_single:
                index_to_gates[q1_idx].append(g)
                g.block_index = q1_idx
                self.execute_gate(g)
            else:
                if g.q2_pre_gates.execute == 1:
                    q2_idx = union_set[g.q2_pre_gates.q1]
                else:
                    q2_idx = union_set[g.q2]
                if q2_idx == q1_idx:
                    index_to_gates[q1_idx].append(g)
                    g.block_index = q1_idx
                    self.execute_gate(g)
                else:
                    union_set_size = 0

                    left1 = 1000000
                    left2 = 1000000
                    right1 = -1
                    right2 = -1
                    for i in range(self.qb_num):
                        if union_set[i] == q1_idx or union_set[i] == q2_idx:
                            union_set_size += 1
                        if union_set[i] == q1_idx:
                            if i < left1:
                                left1 = i
                            if i > right1:
                                right1 = i
                        if union_set[i] == q2_idx:
                            if i < left2:
                                left2 = i
                            if i > right2:
                                right2 = i

                    qb_dis = abs(g.q1 - g.q2)

                    if union_set_size > block_size or qb_dis > max_dis:
                        waiting_gate_list.append(g)
                    else:
                        for i in range(self.qb_num):
                            if union_set[i] == q2_idx:
                                union_set[i] = q1_idx
                        q2_gate_set = index_to_gates[q2_idx]
                        q1_gate_set = index_to_gates[q1_idx]
                        for tem_g in q2_gate_set:
                            q1_gate_set.append(tem_g)
                        q2_gate_set.clear()
                        index_to_gates[q1_idx].append(g)
                        g.block_index = q1_idx
                        self.execute_gate(g)
            if len(self.frontier) == 0:

                max_gate_number = 0
                max_size = 0
                max_index = -1
                for i in range(self.qb_num):

                    tem_list = index_to_gates[i]
                    tem_block = block(tem_list)
                    if tem_block.size > max_size:
                        max_size = tem_block.size
                        max_index = i
                tem_list = index_to_gates[max_index]
                for g in tem_list:
                    g.past_execute()
                block_list.append(block(tem_list.copy()))
                tem_list.clear()

                while len(waiting_gate_list):
                    g = waiting_gate_list.pop()

                    q1_idx = g.q1_pre_gates.q1
                    if union_set[q1_idx] == max_index:
                        g.q1_pre_gates = self.qubits[g.q1]
                    q2_idx = g.q2_pre_gates.q1
                    if union_set[q2_idx] == max_index:
                        g.q2_pre_gates = self.qubits[g.q2]

                    self.frontier.append(g)

                for i in range(self.qb_num):
                    if union_set[i] == max_index:
                        union_set[i] = i

        for gates in index_to_gates.values():
            if len(gates):
                block_list.append(block(gates))

        return block_list

    def to_qasm(self):
        qasm = f'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[{self.qb_num}];'
        for g in self.gates:
            qasm += '\n' + str(g)
        return qasm

class nw_graph(dependency_graph):
    def __init__(self, qb_num):
        super(nw_graph, self).__init__(qb_num)

        self.gate_list = []
        self.all_info = {}

    def add_gates(self, g: gate_node):
        self.gate_list.append(g)
        node_num = len(self.gate_list)
        g.idx = node_num - 1
        super().add_gates(g)

    def initial_info(self):
        for i in range(len(self.gate_list)):
            self.all_info[i] = [([self.gate_list[i]], [i])]

    def is_info_neighbor(self, a, b):
        pass
        a_idx = a[1]
        b_idx = b[1]
        for i in a_idx:
            for j in b_idx:
                gate_i = self.gate_list[i]
                gate_j = self.gate_list[j]
                if gate_j in gate_i.next_gates or gate_i in gate_j.next_gates:
                    return True
        return False

    def blocking_alt(self, block_size):
        self.initial_info()
        while 1:
            new_info = {}
            for idx in self.all_info.keys():
                ori_info = self.all_info[idx]
                current_node = self.gate_list[idx]

                idx_candidate = [idx]
                for g in current_node.next_gates:
                    idx_candidate.append(g.idx)
                next_idx = idx_candidate[random.randint(0, len(idx_candidate) - 1)]

                if next_idx not in new_info.keys():
                    new_info[next_idx] = ori_info
                else:
                    current_info = new_info[next_idx]
                    random.shuffle(current_info)

                    for tem_info in ori_info:

                        flag = False

                        for info in current_info:
                            gates, idxs = info
                            if self.is_info_neighbor(info, tem_info):
                                tem_block = block(gates + tem_info[0])
                                if tem_block.size <= block_size:
                                    flag = True
                                    gates += tem_info[0]
                                    idxs += tem_info[1]
                                    break

                        if not flag:
                            current_info.append(tem_info)

            self.all_info = new_info

            end_flag = True
            for idx in self.all_info.keys():
                if len(self.gate_list[idx].next_gates):
                    end_flag = False
                    break
            if end_flag:
                break
        ret_block_list = []
        for val in self.all_info.values():
            for gates, idxs in val:
                tem_block = block(gates)
                ret_block_list.append(tem_block)

        return ret_block_list

        pass
        tem_idx = list(range(len(self.gate_list)))
        for i in range(len(tem_idx)):
            for j in range(len(ret_block_list)):
                if self.gate_list[i] in ret_block_list[j].gates:
                    tem_idx[i] = j
                    break

        fin_ret_block_list = []
        block_ava = []
        for i in range(len(ret_block_list)):
            block_ava.append(1)

        while 1:
            end_flag = True
            for i in range(len(ret_block_list)):
                if i == 15:
                    print('test')
                if block_ava[i]:
                    end_flag = False
                    tem_block = ret_block_list[i]

                    leaf_flag = True
                    for g in tem_block.gates:
                        for ng in g.next_gates:
                            ng_block_id = tem_idx[ng.idx]
                            if ng_block_id != i and block_ava[ng_block_id] == 1:
                                leaf_flag = False
                                break
                    if leaf_flag:
                        fin_ret_block_list.append(tem_block)
                        block_ava[i] = 0
            if end_flag:
                break
        fin_ret_block_list.reverse()
        ret_block_list = fin_ret_block_list
        return ret_block_list

if __name__ == '__main__':
    random.seed(123)
    qb_num = 8
    d_graph = nw_graph(qb_num)
    for i in range(qb_num):
        for j in range(i + 1, qb_num):
            tem_g = gate_node('cx', i, j)
            d_graph.add_gates(tem_g)

    output = open('qasm_file/qft.qasm', 'w')
    output.write(d_graph.to_qasm())
    blocks = d_graph.blocking(4)
    for b in blocks:
        print(b)