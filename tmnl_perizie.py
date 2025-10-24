Run python tmnl_perizie.py
  python tmnl_perizie.py
  shell: /usr/bin/bash -e {0}
  env:
    pythonLocation: /opt/hostedtoolcache/Python/3.11.13/x64
    PKG_CONFIG_PATH: /opt/hostedtoolcache/Python/3.11.13/x64/lib/pkgconfig
    Python_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.13/x64
    Python2_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.13/x64
    Python3_ROOT_DIR: /opt/hostedtoolcache/Python/3.11.13/x64
    LD_LIBRARY_PATH: /opt/hostedtoolcache/Python/3.11.13/x64/lib
    GOOGLE_SHEET_ID: ***
    TRMNL_WEBHOOK_URL: ***
  File "/home/runner/work/TRMNL_CTU/TRMNL_CTU/tmnl_perizie.py", line 33
    <div class="flex flex--column flex--align-center p-8 rounded-4 
               ^
SyntaxError: unterminated string literal (detected at line 33)
Error: Process completed with exit code 1.
