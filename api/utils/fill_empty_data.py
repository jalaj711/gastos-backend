def fill_empty_data(arr: list, properties: list, key: str, key_iterator: list):
    arr = list(arr)
    missing_elem = {}
    for i in properties:
        missing_elem[i] = 0

    present_keys = []
    for j in arr:
        present_keys.append(j[key])
    
    for k in key_iterator:
        if k not in present_keys:
            missing = {}
            missing[key] = k
            missing.update(missing_elem)
            arr.append(missing)
    
    return arr