## train two policy at same time for env
import argparse
import gym
import os

import ray
from ray import tune
from ray.rllib.policy.policy import PolicySpec
from env import HydroRefuelSys

trial = 1

def get_cli_args():
    """Create CLI parser and return parsed arguments"""
    parser = argparse.ArgumentParser()
    # multi-agent args
    parser.add_argument("--num-HRS", type=int, default=2)

    # general args
    parser.add_argument(
        "--run", type=str, default="PPO", help="The RLlib-registered algorithm to use."
    )
    parser.add_argument(
        "--framework",
        choices=["tf", "tf2", "tfe", "torch"],
        default="tf",
        help="The DL framework specifier.",
    )
    parser.add_argument("--eager-tracing", action="store_true")
    parser.add_argument(
        "--stop-iters", type=int, default=10000000, help="Number of iterations to train."
    )
    parser.add_argument(
        "--local-mode",
        action="store_true",
        help="Init Ray in local mode for easier debugging.",
    )

    args = parser.parse_args()
    print(f"Running with following CLI args: {args}")
    return args


if __name__ == "__main__":
    args = get_cli_args()

    ray.init(num_cpus=4, local_mode=args.local_mode)

    stop = {
        "training_iteration": args.stop_iters,
    }

    HDS_config = {
        "lr": 7.028896641361652e-05,
        "train_batch_size": 1036.9835473579633
    }
    HRS0_config = {
        "lr": 1.938299859903986e-05,
        "train_batch_size": 965.7674677941495
    }
    HRS1_config = {
        "lr": 2.230682720333346e-05,
        "train_batch_size": 2689.2038627775137
    }

    def policy_mapping_fn(agent_id, episdoe, worker, **kwargs):
        if agent_id.startswith("HRS"):
            policy_id = agent_id[:4]
            return policy_id
        else:
            return agent_id

    tune.run(
        args.run,
        local_dir=f'~/CASESTUDY_results/casestudy/trial{trial}',
        stop=stop,
        config={
            "env": HydroRefuelSys,
            "env_config": {
              "num_HRS": args.num_HRS
            },
            "disable_env_checking": True,
            "num_workers": 1,
            # "lr": 1e-6,
            "multiagent": {
                # Use a simple set of policy IDs. Spaces for the individual policies
                # will be inferred automatically using reverse lookup via the
                # `policy_mapping_fn` and the env provided spaces for the different
                # agents. Alternatively, you could use:
                # policies: {main0: PolicySpec(...), main1: PolicySpec}
                # "policies": policies,
                "policies": {
                    "HDS": PolicySpec(observation_space=gym.spaces.Box(0, 100000000, shape=(4, 3)),
                                      action_space=gym.spaces.Box(0, 1, shape=(9,)), config=HDS_config),
                    "HRS0": PolicySpec(observation_space=gym.spaces.Box(0, 100000000, shape=(8,)),
                                       action_space=gym.spaces.Box(0, 1, shape=(5,)), config=HRS0_config),
                    "HRS1": PolicySpec(observation_space=gym.spaces.Box(0, 10000, shape=(8,)),
                                       action_space=gym.spaces.Box(0, 1, shape=(3,)), config=HRS1_config)
                },
                "policy_mapping_fn": policy_mapping_fn,
            },
            "framework": args.framework,
            "eager_tracing": args.eager_tracing,
        },
    )
