def find_between(data, pat_list, start_index=0):
    interactive = False  # Interactive mode
    if len(pat_list) < 2 or start_index == -1:
        return [], -1
    i_list = []
    cur_i = start_index
    prev_length = 0
    for p in pat_list:
        cur_i = data.find(p, cur_i + prev_length)
        if cur_i != -1:
            if interactive:
                print(p, cur_i)
            i_list.append(cur_i)
            prev_length = len(p)
        else:
            if interactive:
                print(p, "FAILED")
                input("")
            return [], -1

    found_list = []
    for i in range(0, len(i_list) - 1):
        found_list.append(data[i_list[i] + len(pat_list[i]) : i_list[i + 1]])
    if interactive:
        print(found_list)
        print("FIND_BETWEEN DONE")
    return found_list, i_list[-1] + len(pat_list[-1])


def find_one(data, pat_list):
    d, i = find_between(data, pat_list)
    if i != -1:
        return d[0]
    else:
        return ""


def find_all(data, pat_list, index=-1):
    i = 0
    ret_list = []
    while i != -1:
        d, i = find_between(data, pat_list, i)
        if i != -1:
            i += 1
            ret_list.append(d[index])
    return ret_list
