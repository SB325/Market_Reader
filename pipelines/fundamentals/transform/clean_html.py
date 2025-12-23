import pdb
import json
import html_to_json

data_obj_out = {}

def serialize_string(data_obj):
    former_company_count = 1
    rows = data_obj.split('\n')
    rows = [row for row in rows if row and ':' in row]
    
    rows_n_levels = []
    for cnt, row in enumerate(rows):
        val = row.split('\t')
        for cnt_, v in enumerate(val):
            if v:
                break
        entry = [cnt_, val[cnt_:]]
        rows_n_levels.append(entry)

    ancestors = []
    final_dict = {}
    for row in rows_n_levels:
        level = row[0]+1
        key = row[1][0].replace(':','').strip()
        value = row[1][-1]
        if len(row[1])==1:
            value = ''
        depth = level-len(ancestors)
        # if 'FORMER COMPANY' in key:
        #     pdb.set_trace()
        if depth==0:
            if level==1:
                final_dict.update({key: value})
            else:
                # traverse to last ancestor
                temp_dict = final_dict[ancestors[0]]
                for ancestor in ancestors[1:]:
                    if isinstance(temp_dict[ancestor], str):
                        break
                    else:
                        temp_dict = temp_dict[ancestor]
                temp_dict.update({key: value})
            ancestors[-1] = key

        elif depth<0:
            ancestors = ancestors[:level-1]
            # traverse to last ancestor
            if not ancestors:
                final_dict.update({key: value})
            else:
                temp_dict = final_dict[ancestors[-1]]
                for ancestor in ancestors[1:]:
                    if isinstance(temp_dict[ancestor], str):
                        break
                    else:
                        temp_dict = temp_dict[ancestor]
                if key in temp_dict.keys():
                    if 'FORMER COMPANY' in key:
                        former_company_count += 1
                        key = f'{key}{former_company_count}'
                    else:
                        pdb.set_trace()
                        print('This case should cover another repeated key')
                        
                temp_dict.update({key: value})
            ancestors.append(key)
            
        elif depth==1:
            # new level introduced
            if level==1:
                final_dict.update({key: value})
            else:
                parent_key = ''
                temp_dict = final_dict[ancestors[0]]
                if temp_dict:
                    for ancestor in ancestors[1:]:
                        if ancestor in temp_dict.keys():
                            if not temp_dict[ancestor]:
                                parent_key = list(temp_dict.keys())[-1]
                                temp_dict[parent_key] = {key: value}
                                break
                            
                        else:
                            temp_dict[ancestor] = {key: value}
                else:
                    final_dict[ancestors[0]] = {key: value}
            ancestors.append(key)

    return final_dict

def next_level(data_obj):
    global data_obj_out
    sub_dict = {}
    sub_list = []

    # data_obj can be a list or dictionary
    if isinstance(data_obj, list):
        # break down to next non-list value
        for obj in data_obj:
            if isinstance(obj, str):
                # pdb.set_trace()
                obj = html_to_json.convert(obj)
            
            for key, value in obj.items():
                sub_dict.update({key: next_level(value)})

    elif isinstance(data_obj, dict):
        for key, value in data_obj.items():
            # pdb.set_trace()
            sub_dict.update({key: next_level(value)})

    elif isinstance(data_obj, str):
        if '>' in data_obj:
            json_obj = html_to_json.convert(data_obj)
            if not json_obj:
                pdb.set_trace()
                return None
            for key, value in json_obj.items():
                sub_dict.update({key: next_level(value)})

        elif '\n\t' in data_obj:
            data_obj_out = serialize_string(data_obj)
            return data_obj_out

    else:
        pdb.set_trace()
        print("what's going on?")

    return sub_dict

def clean_html(data: dict, verbose: bool = False):
    global data_obj_out
    # Jsonify data.content = data.json
    # if primaryDocDescription is empty, derive from data.json
    # update data dictionary with data.json and return

    input_json = html_to_json.convert(data['rawContent'])  # dict

    try:
        clean_json = next_level(input_json)
    except:
        print('recursion limit probably reached. Continuing')

    if not data_obj_out:
        if verbose:
            print("check input_json and clean_json to find why obj is missing.")

    data.update({'cleanContent' : json.dumps(data_obj_out)})