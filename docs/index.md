# Tasks

The available values for `level_name` are as follows:

*   'architecture_comparison/fast_map_three_objs'
*   'num_generalization/fast_map_eight_objs'
*   'num_generalization/fast_map_five_objs'
*   'num_generalization/fast_map_three_objs'
*   'new_obj_generalization/fast_map_three_objs_global_five'
*   'new_obj_generalization/fast_map_three_objs_global_ten'
*   'new_obj_generalization/fast_map_three_objs_global_three'
*   'new_obj_generalization/fast_map_three_objs_global_twenty'
*   'new_obj_generalization/fast_map_heldout_test_objs'
*   'intrinsic_motivation/fast_map_three_objs_no_shaping_reward'
*   'fast_slow/fast_map_three_objs'
*   'fast_slow/fast_map_three_objs_bed_tray'
*   'fast_slow/fast_map_three_objs_bed_tray_putting_near'
*   'fast_slow/fast_map_three_objs_bed_tray_putting_on'
*   'fast_slow/slow_learn_three_objs_bed_tray_lifting'
*   'fast_slow/slow_learn_three_objs_bed_tray_putting_near'
*   'fast_slow/slow_learn_three_objs_bed_tray_putting_on'
*   'fast_slow/two_phase_slow_learn_three_objs_bed_tray_putting_near'
*   'fast_slow/two_phase_slow_learn_three_objs_bed_tray_putting_on'
*   'fast_slow/test_holdout_fast_map_three_objs_bed_tray_putting_on'
*   'with_distractors/eval_fast_map_three_episodes_three_objs_five_distractor',
*   'with_distractors/eval_fast_map_four_episodes_three_objs_one_distractor',
*   'with_distractors/eval_fast_map_three_objs_ten_distractor',
*   'with_distractors/eval_fast_map_three_objs_twenty_distractor',
*   'with_distractors/fast_map_three_objs_no_distractor',
*   'with_distractors/fast_map_three_objs_one_distractor',
*   'with_distractors/fast_map_three_objs_two_distractor',

# Experiments from "Grounded Language Learning: Fast and Slow"

These tasks correspond different experiments:

1.  architecture_comparison (Table 1, Section 4.0):

    *   Train on 'architecture_comparison/fast_map_three_objs'

2.  num_generalization (Figure 2, Section 4.1). E.g:

    *   Train on 'num_generalization/fast_map_three_objs'
    *   Test on 'num_generalization/fast_map_five_objs',
        'num_generalization/fast_map_eight_objs'

3.  new_obj_generalization (Figure 3, Section 4.1). E.g:

    *   Train on 'new_obj_generalization/fast_map_three_objs_global_ten'
    *   Test on 'new_obj_generalization/fast_map_heldout_test_objs'

4.  instrinsic_motivation (Figure 5, Section 4.2):

    *   Train on 'intrinsic_motivation/fast_map_three_objs_no_shaping_reward'

5.  fast_slow (Figure 6, Section 4.3). E.g. (unfamiliar objects, unfamiliar
    task):

    *   Train on 'fast_slow/slow_learn_three_objs_bed_tray_lifting',
        'fast_slow/slow_learn_three_objs_bed_tray_putting_near',
        'fast_slow/slow_learn_three_objs_bed_tray_putting_on',
        'fast_slow/fast_map_three_objs',
        'fast_slow/fast_map_three_objs_bed_tray'
    *   Test on 'fast_slow/test_holdout_fast_map_three_objs_bed_tray_putting_on'

The sections refer to the version of the paper hosted on arXiv on 1 November
2020 ([arxiv](https://arxiv.org/pdf/2009.01719.pdf)). Note that we do not
release the experiments involving ShapeNet assets (Figure 4, Section 4.1) for
copyright reasons.

# Experiments from "Towards mental time travel: a hierarchical memory for RL..."

The tasks prefixed with `with_distractors` are the rapid-word-learning tasks
from Figure 5, Section 3.3:

1.  Length generalization (Fig. 5c):

    *   Train on 'with_distractors/fast_map_three_objs_no_distractor'
        'with_distractors/fast_map_three_objs_one_distractor'
        'with_distractors/fast_map_three_objs_two_distractor'
    *   Test on 'with_distractors/eval_fast_map_three_objs_twenty_distractor'

2.  Generalization to multi-episode evaluation (Fig. 5d-e) with:

    *   Train on same as previous:
        'with_distractors/fast_map_three_objs_no_distractor'
        'with_distractors/fast_map_three_objs_one_distractor'
        'with_distractors/fast_map_three_objs_two_distractor'
    *   Test on
        'with_distractors/eval_fast_map_four_episodes_three_objs_one_distractor'
        'with_distractors/eval_fast_map_three_episodes_three_objs_five_distractor'

The section and figure numbers refer to the paper version
([arXiv](https://arxiv.org/abs/2105.14039)) that was posted on 28th May, 2021.

# Actions

The environment provides the following actions:

*   `STRAFE_LEFT_RIGHT`
*   `MOVE_BACK_FORWARD`
*   `LOOK_LEFT_RIGHT`
*   `LOOK_DOWN_UP`
*   `HAND_ROTATE_AROUND_RIGHT`
*   `HAND_ROTATE_AROUND_UP`
*   `HAND_ROTATE_AROUND_FORWARD`
*   `HAND_PUSH_PULL`
*   `HAND_GRIP`

Each action is a `double` scalar, with an inclusive range of `[-1.0, 1.0]`
except for HAND_GRIP, which is a binary action taking values `0` or `1`. It is
not compulsory to send a value for each action every step, but note that actions
are "sticky", meaning an action's value will only change when a new value is
provided. For example:

```python
env = dm_fast_mapping.load_from_docker(settings)
env.reset()
env.step({'STRAFE_LEFT_RIGHT': -1.0}) # Result: strafe Left.
env.step({'MOVE_BACK_FORWARD': 1.0}) # Result: strafe left & move backward.

env.step({'STRAFE_LEFT_RIGHT': 0.0,
          'MOVE_BACK_FORWARD': 0.0}) # Result: stationary.
```

Note that when using the provided script `human_agent.py` to try the tasks, only
the `STRAFE_LEFT_RIGHT` (keys `a`, `d`), `MOVE_BACK_FORWARD` (`s`, `w`),
`LOOK_LEFT_RIGHT` (`left_arrow`, `right_arrow`), `LOOK_DOWN_UP` (`down_arrow`,
`up_arrow`) and `HAND_GRIP`(`spacebar`) are available.

# Observations

For the 8 Unity-based tasks, the environment provides the following
observations:

*   `RGB_INTERLEAVED`: First person RGB camera observation. The `width` and
    `height` can be adjusted through the `EnvironmentSettings`, but the
    observation will always have a fixed 4:3 aspect ratio.
*   `TEXT`: A string indicating the instructions or language information
    provided by the environment.

# Configurable environment settings

Required attributes:

*   `seed`: Seed to initialize the environment's RNG.
*   `level_name`: Name of the level to load.

Optional attributes:

*   `width`: Width (in pixels) of the desired RGB observation; defaults to 96.
*   `height`: Height (in pixels) of the desired RGB observation; defaults to 72.
*   `episode_length_seconds`: Maximum episode length (in seconds); defaults
    to 120.
*   `num_action_repeats`: Number of times to step the environment with the
    provided action in calls to `step()`.
