# Lint as: python3
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
"""Python utility functions for loading DeepMind Fast Language Learning Tasks."""

import codecs
import collections
import json
import os
import re
import subprocess
import time
import typing

from absl import logging
import dm_env
import docker
import grpc
import numpy as np
import portpicker

from dm_env_rpc.v1 import connection as dm_env_rpc_connection
from dm_env_rpc.v1 import dm_env_adaptor
from dm_env_rpc.v1 import dm_env_rpc_pb2
from dm_env_rpc.v1 import error
from dm_env_rpc.v1 import tensor_utils

# Maximum number of times to attempt gRPC connection.
_MAX_CONNECTION_ATTEMPTS = 10

# Port to expect the docker environment to internally listen on.
_DOCKER_INTERNAL_GRPC_PORT = 10000

_DEFAULT_DOCKER_IMAGE_NAME = 'gcr.io/deepmind-environments/dm_fast_mapping:v1.1.0'

_FAST_MAPPING_TASK_OBSERVATIONS = ['RGB_INTERLEAVED', 'TEXT']

FAST_MAPPING_TASK_LEVEL_NAMES = frozenset((
    'architecture_comparison/fast_map_three_objs',
    'fast_slow/fast_map_three_objs_bed_tray',
    'fast_slow/fast_map_three_objs_bed_tray_putting_near',
    'fast_slow/fast_map_three_objs_bed_tray_putting_on',
    'fast_slow/fast_map_three_objs',
    'fast_slow/slow_learn_three_objs_bed_tray_lifting',
    'fast_slow/slow_learn_three_objs_bed_tray_putting_near',
    'fast_slow/slow_learn_three_objs_bed_tray_putting_on',
    'fast_slow/test_holdout_fast_map_three_objs_bed_tray_putting_on',
    'fast_slow/two_phase_slow_learn_three_objs_bed_tray_putting_near',
    'fast_slow/two_phase_slow_learn_three_objs_bed_tray_putting_on',
    'intrinsic_motivation/fast_map_three_objs_no_shaping_reward',
    'new_obj_generalization/fast_map_heldout_test_objs',
    'new_obj_generalization/fast_map_three_objs_global_five',
    'new_obj_generalization/fast_map_three_objs_global_ten',
    'new_obj_generalization/fast_map_three_objs_global_three',
    'new_obj_generalization/fast_map_three_objs_global_twenty',
    'num_generalization/fast_map_eight_objs',
    'num_generalization/fast_map_five_objs',
    'num_generalization/fast_map_three_objs',
    'with_distractors/eval_fast_map_two_episodes_three_objs_five_distractor',
    'with_distractors/eval_fast_map_three_episodes_three_objs_five_distractor',
    'with_distractors/eval_fast_map_four_episodes_three_objs_no_distractor',
    'with_distractors/eval_fast_map_four_episodes_three_objs_one_distractor',
    'with_distractors/eval_fast_map_three_objs_ten_distractor',
    'with_distractors/eval_fast_map_three_objs_twenty_distractor',
    'with_distractors/fast_map_three_objs_no_distractor',
    'with_distractors/fast_map_three_objs_one_distractor',
    'with_distractors/fast_map_three_objs_two_distractor',
))

_ConnectionDetails = collections.namedtuple('_ConnectionDetails',
                                            ['channel', 'connection', 'specs'])


class _FastMappingTasksEnv(dm_env_adaptor.DmEnvAdaptor):
  """An implementation of dm_env_rpc.DmEnvAdaptor for Fast Language Learning tasks."""

  def __init__(self, connection_details, requested_observations,
               num_action_repeats):
    super(_FastMappingTasksEnv,
          self).__init__(connection_details.connection,
                         connection_details.specs, requested_observations)
    self._channel = connection_details.channel
    self._num_action_repeats = num_action_repeats

  def close(self):
    super(_FastMappingTasksEnv, self).close()
    self._channel.close()

  def step(self, action):
    """Implementation of dm_env.step that supports repeated actions."""

    timestep = None
    discount = None
    reward = None
    for _ in range(self._num_action_repeats):
      next_timestep = super(_FastMappingTasksEnv, self).step(action)

      # Accumulate reward per timestep.
      if next_timestep.reward is not None:
        reward = (reward or 0.) + next_timestep.reward

      # Calculate the product for discount.
      if next_timestep.discount is not None:
        discount = discount if discount else []
        discount.append(next_timestep.discount)

      timestep = dm_env.TimeStep(next_timestep.step_type, reward,
                                 # Note: np.product(None) returns None.
                                 np.product(discount),
                                 next_timestep.observation)

      if timestep.last():
        return timestep

    return timestep


class _FastMappingTasksContainerEnv(_FastMappingTasksEnv):
  """An implementation of _FastMappingTasksEnv.

    Ensures that the provided Docker container is closed on exit.
  """

  def __init__(self, connection_details, requested_observations,
               num_action_repeats, container):
    super(_FastMappingTasksContainerEnv,
          self).__init__(connection_details, requested_observations,
                         num_action_repeats)
    self._container = container

  def close(self):
    super(_FastMappingTasksContainerEnv, self).close()
    try:
      self._container.kill()
    except docker.errors.NotFound:
      pass  # Ignore, container has already been closed.


class _FastMappingTasksProcessEnv(_FastMappingTasksEnv):
  """An implementation of _FastMappingTasksEnv.

    Ensure that the provided running process is closed on exit.
  """

  def __init__(self, connection_details, requested_observations,
               num_action_repeats, process):
    super(_FastMappingTasksProcessEnv,
          self).__init__(connection_details, requested_observations,
                         num_action_repeats)
    self._process = process

  def close(self):
    super(_FastMappingTasksProcessEnv, self).close()
    self._process.terminate()
    self._process.wait()


def _check_grpc_channel_ready(channel):
  """Helper function to check the gRPC channel is ready N times."""
  for _ in range(_MAX_CONNECTION_ATTEMPTS - 1):
    try:
      return grpc.channel_ready_future(channel).result(timeout=1)
    except grpc.FutureTimeoutError:
      pass
  return grpc.channel_ready_future(channel).result(timeout=1)


def _can_send_message(connection):
  """Returns if `connection` is healthy and able to process requests."""
  try:
    # This should return a response with an error unless the server isn't yet
    # receiving requests.
    connection.send(dm_env_rpc_pb2.StepRequest())
  except error.DmEnvRpcError:
    return True
  except grpc.RpcError:
    return False


def _create_channel_and_connection(port):
  """Returns a tuple of `(channel, connection)`."""
  for _ in range(_MAX_CONNECTION_ATTEMPTS):
    channel = grpc.secure_channel('localhost:{}'.format(port),
                                  grpc.local_channel_credentials())
    _check_grpc_channel_ready(channel)
    connection = dm_env_rpc_connection.Connection(channel)
    if _can_send_message(connection):
      break
    else:
      # A gRPC server running within Docker sometimes reports that the channel
      # is ready but transitively returns an error (status code 14) on first
      # use.  Giving the server some time to breath and retrying often fixes the
      # problem.
      connection.close()
      channel.close()
      time.sleep(1.0)

  return channel, connection


def _parse_exception_message(message):
  """Returns a human-readable version of a dm_env_rpc json error message."""
  try:
    match = re.match(r'^message\:\ \"(.*)\"$', message)
    json_data = codecs.decode(match.group(1), 'unicode-escape')
    parsed_json_data = json.loads(json_data)
    return ValueError(json.dumps(parsed_json_data, indent=4))
  except:  # pylint: disable=bare-except
    return message


def _wrap_send(send):
  """Wraps `send` in order to reformat exceptions."""
  try:
    return send()
  except ValueError as e:
    e.args = [_parse_exception_message(e.args[0])]
    raise


def _connect_to_environment(port, settings):
  """Helper function for connecting to a running dm_fast_mapping environment."""
  if settings.level_name not in FAST_MAPPING_TASK_LEVEL_NAMES:
    raise ValueError(
        'Level named "{}" is not a valid dm_fast_mapping level.'.format(
            settings.level_name))
  channel, connection = _create_channel_and_connection(port)
  original_send = connection.send
  connection.send = lambda request: _wrap_send(lambda: original_send(request))
  world_name = connection.send(
      dm_env_rpc_pb2.CreateWorldRequest(
          settings={
              'seed': tensor_utils.pack_tensor(settings.seed),
              'episodeId': tensor_utils.pack_tensor(0),
              'levelName': tensor_utils.pack_tensor(settings.level_name),
          })).world_name
  join_world_settings = {
      'width':
          tensor_utils.pack_tensor(settings.width),
      'height':
          tensor_utils.pack_tensor(settings.height),
      'EpisodeLengthSeconds':
          tensor_utils.pack_tensor(settings.episode_length_seconds),
      'ShowReachabilityHUD': tensor_utils.pack_tensor(False),
  }
  specs = connection.send(
      dm_env_rpc_pb2.JoinWorldRequest(
          world_name=world_name, settings=join_world_settings)).specs
  return _ConnectionDetails(channel=channel, connection=connection, specs=specs)


class EnvironmentSettings(typing.NamedTuple):
  """Collection of settings used to start a specific Fast Language Learning task.

    Required attributes:
      seed: Seed to initialize the environment's RNG.
      level_name: Name of the level to load.
    Optional attributes:
      width: Width (in pixels) of the desired RGB observation; defaults to 96.
      height: Height (in pixels) of the desired RGB observation; defaults to 72.
      episode_length_seconds: Maximum episode length (in seconds); defaults to
        120.
      num_action_repeats: Number of times to step the environment with the
        provided action in calls to `step()`.
  """
  seed: int
  level_name: str
  width: int = 96
  height: int = 72
  episode_length_seconds: float = 120.0
  num_action_repeats: int = 1


def _validate_environment_settings(settings):
  """Helper function to validate the provided environment settings."""
  if settings.episode_length_seconds <= 0.0:
    raise ValueError('episode_length_seconds must have a positive value.')
  if settings.num_action_repeats <= 0:
    raise ValueError('num_action_repeats must have a positive value.')
  if settings.width <= 0 or settings.height <= 0:
    raise ValueError('width and height must have a positive value.')
  if ('with_distractors/' in settings.level_name and
      settings.episode_length_seconds != 450.0):
    raise ValueError(
        'episode_length_seconds must be 450.0 for with_distractors/ levels.')


def load_from_disk(path, settings):
  """Load Fast Language Learning Tasks from disk.

  Args:
    path: Directory containing dm_fast_mapping environment.
    settings: EnvironmentSettings required to start the environment.

  Returns:
    An implementation of dm_env.Environment.

  Raises:
    RuntimeError: If unable to start environment process.
  """
  _validate_environment_settings(settings)

  executable_path = os.path.join(path, 'Linux64Player')
  libosmesa_path = os.path.join(path, 'external_libosmesa_llvmpipe.so')
  if not os.path.exists(executable_path) or not os.path.exists(libosmesa_path):
    raise RuntimeError(
        'Cannot find dm_fast_mapping executable or dependent files at path: {}'
        .format(path))

  port = portpicker.pick_unused_port()

  process_flags = [
      executable_path,
      # Unity command-line flags.
      '-logfile',
      '-batchmode',
      '-noaudio',
      # Other command-line flags.
      '--logtostderr',
      '--server_type=GRPC',
      '--uri_address=[::]:{}'.format(port),
  ]

  os.environ.update({
      'UNITY_RENDERER': 'software',
      'UNITY_OSMESA_PATH': libosmesa_path,
  })

  process = subprocess.Popen(
      process_flags, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  if process.poll() is not None:
    raise RuntimeError('Failed to start dm_fast_mapping process correctly.')

  return _FastMappingTasksProcessEnv(
      _connect_to_environment(port, settings), _FAST_MAPPING_TASK_OBSERVATIONS,
      settings.num_action_repeats, process)


def load_from_docker(settings, name=None):
  """Load Fast Language Learning Tasks from docker container.

  Args:
    settings: EnvironmentSettings required to start the environment.
    name: Optional name of Docker image that contains the dm_fast_mapping
      environment. If left unset, uses the dm_fast_mapping default name.

  Returns:
    An implementation of dm_env.Environment
  """
  _validate_environment_settings(settings)

  name = name or _DEFAULT_DOCKER_IMAGE_NAME
  client = docker.from_env()

  port = portpicker.pick_unused_port()

  try:
    client.images.get(name)
  except docker.errors.ImageNotFound:
    logging.info('Downloading docker image "%s"...', name)
    client.images.pull(name)
    logging.info('Download finished.')

  container = client.containers.run(
      name,
      auto_remove=True,
      detach=True,
      ports={_DOCKER_INTERNAL_GRPC_PORT: port})

  return _FastMappingTasksContainerEnv(
      _connect_to_environment(port, settings), _FAST_MAPPING_TASK_OBSERVATIONS,
      settings.num_action_repeats, container)
