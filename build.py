from settings import get_media_path
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


SPEC_PATH_ONE_FILE = "run_desktop_onefile.spec"
SPEC_PATH = "run_desktop.spec"
TEMP_SPEC_PATH = '_spec.spec'

one_file = input('One file? [y/n]\n').lower().startswith('y')
include_data = input('Include data? [y/n]\n').lower().startswith('y')

with open(SPEC_PATH_ONE_FILE if one_file else SPEC_PATH, mode='r') as spec_file:
    with open(TEMP_SPEC_PATH, mode='w') as temp_spec_file:
        temp_spec_file.write(
            (spec_file.read().replace("datas=[]", "datas=" + str(make_datas())) if
             include_data else
             spec_file.read()).replace(
                'icon=""',
                ('icon="%s"' % (get_media_path('icon.ico'),)) if
                os.path.isfile(get_media_path('icon.ico')) else
                ''
            )
        )

if os.path.isdir("build"):
    print("Deleting old build")
    os.remove("build")
if os.path.isdir("dist"):
    print("Deleting old dist")
    os.remove("dist")

print('Building...')
os.system("pyinstaller %s" % (TEMP_SPEC_PATH,))
print('Exiting')

if one_file and not include_data:
    print("Moving .exe to root directory")
    os.replace("dist\\Emoveo.exe", "Emoveo.exe")

input("Press enter to continue")
