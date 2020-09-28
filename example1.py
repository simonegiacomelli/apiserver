#!/usr/bin/env python3
import getpass
import os
import subprocess
import time
import urllib.request
from functools import partial
from http.server import HTTPServer

from dispatch import Dispatch
from request_handler import RequestHandler


# the API_ method returns a string

class run:
    def __init__(self, cmd, cwd=None):
        super().__init__()
        self.cmd = cmd
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
        self.status, self.stdout, self.stderr = res.returncode, res.stdout.decode("utf-8"), res.stderr.decode("utf-8")

    def __str__(self):
        st = 'OK' if self.status == 0 else f'FAILED status={self.status}'
        return \
            f'status={st}\n' \
            f'command={" ".join(self.cmd)}\n' \
            f'stdout: ------------------------------\n' \
            f'{self.stdout}\n' \
            f'stderr: ------------------------------\n' \
            f'{self.stderr}'


class Example1:
    """
    manage an array of python web servers
    """
    ports = list(range(5001, 5004))
    executable = 'example1helper.py'

    # -l long output, also command line with pid
    # -f Match against full argument lists
    pgrep_base_args = ['-u', getpass.getuser(), '-l', '-f', executable]

    def API_execute(self):
        pgrep_res = self.pgrep_processes()
        if pgrep_res.status == 0:
            res = 'something is already in execution. See here:\n\n' + str(pgrep_res)
        else:
            res = 'execute() done. See here:\n' + self.API_pkill_and_execute()

        return res

    def API_pkill_and_execute(self):
        self.pkill_processes()

        def new(port):
            cmd = ['nohup', './' + self.executable, f'{port}']
            pid = subprocess.Popen(cmd, cwd=".",
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   preexec_fn=os.setpgrp).pid

            time.sleep(0.1)
            return f'command={" ".join(cmd)} -> pid {pid}'

        lines = [new(port) for port in self.ports]
        result = '\n'.join(lines)
        return result

    def API_pkill_processes(self):
        return str(self.pkill_processes())

    def API_pgrep_processes(self):
        return str(self.pgrep_processes())

    def API_git_pull(self):
        return str(run(['git', 'pull'], cwd='..'))

    def pkill_processes(self) -> run:
        return run(['pkill'] + self.pgrep_base_args)

    def pgrep_processes(self) -> run:
        return run(['pgrep'] + self.pgrep_base_args)

    def API_health(self):
        ok = []
        failed = []
        for port in self.ports:
            port = str(port)
            try:
                decode = urllib.request.urlopen(f'http://localhost:{port}', timeout=1).read().decode('utf-8')
                ok.append(port + ' ' + decode)
            except Exception as ex:
                failed.append(port + ' ' + str(ex))

        res = ''
        ok_lines = '\n\n'.join(ok)
        failed_lines = '\n\n'.join(failed)
        if len(failed) > 0:
            res += f'status=FAILED\n{failed_lines}\n\n'

        res += f'status=OK\n\n{ok_lines}'
        return res


def main():
    os.chdir(os.path.dirname(__file__))
    port = 8090
    print('Starting server web v0.1 on port %d...' % port)

    print(Example1().API_execute())

    api_dispatch = Dispatch().register(Example1, 'API_')

    def handler(request: RequestHandler) -> bool:
        params, rpath = request.decode_request()
        api_name = rpath[1:]  # remove initial /
        print('api_name = ' + api_name)
        if api_name == 'list':
            request.send_json(list(api_dispatch.registered.keys()))
        elif api_name == '':
            request.serve_file(os.path.dirname(__file__), "index.html")
        elif api_name == 'favicon.ico':
            request.send_response(404, '')
        else:
            instance = Example1()
            instance.request = request
            result = api_dispatch.dispatch(instance, api_name, params)
            if isinstance(result, str):
                print(result)
                request.send_string(result)
            elif isinstance(result, (list, set, dict, tuple)):
                request.send_json(result)
            else:
                request.send_json(result.__dict__)

        return True

    httpd = HTTPServer(('', port), partial(RequestHandler, handler=handler))
    httpd.timeout = 10

    print('serving...')
    httpd.serve_forever()
    exit(0)


if __name__ == '__main__':
    main()
