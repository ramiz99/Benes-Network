# ----------------------------------------------------------------------------
#
# Detecting chains of dependencies in first column of Benes network
#
# ----------------------------------------------------------------------------

import random
import time
import itertools

# ########################################################
#   Function to fill idle input ports with available ones
# ########################################################
def perform_fill(demand_in, N):
    bus = [0 for ind in range (N)]  # N bits bus
    phase_0_imp = 0
    count_valid_demand_post = 0
    demand = demand_in

    # Phase 1
    #   If an SE has a single valid demand and
    #   its pairing demand to complete a single SE chain is not requested by any other SE,
    #   Than take it
    # ##############################################################
    if with_phase_0 == 1:
        if debug: print ('\nphase 1')
        # publish input port of idle demands on the bus
        for i in range (N):
            if demand_in[i] != -1: bus[demand_in[i]] = 1

        if debug: print ('bus     \t', bus)

        # change demand from -1 if neighbor is available
        for i in range (N // 2):
            if (demand[2 * i] == -1 or demand[2 * i + 1] == -1) and not (
                    demand[2 * i] == -1 and demand[2 * i + 1] == -1):
                if demand[2 * i] == -1:
                    pos = i * 2
                    pos_o = i * 2 + 1
                else:
                    pos = i * 2 + 1
                    pos_o = i * 2
                # set required port
                if demand[pos_o] % 2 == 0:
                    dem = demand[pos_o] + 1
                else:
                    dem = demand[pos_o] - 1
                if bus[dem] == 0:
                    demand[pos] = dem
                    phase_0_imp += 1
        if debug: print ('new demand\t', demand)

        # Phase 2
        #   Each SE with idle input takes an idle output demand
        # #################################################################

    if debug: print ('\nphase 2')

    # step 1
    #   Each SE with idle input detects its sequence among all other SEs with idle input
    bus = [0 for ind in range (N)]  # N bits bus
    pe = [-1 for ind in range (N)]  # state per PE

    # publish on the bus the input port of idle demands
    for i in range (N):
        if demand[i] == -1: bus[i] = 1

    # find the sequence of each idle input among all idle inputs
    for i in range (N):
        if demand[i] == -1:
            # find first 1 from 0 up to port i itself
            count = 0
            for x in range (0, i + 1):
                if bus[x] == 1:
                    count += 1
            pe[i] = count

    if debug:
        print ('step 1\nbus', end='\t')
        for i in range (N // 2):
            print (bus[2 * i:2 * i + 2], end=' - ')
        print ()
        print ('pes:', pe)

    # step 2
    #   Each port with invalid input request takes an output port value
    #   among all available values based on its sequence
    bus = [0 for ind in range (N)]  # N bits bus
    for i in range (N):
        if demand[i] != -1: bus[demand[i]] = 1

    if debug:
        print ('\nstep 2')
        for i in range (N // 2):
            print (bus[2 * i:2 * i + 2], end=' - ')
        print ()

    for i in range (N):
        if demand[i] == -1:
            count = 0
            for y in range (N):
                if bus[y] == 0: count += 1
                if count == pe[i]:
                    demand[i] = y
                    break

    if debug:
        print ('new demand', demand)

    return demand, phase_0_imp


# ##################################################


# #######################################################
# define PEs as class
# #######################################################
class PE:
    def __init__(self, demand, i):
        self.demand = demand  # demand for the pe
        self.num = i  # index of the pe
        self.done = 0  # done processing for current demand permutation
        self.state = 0  # initial state of a PE

    # check single loop pe
    def check_single_loop(self):
        if self.demand[0] // 2 == self.demand[1] // 2 and self.demand[0] > -1 and self.demand[1] > -1:
            return 1  # single loop
        elif self.demand[0] == -1 and self.demand[1] == -1:
            return 2  # no demands
        else:
            return 0  # no single loop, with demands


# ##################################################
# MAIN
# ##################################################

startTime = time.time ()
samples = 10000  # number of tries
dont_care = 0.  # percentage of less than 100% traffic
dont_care_count = 0  # <100% traffic count
with_phase_0 = 1  # with first phase of filling idle ports
time_pes_per_clk = 2
time_overhead_clks = 2
fn_wr = open ('chains.txt', 'w')
debug = 0  # debug

print ('dont care\t', dont_care)
print ('phase0 en\t', with_phase_0)

for N in (4, 8, 16, 32, 64, 128, 256, 512, 1024):
    startTime = time.time ()

    if N == 8: Permutations = list (itertools.permutations ([0, 1, 2, 3, 4, 5, 6, 7]))
    if N == 4: Permutations = list (itertools.permutations ([0, 1, 2, 3]))

    if N == 4: samples = 24
    elif N == 8: samples = 40320
    elif N < 512: samples = 10000
    else: samples = 10000
    counter = 0

    # initialize statistics
    # ##################################################
    hist_num = [0 for ind in range (N // 2)]  # number of chains, hist starts at 1
    hist_len = [0 for ind in range (N // 2)]  # length of chain,  hist starts at 1
    hist_first_len = [0 for ind in range (N // 2)]
    TotalNumChains = 0  # total number of chains
    TotalLenChains = 0
    hist_time = [0 for ind in range (N + 6)]  # processing time,  hist starts at 0
    total_proc_time = 0  # total processing time
    max_proc_time = 0  # max processing time
    min_proc_time = 2000000  # max processing time

    first_chain_sum_len = 0
    sum_phase_0_imp = 0

    # start loop for permutations
    # ##################################################
    for t in range (samples):

        # initialization
        chains = []
        pe_list = []
        demand_proc_time = 0

        # Set random demand
        vector = list (range (N))
        demand = random.sample (vector, N)
        # reduce demand from 100%
        dont_care_count += N * dont_care
        while (dont_care_count >= 1):
            dont_care_count -= 1
            ind = random.randint (0, N - 1)
            while (demand[ind] == -1): ind = random.randint (0, N - 1)
            demand[ind] = -1

        if N == 8 or N == 4:
            demand = Permutations[t]

        # ##################################################
        # first phase - complete partial demands to full 100% demands
        # ##################################################

        if dont_care > 0:
            demand, phase_0_imp = perform_fill (demand, N)
            sum_phase_0_imp += phase_0_imp

        # ##################################################
        # second phase - detect single PE chains
        # ##################################################

        # 1) set pes
        # 2) set all single pe chains
        pe = []
        for i in range (N // 2):
            pe.append (PE (demand[i * 2:i * 2 + 2], i))
            result = pe[i].check_single_loop ()
            if result == 1:  # single loop
                chains.append ([i])
                pe[i].state = 0
            if result > 0:
                pe[i].done = 1  # single loop or not single loop but with demands
            else:
                pe_list.append (i)  # no demands for this pe, add dummy demands in step 3

        if debug:
            print ('Start', demand, end='\t')
            for i in range (N // 2):
                print (i, pe[i].demand, pe[i].done, end=',  ')
            print ('\tchains\t', chains, '\tpes lst\t', pe_list)

        # chains = []     # don't include in statistics chains of a single SE

        # ##################################################
        # third phase - find chains (bigger than single PE)
        # ##################################################
        while (pe_list != []):
            # select first pe in chain and add to chain
            single_chain = []
            start_pe = random.choice (pe_list)
            pe_list.remove (start_pe)
            pe[start_pe].done = 1
            pe[start_pe].state = 0
            single_chain.append (start_pe)
            # set value for left search and for right search
            pe_left = start_pe
            pe_right = start_pe
            pe_left_v = pe[pe_left].demand[0] != -1
            pe_right_v = pe[pe_right].demand[1] != -1
            pe_left_demand = pe[pe_left].demand[0] // 2
            pe_right_demand = pe[pe_right].demand[1] // 2

            # print('outer while:', pe_left, pe_left_v, pe_right, pe_right_v, '\t', pe_list)

            # find chain
            found_left = 1
            found_right = 1
            while (found_left == 1 or found_right == 1):
                # search left
                if found_left == 1:
                    found_left = 0
                    if pe_left_v == 1:
                        for element in pe_list:
                            if pe[element].demand[0] // 2 == pe_left_demand or pe[element].demand[1] // 2 == pe_left_demand:
                                # print('found left', element, pe[element].demand, pe_left_demand)
                                found_left = 1
                                single_chain.append (element)
                                pe_list.remove (element)
                                pe_left = element
                                if pe[pe_left].demand[0] // 2 == pe_left_demand:
                                    pe_left_demand = pe[pe_left].demand[1] // 2
                                    pe_left_v = pe[pe_left].demand[1] != -1
                                elif pe[pe_left].demand[1] // 2 == pe_left_demand:
                                    pe_left_demand = pe[pe_left].demand[0] // 2
                                    pe_left_v = pe[pe_left].demand[0] != -1
                            if found_left == 1: break
                # search right
                if found_right == 1:
                    found_right = 0
                    if pe_right_v == 1:
                        for element in pe_list:
                            if pe[element].demand[0] // 2 == pe_right_demand or pe[element].demand[1] // 2 == pe_right_demand:
                                found_right = 1
                                single_chain.append (element)
                                pe_list.remove (element)
                                pe_right = element
                                if pe[pe_right].demand[0] // 2 == pe_right_demand:
                                    pe_right_demand = pe[pe_right].demand[1] // 2
                                    pe_right_v = pe[pe_right].demand[1] != -1
                                elif pe[pe_right].demand[1] // 2 == pe_right_demand:
                                    pe_right_demand = pe[pe_right].demand[0] // 2
                                    pe_right_v = pe[pe_right].demand[0] != -1
                            if found_right == 1: break
            # end of while for finding a chain

            # statistics on length of first found chain
            if chains == []:
                first_chain_sum_len += len (single_chain)
                hist_first_len[len (single_chain) - 1] += 1
            # add to list of chains
            chains.append (single_chain)
            # calculate processing time of found chains
            if len (single_chain) <= 1 + 2 * time_pes_per_clk:
                TimePerChain = 1
            else:
                tt = (len (single_chain) - (1 + 2 * time_pes_per_clk)) // (2 * time_pes_per_clk)
                res = (len (single_chain) - (1 + 2 * time_pes_per_clk)) % (2 * time_pes_per_clk)
                if res > 0:
                    TimePerChain = 1 + tt + 1
                else:
                    TimePerChain = 1 + tt
            # add found chain to length statistics
            hist_len[len (single_chain) - 1] += 1
            TotalLenChains += len (single_chain)

            demand_proc_time += TimePerChain + time_overhead_clks
            # print('<<<<<<<<', t, single_chain, len(single_chain) , 'chain',TimePerChain, 'demand', demand_proc_time)

        # end of outer while - no more PEs

        if debug:
            print ('Final chains\t', chains, '\n\n')

        #print(demand, chains)

        # statistics: hist of number of chains and hist of size of chains
        if len (chains) > 0:
            hist_num[len (chains) - 1] += 1
            TotalNumChains += len (chains)
            total_proc_time += demand_proc_time
            if max_proc_time < demand_proc_time: max_proc_time = demand_proc_time
            if min_proc_time > demand_proc_time: min_proc_time = demand_proc_time
            hist_time[demand_proc_time] += 1
            # print ('<<<<<<<<', t, 'total', demand_proc_time, total_proc_time)
    # end of loop on number of tries

    # print statistics results
    # ##################################################

    print ('\nN=', N)
    if N == 8 or N == 4:
        print ('number of perms with all chains:', counter, samples, counter / len (Permutations))
    else:
        print ('number of perms with all chains:', counter, samples, counter / samples)

    print ('avg number of chains\t', round (TotalNumChains / samples, 3))
    print ('avg length of chains\t', round (TotalLenChains / TotalNumChains, 3))
    print ('avg length of 1st chain\t', round (first_chain_sum_len / samples, 3))
    print ('avg processing time\t', round (total_proc_time / samples, 3))
    print ('max processing time\t', max_proc_time, 'min', min_proc_time)

    str_w = str (N) + '\t' + str (samples) + '\t'
    print ('hist #chains\tN=', N, '\tSamples=\t', samples, end='\t')
    for i in range (len (hist_num)):  # no occurances above 12so stop at 15   '''range(16): #'''
        print ('%2.2f\t' % round (100 * hist_num[i] / samples, 2), end='')
        if i < 20: str_w += str ('%2.2f\t' % round (100 * hist_num[i] / samples, 2))
    print ()
    str_w += '\n'
    fn_wr.write (str_w)

    print ('hist, length\tN=', N, '\tSamples=\t', samples, end='\t')
    for i in range (0, len (hist_len)):  # , N//32):
        print ('%2.2f\t' % round (100 * hist_len[i] / TotalNumChains, 2), end='')
    print ()

    print ('first, length\tN=', N, '\tSamples=\t', samples, end='\t')
    for i in range (0, len (hist_first_len)):  # , N//32):
        print ('%2.2f\t' % round (100 * hist_first_len[i] / samples, 2), end='')
    print ()

    print ('process time\tN=', N, '\tSamples=\t', samples, end='\t')
    for i in range (len (hist_time)):
        print ('%2.2f\t' % round (100 * hist_time[i] / samples, 2), end='')
    print ()

    print ('execution time  \t', round (time.time () - startTime, 3))

fn_wr.close ()
