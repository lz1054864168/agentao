"""Main entry point for ChatAgent."""

import warnings
warnings.filterwarnings("ignore", message="urllib3.*or chardet.*doesn't match")

from chatagent.cli import entrypoint

if __name__ == "__main__":
    entrypoint()
