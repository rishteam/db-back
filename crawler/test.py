from .course import get_course_list, get_course_list_HTML, ALL_YEAR
from .parser import courseHTML_to_dict

# import json
import hashlib
import requests
import json

testacc = [('406262515', 'aa987654321')
        , ('406262319', 'aa987654321')
        , ('406262084', 'aa987654321')]
CUR = 2

if __name__ == '__main__':
    r = requests.Session()


    print(get_course_list(*testacc[CUR], None, ALL_YEAR))

    # with open('/home/roy4801/Desktop/proj/database/login/1081_1.html', 'r') as f:
    #     html = f.read()

    # print(courseHTML_to_dict(html))

    # cur_hash = hashlib.md5(json_li).hexdigest()
    # print(cur_hash)

    # print(bytes(json.dumps(d), 'ascii').decode('unicode-escape'))
