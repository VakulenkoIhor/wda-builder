from sys import platform
import argparse
import subprocess
import os
from datetime import datetime
from tempfile import gettempdir
from .utils import md5, get_current_xcode_version

def wda_build():
    if platform != 'darwin':
        print("You can't use current OS. MacOS with XCode only supported.")
        exit(13)

    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--development-team-id', required=True, help='Apple Development team id')
    parser.add_argument('-w', '--wda-version', help='Appium Wweb driver agent version', default='latest')
    parser.add_argument('-v', '--verbosity', action='store_true')
    args = parser.parse_args()
    print(args)

    # Init build parameters
    verbosity = args.verbosity
    current_date = datetime.now().strftime("%Y-%b-%d")
    current_path = os.getcwd()
    if (not os.access(current_path, os.W_OK)):
        print("Current %s folder is not writable" % current_path)
        exit(13)
    temp_path = os.path.join(gettempdir(), 'WDABuilder')

    development_team_id = args.development_team_id # J99FJA3665
    appium_webdriveragent_version = args.wda_version # '4.13.1'
    xcode_version = get_current_xcode_version()

    build_id = '%s_%s_%s' % (development_team_id, appium_webdriveragent_version, xcode_version)
    build_hash = md5(build_id)

    # Prepare temporary folder
    wda_path = os.path.join(temp_path, development_team_id, xcode_version, appium_webdriveragent_version)
    if (os.path.exists(wda_path) == False):
        try:
            os.makedirs(wda_path)
        except OSError as e:
            print("Failed to create %s folder. Error: %s" % (wda_path, e.strerror))
            exit(e.errno)

    # Download appium web driver agent
    try:
        result = subprocess.run(
            ["npm init --yes --force && npm i appium-webdriveragent@%s --save" % appium_webdriveragent_version],
            shell=True, capture_output=True, text=True, check=True, cwd=wda_path)
        if verbosity:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error: %s" % e.stderr)
        exit(e.returncode)

    # Prepare appium web driver agent
    appium_webdriveragent_project_path = os.path.join(wda_path,
                                                      'node_modules/appium-webdriveragent/WebDriverAgent.xcodeproj/project.pbxproj')
    try:
        with open(appium_webdriveragent_project_path, 'r') as file:
            data = file.read()
            data = data.replace('ProvisioningStyle = Manual;', 'ProvisioningStyle = Automatic;')
            data = data.replace('DEVELOPMENT_TEAM = "";', "DEVELOPMENT_TEAM = %s;" % development_team_id)
        with open(appium_webdriveragent_project_path, 'w') as file:
            file.write(data)
    except OSError as e:
        print("Failed to modify %s file. Error: %s" % (appium_webdriveragent_project_path, e.strerror))
        exit(e.errno)

    # Build appium web driver agent
    wda_project_path = os.path.join(wda_path, 'node_modules/appium-webdriveragent')
    wda_derived_data_path = os.path.join(wda_path, 'WebDriverAgent-%s' % build_hash)
    try:
        os.makedirs(wda_derived_data_path, exist_ok=True)
        result = subprocess.run([
                           'xcodebuild -project WebDriverAgent.xcodeproj -derivedDataPath "%s" -allowProvisioningUpdates -scheme WebDriverAgentRunner -destination generic/platform=iOS DEVELOPMENT_TEAM=%s' % (
                           wda_derived_data_path, development_team_id)], shell=True, capture_output=True, text=True,
                       check=True, cwd=wda_project_path)
        if verbosity:
            print(result.stdout)
        if not "** BUILD SUCCEEDED **" in result.stdout:
            raise Exception('Failed to make a build. Error: Unsuccessful build occurred')
    except OSError as e:
        print("Failed to create %s folder. Error: %s" % (wda_derived_data_path, e.strerror))
        exit(e.errno)
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        exit(e.returncode)
    except Exception as e:
        print(str(e))
        exit(13)

    # Pack appium web driver agent
    wda_build_path = wda_path
    wda_derived_data_package_name = 'WebDriverAgent-%s_%s.tgz' % (build_hash, current_date)
    wda_derived_data_temp_package = os.path.join(wda_build_path, wda_derived_data_package_name)
    try:
        os.makedirs(wda_build_path, exist_ok=True)
        subprocess.run(['tar -czf %s WebDriverAgent-%s' % (wda_derived_data_temp_package, build_hash)], shell=True,
                       capture_output=True, text=True, check=True, cwd=wda_path)
    except OSError as e:
        print("Failed to create %s folder. Error: %s" % (wda_build_path, e.strerror))
        exit(e.errno)
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        exit(e.returncode)

    # Pack appium web driver agent project
    wda_node_modules_path = os.path.join(wda_path, 'node_modules')
    wda_project_package_name = 'appium-webdriveragent-%s_%s.tgz' % (build_hash, current_date)
    wda_project_temp_package = os.path.join(wda_build_path, wda_project_package_name)
    try:
        subprocess.run(['tar -czf %s appium-webdriveragent' % (wda_project_temp_package)], shell=True,
                       capture_output=True, text=True, check=True, cwd=wda_node_modules_path)
    except subprocess.CalledProcessError as e:
        print(e.stderr)
        exit(e.returncode)

    # Move artifacts
    wda_derived_data_package = os.path.join(current_path, wda_derived_data_package_name)
    wda_project_package = os.path.join(current_path, wda_project_package_name)
    try:
        os.rename(wda_derived_data_temp_package, wda_derived_data_package)
        print(wda_derived_data_package)
        os.rename(wda_project_temp_package, wda_project_package)
        print(wda_project_package)
    except Exception as e:
        print(str(e))
        exit(13)

    exit(0)
