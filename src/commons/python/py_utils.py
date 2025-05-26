#!/usr/bin/env python
import sys
import os
import subprocess
import json
import time

# Define colors using ANSI escape codes
colors = {
    "dark_red": "\033[38;5;124m",
    "red": "\033[38;5;160m",
    "light_red": "\033[38;5;196m",
    "dark_green": "\033[38;5;154m",
    "green": "\033[38;5;155m",
    "light_green": "\033[38;5;156m",
    "dark_yellow": "\033[38;5;226m",
    "yellow": "\033[38;5;227m",
    "light_yellow": "\033[38;5;228m",
    "dark_purple": "\033[38;5;91m",
    "purple": "\033[38;5;92m",
    "light_purple": "\033[38;5;93m",
    "dark_sky": "\033[38;5;6m",
    "sky": "\033[38;5;12m",
    "light_sky": "\033[38;5;51m",
    "dark_blue": "\033[38;5;27m",
    "blue": "\033[38;5;33m",
    "light_blue": "\033[38;5;39m",
    "clear": "\033[0m",
    "color_reset": "\033[0m",
}

# Set log level colors
log_levels = {
    "info": colors["sky"],
    "debug": colors["light_sky"],
    "pending": colors["blue"],
    "warn": colors["dark_red"],
    "error": colors["red"],
    "fail": colors["light_red"],
    "die": colors["light_red"],
    "success": colors["light_green"],
    "pass": colors["green"],
}

# Log functions with different severity levels


def die(message):
    print(f"{log_levels['die']}[FATAL]: {message}{colors['color_reset']}")
    sys.exit(1)


def debug(message, show_debug_log=True):
    if show_debug_log:
        print(f"{log_levels['debug']}[DEBUG] {message}{colors['color_reset']}")


def info(message):
    print(f"{log_levels['info']}[INFO] {message}{colors['color_reset']}")


def warn(message):
    print(f"{log_levels['warn']}[WARN] {message}{colors['color_reset']}")


def error(message):
    print(f"{log_levels['error']}[ERROR] {message}{colors['color_reset']}")


def fail(message):
    print(f"{log_levels['fail']}[FAIL] {message}{colors['color_reset']}")


def success(message):
    print(f"{log_levels['success']}[SUCCESS] {message}{colors['color_reset']}")


def pass_message(message):
    print(f"{log_levels['pass']}[PASS] {message}{colors['color_reset']}")


def pending(message):
    print(f"{log_levels['pending']}[PENDING] {message}{colors['color_reset']}")


def is_positive(input_string):
    # Check if the input is a boolean and convert to string
    if isinstance(input_string, bool):
        input_string = str(input_string).lower()

    if not input_string:
        raise ValueError("Input cannot be empty or None.")

    # Convert to lowercase to handle case insensitivity
    input_string_lower = input_string.lower()

    # Return 0 when input is "yes", "true", or True
    if input_string_lower in ["yes", "true", "0"] or input_string == True:
        return 0
    # Return 1 when input is "no", "false", or False
    elif input_string_lower in ["no", "false", "1"] or input_string == False:
        return 1
    else:
        # Return error if the input is something else
        raise ValueError(
            "Invalid input. Please provide 'yes', 'no', 'true', 'false', or a boolean."
        )


def stop_when_error_happened(
    result, index_role_name, report_file, input_should_stop=False
):
    if result != "0":
        warn(f"There are some errors in the role({index_role_name})")
        should_stop = is_positive(os.environ["STOP_WHEN_FAILED"])

        if input_should_stop:
            warn(
                f"Only for this role({index_role_name}) set 'STOP_WHEN_ERROR_HAPPENED' to {input_should_stop}"
            )
            should_stop = is_positive(input_should_stop)

        if should_stop == 0:
            with open(report_file, "a") as f:
                f.write(f"{index_role_name}::{result}\n")
            die(
                f"STOP_WHEN_ERROR_HAPPENED({should_stop}) is set and there are some errors detected, stopping all processes."
            )
        else:
            warn(
                f"STOP_WHEN_ERROR_HAPPENED({should_stop}) is NOT set, so skipping this error."
            )


def remove_comment_lines(command: str) -> str:
    lines = command.splitlines()
    filtered_lines = [line for line in lines if not line.strip().startswith("#")]
    return "\n".join(filtered_lines)


def check_pod_status(pod_selector, pod_namespace):
    """Check if pods with given selector are running and ready"""
    try:
        cmd = f"oc get pods -l {pod_selector} -n {pod_namespace} -o json"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            error("Error running kubectl command.")
            print(result.stderr)
            return False

        pods = json.loads(result.stdout)
        if not pods.get("items"):
            error(
                f"No pods found with selector {pod_selector} in {pod_namespace}. Pods may not be up yet."
            )
            return False

        for pod in pods["items"]:
            phase = pod["status"]["phase"]
            if phase not in ["Running", "Succeeded"]:
                return False

            conditions = pod["status"].get("conditions", [])
            ready = any(
                cond["type"] == "Ready" and cond["status"] == "True"
                for cond in conditions
            )
            if not ready:
                return False

        return True
    except Exception as e:
        error(f"Error checking pod status: {e}")
        return False


def wait_pod_containers_ready(pod_label, namespace):
    """Wait for pods with given label to be ready"""
    checkcount = 20
    tempcount = 0

    while True:
        try:
            result = subprocess.run(
                f"oc get pod -l {pod_label} -n {namespace} --ignore-not-found",
                shell=True,
                capture_output=True,
                text=True,
            )

            if result.stdout.strip():
                ready_cmd = f"oc get pod -l {pod_label} -n {namespace} --no-headers | head -1 | awk '{{print $2}}' | cut -d/ -f1"
                desired_cmd = f"oc get pod -l {pod_label} -n {namespace} --no-headers | head -1 | awk '{{print $2}}' | cut -d/ -f2"

                ready = subprocess.run(
                    ready_cmd, shell=True, capture_output=True, text=True
                ).stdout.strip()
                desired = subprocess.run(
                    desired_cmd, shell=True, capture_output=True, text=True
                ).stdout.strip()

                if ready == desired:
                    success(f"Pod(s) with label '{pod_label}' is(are) Ready!")
                    break
                else:
                    pending(
                        f"Pod(s) with label '{pod_label}' is(are) NOT Ready yet: {tempcount} times"
                    )
                    pending("Wait for 10 seconds")
                    time.sleep(10)
            else:
                pending("Pod is NOT created yet")
                time.sleep(10)

            tempcount += 1
            if checkcount == tempcount:
                error(f"Pod(s) with label '{pod_label}' is(are) NOT Ready")
                sys.exit(1)

        except Exception as e:
            error(f"Error waiting for pod containers: {e}")
            sys.exit(1)


def wait_for_pods_ready(pod_selector, pod_namespace):
    """Wait for pods with given selector to be ready"""
    wait_counter = 0

    while True:
        try:
            result = subprocess.run(
                f"oc get pods -l {pod_selector} -n {pod_namespace} -o jsonpath='{{.items[*]}}'",
                shell=True,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                print(result.stderr)
                error("Error running kubectl command.")
            elif not result.stdout.strip():
                pending(
                    f"No pods found with selector '{pod_selector}' -n '{pod_namespace}'. Pods may not be up yet."
                )
            elif check_pod_status(pod_selector, pod_namespace):
                pass_message(
                    f"All {pod_selector} pods in '{pod_namespace}' namespace are running and ready."
                )
                return True
            else:
                print(
                    f"Pods found with selector '{pod_selector}' in '{pod_namespace}' namespace are not ready yet."
                )

            if wait_counter >= 30:
                subprocess.run(
                    f"oc get pods -l {pod_selector} -n {pod_namespace}", shell=True
                )
                fail(
                    f"Timed out after {30 * wait_counter // 60} minutes waiting for pod with selector: {pod_selector}"
                )
                return False

            wait_counter += 1
            info("Waiting 10 secs ...")
            time.sleep(10)

        except Exception as e:
            error(f"Error waiting for pods: {e}")
            return False


def wait_for_pod_name_ready(pod_name: str, pod_namespace: str) -> int:
    """
    Wait for specific pod to be ready using Kubernetes API

    Args:
        pod_name (str): Name of the pod to wait for
        pod_namespace (str): Namespace where the pod is located

    Returns:
        int: 0 if pod is ready, 1 if there was an error or timeout
    """
    try:
        from kubernetes import client, config
        from kubernetes.client.rest import ApiException
        import time

        # Load kube config
        try:
            config.load_kube_config()
        except Exception as e:
            error(f"Failed to load kube config: {e}")
            return 1

        # Create API client
        v1 = client.CoreV1Api()

        info(f"Waiting for pod {pod_name}")
        start_time = time.time()
        timeout = 300  # 5 minutes timeout

        while time.time() - start_time < timeout:
            try:
                # Get pod status
                pod = v1.read_namespaced_pod(pod_name, pod_namespace)

                # Check if pod is ready
                if pod.status.phase == "Running":
                    # Check all container statuses
                    all_ready = True
                    for container in pod.status.container_statuses:
                        if not container.ready:
                            all_ready = False
                            break

                    if all_ready:
                        pass_message(
                            f"The pod({pod_name}) in '{pod_namespace}' namespace is running and ready."
                        )
                        return 0

                time.sleep(1)  # Wait 1 second before next check

            except ApiException as e:
                if e.status == 404:
                    # Pod not found yet, continue waiting
                    time.sleep(1)
                    continue
                else:
                    error(f"Error checking pod status: {e}")
                    return 1

        error(f"Timed out after {timeout}s waiting for pod({pod_name})")
        return 1

    except Exception as e:
        error(f"Error waiting for pod: {e}")
        return 1


def wait_for_just_created_pod_ready(namespace):
    """Wait for newly created pod to be ready"""
    wait_counter = 0
    created_pod_name = ""

    while not created_pod_name:
        try:
            result = subprocess.run(
                f"oc get event -n {namespace} | grep 'Started container manager' | grep -E '^[0-9]s' | grep -v -e '^[0-9]m' | awk '{{print $4}}' | cut -d'/' -f2",
                shell=True,
                capture_output=True,
                text=True,
            )
            created_pod_name = result.stdout.strip()

            if wait_counter >= 12:
                subprocess.run(
                    f"oc get pods {created_pod_name} -n {namespace}", shell=True
                )
                sys.exit(1)

            pending(f"No pods created in {namespace}. Pods may not be up yet.")
            wait_counter += 1
            pending("Waiting 5 secs ...")
            time.sleep(5)

        except Exception as e:
            error(f"Error waiting for created pod: {e}")
            sys.exit(1)

    info("Caught 'Started container manager' event")
    return wait_for_pod_name_ready(created_pod_name, namespace)


def wait_for_csv_installed(csv, namespace):
    """Wait for CSV to be installed"""
    ii = 0
    print()
    info(f'[START] Watching if CSV "{csv}" is installed')

    while True:
        try:
            result = subprocess.run(
                f"oc get csv -n {namespace} 2>&1 | grep {csv} | awk '{{print $NF}}'",
                shell=True,
                capture_output=True,
                text=True,
            )
            csv_status = result.stdout.strip()

            if csv_status == "Succeeded":
                break

            print(".", end="", flush=True)
            ii += 1

            if ii == 100:
                fail(f'CSV "{csv}" is NOT installed and it exceeds maximum tries(300s)')
                fail(f'please check the CSV "{csv}"')
                sys.exit(1)

            time.sleep(3)

            if ii % 20 == 0:
                print()
                pending(f'CSV "{csv}" is NOT installed yet')

        except Exception as e:
            error(f"Error waiting for CSV: {e}")
            sys.exit(1)

    print()
    success(f'[END] CSV "{csv}" is successfully installed')


def oc_wait_object_availability(cmd, interval, iterations):
    """Wait for object to be available"""
    ii = 0
    info(f'[START] Wait for "{cmd}" ')

    while ii <= iterations:
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True)
            if result.returncode == 0:
                break

            ii += 1
            if ii == 100:
                warn(f"{cmd} did not return a value")
                sys.exit(1)

            time.sleep(interval)

        except Exception as e:
            error(f"Error waiting for object: {e}")
            sys.exit(1)

    success(f'[END] "{cmd}" is successfully done')


def oc_wait_return_true(cmd, interval, iterations):
    """Wait for command to return true"""
    ii = 0
    info(f'[START] Wait for "{cmd}" ')

    while ii <= iterations:
        try:
            result = subprocess.run(cmd, shell=True)
            if result.returncode == 0:
                break

            ii += 1
            if ii == iterations:
                warn(f"{cmd} did not return a value")
                return 1

            time.sleep(interval)

        except Exception as e:
            error(f"Error waiting for command: {e}")
            return 1

    success(f"[END] \"{cmd}\" return 'true' successfully")
    return 0


def get_root_directory():
    """Get the root directory of the project"""
    current_dir = os.path.dirname(os.path.abspath(__file__))

    while not os.path.isdir(os.path.join(current_dir, ".git")) and current_dir != "/":
        current_dir = os.path.dirname(current_dir)

    if os.path.isdir(os.path.join(current_dir, ".git")):
        info(f"The root directory is: {current_dir}")
        return current_dir
    else:
        error("Error: Unable to find .git folder.")
        return None


def check_if_result(rc):
    """Check if command result is successful"""
    if rc != 0:
        die("FAIL")
    else:
        success("PASS")


def check_oc_status():
    """Check OpenShift connection and user role"""
    info("Checking oc connection and user role")

    try:
        result = subprocess.run("oc whoami", shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            error("You are NOT logged to the cluster. Please log in to your cluster")
            sys.exit(1)

        userName = result.stdout.strip()
        result = subprocess.run(
            "oc get group", shell=True, capture_output=True, text=True
        )
        groupNames = [
            line.split()[0]
            for line in result.stdout.splitlines()[1:]
            if userName in line
        ]

        for groupName in groupNames:
            result = subprocess.run(
                "oc get clusterrolebindings -o json",
                shell=True,
                capture_output=True,
                text=True,
            )
            clusterAdmin = sum(
                1
                for line in result.stdout.splitlines()
                if "cluster-admin" in line and (userName in line or groupName in line)
            )

            if clusterAdmin >= 1:
                pass_message("You logged to the cluster as a cluster-admin")
                break
            else:
                error("You logged to the cluster but you are not cluster-admin")
                info("        Please log in to your cluster as a cluster-admin")
                sys.exit(1)

    except Exception as e:
        error(f"Error checking oc status: {e}")
        sys.exit(1)


def check_rosa_access():
    """Check ROSA access"""
    info("Checking ROSA access")

    # Check AWS credentials
    if not os.path.isdir(os.path.expanduser("~/.aws")):
        error("~/.aws directory does not exist.")
        sys.exit(1)

    if not os.path.isfile(os.path.expanduser("~/.aws/credentials")):
        error("credentials file does not exist in ~/.aws.")
        sys.exit(1)

    if not os.path.isfile(os.path.expanduser("~/.aws/config")):
        if not os.environ.get("AWS_REGION"):
            error(
                "Neither config file exists in ~/.aws nor AWS_REGION environment variable is set."
            )
            sys.exit(1)

    # Check ROSA login
    try:
        result = subprocess.run(
            f"rosa login --token={os.environ.get('OCM_TOKEN')}", shell=True
        )
        if result.returncode != 0:
            error("rosa login failed")
            sys.exit(1)

        result = subprocess.run("rosa list clusters", shell=True)
        if result.returncode != 0:
            error("rosa can not list cluster. It would fail to create a new cluster")
            error("please check region and permission")
            sys.exit(1)

        success("All checks passed!")

    except Exception as e:
        error(f"Error checking ROSA access: {e}")
        sys.exit(1)


def validate_script_params(
    params_str: str, allowed_params: list[str]
) -> tuple[bool, list[str]]:
    """
    Validate script parameters against a list of allowed parameters.

    Args:
        params_str (str): Space-separated string of parameter pairs (e.g., "NAME=value WITH_ISTIO=true")
        allowed_params (list[str]): List of allowed parameter names

    Returns:
        tuple[bool, list[str]]: (is_valid, unknown_params)
            - is_valid: True if all parameters are allowed, False otherwise
            - unknown_params: List of unknown parameters found
    """
    # Parse params_str into list of parameter names
    params = []
    if params_str:
        param_pairs = params_str.split()
        for param_pair in param_pairs:
            if param_pair:
                param_name = param_pair.split("=")[0]
                params.append(param_name)

    # Check for unknown parameters
    unknown_params = []
    for param in params:
        if param not in allowed_params:
            unknown_params.append(param)

    # Return validation result
    is_valid = len(unknown_params) == 0
    return is_valid, unknown_params
