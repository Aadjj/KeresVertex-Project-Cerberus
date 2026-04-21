import subprocess

def get_hwid():
    cmd = 'wmic csproduct get uuid'
    uuid = str(subprocess.check_output(cmd, shell=True))
    return uuid

def verify_deployment():
    authorized_ids = ["124522215481651"]
    if get_hwid() not in authorized_ids:
        print("Unauthorized environment. Fail")
        exit()