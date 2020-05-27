import os

include = ['media', 'ui']
include_files = ['database.db']


def make_datas(path='.'):
    datas = []
    for p, ds, fs in os.walk(path):
        p = os.path.normcase(os.path.normpath(p))
        inc = False
        for i in include:
            i = os.path.normcase(os.path.normpath(i))
            if os.path.commonprefix([p, i]) == i:
                inc = True
                break
        if inc:
            for f in fs:
                ffp = os.path.join(p, f)
                datas.append((ffp, p))
    for f in include_files:
        if os.path.isfile(f):
            datas.append((f, os.path.normpath(os.path.dirname(f))))
    return datas


print(make_datas())
