import copy
import subprocess
import sys
import threading
import os
import shutil


def is_file_empty(path):
    return os.stat(path).st_size == 0


DEFAULT_SETTINGS = {
    "DOCKER_ROOT": os.path.expanduser("~"),
    "DOCKER_MOUNT_PATH": '/home/trial',
    "DOCKER_MEM_LIMIT": "1g",
    "DOCKER_CPU_QUOTA_LIMIT": "90000",
    "DOCKER_IMAGE_NAME": "pybuntu",

}


class Docker:
    def __init__(self, unique_code, code_file, input_file, time_limit=1000, custom_settings=None):
        """

        :param unique_code: A unique code that is set for diretory
        :param code_file: Code file
        :param input_file: Input File
        :param time_limit: the code will be terminated if it exceeds this limit (in seconds)
        """
        if sys.platform != "linux":
            raise EnvironmentError("pydock currently supports only linux systems")

        else:
            if code_file[0] != "/" or input_file[0] != "/":
                raise ValueError(
                    "You must supply the absolute path of the code file and input file not the relative path")

        self.settings = copy.deepcopy(DEFAULT_SETTINGS)

        if custom_settings is not None:
            if isinstance(custom_settings, dict):
                for key in custom_settings:
                    self.settings[key] = custom_settings[key]
            else:
                raise ValueError("custom settings must be a type of dictionary object")

        self.CONTAINER_UNIQUE_CODE = str(unique_code)
        self.LOAD_VOLUME_DIR = os.path.join(self.settings["DOCKER_ROOT"], self.CONTAINER_UNIQUE_CODE)
        self.code_file_abs = code_file
        self.inp_file_abs = input_file
        self.code_file_name = os.path.basename(code_file)
        self.input_file_name = os.path.basename(input_file)
        self.time_limit = str(time_limit)

        self.output_file = os.path.join(self.LOAD_VOLUME_DIR, "output.txt")
        self.error_file = os.path.join(self.LOAD_VOLUME_DIR, "error.txt")
        self.exit_code_file = os.path.join(self.LOAD_VOLUME_DIR, "exit_code.txt")

    def setUp(self):

        if os.path.isdir(self.LOAD_VOLUME_DIR):
            raise IsADirectoryError(
                "A directory with same name already exists at this path. Name = " + self.LOAD_VOLUME_DIR)

        os.makedirs(self.LOAD_VOLUME_DIR)
        code_file_copy_path = os.path.join(self.LOAD_VOLUME_DIR, self.code_file_name)
        input_file_copy_path = os.path.join(self.LOAD_VOLUME_DIR, self.input_file_name)

        shutil.copy(self.code_file_abs, code_file_copy_path)
        shutil.copy(self.inp_file_abs, input_file_copy_path)

    def start_container(self):
        docker_process = subprocess.run(
            ["docker", "run", "--name", self.CONTAINER_UNIQUE_CODE, "--rm", "-v",
             self.LOAD_VOLUME_DIR + ":" + self.settings["DOCKER_MOUNT_PATH"],
             "-dit",
             "--memory=" + self.settings["DOCKER_MEM_LIMIT"], "--cpu-quota=" + self.settings["DOCKER_CPU_QUOTA_LIMIT"],
             self.settings["DOCKER_IMAGE_NAME"]])

    def run_code(self):

        main_cmd = f"timeout {self.time_limit}s bash -c 'cat {self.settings['DOCKER_MOUNT_PATH']}/{self.input_file_name} | python3.6 {self.settings['DOCKER_MOUNT_PATH']}/{self.code_file_name} > output.txt' ; echo $? > exit_code.txt"

        # print(main_cmd)
        fe = open(self.error_file, "w")
        dock_ex = subprocess.run(
            ["docker", "exec", "-t", self.CONTAINER_UNIQUE_CODE, "sh", "-c", main_cmd],
            stdout=fe
        )

        fe.close()

        if is_file_empty(self.error_file) is False:
            # print("Code Errored")
            # f = open(self.error_file, "r")
            # print(f.readlines())
            # f.close()

            return -1
        else:
            # No error
            # get exit code
            fx = open(self.exit_code_file, "w")
            docker_ex = subprocess.run(
                ["docker", "exec", "-t", self.CONTAINER_UNIQUE_CODE, "sh", "-c", "cat exit_code.txt"],
                stdout=fx
            )

            fx.close()
            f = open(self.exit_code_file, "r")
            line1 = f.readlines()[0]
            line1 = line1.strip("\n")
            f.close()

            if line1 == "124":
                # print("Code timed out")

                return 124
            else:
                # code executed normally
                # collect output
                fo = open(self.output_file, "w")
                docker_ex = subprocess.run(
                    ["docker", "exec", "-t", self.CONTAINER_UNIQUE_CODE, "sh", "-c", "cat output.txt"],
                    stdout=fo
                )
                fo.close()

                # f = open(self.output_file, "r")
                # print(f.readlines())
                # f.close()
                return 0

    def stop_container(self):
        subprocess.run(["docker", "stop", self.CONTAINER_UNIQUE_CODE])

    def delete_dir(self):
        shutil.rmtree(self.LOAD_VOLUME_DIR)

    def destroy(self):
        self.stop_container()
        self.delete_dir()

    def run(self):
        # This method is meant to be called on an instance of this class
        # It does not delete the volume dir. It is the duty of caller to call delete_dir function again after this one
        try:
            self.setUp()
            self.start_container()
            status_code = self.run_code()
            self.stop_container()
            return status_code
        except:
            self.stop_container()
            self.delete_dir()
            print("Unexpected error:", sys.exc_info()[0])
            raise
            pass

    @classmethod
    def run_code_and_collect_output(cls, unique_code, code_file, input_file, time_limit):
        # This method is meant to be called on the class. It deletes everything n completion
        instance = Docker(unique_code=unique_code, code_file=code_file, input_file=input_file, time_limit=time_limit)
        try:

            instance.setUp()
            instance.start_container()

            status_code = instance.run_code()
            instance.stop_container()
            instance.delete_dir()
            return status_code
        except:
            instance.stop_container()
            instance.delete_dir()
            print("Unexpected error:", sys.exc_info()[0])
            raise
