import json
import os
import urllib.request


def bump_version(level, deploy_environment):
    # Retrieve JSON data
    url = "https://test.pypi.org/pypi/finx-io/json"
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())

    # Extract current version
    current_version = data["info"]["version"]
    major, minor, patch = map(int, current_version.split("."))

    # Increase version number based on level
    if level == "major" and deploy_environment == "test":
        major += 1
        minor = 0
        patch = 0
    elif level == "minor" and deploy_environment == "test":
        minor += 1
        patch = 0
    elif level == "patch" and deploy_environment == "test":
        patch += 1
    else:
        raise ValueError("Invalid level. Please choose 'major', 'minor', or 'patch'.")

    # Build and return the new version string
    new_version = f"{major}.{minor}.{patch}"
    os.environ["FINX_NEW_VERSION"] = new_version
    os.environ["FINX_VERSION"] = current_version
    return new_version


if os.getenv("DEPLOY_LEVEL"):
    DEPLOY_LEVEL = os.getenv("DEPLOY_LEVEL")
    DEPLOY_ENVIRONMENT = os.getenv("DEPLOY_ENVIRONMENT")
    NEXT_VERSION = bump_version(DEPLOY_LEVEL, DEPLOY_ENVIRONMENT)
    VERSION = os.getenv("FINX_VERSION")

else:
    url = "https://pypi.org/pypi/finx-io/json"
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())
    current_version = data["info"]["version"]
    os.environ["FINX_VERSION"] = current_version
    VERSION = current_version
