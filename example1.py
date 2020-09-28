#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import getpass
import urllib.request
from functools import partial
from http.server import HTTPServer

from dispatch import Dispatch
from request_handler import RequestHandler


def run(cmd, cwd=None):
    print(f'running command [{cmd}]')
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    code, stdout, stderr = res.returncode, res.stdout.decode("utf-8"), res.stderr.decode("utf-8")
    print(f'stdout=[[{stdout}]]')
    print(f'stderr=[[{stderr}]]')
    print('-' * 40)
    print(f'status={code}')
    return {'status': code, 'stdout': stdout, 'stderr': stderr}


class Example1:
    """
    manage an array of python
    """
    ports = list(range(5001, 5004))
    executable = 'example1helper.py'

    # -l long output, also command line with pid
    # -f Match against full argument lists
    pgrep_base_args = ['-u', getpass.getuser(), '-l', '-f', executable]

    def API_execute(self):
        res = self.API_pgrep_processes()
        if res['status'] == 0:
            res['message'] = 'already in execution'
        else:
            res = self.API_execute_no_checks()
            res['message'] = 'execute done'
        print(res)
        return res

    def API_execute_no_checks(self):
        self.API_pkill_processes()

        def new(port):
            cmd = ['nohup', './' + self.executable, f'{port}']
            print(f'running command {" ".join(cmd)}')
            res = subprocess.Popen(cmd, cwd=".",
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, preexec_fn=os.setpgrp)
            time.sleep(0.1)
            return res

        pid_list = [new(port).pid for port in self.ports]
        result = {'pid_list': pid_list}
        print(result)
        return result

    def API_pkill_processes(self):
        return run(['pkill'] + self.pgrep_base_args)

    def API_git_pull(self):
        return run(['git', 'pull'], cwd='..')

    def API_pgrep_processes(self):
        return run(['pgrep'] + self.pgrep_base_args)

    def API_aspetta(self):
        time.sleep(3)
        return 'waited a bit'

    def API_health(self):
        ok = []
        failed = []
        for port in self.ports:
            try:
                decode = urllib.request.urlopen(f'http://localhost:{port}', timeout=1).read().decode('utf-8')
                ok.append((port, decode))
            except Exception as ex:
                failed.append((port, str(ex)))

        res = {}
        if len(failed) > 0:
            res['result'] = 'FAILED'
            res['errors'] = failed
        else:
            res['result'] = 'everything ok'
        res['ok'] = ok
        print(res)
        return res


def main():
    os.chdir(os.path.dirname(__file__))
    port = 8090
    print('Starting server web v0.1 on port %d...' % port)

    Example1().API_execute()

    api_dispatch = Dispatch().register(Example1, 'API_')

    def handler(request: RequestHandler) -> bool:
        params, rpath = request.decode_request()
        api_name = rpath[1:]  # remove initial /
        print('api_name = ' + api_name)
        if api_name == 'list':
            request.send_json(list(api_dispatch.registered.keys()))
        elif api_name == '':
            request.serve_file(os.path.dirname(__file__), "index.html")
        else:
            instance = Example1()
            instance.request = request
            result = api_dispatch.dispatch(instance, api_name, params)
            if result is not None:
                request.send_json(result)

        return True

    httpd = HTTPServer(('', port), partial(RequestHandler, handler=handler))
    httpd.timeout = 10

    print('serving...')
    httpd.serve_forever()
    exit(0)


if __name__ == '__main__':
    main()
