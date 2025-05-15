# from click.testing import CliRunner
import yaml
import pytest
import tempfile
import shutil
import types
import os
import random
import string
import subprocess
from unittest.mock import Mock
from core.context import LoopyContext
from core.initializer import Initializer
from core.env import EnvManager
from core.config_loader import ConfigLoader

timeout = 120


def generate_random_name(length=5):
    return "".join(random.choices(string.ascii_lowercase, k=length))
