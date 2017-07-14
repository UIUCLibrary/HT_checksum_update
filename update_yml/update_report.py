import logging
import os

from update_yml import checksum_report
from update_yml.utils import calculate_md5


def update_hash_value(checksum_file, target, new_hash):
    with open(checksum_file, "r+") as f:
        starting_point = f.tell()
        line = f.readline()
        while line:
            md5, filename = checksum_report.parse_checksum(line)

            # open the checksum.md5 file to the point of the invalid checksum
            if filename == target:
                f.seek(starting_point)
                newline = "{} *{}\n".format(new_hash, target)

                # In order to make sure that the new data isn't corrupted, the lines should be the same size
                assert len(newline) == len(line)

                # overwrite the checksum value with the new one
                f.write(newline)
                return
            starting_point = f.tell()
            line = f.readline()
    raise ValueError("No entry found for {}".format(target))


def update_checksum(checksum_file, target):
    # calculate the new value
    logger = logging.getLogger(__name__)
    logger.debug("Calculating md5 checksum for {}".format(target))
    result = calculate_md5(target)
    logger.debug("Updating {} so that the value for is {}".format(checksum_file, target, result))
    update_hash_value(checksum_file, os.path.basename(target), new_hash=result)
    logger.info("Updated the checksum value for {} in {}".format(os.path.basename(target), checksum_file))
