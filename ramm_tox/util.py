import os
import errno
from unipath import Path

__all__ = ['init_paths', 'mkdirp']

def init_paths():
    """Set useful path variables and create output path."""
    global project_path, output_path, data_path
    project_path = Path(__file__).absolute().ancestor(2)
    output_path = project_path.child('output')
    # DATA_PATH must point to the external data directory.
    data_path = None
    if 'DATA_PATH' in os.environ:
        data_path = Path(os.environ['DATA_PATH'])
    if data_path is None or not data_path.exists():
        raise RuntimeError(
            "The environment variable 'DATA_PATH' must contain the path to the "
            "Dropbox folder containing the data files for this project."
            )
    mkdirp(output_path)
    
def mkdirp(path):
    try:
        os.makedirs(path)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise
