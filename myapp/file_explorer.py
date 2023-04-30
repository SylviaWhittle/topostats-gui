import os
from flask import Blueprint, render_template, url_for, request, jsonify, Response, make_response
from pathlib import Path
from pprint import pprint
import json
import time
import base64
import re

bp = Blueprint('file_explorer', __name__)

# @bp.route('/')
# def index():
#     # get file structure

#     directories = ['Documents', 'Images', 'Videos', 'Desktop']

#     files = ['file1.txt', 'file2.txt', 'image1.png']

#     return render_template('main-page/index.html', info='info!', files = files, directories = directories)


def list_directory(requested_dir: str, current_path: str):

    print('---- processing directory ----')
    print(f'requested_dir {requested_dir}')
    print(f'current_path: {current_path}')

    if requested_dir == 'None' or requested_dir == 'undefined':
        requested_dir = None
    if current_path == 'None' or current_path == 'undefined':
        current_path = None

    if requested_dir is None and current_path is None:
        print('requested_dir and current_path both None')
        current_path = Path('./')
    elif current_path is None:
        print('current_path is None')
        raise ValueError('current_path can not be None if requested_dir is not None')
    elif requested_dir == '..':
        print(f' back: current path: {current_path} | current path parent: {Path(current_path).parent}')
        current_path = Path(current_path).parent
    else:
        print('entering sub-directory')
        current_path = Path(current_path) / requested_dir
        print(f'sub directory: {current_path}')
    
    # find files and directories in current path
    directories = []
    files = []
    yaml_files = []

    for entry in current_path.glob('./*'):
        if entry.is_dir():
            print(f'is directory: {str(entry)}')
            directories.append(str(entry.relative_to(current_path)))
        else:
            print(f'is file: {str(entry)}')
            # Check if file is a YAML file
            if entry.suffix == '.yaml' or entry.suffix == '.yml':
                yaml_files.append(str(entry.relative_to(current_path)))
            else:
                files.append(str(entry.relative_to(current_path)))

    print('----                 ----')

    return str(current_path.resolve()), files, yaml_files, directories


@bp.route('/', methods=['POST', 'GET'])
def explore():
    requested_dir = request.args.get('path')
    current_path = request.args.get('current_path')

    print('EXPLORE TRIGGERED')
    print(f'requested_dir={requested_dir}')
    print(f'current_path={current_path}')

    current_path, files, yaml_files, directories = list_directory(requested_dir=requested_dir, current_path=current_path)

    return render_template('main-page/index.html', current_path=current_path, files=files, yaml_files=yaml_files, directories=directories)


@bp.route('/get-data', methods=['POST', 'GET'])
def get_data():
    print('GET-DATA TRIGGERED')
    request_json = request.get_json()
    print(f'request json: {request_json}')

    requested_dir = str(request_json['requested_dir'])
    print(f'input requested dir: {requested_dir}')
    current_path = str(request_json['current_path'])
    print(f'input current_path: {current_path}')
    
    current_path, files, yaml_files, directories = list_directory(requested_dir=requested_dir, current_path=current_path)

    data = {
        "current_path": current_path,
        "files": files,
        "yaml_files": yaml_files,
        "directories": directories
    }

    print('sending data:')
    print(data)

    return jsonify(data)

@bp.route('/load-config', methods=['POST', 'GET'])
def load_config():

    print('LOAD CONFIG TRIGGERED')

    # get path to config
    config_path = request.form['config_file_path']
    print(f'(loading) config file path: {config_path}')
    config_path = Path(config_path)
    print(f'(loading) config file path Path-ed: {config_path}')

    # verify config path
    if not config_path.exists:
        return Response("File does not exist", status=400)

    # open config file
    with open(config_path, 'r') as f:
        config = f.read()
    print(f'(loading) config loaded: {config}')

    # return config file contents
    return config

@bp.route('/update-config', methods=['POST'])
def update_config():

    # get updated config and path
    config_path = request.form['config_file_path']
    print(f'(updating) config file path: {config_path}')
    config_path = Path(config_path)
    print(f'(updating) config file path Path-ed: {config_path}')

    config = request.form['config']
    print(f'(updating) received config: {config}')

    # open config file and update it
    with open(config_path, 'w') as f:
        f.write(config)

    return 'successfully saved config'



@bp.route('/render_images', methods=['POST'])
def render_images():

    output_path = request.form['output_path']
    output_path = Path(output_path) / "processed"

    images = []

    for png_file in output_path.glob("./*.png"):
        print(f'encoding image: {png_file}')
        with open(png_file, "rb") as f:
            image_binary = f.read()
        images.append(base64.b64encode(image_binary).decode('utf-8'))

    return jsonify(images)

@bp.route('/run_topostats', methods=['POST', 'GET'])
def run_topostats():

    print("RUNNING TOPOSTATS")
    config_file_path = request.form['config_file_path']
    config_file_path = Path(config_file_path)
    print(f'config file: {config_file_path}')

    os.system(f"run_topostats -c {config_file_path}")

    print('finished running topostats, returning log file')

    # Get the latest log and return it
    log_files = [f for f in os.listdir() if re.search(r'\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}', f)]
    if len(log_files) == 0:
        return "no output log file found"
    latest_log = max(log_files, key=lambda x: re.search(r'\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}', x).group())
    with open(latest_log, 'r') as f:
        log = f.read()
    return log
