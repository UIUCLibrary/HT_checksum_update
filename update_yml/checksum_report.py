import logging
import os

from update_yml.package import get_dirs
from update_yml.utils import InvalidChecksum, calculate_md5


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
    new_checksum_report = os.path.join(path, "checksum.md5")
    logger.info("Validating checksums in {}".format(new_checksum_report))

    for failing_checksum in find_failing_checksums(path=path, report=new_checksum_report):
        yield new_checksum_report, failing_checksum


def get_outdated_files(path):
    out_of_date_files = []
    for package in get_dirs(path):
        for file in find_checksum_mismatch(package):
            out_of_date_files.append(file)

    return out_of_date_files
