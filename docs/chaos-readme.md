# Chaos Testing for Home Lab

This document describes the **Chaos Testing script** used in the
`home_lab` environment.

The goal of chaos testing is to intentionally introduce failures into
the infrastructure in order to observe system behavior and improve
resilience.

The script performs **random disruptive actions on Docker containers**
while providing a **kill switch mechanism** to safely stop the
experiment.

------------------------------------------------------------------------

# Purpose

Chaos testing helps simulate real-world failures such as:

-   container crashes
-   service restarts
-   resource starvation
-   network disruptions

These tests help verify:

-   service recovery behavior
-   monitoring alerts (Uptime Kuma)
-   container restart policies
-   infrastructure stability

------------------------------------------------------------------------

# Script Location

    scripts/chaos.sh

Kill switch file:

    scripts/chaos.stop

------------------------------------------------------------------------

# How It Works

The chaos script runs in a loop and randomly performs disruptive actions
on running containers.

Possible actions include:

-   restarting a container
-   killing a container
-   limiting container CPU
-   disconnecting a container from the Docker network

Each action is performed at a fixed interval (default: 60 seconds).

The script intentionally avoids disrupting **critical infrastructure
services**.

------------------------------------------------------------------------

# Protected Containers

Certain containers are excluded from chaos actions.

Example protected services:

    npm
    portainer

These services are considered **core infrastructure components** and
should remain stable during experiments.

------------------------------------------------------------------------

# Kill Switch

The chaos script continuously checks for the presence of a kill switch
file.

If the following file exists:

    scripts/chaos.stop

the script will immediately terminate.

This ensures chaos testing can be stopped instantly if the environment
becomes unstable.

------------------------------------------------------------------------

# Starting Chaos Testing

Run the script from the repository root:

    bash scripts/chaos.sh

Once started, the script will periodically perform random disruption
events.

Example log output:

    [CHAOS] Restarting uptime-kuma
    [CHAOS] Killing adminer
    [CHAOS] CPU limiting plex

------------------------------------------------------------------------

# Stopping Chaos Testing

To immediately stop the chaos experiment, create the kill switch file:

    touch scripts/chaos.stop

The script will detect this file and exit.

------------------------------------------------------------------------

# Restoring the Environment

After chaos testing, the environment can be restored by restarting the
stack:

    docker compose up -d

This ensures all services are running and connected to the correct
Docker networks again.

------------------------------------------------------------------------

# Best Practices

When running chaos experiments:

-   Avoid disrupting critical infrastructure containers
-   Monitor the environment using **Uptime Kuma**
-   Run experiments during non-critical periods
-   Always keep the **kill switch available**

Chaos testing should be used as a learning tool to better understand how
services behave during failures.

------------------------------------------------------------------------

# Summary

Chaos testing provides a safe way to experiment with infrastructure
failures and observe recovery behavior.

Key features of this implementation:

-   random container disruption
-   protected core services
-   simple kill switch mechanism
-   easy environment recovery

This helps improve confidence in the stability and resilience of the
`home_lab` infrastructure.
