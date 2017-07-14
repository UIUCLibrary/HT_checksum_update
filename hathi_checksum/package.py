import os


def get_dirs(root):
    for item in os.scandir(root):
        if item.is_dir():
            yield item.path

