from .course import get_currnet_course_list, get_current_course_list_HTML

# import json
import hashlib
import requests
import json

testacc = [('406262515', 'aa987654321')
        , ('406262319', 'aa987654321')
        , ('406262084', 'aa987654321')]
CUR = 1

if __name__ == '__main__':
    r = requests.Session()

    print(get_currnet_course_list('406262515', 'aa987654321'))

    # li = get_currnet_course_list(*testacc[CUR])
    # json_li = json.dumps(li, sort_keys=True).encode('utf-8')

    # cur_hash = hashlib.md5(json_li).hexdigest()
    # print(cur_hash)

    # print(bytes(json.dumps(d), 'ascii').decode('unicode-escape'))
