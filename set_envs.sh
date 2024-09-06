#!/bin/sh

# command: source set_envs.sh

export $(xargs <.env)
