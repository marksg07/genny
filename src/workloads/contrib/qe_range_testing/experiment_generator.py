from random import randint
import random
import math
from jinja2 import Environment, PackageLoader, select_autoescape
import itertools
env = Environment(
    loader=PackageLoader("qe_range_testing"),
    autoescape=select_autoescape()
)

insert_threads = 8
query_threads = 1
document_count = 100000
query_count = 10000
assert document_count % insert_threads == 0
assert query_count % query_threads == 0

class Experiment1Stuff:
    def generate_queries(n, ub):
        queries = []
        for _ in range(n):
            v1 = randint(1, ub)
            v2 = randint(1, ub)
            queries.append((min(v1, v2), max(v1, v2)))
        return queries

    def export_queries(queries, query_min_file, query_max_file):
        with open(query_min_file, 'w+') as minf:
            minf.writelines(f'{lower}\n' for lower, _ in queries)

        with open(query_max_file, 'w+') as maxf:
            maxf.writelines(f'{upper}\n' for _, upper in queries)
                

    def query_minmax_file_names(upper_bound):
        s = f'queries/experiment1_1_{{}}_ub{upper_bound}.txt'
        return (s.format("min"), s.format("max"))

    def range_list_file_name(upper_bound):
        return f'queries/experiment1_1_ranges_ub{upper_bound}.txt'

    def generate_all_queries_for_experiment1():
        for upper_bound in [2**9-1, 2**13-1, 2**17-1, 2**31-1]:
            queries = generate_queries(query_count, upper_bound)
            minf, maxf = query_minmax_file_names(upper_bound)
            export_queries(queries, minf, maxf)

    
    def generate_all_workloads_for_experiment1(is_local):
        if is_local: 
            basedir = './src/workloads/contrib/qe_range_testing/'
        else: 
            basedir = './src/genny/src/workloads/contrib/qe_range_testing/'
        if is_local:
            crypt_path = '/home/ubuntu/mongo_crypt/lib/mongo_crypt_v1.so'
        else:
            crypt_path = '/data/workdir/mongocrypt/lib/mongo_crypt_v1.so'
        wldir = 'local' if is_local else 'evergreen'
        main_template = env.get_template("experiment-1.yml.j2")
        storage_template = env.get_template("experiment-1-storage.yml.j2")
        for upper_bound in [2**9-1, 2**13-1, 2**17-1, 2**31-1]:
            minf, maxf = query_minmax_file_names(upper_bound)
            for sparsity in [1, 2, 3, 4]:
                for contention in [0, 4, 8]: 
                    with open(f'workloads/{wldir}/experiment1_1_c{contention}_s{sparsity}_ub{upper_bound}.yml', 'w+') as f:
                        f.write(main_template.render(upper_bound=upper_bound, contention_factor=contention, sparsity=sparsity, document_count=document_count, query_count=query_count, insert_threads=insert_threads, query_threads=query_threads, query_min_file=basedir + minf, query_max_file=basedir + maxf, use_crypt_shared_lib=True, crypt_shared_lib_path=crypt_path))
        with open(f'workloads/{wldir}/experiment1_1_storage_unencrypted.yml', 'w+') as f:
            f.write(storage_template.render(use_encryption=False, document_count=document_count, query_count=query_count, insert_threads=insert_threads, query_threads=query_threads, query_min_file=basedir + minf, query_max_file=basedir + maxf, use_crypt_shared_lib=True, crypt_shared_lib_path=crypt_path))

    def generate_all_workloads_for_experiment0(is_local):
        if is_local:
            crypt_path = '/home/ubuntu/mongo_crypt/lib/mongo_crypt_v1.so'
        else:
            crypt_path = '/data/workdir/mongocrypt/lib/mongo_crypt_v1.so'
        wldir = 'local' if is_local else 'evergreen'
        main_template = env.get_template("experiment-0.yml.j2")
        for upper_bound in [2**9-1, 2**31-1]:
            for sparsity in [1, 4]:
                for contention in [0, 8]: 
                    for small in [False, True]:
                        if small:
                            query_max = 2
                        else:
                            query_max = upper_bound - 1
                        with open(f'workloads/{wldir}/experiment0_c{contention}_s{sparsity}_ub{upper_bound}_{"small" if small else "big"}.yml', 'w+') as f:
                            f.write(main_template.render(upper_bound=upper_bound, contention_factor=contention, sparsity=sparsity, document_count=document_count, query_count=query_count, insert_threads=insert_threads, query_threads=query_threads, query_min=1, query_max=query_max, use_crypt_shared_lib=True, crypt_shared_lib_path=crypt_path))


    def print_wl_names():
        fmt = '    - "qe_range_testing_workloads_evergreen_{}"'

        for upper_bound in [2**9-1, 2**13-1, 2**17-1, 2**31-1]:
            for sparsity in [1, 2, 3, 4]:
                for contention in [0, 4, 8]: 
                    s = f'experiment1_1_c{contention}_s{sparsity}_ub{upper_bound}'
                    print(fmt.format(s))
        print(fmt.format('experiment1_1_storage_unencrypted'))
        for upper_bound in [2**9-1, 2**31-1]:
            for sparsity in [1, 4]:
                for contention in [0, 8]: 
                    for small in [False, True]:
                        print(fmt.format(f'experiment0_c{contention}_s{sparsity}_ub{upper_bound}_{"small" if small else "big"}'))


#class Experiment2Stuff:

eps = 7./3 - 4./3 - 1
def generate_exp2_queries(n, lb, ub, sel, mult):
    queries = []
    for _ in range(n):
        if mult is not None:
            mn = randint(lb, ub + 1 - sel)
            mx = mn + sel - 1
            queries.append((mn * mult, mx * mult))
        else:
            mn = random.uniform(lb, ub - sel)
            mx = mn + sel
            queries.append((mn, mx))
    return queries

def experiment2_query_file(minmax, qtype, sel, spacing):
    return f'queries/experiment2_{minmax}_{qtype}_sel{sel}_{spacing}.txt'

def generate_all_queries_for_experiment2():
    print('Generating exp 2 queries')
    for (qtype, qnum) in [('fixed', 1), ('rand', query_count)]:
        for sel in [5, 100, 1000, 10000]:
            for (spacing, multiplier, prec) in [('ones', 1, 0), ('tenthousandths', 0.0001, 4), ('uniform', None, None)]:
                queries = generate_exp2_queries(qnum, 1, 100000, sel, multiplier)
                if prec is not None:
                    queries = [(round(query[0], prec), round(query[1], prec)) for query in queries]
                with open(experiment2_query_file('min', qtype, sel, spacing), 'w') as f:
                    f.writelines('\n'.join([str(query[0]) for query in queries]))
                with open(experiment2_query_file('max', qtype, sel, spacing), 'w') as f:
                    f.writelines('\n'.join([str(query[1]) for query in queries]))

tenthoufile = 'misc/tenthousandths.txt'
onesfile = 'misc/ones.txt'
def generate_numbers_file():
    shuffled_range = list(range(1, 100001))
    random.shuffle(shuffled_range)
    r = [i * 0.0001 for i in shuffled_range]
    with open(tenthoufile, 'w+') as f:
        f.write('\n'.join([str(round(i,4)) for i in r]))
    with open(onesfile, 'w+') as f:
        f.write('\n'.join([str(i) for i in shuffled_range]))
    #for i in range(0.0001, 10.000001, 0.0001):

exp2fields = [
    ('f_sint32_1', 'Int32', 'ones', 'ones'),
    ('f_sint32_2', 'Int32', 'ones', 'ones'),
    ('f_bin64_1', 'Double', 'ones', 'uniform'),
    ('f_bin64_2', 'Double', 'tenthousandths', 'tenthousandths'),
    ('f_dec128_1', 'Decimal', 'ones', 'uniform'),
    ('f_dec128_2', 'Decimal', 'tenthousandths', 'tenthousandths'),
]

class Experiment2Experiment:
    def __init__(self, is_encrypted, field_name, field_type, spacing, query_type, selectivity, query_spacing, basedir, contention=None, sparsity=None, use_in_query=None):
        self.field_name = field_name
        self.field_type = field_type
        self.query_type = query_type
        self.selectivity = selectivity
        self.spacing = spacing
        self.query_spacing = query_spacing
        self.is_encrypted = is_encrypted
        if is_encrypted:
            assert sparsity is not None
            assert contention is not None
        self.sparsity = sparsity
        self.contention = contention
        self.use_in_query = False if use_in_query is None else use_in_query
        self.min_file = basedir + experiment2_query_file('min', query_type, selectivity, query_spacing)
        self.max_file = basedir + experiment2_query_file('max', query_type, selectivity, query_spacing)
        self.gen_file = basedir + f'misc/{spacing}.txt'

    def get_full_name(self):
        if self.is_encrypted:
            return f'experiment2_encrypted_{self.field_name}_sp{self.sparsity}_cf{self.contention}_sel{self.selectivity}_{self.query_type}'
        else:
            return f'experiment2_unencrypted_{"in_query" if self.use_in_query else "range_query"}_{self.field_name}_sel{self.selectivity}_{self.query_type}'
        
    def get_query_metric_name(self):
        return f'range_query_{self.field_name}_{self.query_type}_sel{self.selectivity}'

def experiment2_experiments(basedir):
    encryption_options = list(itertools.product([True], [1, 2, 3, 4], [0, 4, 8], [None]))
    encryption_options += [(False, None, None, True), (False, None, None, False)]
    return [Experiment2Experiment(is_encrypted, name, type, spacing, qtype, sel, query_spacing, basedir, contention, sparsity, use_in_query)
                    for name, type, spacing, query_spacing in exp2fields 
                    for qtype in ['fixed', 'rand'] 
                    for sel in [5, 100, 1000, 10000]
                    for is_encrypted, sparsity, contention, use_in_query in encryption_options
                    ]


def generate_all_workloads_for_experiment2(is_local):
    print(f'Generating experiment 2 workloads, is_local={is_local}')
    if is_local: 
        basedir = './src/workloads/contrib/qe_range_testing/'
    else: 
        basedir = './src/genny/src/workloads/contrib/qe_range_testing/'
    if is_local:
        crypt_path = '/home/ubuntu/mongo_crypt/lib/mongo_crypt_v1.so'
    else:
        crypt_path = '/data/workdir/mongocrypt/lib/mongo_crypt_v1.so'
    wldir = 'local' if is_local else 'evergreen'
    main_template = env.get_template("experiment-2.yml.j2")
    experiments = experiment2_experiments(basedir)
    # encrypted tests
    print("N experiments", len(experiments))
    for ex in experiments:
        with open(f'workloads/{wldir}/{ex.get_full_name()}.yml', 'w') as f:
            f.write(main_template.render(encrypt=ex.is_encrypted,
                            contention_factor=ex.contention, sparsity=ex.sparsity, 
                            document_count=document_count, query_count=query_count, 
                            insert_threads=insert_threads,
                            use_crypt_shared_lib=True, crypt_shared_lib_path=crypt_path, 
                            tenthoufile=basedir+tenthoufile, onesfile=basedir+onesfile,
                            experiments=[ex], fields=[ex.field_name]))
            
def generate_config_file_for_experiment2():
    template = env.get_template("experiment-2-perfconfig.yml.j2")
    experiments = experiment2_experiments('')
    with open('generated/experiment_2_perfconfig.yml', 'w') as f:
        f.write(template.render(experiments=[ex.get_full_name() for ex in experiments],
                                query_metric_names={ex.get_query_metric_name() for ex in experiments}))

#class Experiment3Stuff:
def get_inserts():
    l = list(range(document_count))
    random.shuffle(l)
    return l

INSERT_FILE='data/experiment3_data.txt'
def generate_inserts():
    inserts = get_inserts()
    with open(INSERT_FILE, 'w') as f:
        f.write('\n'.join(str(i) for i in inserts))

def generate_all_workloads_for_experiment3(is_local):
    if is_local: 
        basedir = './src/workloads/contrib/qe_range_testing/'
    else: 
        basedir = './src/genny/src/workloads/contrib/qe_range_testing/'
    if is_local:
        crypt_path = '/home/ubuntu/mongo_crypt/lib/mongo_crypt_v1.so'
    else:
        crypt_path = '/data/workdir/mongocrypt/lib/mongo_crypt_v1.so'
    wldir = 'local' if is_local else 'evergreen'
    template = env.get_template("experiment3.yml.j2")
    for alldiff in [False, True]:
        for sparsity in [1, 2, 3, 4]:
            for contention in [0, 4, 8]: 
                for upper_bound in [2**17-1, 2**26-1, 2**31-1]:
                    with open(f'workloads/{wldir}/experiment_i1_encrypted_{"diff" if alldiff else "same"}_c{contention}_s{sparsity}_ub{upper_bound}.yml', 'w+') as f:
                        f.write(template.render(encrypt=True, equality=False,
                                                upper_bound=upper_bound, contention=contention, sparsity=sparsity,
                                                document_count=document_count, insert_threads=insert_threads,
                                                alldiff=alldiff, data_path=basedir+INSERT_FILE,
                                                use_crypt_shared_lib=True, crypt_shared_lib_path=crypt_path))
                with open(f'workloads/{wldir}/experiment_i1_encrypted_{"diff" if alldiff else "same"}_equality_c{contention}_s{sparsity}.yml', 'w+') as f:
                        f.write(template.render(encrypt=True, equality=True,
                                                upper_bound=0, contention=contention, sparsity=sparsity,
                                                document_count=document_count, insert_threads=insert_threads,
                                                alldiff=alldiff, data_path=basedir+INSERT_FILE,
                                                use_crypt_shared_lib=True, crypt_shared_lib_path=crypt_path))
        with open(f'workloads/{wldir}/experiment_i1_unencrypted_{"diff" if alldiff else "same"}.yml', 'w+') as f:
            f.write(template.render(encrypt=False,
                                    document_count=document_count, insert_threads=insert_threads,
                                    alldiff=alldiff, data_path=basedir+INSERT_FILE,
                                    use_crypt_shared_lib=True, crypt_shared_lib_path=crypt_path))

def generate_config_file_for_experiment3():
    template = env.get_template("experiment-3-perfconfig.yml.j2")
    experiments = []
    for alldiff in [False, True]:
        for sparsity in [1, 2, 3, 4]:
            for contention in [0, 4, 8]: 
                for upper_bound in [2**17-1, 2**26-1, 2**31-1]:
                    experiments.append(f'experiment_i1_encrypted_{"diff" if alldiff else "same"}_c{contention}_s{sparsity}_ub{upper_bound}')
                experiments.append(f'experiment_i1_encrypted_{"diff" if alldiff else "same"}_equality_c{contention}_s{sparsity}')
        experiments.append(f'experiment_i1_unencrypted_{"diff" if alldiff else "same"}')
    experiments = sorted(experiments)
    with open('generated/experiment_3_perfconfig.yml', 'w') as f:
        f.write(template.render(experiments=experiments, thread_count=insert_threads))

def generate_all_workloads_for_experiment_iht(is_local):
    if is_local: 
        basedir = './src/workloads/contrib/qe_range_testing/'
    else: 
        basedir = './src/genny/src/workloads/contrib/qe_range_testing/'
    if is_local:
        crypt_path = '/home/ubuntu/mongo_crypt/lib/mongo_crypt_v1.so'
    else:
        crypt_path = '/data/workdir/mongocrypt/lib/mongo_crypt_v1.so'
    wldir = 'local' if is_local else 'evergreen'
    template = env.get_template("experiment3.yml.j2")
    for alldiff in [False, True]:
        for upper_bound in [2**10-1, 2**15-1, 2**31-1]:
            for contention in [0, 4, 8]: 
                for sparsity in [1, 2, 3, 4]:
                    for trim_factor in [0, 2, 4, 6, 8]:
                        with open(f'workloads/{wldir}/experiment_iht_{"diff" if alldiff else "same"}_c{contention}_s{sparsity}_ub{upper_bound}_tf{trim_factor}.yml', 'w+') as f:
                            f.write(template.render(encrypt=True, equality=False, trim_factor=trim_factor,
                                                    upper_bound=upper_bound, contention=contention, sparsity=sparsity,
                                                    document_count=document_count, insert_threads=insert_threads,
                                                    alldiff=alldiff, data_path=basedir+get_insert_file(upper_bound),
                                                    use_crypt_shared_lib=True, crypt_shared_lib_path=crypt_path))
                with open(f'workloads/{wldir}/experiment_iht_{"diff" if alldiff else "same"}_equality_c{contention}_ub{upper_bound}.yml', 'w+') as f:
                    f.write(template.render(encrypt=True, equality=True, trim_factor=trim_factor,
                                            upper_bound=upper_bound, contention=contention, sparsity=sparsity,
                                            document_count=document_count, insert_threads=insert_threads,
                                            alldiff=alldiff, data_path=basedir+get_insert_file(upper_bound),
                                            use_crypt_shared_lib=True, crypt_shared_lib_path=crypt_path))
            with open(f'workloads/{wldir}/experiment_iht_{"diff" if alldiff else "same"}_unencrypted_ub{upper_bound}.yml', 'w+') as f:
                f.write(template.render(encrypt=False, equality=False, trim_factor=trim_factor,
                                        upper_bound=upper_bound, contention=contention, sparsity=sparsity,
                                        document_count=document_count, insert_threads=insert_threads,
                                        alldiff=alldiff, data_path=basedir+get_insert_file(upper_bound),
                                        use_crypt_shared_lib=True, crypt_shared_lib_path=crypt_path))
            

PATCHES = {
    'first_iht': '6552a1441e2d17820ea67670',
    'fixed_spread_iht': '6553cc2d850e61f31d0bf529',
    'equality_unenc_iht': '6553d6fe2a60ed842338927b',
    'unenc_i3': '65492a8e3e8e868f07816b54',
    'equality_i3': '654ab0cd1e2d17e7616a095b',
}

def generate_config_file_for_experiment_iht():
    def patch_id(is_encrypted, is_equality, alldiff, upper_bound):
        def _inner():
            new_spread = alldiff and upper_bound != 2**31-1
            if is_encrypted:
                if is_equality:
                    if new_spread: 
                        return 'equality_unenc_iht'
                    else:
                        return 'equality_i3'
                else:
                    if new_spread:
                        return 'fixed_spread_iht'
                    else:
                        return 'first_iht'
            else:
                if new_spread:
                    return 'equality_unenc_iht'
                else:
                    return 'unenc_i3'
        return PATCHES[_inner()]

    template = env.get_template("experiment-3-perfconfig.yml.j2")
    experiment_patches = {v: [] for v in PATCHES.values()}
    for upper_bound in [2**10-1, 2**15-1, 2**31-1]:
        for alldiff in [False, True]:
            range_patchid = patch_id(True, False, alldiff, upper_bound)
            for contention in [0, 4, 8]: 
                for sparsity in [1, 2, 3, 4]:
                    for trim_factor in [0, 2, 4, 6, 8]:
                        experiment_patches[range_patchid].append(f'experiment_iht_{"diff" if alldiff else "same"}_c{contention}_s{sparsity}_ub{upper_bound}_tf{trim_factor}')
                eq_patch_id = patch_id(True, True, alldiff, upper_bound)
                if upper_bound == 2**31 - 1: 
                    experiment_patches[eq_patch_id].append(f'experiment_i1_encrypted_{"diff" if alldiff else "same"}_equality_c{contention}_s1')
                elif alldiff:
                    experiment_patches[eq_patch_id].append(f'experiment_iht_{"diff" if alldiff else "same"}_equality_c{contention}_ub{upper_bound}')
            unenc_patchid = patch_id(False, False, alldiff, upper_bound)
            if upper_bound == 2**31 - 1:
                experiment_patches[unenc_patchid].append(f'experiment_i1_unencrypted_{"diff" if alldiff else "same"}')
            elif alldiff:
                experiment_patches[unenc_patchid].append(f'experiment_iht_{"diff" if alldiff else "same"}_unencrypted_ub{upper_bound}')
                    
    with open('generated/experiment_iht_perfconfig.yml', 'w') as f:
        f.write(template.render(experiments_by_patch=experiment_patches, all_experiments = sum(experiment_patches.values(), []), thread_count=insert_threads))

def get_iht_inserts(max_val):
    domain_size = min(max_val + 1, document_count)
    times = document_count // domain_size
    looped_doc_count = domain_size * times
    remainder = document_count - looped_doc_count
    
    l = list(itertools.islice(itertools.cycle(range(domain_size)), looped_doc_count))
    l += list(random.sample(range(domain_size), remainder))
    assert(len(l) == document_count)
    print(max(l), min(l))
    assert(max(l) == max_val or max_val > document_count)
    assert(min(l) == 0)
    random.shuffle(l)
    return l

def generate_iht_inserts():
    for upper_bound in [2**10-1, 2**15-1, 2**31-1]:
        inserts = get_iht_inserts(upper_bound)
        with open(get_insert_file(upper_bound), 'w') as f:
            f.write('\n'.join(str(i) for i in inserts))

def get_insert_file(ub):
    return f'data/experiment_iht_ub{ub}_data.txt'

def get_i2_uniform(minsupp, maxsupp, prec, minfreq, maxfreq):
    prec_factor = 10**prec
    # max_picks = int(math.ceil(document_count / minfreq))
    chosen = []
    chosen_set = set()
    
    while len(chosen) < document_count:
        next_val = random.randint(minsupp * prec_factor, maxsupp * prec_factor)
        if next_val in chosen_set:
            continue
        freq = random.randint(minfreq, maxfreq)
        freq = min(freq, document_count - len(chosen))
        chosen += [next_val] * freq
        chosen_set.add(next_val)
    assert len(chosen) == document_count
    print(f'Generated {document_count} values, {len(chosen_set)} are unique')
    chosen = [c / (1.0*prec_factor) for c in chosen]
    random.shuffle(chosen)
    return chosen

def calculate_harmonic_sum(n, alpha):
    total_sum = 0.0
    for i in range(1, n + 1):
        total_sum = total_sum + 1 / math.pow(i, alpha)
    return total_sum

def get_i2_zipf(values):
    num_values = len(values)
    sum_freq = 0
    alpha = 1.1
    freq_list = []

    H = calculate_harmonic_sum(num_values, alpha)

    for i in range(num_values):
        f_i = max(1, int(round(document_count * (math.pow(i + 1, -alpha) / H))))
        freq_list.append(f_i)
        sum_freq += f_i

    if sum_freq != document_count:
        print(f'Subbing {sum_freq - document_count}')
        freq_list[0] -= sum_freq - document_count
    print(freq_list, len(freq_list), sum(freq_list))

    ret = []
    for i in range(num_values):
        ret += [values[i]] * freq_list[i]
    random.shuffle(ret)
    assert len(ret) == document_count
    return ret

def generate_i2_inserts():
    ubig = get_i2_uniform(0, 10**10, 4, 1, 5)
    usmall = get_i2_uniform(1699021116, 1699024716, 0, 500, 1000)
    zbig = get_i2_zipf([i / 100. for i in range(0, 10000)])
    zsmall = get_i2_zipf(list(range(0, 200)))
    fname_map = {'uniform_big': (ubig, 4), 'uniform_small': (usmall, 0), 'zipf_big': (zbig, 2), 'zipf_small': (zsmall, 0)}
    for fname, (docs, rounding) in fname_map.items():
        with open(f'data/{fname}.txt', 'w') as f:
            f.write('\n'.join([str(round(d, rounding)) for d in docs]))

class ExpI2Field:
    def __init__(self, datafile_name, upper_bound, precision):
        self.name = datafile_name
        self.ub = upper_bound
        self.prec = precision

expi2fields = [
    ExpI2Field('uniform_big', 10**10, 4),
    ExpI2Field('uniform_small', 10**13, 0),
    ExpI2Field('zipf_big', 100, 2),
    ExpI2Field('zipf_small', 199, 0)
]

def generate_i2_workloads(is_local):
    if is_local: 
        basedir = './src/workloads/contrib/qe_range_testing/'
    else: 
        basedir = './src/genny/src/workloads/contrib/qe_range_testing/'
    if is_local:
        crypt_path = '/home/ubuntu/mongo_crypt/lib/mongo_crypt_v1.so'
    else:
        crypt_path = '/data/workdir/mongocrypt/lib/mongo_crypt_v1.so'
    wldir = 'local' if is_local else 'evergreen'
    template = env.get_template("experiment-i2.yml.j2")
    for field in expi2fields:
        for contention in [0, 4, 8]: 
            for sparsity in [1, 2, 3, 4]:
                for trim_factor in [0, 2, 4, 6, 8]:
                    with open(f'workloads/{wldir}/experiment_i2_ran_{field.name}_c{contention}_s{sparsity}_tf{trim_factor}.yml', 'w+') as f:
                        f.write(template.render(encrypt=True, equality=False, trim_factor=trim_factor,
                                                upper_bound=field.ub, contention=contention, sparsity=sparsity,
                                                document_count=document_count, insert_threads=insert_threads,
                                                precision=field.prec, data_path=basedir+f'data/{field.name}.txt',
                                                use_crypt_shared_lib=True, crypt_shared_lib_path=crypt_path))
            with open(f'workloads/{wldir}/experiment_i2_eq_{field.name}_c{contention}.yml', 'w+') as f:
                f.write(template.render(encrypt=True, equality=True,
                                        contention=contention,
                                        document_count=document_count, insert_threads=insert_threads,
                                        data_path=basedir+f'data/{field.name}.txt',
                                        use_crypt_shared_lib=True, crypt_shared_lib_path=crypt_path))
        with open(f'workloads/{wldir}/experiment_i2_eq_{field.name}_c{contention}.yml', 'w+') as f:
            f.write(template.render(encrypt=False,
                                    document_count=document_count, insert_threads=insert_threads,
                                    data_path=basedir+f'data/{field.name}.txt',
                                    use_crypt_shared_lib=True, crypt_shared_lib_path=crypt_path))


# generate_inserts()


# generate_all_queries_for_experiment1()
# generate_all_workloads_for_experiment1(is_local=False)
# generate_all_workloads_for_experiment1(is_local=True)
# print_wl_names()
# generate_all_workloads_for_experiment0(is_local=False)
# generate_all_workloads_for_experiment0(is_local=True)

#generate_numbers_file()
# generate_all_queries_for_experiment2()
# generate_all_workloads_for_experiment2(is_local=True)
# generate_all_workloads_for_experiment2(is_local=False)
# generate_config_file_for_experiment2()

# generate_all_workloads_for_experiment3(is_local=True)
# generate_all_workloads_for_experiment3(is_local=False)
# generate_config_file_for_experiment3()

# generate_iht_inserts()
# generate_all_workloads_for_experiment_iht(is_local=True)
# generate_all_workloads_for_experiment_iht(is_local=False)
# generate_config_file_for_experiment_iht()

# generate_i2_inserts()
generate_i2_workloads(True)
generate_i2_workloads(False)