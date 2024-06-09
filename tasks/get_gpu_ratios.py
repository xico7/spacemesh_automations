import os
import re
import subprocess
import time
from utils import run_shell_command, CommandFailed
import logging
import logs


LOG = logging.getLogger(logs.LOG_BASE_NAME + '.' + __name__)


def get_gpu_ratios(args):
    os.chdir(args["postcli_executable_dir"])

    providers = [provider_id for provider_id in re.findall(
        "ID: \(uint32\) (.*),", run_shell_command('./postcli -printProviders')) if provider_id != "4294967295"]

    providers_file_size = {}

    if providers:
        for provider in providers:
            try:
                run_shell_command(f"rm {args['dir_path_to_write_test_file']}/postdata_0.bin")
            except CommandFailed:
                pass
            postcli_args = ['./postcli', '-provider', provider, '-commitmentAtxId', "00045b854f2baef1de75b753270e68b3b0dcee219167b84c6b7f302ca234ebe3", '-labelsPerUnit',
                            '4294967296', '-maxFileSize', '2147483648', '-numUnits', "4",
                            '-datadir', args['dir_path_to_write_test_file']]
            postcli_process = subprocess.Popen(postcli_args)

            time.sleep(20)
            postcli_process.terminate()

            providers_file_size[provider] = int(run_shell_command(
                f"du -h {args['dir_path_to_write_test_file']}/postdata_0.bin").split('\t')[0].strip("M"))
            run_shell_command(f"rm {args['dir_path_to_write_test_file']}/postdata_0.bin")
    else:
        LOG.info("No providers detected.")

    values_sum = sum([v for v in providers_file_size.values()])

    with open(args['dir_path_to_write_ratios'], 'w') as csv_ratios_f:
        csv_ratios_f.write("provider_id,percentage_of_files_to_get\n")

        for provider, written_mb in providers_file_size.items():
            csv_ratios_f.write(f"{provider},{written_mb / values_sum}\n")

