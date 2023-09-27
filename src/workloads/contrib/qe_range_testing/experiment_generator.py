from random import randint
from jinja2 import Environment, PackageLoader, select_autoescape
env = Environment(
    loader=PackageLoader("qe_range_testing"),
    autoescape=select_autoescape()
)
insert_threads = 16
query_threads = 1
document_count = 100000
query_count = 100000
assert document_count % insert_threads == 0
assert query_count % query_threads == 0

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
                     
tenthoufile = 'misc/tenthousandths.txt'
onesfile = 'misc/ones.txt'
def generate_numbers_file():
    r = [i * 0.0001 for i in range(1, 100001)]
    with open(tenthoufile, 'w+') as f:
        f.write('\n'.join([str(round(i,4)) for i in r]))
    with open(onesfile, 'w+') as f:
        f.write('\n'.join([str(i) for i in range(1, 100001)]))
    #for i in range(0.0001, 10.000001, 0.0001):

                    
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
    for sparsity in [1, 2, 3, 4]:
        for contention in [0, 4, 8]: 
            with open(f'workloads/{wldir}/experiment2_c{contention}_s{sparsity}.yml', 'w+') as f:
                f.write(main_template.render(contention_factor=contention, sparsity=sparsity, document_count=document_count, query_count=query_count, insert_threads=insert_threads, query_threads=query_threads, use_crypt_shared_lib=True, crypt_shared_lib_path=crypt_path, tenthoufile=basedir+tenthoufile, onesfile=basedir+onesfile))
            
# generate_all_queries_for_experiment1()
# generate_all_workloads_for_experiment1(is_local=False)
# generate_all_workloads_for_experiment1(is_local=True)
# print_wl_names()
# generate_all_workloads_for_experiment0(is_local=False)
# generate_all_workloads_for_experiment0(is_local=True)

#generate_numbers_file()
generate_all_workloads_for_experiment2(is_local=True)