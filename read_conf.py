import json

with open('confirmation_codes.json', 'r') as jf:
    jsob = json.load(jf)

def conf_codes():
    jsob_len = len(jsob)
    for k in range(jsob_len):
        jsob[int(k)] = jsob[str(k)]
        del jsob[str(k)]
    return jsob


if __name__ == '__main__':
    for k, v in conf_codes().items():
        print(k, '-', v)