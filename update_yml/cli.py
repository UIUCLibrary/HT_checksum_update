import hashlib
import os

import sys

from .package import get_dirs
import logging

# PATH = r"D:\test\uiu_uiuc-loc_20170713_uiuc_DigitalRareBooksCollections_095"
PATH = r"D:\hathigood"


class ValidationError(Exception):
    pass


class InvalidChecksum(ValidationError):
    pass


def parse_checksum(line):
    md5_hash, raw_filename = line.strip().split(" ")
    if len(md5_hash) != 32:
        raise InvalidChecksum("Invalid Checksum")
    assert raw_filename[0] == "*"
    filename = raw_filename[1:]
    return md5_hash, filename


def extracts_checksums(report):
    with open(report, "r") as f:
        for line in f:
            md5, filename = parse_checksum(line)
            yield md5, filename

def calculate_md5(filename, chunk_size=8192):
    md5 = hashlib.md5()

    with open(filename, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            md5.update(data)
        return md5.hexdigest()

def find_failing_checksums(path, report):
    """
        validate that the checksums in the *.fil file match

    Args:
        path:
        report:

    Returns:

    """

    logger = logging.getLogger(__name__)
    # report_builder = result.SummaryDirector(source=path)

    for report_md5_hash, filename in extracts_checksums(report):
        logger.debug("Calculating the md5 checksum hash for {}".format(filename))
        file_path = os.path.join(path, filename)
        file_md5_hash = calculate_md5(filename=file_path)
        if file_md5_hash != report_md5_hash:
            yield file_path


def find_checksum_mismatch(path):
    logger = logging.getLogger(__name__)
    checksum_report = os.path.join(path, "checksum.md5")
    logger.info("Validating checksums in {}".format(checksum_report))

    for failing_checksum in find_failing_checksums(path=path, report=checksum_report):
        yield checksum_report, failing_checksum


def main():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    out_of_date_files = get_outdated_files()

    if not out_of_date_files:
        logger.info("All files are up to date")
        sys.exit(0)

    logger.info("Found the following files out of date checksums:")
    for source, outdated_file in out_of_date_files:
        logger.info(outdated_file)

    # TODO: Ask the user wants to update the following files

    # TODO: if the users says, "yes", update the checksum files

    # TODO: calculate the new value

    # TODO: open the checksum.md5 file to the point of the invalid checksum

    # TODO: overwrite the checksum value with the new one


def get_outdated_files():
    out_of_date_files = []
    for package in get_dirs(PATH):
        logging.info(package)
        for file in find_checksum_mismatch(package):
            out_of_date_files.append(file)

    return out_of_date_files


if __name__ == '__main__':
    main()