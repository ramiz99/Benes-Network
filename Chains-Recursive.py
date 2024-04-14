# ----------------------------------------------------------------------------
#
# Detecting chains of dependencies in first column of Benes network
#
# ----------------------------------------------------------------------------

import random
import time

# #######################################################
# define PEs as class
# #######################################################
class PE:
    def __init__(self, demand, i):
        self.demand = demand    # demand for the pe
        self.num = i            # index of the pe
        self.done = 0           # done processing for current demand permutation
        self.state = 0          # initial state of a PE
        if self.state == 0: self.inner_demand = self.demand[:]
        else:               self.inner_demand = self.demand[::-1]

    # set inner demand, that is demand after PE state
    def SetInnerDemand(self):
        if self.state == 0: self.inner_demand = self.demand[:]
        else:               self.inner_demand = self.demand[::-1]
        return

    # check single loop pe
    def check_single_loop(self):
        if self.demand[0]//2==self.demand[1]//2 and self.demand[0]>-1 and self.demand[1]>-1: return 1   # single loop
        elif self.demand[0]==-1 and self.demand[1]==-1: return 2                                        # no demands
        else: return 0                                                                                  # no single loop, with demands

# #################################################################################################################################

# ########################################################
#   Function to fill idle input ports with available ones
# ########################################################
def perform_fill(demand_in, N):
    bus = [0 for ind in range (N)]  # N bits bus
    demand = demand_in

    # Phase 0
    #   If an SE has a single valid demand and
    #   its pairing demand to complete a single SE chain is not requested by any other SE,
    #   Than take it
    # ##############################################################
    if with_phase_0 == 1:
        if debug: print ('\nphase 0')
        # publish input port of idle demands on the bus
        for i in range (N):
            if demand_in[i] != -1: bus[demand_in[i]] = 1
        if debug: print ('bus     \t', bus)
        if debug: print ('old demand\t', demand_in)
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
                if demand[pos_o] % 2 == 0:  dem = demand[pos_o] + 1
                else:                       dem = demand[pos_o] - 1
                if bus[dem] == 0: demand[pos] = dem
        if debug: print ('new demand\t', demand)

    # Phase 1
    #   Each SE with idle input takes an idle output demand
    # #################################################################

    if with_phase_1 == 1:
        if debug: print ('\nphase 1')

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

    return demand
# ##################################################

# ########################################################
#   Function to detect all chains
# ########################################################
def perform_chains(demand, N):

    # end recursion when applies
    if N==RecursionEndsAt:
        return 0, 0, 0, 0, 0, [], []
        # max_chain, min_chain, number_of_chains, demand_proc_time, demand_upper, demand_lower

    # initialization
    chains = []                 # list of chains
    pe_list = []                # list of unassigned PEs
    demand_proc_time = 0
    number_of_chains = 0
    pe = []
    demand_upper = [-1 for ind in range (N//2)]
    demand_lower = [-1 for ind in range (N//2)]

    # ##################################################
    # 2nd phase - detect single PE chains
    # ##################################################
    for i in range (N // 2):
        pe.append (PE (demand[i * 2:i * 2 + 2], i))     # create PEs, done = 0, state = 0
        result = pe[i].check_single_loop ()
        if result == 1:                                 # single loop, state is set to bar
            chains.append ([i])
            pe[i].done = 1
            pe[i].state = 0
        elif result == 2:                               # both demands are -1
            pe[i].done = 1
            pe[i].state = 0
        else:
            pe_list.append (i)                          # add to list, PE to process

    if debug:
        print ('Start', demand, end='\t')
        for i in range (N // 2):
            print (i, pe[i].demand, pe[i].done, end=',  ')
        print ('\tchains\t', chains, '\tremaining pes\t', pe_list)

    # include single SE chains to the stats
    chains = []                                         # don't include in statistics chains of a single SE

    # ##################################################
    # 3rd phase - find chains (bigger than single PE)
    # ##################################################
    # create UpBus/DownBus
    UpBus = [0 for i in range (N // 2)]
    DownBus = [0 for i in range (N // 2)]
    publish_pes = []                                    # pes that will publish

    start = 1
    while (pe_list != [] or publish_pes!=[]):
        # select first pe in chain and add to chain
        if start == 1:
            start_pe = random.choice (pe_list)
            pe_list.remove (start_pe)
            pe[start_pe].done = 1
            pe[start_pe].state = 0
            pe[start_pe].SetInnerDemand()
            single_chain = [start_pe]
            # contains what value to publish, 1st is upbus, 2nd is downbus
            publish_pes.append([start_pe, pe[start_pe].inner_demand[0]//2, pe[start_pe].inner_demand[1]//2])
            start = 0

        # publish in UpBus and in DownBus
        for e in publish_pes:
            if e[1]!=-1: UpBus[e[1]] = 1
            if e[2]!=-1: DownBus[e[2]] = 1

        # listen to busses
        publish_pes_new = []
        #for i in range(N//2):
        for i in pe_list:
            if i not in publish_pes and pe[i].done == 0:
                if pe[i].demand[0]!=-1 and UpBus[pe[i].demand[0]//2]==1 or pe[i].demand[1]!=-1 and UpBus[pe[i].demand[1]//2]==1:
                    if i in pe_list: pe_list.remove (i)
                    pe[i].done = 1
                    if i not in single_chain: single_chain.append(i)
                    if pe[i].demand[0]!=-1 and UpBus[pe[i].demand[0]//2]==1:
                        pe[i].state = 1
                        publish_pes_new.append([i, pe[i].demand[1]//2, -1])
                    else:
                        pe[i].state = 0
                        publish_pes_new.append([i, pe[i].demand[0]//2, -1])
                if pe[i].demand[0]!=-1 and DownBus[pe[i].demand[0]//2]==1 or pe[i].demand[1]!=-1 and DownBus[pe[i].demand[1]//2]==1:
                    if i in pe_list: pe_list.remove (i)
                    pe[i].done = 1
                    if i not in single_chain: single_chain.append (i)
                    if pe[i].demand[0]!=-1 and DownBus[pe[i].demand[0] // 2] == 1:
                        pe[i].state = 0
                        publish_pes_new.append([i, -1, pe[i].demand[1]//2])
                    else:
                        pe[i].state = 1
                        publish_pes_new.append([i, -1, pe[i].demand[0]//2])

        if publish_pes_new == []:
            chains.append(single_chain)
            start = 1
            # calculate processing time of found chains
            if len (single_chain) <= (1 + 2 * time_pes_per_clk):
                TimePerChain = 1
            else:
                tt = (len (single_chain) - (1 + 2 * time_pes_per_clk)) // (2 * time_pes_per_clk)
                res = (len (single_chain) - (1 + 2 * time_pes_per_clk)) % (2 * time_pes_per_clk)
                if res > 0: TimePerChain = 1 + tt + 1
                else: TimePerChain = 1 + tt
            demand_proc_time += TimePerChain + time_overhead_clks
        publish_pes = publish_pes_new

    # calculate demands to sub-layers once all settings is completed.
    for i in range(N//2):
        pe[i].SetInnerDemand()
        demand_upper[i] = pe[i].inner_demand[0]//2
        demand_lower[i] = pe[i].inner_demand[1]//2

    if debug:
        print ('chains\t', 'N=', N, chains)
        print('states:', end='')
        for h in range(N//2):
            print(h, '=', pe[h].state, end=', ' )
        print()

    number_of_chains += len(chains)
    max_chain = len(chains)
    min_chain = len(chains)

    # ---------------------------------------------------------
    max_length = 0
    if len(chains)>0:
        for a in chains:
            if len(a)>max_length: max_length = len(a)
    mm = 1
    if max_length>2 and max_length<=4: mm = 2
    elif max_length>4 and max_length<=8: mm = 3
    elif max_length>8 and max_length<=16: mm = 4
    elif max_length>16 and max_length<=32: mm = 5
    elif max_length>32 and max_length<=64: mm = 6
    elif max_length>64 and max_length<=128: mm = 7
    elif max_length>128 and max_length<=256: mm = 8
    elif max_length>256 and max_length<=512: mm = 9
    elif max_length>512 and max_length<=1024: mm = 10
    #print('--', N, max_length, mm, '--', chains)
    # ---------------------------------------------------------


    mm_u, max_chain_u, min_chain_u, numchains_u, demand_proc_time_u, demand_upper_u, demand_lower_u = perform_chains (demand_upper, N//2)
    mm_d, max_chain_d, min_chain_d, numchains_d, demand_proc_time_d, demand_upper_d, demand_lower_d = perform_chains (demand_lower, N//2)

    if demand_proc_time_u > demand_proc_time_d: demand_proc_time += demand_proc_time_u
    else:                                       demand_proc_time += demand_proc_time_d
    if max_chain_u > max_chain_d:               max_chain += max_chain_u
    else:                                       max_chain += max_chain_d
    if min_chain_u < min_chain_d:               min_chain += min_chain_u
    else:                                       min_chain += min_chain_d

    number_of_chains += (numchains_u + numchains_d)/2

    return mm, max_chain, min_chain, number_of_chains, demand_proc_time, demand_upper, demand_lower

# #######################################################


# ##################################################
# MAIN
# ##################################################

startTime = time.time ()
fn_wr = open ('chains-rec.txt', 'w')
samples = 100000      # number of tries
dont_care = 0.1          # percentage of less than 100% traffic
dont_care_count = 0     # <100% traffic count
time_pes_per_clk = 2    # number of pes per clock per bus
time_overhead_clks = 3  # overhead number of clock cycles
with_phase_0 = 0        # for partial permutations only
with_phase_1 = 0        # for partial permutations only
RecursionEndsAt = 8     # size to end recursion
debug = 0               # debug

print('dont care\t', dont_care)
print('time_pes_per_clk\t', time_pes_per_clk)
print('time_overhead_clks\t', time_overhead_clks)

str_num_hist = 'Num\n'
str_time_hist = 'Time\n'
str_minmax_time = 'MinAvgMax Time\n'
str_minmax_num = 'MinAvgMax Size\n'

st = 'time_pes_per_clk\t' + str(time_pes_per_clk) + '\n' + 'time_overhead_clks\t' + str(time_overhead_clks) + '\n\n'
fn_wr.write(st)

for N in (8, 16, 32, 64, 128, 256, 512, 1024):
    #if N==1024: samples = 1000000
    print('\nN\t', N)
    print('samples\t', samples)
    startTime = time.time ()

    RecursionEndsAt = N//2

    # ##################################################
    # initialize statistics
    # ##################################################
    hist_num = [0 for ind in range (N//2)]        # number of chains, hist starts at 1
    hist_time = [0 for ind in range (1000)]        # processing time,  hist starts at 0
    TotalNumChains = 0                            # total number of chains
    total_proc_time = 0                           # total processing time
    max_proc_time = 0                             # max processing time
    min_proc_time = 1000000                       # max processing time
    Max_num_chains = 0
    Min_num_chains = 1000000

    avg_log_length = 0
    hist_length = [0 for ind in range (N)]

    # ##################################################
    # start loop for permutations
    # ##################################################
    for t in range (samples):

        # ##################################################
        # Generate random demand
        # ##################################################
        vector = list (range (N))
        demand = random.sample (vector, N)
        dont_care_count += N*dont_care
        while(dont_care_count>=1):          # reduce demand from 100%
            dont_care_count -= 1
            ind = random.randint(0, N-1)
            while (demand[ind] == -1): ind = random.randint(0, N-1)
            demand[ind] = -1

        # ##################################################
        # 1st phase - Complete partial demands to full 100% demands
        # ##################################################
        if dont_care>0:
            demand = perform_fill(demand, N)
        
        # ##################################################
        # 2nd, 3rd phases: collect all chains
        # ##################################################
        mm, max_chain, min_chain, Numchains, demand_proc_time, demand_upper, demand_lower = perform_chains(demand, N)

        avg_log_length += mm
        hist_length[mm] += 1

        # add extra processing time per layer as per the algorithm
        #                               phases 2,4,5
        if N==32:   demand_proc_time +=   10
        if N==64:   demand_proc_time +=   15
        if N==128:  demand_proc_time +=   20
        if N==256:  demand_proc_time +=   25
        if N==512:  demand_proc_time +=   30
        if N==1024: demand_proc_time +=   35
        if N==2048: demand_proc_time +=   40

        if debug:
            print('>>>', N, demand)
            print('>>>', 'demandUp', demand_upper, 'demandDown', demand_lower)

        # ##################################################
        # Collect statistics
        # ##################################################
        if Numchains>0:
            hist_num[int(Numchains)-1] += 1
            TotalNumChains += Numchains
            total_proc_time += demand_proc_time
            if max_proc_time < demand_proc_time: max_proc_time = demand_proc_time
            if min_proc_time > demand_proc_time: min_proc_time = demand_proc_time
            if Max_num_chains < max_chain: Max_num_chains = max_chain
            if Min_num_chains > min_chain: Min_num_chains = min_chain
            if demand_proc_time<1000: hist_time[demand_proc_time] += 1
            else: print('need to increase his_time', demand_proc_time)

    # end of loop on number of tries

    # ##################################################
    # print statistics results
    # ##################################################
    str_minmax_time += str (N) + '\t'
    str_minmax_num += str(N) + '\t'
    str_num_hist += str (N) + '\t' + str (samples) + '\t'
    str_time_hist += str (N) + '\t' + str (samples) + '\t'

    print('number of chains:\t','min\t', Min_num_chains, '\tavg\t', round(TotalNumChains/samples, 3), '\tmax\t', Max_num_chains)
    print('processing time:\t', 'min\t', min_proc_time, '\tavg\t', round(total_proc_time/samples, 3), '\tmax\t', max_proc_time)

    str_minmax_time += str(min_proc_time) + '\t' + str(round(total_proc_time/samples, 3)) + '\t' + str(max_proc_time) + '\n'
    str_minmax_num += str(Min_num_chains) + '\t' + str (round(TotalNumChains/samples, 3)) + '\t' + str (Max_num_chains) + '\n'

    print('hist #chains\tN=', N, '\tSamples=\t', samples, end='\t')
    for i in range(len (hist_num)):
        print ('%2.4f\t' % round (100 * hist_num[i] / samples, 4), end='')
        str_num_hist += str(round (100 * hist_num[i] / samples, 4)) + '\t'
    print()
    str_num_hist += '\n'

    print('process time\tN=', N, '\tSamples=\t', samples, end='\t')
    for i in range(len(hist_time)):
        print ('%2.4f\t' % round(100*hist_time[i]/samples, 4), end='')
        str_time_hist += str (round(100*hist_time[i]/samples, 4)) + '\t'
    print()
    str_time_hist += '\n'

    print('-- average max length of loops', avg_log_length/samples)
    print('hist length\n')
    for i in range(N):
        print(hist_length[i], end='\t')
    print()

    '''
    fn_wr.write(str_minmax_num)
    fn_wr.write('\n')
    fn_wr.write(str_num_hist)
    fn_wr.write('\n')
    fn_wr.write(str_minmax_time)
    fn_wr.write('\n')
    fn_wr.write(str_time_hist)
    fn_wr.flush()
    print ('execution time  \t', round (time.time () - startTime, 3))
    '''
    # end of loop on samples
fn_wr.write('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n')

fn_wr.write(str_minmax_num)
fn_wr.write('\n')
fn_wr.write(str_num_hist)
fn_wr.write('\n')
fn_wr.write(str_minmax_time)
fn_wr.write('\n')
fn_wr.write(str_time_hist)
fn_wr.close()
# end of loop on N
