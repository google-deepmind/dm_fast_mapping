# Copyright 2019 DeepMind Technologies Limited. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or  implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Python utilities for running dm_fast_mapping."""

from dm_fast_mapping import _load_environment
from dm_fast_mapping._version import __version__

EnvironmentSettings = _load_environment.EnvironmentSettings

FAST_MAPPING_TASK_LEVEL_NAMES = _load_environment.FAST_MAPPING_TASK_LEVEL_NAMES

load_from_disk = _load_environment.load_from_disk
load_from_docker = _load_environment.load_from_docker
