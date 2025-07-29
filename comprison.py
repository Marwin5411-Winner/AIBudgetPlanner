import time
import random


def compare_data_structures():

    data_size = 10000
    sample_data = list(range(data_size))
    random.shuffle(sample_data)





    lst = sample_data.copy()
    tpl = tuple(sample_data)
    st = set(sample_data)

    print("Operation\tList\t\tTuple\t\tSet")
    print("-" * 60)

    
    
    
    
    add_elem = data_size + 1
    start = time.time()
    lst.append(add_elem)
    list_add_time = time.time() - start

    start = time.time()
    tpl = tpl + (add_elem,)
    tuple_add_time = time.time() - start

    start = time.time()
    st.add(add_elem)
    set_add_time = time.time() - start

    print(f"Add\t\t{list_add_time:.6f}\t{tuple_add_time:.6f}\t{set_add_time:.6f}")

    # Remove
    rem_elem = sample_data[0]
    start = time.time()
    lst.remove(rem_elem)
    list_rem_time = time.time() - start

    start = time.time()
    tpl = tuple(x for x in tpl if x != rem_elem)
    tuple_rem_time = time.time() - start

    start = time.time()
    st.remove(rem_elem)
    set_rem_time = time.time() - start

    print(f"Remove\t\t{list_rem_time:.6f}\t{tuple_rem_time:.6f}\t{set_rem_time:.6f}")

    
    
    
    
    search_elem = sample_data[data_size // 2] # Get middle Element
    start = time.time()
    _ = search_elem in lst
    list_search_time = time.time() - start

    start = time.time()
    _ = search_elem in tpl
    tuple_search_time = time.time() - start

    start = time.time()
    _ = search_elem in st
    set_search_time = time.time() - start

    print(f"Search\t\t{list_search_time:.6f}\t{tuple_search_time:.6f}\t{set_search_time:.6f}")

    
    
    
    
    start = time.time()
    tuple(lst)
    list_convert_time = time.time() - start

    start = time.time()
    list(tpl)
    tuple_convert_time = time.time() - start

    start = time.time()
    list(st)
    set_convert_time = time.time() - start

    print(f"Convert\t\t{list_convert_time:.6f}\t{tuple_convert_time:.6f}\t{set_convert_time:.6f}")




    start = time.time()
    sorted(lst)
    list_sort_time = time.time() - start

    start = time.time()
    sorted(tpl)
    tuple_sort_time = time.time() - start

    start = time.time()
    sorted(st)
    set_sort_time = time.time() - start

    print(f"Sort\t\t{list_sort_time:.6f}\t{tuple_sort_time:.6f}\t{set_sort_time:.6f}")

if __name__ == "__main__":
    compare_data_structures()