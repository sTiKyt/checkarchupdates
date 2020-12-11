#!/usr/bin/env python

from os import getuid, getenv, remove, makedirs, path, symlink
from atexit import register as reg_exit_handler
from subprocess import Popen, PIPE, DEVNULL
from distutils.spawn import find_executable
from time import sleep
import argparse


class ArchUpdates:
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.userid = getuid()
        self.tmpdir = getenv("TMPDIR") if getenv("TMPDIR") is not None else "/tmp"
        self.updates_db = f"{self.tmpdir}/checkup-db-{self.userid}/"

        self.parser.add_argument("-d", "--download", dest="download_to_cache", help="Download pending updates to the pacman cache", action="store_true")

        self.args = self.parser.parse_args()

        if find_executable("pacman-conf") is not None:
            self.db_path = Popen(["pacman-conf"], stdout=PIPE).stdout.read().decode("utf-8").split("\n", 3)[2].split(" = ", 2)[1]
        else:
            self.db_path = "/var/lib/pacman/"

        if not path.isdir(self.updates_db):
            makedirs(self.updates_db)

        if not path.islink(f'{self.updates_db}/local'):
            symlink(f"{self.db_path}/local", self.updates_db)
        if not Popen(["fakeroot", "--", "pacman", "-Sy", "--dbpath", f"{self.updates_db}"], stdout=PIPE, stderr=DEVNULL).stdout.read().decode("utf-8"):
            print("Cannot fetch updates")
            exit()

    def get_updates(self):
        raw_data = Popen(["pacman", "-Qu", "--dbpath", f"{self.updates_db}"], stdout=PIPE, stderr=DEVNULL).stdout.read()
        list_of_updates = Popen(["grep", "-e", "->"], stdin=PIPE, stdout=PIPE, stderr=DEVNULL).communicate(raw_data)[0].decode("utf-8").splitlines()
        return list_of_updates

    def download_updates_to_cache(self):
        if self.args.download_to_cache:
            if self.userid == 0:
                if len(self.get_updates()) > 0:
                    print(f'{len(self.get_updates())} updates available to download')
                    print("Proceeding...")
                    for value in self.get_updates():
                        split_value = value.split(" ", 3)
                        process = Popen(["pacman", "-Sw", "--noconfirm", split_value[0], "--dbpath", f"{self.updates_db}", "--logfile", f'{DEVNULL}'])
                        while process.poll() is None:
                            sleep(1)
                else:
                    print("There are no updates to download")
            else:
                print("You cannot perform this operation unless you are root")
                exit()

    def remove_db_lock(self):
        try:
            remove(f"{self.updates_db}db.lck")
        except FileNotFoundError:
            pass


def main():
    reg_exit_handler(ArchUpdates().remove_db_lock)
    ArchUpdates().download_updates_to_cache()
    print("\n".join(ArchUpdates().get_updates()))
# main() # For Debugging Purposes, make sure to comment out before building package
