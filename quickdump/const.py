DEFAULT_DUMP_LABEL = "quickdump"
DEFAULT_SERVER_DUMP_LABEL = "server_quickdump"
DEFAULT_DUMP_DIRNAME: str = ".quickdump"


DUMP_FILE_EXTENSION = "qd"
COMPRESSED_DUMP_FILE_EXTENSION = "cqd"


class Suffix:
    Year = Y = y = "%Y"
    Month = m = "%Y_%m"
    Day = d = "%Y_%m_%d"
    Hour = H = "%Y_%m_%d__%H"
    Minute = M = "%Y_%m_%d__%H_%M"
    NoSuffix = N = n = ""
