import io
import os
import re
import sys
import textwrap
import traceback
import yaml


def render(tpl, data, err_msg=True):
    # Init python generated code
    py = ''
    pyindt = 0
    # Traverse template lines
    for ln in tpl.splitlines():
        # Determine kind of line, add line to generated python code
        if ln.strip().startswith("#@"):  # PYTHON
            pyln = ln.strip()[2:].strip()
            if pyln == 'end':
                pyindt -= 1
            elif pyln == 'else:':
                py += '  ' * (pyindt - 1) + pyln + os.linesep
            elif pyln.startswith('elif '):
                py += '  ' * (pyindt - 1) + pyln + os.linesep
            else:
                py += '  ' * pyindt + pyln + os.linesep
                if pyln and pyln[-1] == ':':
                    pyindt += 1
        elif "<@" in ln:  # TEXT + PYTHON INLINE
            ln = ln.replace("{", "{{").replace("}", "}}")
            if ln.strip().split("<@")[0] == '':
                pyln = f'''ln={ln.strip().encode('unicode_escape')}.decode('unicode_escape');'''
                pyln += f'''print(textwrap.indent(re.sub('<@(.*?)@>', '{{}}', ln).format(*(lambda globs, locs, ln: [eval(expr, globs, locs) for expr in re.findall('<@(.*?)@>', ln)])(globals(), locals(), ln)),'{ln.split("<@")[0]}'))'''
                py += '  ' * pyindt + pyln + os.linesep
            else:
                pyln = f'''ln={ln.encode('unicode_escape')}.decode('unicode_escape');'''
                pyln += '''print(re.sub('<@(.*?)@>', '{}', ln).format(*(lambda globs, locs, ln: [eval(expr, globs, locs) for expr in re.findall('<@(.*?)@>', ln)])(globals(), locals(), ln)))'''
                py += '  ' * pyindt + pyln + os.linesep
        else:  # TEXT
            py += '  ' * pyindt + f'''print({ln.encode('unicode_escape')}.decode('unicode_escape'))''' + os.linesep
    # Capture ouput of generated python code
    stdout_prev = sys.stdout
    stdout = sys.stdout = io.StringIO()
    try:
        exec(py, None, data)
        sys.stdout = stdout_prev
    except Exception as e:
        sys.stdout = stdout_prev
        if err_msg:
            print(f"[x] Error in generated py code, [line {traceback.extract_tb(sys.exc_info()[2])[1][1]}]: {e}\n")
        raise e
    # Return output of generated python code
    return stdout.getvalue().rstrip()
