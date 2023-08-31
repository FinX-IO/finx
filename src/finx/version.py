# If building the SDK to test-pypi or to pypi, the following environment variables are required:
#
# 1. `TWINE_USERNAME` - The username for the pypi account.
# 2. `TWINE_PASSWORD` - The password for the pypi account.
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
    try:
        major, minor, patch = map(int, current_version.split(".")[:3])
    except Exception as e:
        print(e)

    # Increase version number based on level
    if level == "major" and deploy_environment == "test":
        major += 1
        minor = 0
        patch = 0
        return f"{major}.{minor}.{patch}"
    elif level == "minor" and deploy_environment == "test":
        minor += 1
        patch = 0
        return f"{major}.{minor}.{patch}"
    elif level == "patch" and deploy_environment == "test":
        patch += 1
        return f"{major}.{minor}.{patch}"
    if level == "major" and deploy_environment == "prod":
        major += 0
        minor = 0
        patch = 0
        return f"{major}.{minor}.{patch}"
    elif level == "minor" and deploy_environment == "prod":
        minor += 0
        patch = 0
        return f"{major}.{minor}.{patch}"
    elif level == "patch" and deploy_environment == "prod":
        patch += 0
        return f"{major}.{minor}.{patch}"
    if deploy_environment == "no-deploy":
        return f"{major}.{minor}.{patch}"
    else:
        raise ValueError("Invalid level. Please choose 'major', 'minor', or 'patch'.")


if os.getenv("DEPLOY_ENVIRONMENT") == "test":
    DEPLOY_LEVEL = os.getenv("DEPLOY_LEVEL")
    DEPLOY_ENVIRONMENT = os.getenv("DEPLOY_ENVIRONMENT")
    VERSION = bump_version(DEPLOY_LEVEL, DEPLOY_ENVIRONMENT)
    os.environ["FINX_VERSION"] = VERSION
elif os.getenv("DEPLOY_ENVIRONMENT") == "prod":
    DEPLOY_LEVEL = os.getenv("DEPLOY_LEVEL")
    DEPLOY_ENVIRONMENT = os.getenv("DEPLOY_ENVIRONMENT")
    VERSION = bump_version(DEPLOY_LEVEL, DEPLOY_ENVIRONMENT)
    os.environ["FINX_VERSION"] = VERSION


