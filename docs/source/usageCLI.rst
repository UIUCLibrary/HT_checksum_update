This is a command line script so you will need a terminal window open to use it.

Update the checksum.md5 file
----------------------------
To update the checksum.md5 files, type "udhtchecksum" followed by path to the package. If the path has spaces in it, you must
surround the path by quotes.


    :command:`udhtchecksum "Y:\\DCC Unprocessed Files\\20170523_CavagnaCollectionRBML_rj"`




The Help Screen
---------------
This documentation should be up to date. However, you can always type :command:`udhtchecksum -h` or
:command:`udhtchecksum --help` into a command prompt to display the script usage instructions along with any
additional the options.


:command:`udhtchecksum -h`

.. code-block:: console

    C:\Users\hborcher.UOFI> udhtchecksum -h

    usage: __main__.py [-h] [--version] [--debug] [--log-debug LOG_DEBUG] path

    positional arguments:
      path                  Path to the Hathi Packages

    optional arguments:
      -h, --help            show this help message and exit
      --version             show program's version number and exit

    Debug:
      --debug               Run script in debug mode
      --log-debug LOG_DEBUG
                            Save debug information to a file





It's that simple!