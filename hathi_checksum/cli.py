import argparse
import itertools
import logging
import os
import sys
import typing

import hathi_checksum
from hathi_checksum import utils
from hathi_checksum.checksum_report import get_outdated_files
from hathi_checksum.update_report import update_checksum


# # PATH = r"D:\tests\uiu_uiuc-loc_20170713_uiuc_DigitalRareBooksCollections_095"
# PATH = r"D:\hathigood"


def create_message_list(files: typing.List[tuple])->str:
    # sorter_function = lambda x: x[0]
    def sorter_function(x):
        return x[0]

    sorted_files = sorted(files, key=sorter_function)
    grouped = itertools.groupby(sorted_files, key=sorter_function)
    group_message = []
    for g, items in grouped:
        changed_files = ", ".join([os.path.basename(filename) for _, filename in items])
        group_message.append("{}:\n[{}]".format(g, changed_files))

    return "\n".join(group_message)


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--version',
        action='version',
        version=hathi_checksum.__version__)
    parser.add_argument("path", help="Path to the Hathi Packages")
    debug_group = parser.add_argument_group("Debug")
    debug_group.add_argument(
        '--debug',
        action="store_true",
        help="Run script in debug mode")
    debug_group.add_argument("--log-debug", dest="log_debug", help="Save debug information to a file")
    return parser


# def setup_logger(debug_mode, log_file):
#     print(__package__)
def setup_logger(logger: logging.Logger, debug_mode, log_file):
    # logger = logging.getLogger(__package__)
    logger.setLevel(logging.DEBUG)

    debug_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    std_handler = logging.StreamHandler(sys.stdout)
    if log_file == True:
        file_handler = logging.FileHandler(filename=log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(debug_formatter)
        logger.addHandler(file_handler)

    if debug_mode:
        print("Debug mode")
        std_handler.setLevel(logging.DEBUG)
        std_handler.setFormatter(debug_formatter)
    else:
        std_handler.setLevel(logging.INFO)
        logger.setLevel(logging.INFO)

    # std_handler.setFormatter(debug_formatter)

    logger.addHandler(std_handler)


def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    parser = get_parser()
    args = parser.parse_args()

    setup_logger(logging.root, debug_mode=args.debug, log_file=args.log_debug)
    out_of_date_files = get_outdated_files(args.path)

    if not out_of_date_files:
        logger.info("All files are up to date")
        sys.exit(0)

    logger.info("Found the following files out of date checksums:")
    for source, outdated_file in out_of_date_files:
        logger.info(outdated_file)

    # Ask the user wants to update the following files
    try:
        if not utils.ask(
                intro="The following files have been changed.\n{}".format(create_message_list(out_of_date_files)),
                question="Do you wish to update the checksum.md5 files?"):
            sys.exit()

    except utils.CallAbort:
        logger.info("Aborted by user.")
        sys.exit(0)

    # if the users says, "yes", update the checksum files
    logger.info("Updating checksums")
    for checksum_file, filename in out_of_date_files:
        update_checksum(checksum_file=checksum_file, target=filename)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "--pytest":
        import pytest  # type: ignore

        sys.exit(pytest.main(sys.argv[2:]))
    else:
        main()
