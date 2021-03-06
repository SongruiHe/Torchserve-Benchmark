import csv
import json
import re
import shutil
import time
from subprocess import Popen, PIPE

import click
import click_config_file
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import requests
import tempfile
import os
from urllib.parse import urlparse
# from requests_file import FileAdapter

default_ab_params = {'url': "https://torchserve.pytorch.org/mar_files/resnet-18.mar",
                     'gpus': '',
                     'exec_env': 'local',
                     'batch_size': 1,
                     'batch_delay': 200,
                     'workers': 1,
                     'concurrency': 10,
                     'requests': 100,
                     'input': '../examples/image_classifier/kitten.jpg',
                     'content_type': 'application/jpg',
                     'image': '',
                     'docker_runtime': '',
                     'backend_profiling': False,
                     'config_properties': 'config.properties',
                     'inference_model_url': 'predictions/benchmark'
                     }
# TMP_DIR = tempfile.gettempdir()
TMP_DIR = "/home/model-server"

ModelServer_DIR = "/home/model-server"
execution_params = default_ab_params.copy()
result_file = os.path.join(ModelServer_DIR, "benchmark/result.txt")
metric_log = os.path.join(ModelServer_DIR, "benchmark/logs/model_metrics.log")


def json_provider(file_path, cmd_name):
    with open(file_path) as config_data:
        return json.load(config_data)


@click.command()
@click.argument('test_plan', default='custom')
@click.option('--url', '-u', default='https://torchserve.pytorch.org/mar_files/resnet-18.mar',
              help='Input model url')
@click.option('--exec_env', '-e', type=click.Choice(['local', 'docker'], case_sensitive=False), default='local',
              help='Execution environment')
@click.option('--gpus', '-g', default='',
              help='Number of gpus to run docker container with.  Leave empty to run CPU based docker container')
@click.option('--concurrency', '-c', default=10, help='Number of concurrent requests to run')
@click.option('--requests', '-r', default=100, help='Number of requests')
@click.option('--batch_size', '-bs', default=1, help='Batch size of model')
@click.option('--batch_delay', '-bd', default=200, help='Batch delay of model')
@click.option('--input', '-i', default='../examples/image_classifier/kitten.jpg',
              type=click.Path(exists=True), help='The input file path for model')
@click.option('--content_type', '-ic', default='application/jpg', help='Input file content type')
@click.option('--workers', '-w', default=1, help='Number model workers')
@click.option('--image', '-di', default='', help='Use custom docker image for benchmark')
@click.option('--docker_runtime', '-dr', default='', help='Specify required docker runtime')
@click.option('--backend_profiling', '-bp', default=False,
              help='Enable backend profiling using CProfile. Default False')
@click.option('--config_properties', '-cp', default='config.properties',
              help='config.properties path, Default config.properties')
@click.option('--inference_model_url', '-imu', default='predictions/benchmark',
              help='Inference function url - can be either for predictions or explanations. Default predictions/benchmark')

@click_config_file.configuration_option(provider=json_provider, implicit=False,
                                        help="Read configuration from a JSON file")
def benchmark(test_plan, url, gpus, exec_env, concurrency, requests, batch_size, batch_delay, input, workers,
              content_type, image, docker_runtime, backend_profiling, config_properties, inference_model_url):
    input_params = {'url': url,
                    'gpus': gpus,
                    'exec_env': exec_env,
                    'batch_size': batch_size,
                    'batch_delay': batch_delay,
                    'workers': workers,
                    'concurrency': concurrency,
                    'requests': requests,
                    'input': input,
                    'content_type': content_type,
                    'image': image,
                    'docker_runtime': docker_runtime,
                    'backend_profiling': backend_profiling,
                    'config_properties': config_properties,
                    'inference_model_url': inference_model_url
                    }

    # set ab params
    update_exec_params(input_params)
    click.secho("Starting AB benchmark suite...", fg='green')
    click.secho(f"Model name: {execution_params['url']}", fg='red')
    click.secho(f"\n\nConfigured execution parameters are:", fg='green')
    click.secho(f"{execution_params}", fg="blue")

    # Setup execution env
    # if execution_params['exec_env'] == 'local':
    #     click.secho("\n\nPreparing local execution...", fg='green')
    #     local_torserve_start()
    # else:
    #     click.secho("\n\nPreparing docker execution...", fg='green')
    #     docker_torchserve_start()

    prepare_common_dependency()
    check_torchserve_health()
    run_benchmark()
    generate_report()


def check_torchserve_health():
    attempts = 3
    retry = 0
    click.secho("*Testing system health...", fg='green')
    while retry < attempts:
        try:
            resp = requests.get(execution_params['inference_url'] + "/ping")
            if resp.status_code == 200:
                click.secho(resp.text)
                return True
        except Exception as e:
            retry += 1
            time.sleep(3)
    failure_exit("Could not connect to Tochserve instance at " + execution_params['inference_url'])


def run_benchmark():
    register_model()
    # modify_model()

    click.secho("\n\nExecuting Apache Bench tests ...", fg='green')
    click.secho("*Executing inference performance test...", fg='green')
    ab_cmd = f"ab -c {execution_params['concurrency']}  -n {execution_params['requests']} -k -p {TMP_DIR}/benchmark/input -T " \
             f"{execution_params['content_type']} {execution_params['inference_url']}/{execution_params['inference_model_url']} > {result_file}"
    
    execute(ab_cmd, wait=True)

    unregister_model()
    # stop_torchserve()


def register_model():
    click.secho("*Registering model...", fg='green')
    url = execution_params['management_url'] + "/models"
    data = {'model_name': 'benchmark', 'url': execution_params['url'], 'batch_delay': execution_params['batch_delay'],
            'batch_size': execution_params['batch_size'], 'initial_workers': execution_params['workers'],
            'synchronous': 'true'}

    resp = requests.post(url, params=data)

    if not resp.status_code == 200:
        failure_exit(f"Failed to register model.\n{resp.text}")
    click.secho(resp.text)

# This is how to modify model using PUT
def modify_model():
    click.secho("*Modifying model...", fg='green')
    url = execution_params['management_url'] + "/models/benchmark"
    # print(url)
    data = {'min_worker': execution_params['workers'], 'synchronous': 'true','batch_size':3}
    print(data)
    resp = requests.put(url, params=data)
    if not resp.status_code == 200:
        failure_exit(f"Failed to modify model.\n{resp.text}")
    click.secho(resp.text)

def unregister_model():
    click.secho("*Unregistering model ...", fg='green')
    resp = requests.delete(execution_params['management_url'] + "/models/benchmark")
    if not resp.status_code == 200:
        failure_exit(f"Failed to unregister model. \n {resp.text}")
    click.secho(resp.text)


def execute(command, wait=False, stdout=None, stderr=None, shell=True):
    print(command)
    cmd = Popen(command, shell=shell, close_fds=True, stdout=stdout, stderr=stderr, universal_newlines=True)
    if wait:
        cmd.wait()
    return cmd


def prepare_common_dependency():
    click.secho("Removing output generated last time...", fg='green')
    execute(f'rm -f {ModelServer_DIR}/benchmark/input {ModelServer_DIR}/benchmark/*.txt {ModelServer_DIR}/benchmark/*.png {ModelServer_DIR}/benchmark/*.csv', wait=True)
    input = execution_params['input']
    # shutil.rmtree(os.path.join(TMP_DIR, "benchmark"), ignore_errors=True)
    # os.makedirs(os.path.join(TMP_DIR, "benchmark/conf"), exist_ok=True)
    # os.makedirs(os.path.join(TMP_DIR, "benchmark/logs"), exist_ok=True)

    # shutil.copy(execution_params['config_properties'], os.path.join(TMP_DIR, 'benchmark/conf/'))
    shutil.copyfile(input, os.path.join(TMP_DIR, 'benchmark/input'))



def getAPIS():
    MANAGEMENT_API = "http://127.0.0.1:8081"
    INFERENCE_API = "http://127.0.0.1:8080"
    
    with open(f"{TMP_DIR}/benchmark/conf/{execution_params['config_properties']}", "r") as fp:
        lines = fp.readlines()
    for line in lines:
        line = line.strip()
        if "management_address" in line:
            MANAGEMENT_API = line.split("=")[1]
        if "inference_address" in line:
            INFERENCE_API = line.split("=")[1]
    
    execution_params['inference_url'] = INFERENCE_API
    execution_params['management_url'] = MANAGEMENT_API
    execution_params['config_properties_name'] = execution_params['config_properties'].strip().split("/")[-1]


def update_exec_params(input_param):
    for k, v in input_param.items():
        if default_ab_params[k] != input_param[k]:
            execution_params[k] = input_param[k]
    getAPIS()

            
def generate_report():
    click.secho("\n\nGenerating Reports...", fg='green')
    extract_metrics()
    generate_csv_output()
    generate_latency_graph()
    generate_profile_graph()
    click.secho("\nTest suite execution complete.", fg='green')


metrics = {"predict.txt": "PredictionTime",
           "handler_time.txt": "HandlerTime",
           "waiting_time.txt": "QueueTime",
           "worker_thread.txt": "WorkerThreadTime"}


def extract_metrics():

    #### Only select logs generated this time
    with open(metric_log) as f:
        lines = f.readlines()
    num=0
    list=[]
    for line in lines:
        if "DELETE" in line:
            list.append(num)
        num+=1

    # print(list)
    if len(list)==1:
        index = 0
    else:
        index = list[-2]  # From this row to the end, is needed to generate graphs
    
    lines = lines[index:]

    ##
    for k, v in metrics.items():
        all_lines = []
        pattern = re.compile(v)
        for line in lines:
            if pattern.search(line):
                all_lines.append(line.split("|")[0].split(':')[3].strip())

        out_fname = f'{ModelServer_DIR}/benchmark/{k}'
        click.secho(f"\nWriting extracted {v} metrics to {out_fname} ", fg='green')
        with open(out_fname, 'w') as outf:
            all_lines = map(lambda x: x + '\n', all_lines)
            outf.writelines(all_lines)


def generate_csv_output():
    click.secho("*Generating CSV output...", fg='green')
    batched_requests = execution_params['requests'] / execution_params['batch_size']
    line50 = int(batched_requests / 2)
    # print(line50)
    line90 = int(batched_requests * 9 / 10)
    line99 = int(batched_requests * 99 / 100)
    artifacts = {}
    with open(f'{ModelServer_DIR}/benchmark/result.txt') as f:
        data = f.readlines()
    artifacts['Benchmark'] = "AB"
    artifacts['Model'] = execution_params['url']
    artifacts['Concurrency'] = execution_params['concurrency']
    artifacts['Requests'] = execution_params['requests']
    artifacts['TS failed requests'] = extract_entity(data, 'Failed requests:', -1)
    artifacts['TS throughput'] = extract_entity(data, 'Requests per second:', -3)
    artifacts['TS latency P50'] = extract_entity(data, '50%', -1)
    artifacts['TS latency P90'] = extract_entity(data, '90%', -1)
    artifacts['TS latency P99'] = extract_entity(data, '99%', -1)
    artifacts['TS latency mean'] = extract_entity(data, 'Time per request:.*mean\)', -3)
    artifacts['TS error rate'] = int(artifacts['TS failed requests']) / execution_params['requests'] * 100

    with open(os.path.join(TMP_DIR, 'benchmark/predict.txt')) as f:
        lines = f.readlines()
        lines.sort(key=float)
        artifacts['Model_p50'] = lines[line50].strip()
        artifacts['Model_p90'] = lines[line90].strip()
        artifacts['Model_p99'] = lines[line99].strip()

    for m in metrics:
        df = pd.read_csv(f"{TMP_DIR}/benchmark/{m}", header=None, names=['data'])
        artifacts[m.split('.txt')[0] + "_mean"] = df['data'].values.mean().round(2)

    with open(os.path.join(TMP_DIR, 'benchmark/ab_report.csv'), 'w') as csv_file:
        csvwriter = csv.writer(csv_file)
        csvwriter.writerow(artifacts.keys())
        csvwriter.writerow(artifacts.values())

    return artifacts


def extract_entity(data, pattern, index, delim=" "):
    pattern = re.compile(pattern)
    for line in data:
        if pattern.search(line):
            return line.split(delim)[index].strip()


def generate_latency_graph():
    click.secho("*Preparing graphs...", fg='green')
    df = pd.read_csv(os.path.join(TMP_DIR, 'benchmark/predict.txt'), header=None, names=['latency'])
    iteration = df.index
    latency = df.latency
    a4_dims = (11.7, 8.27)
    plt.figure(figsize=(a4_dims))
    plt.xlabel('Requests')
    plt.ylabel('Prediction time')
    plt.title('Prediction latency')
    plt.bar(iteration, latency)
    plt.savefig(f"{TMP_DIR}/benchmark/predict_latency.png")


def generate_profile_graph():
    click.secho("*Preparing Profile graphs...", fg='green')

    plot_data = {}
    for m in metrics:
        df = pd.read_csv(f'{TMP_DIR}/benchmark/{m}', header=None)
        m = m.split('.txt')[0]
        plot_data[f"{m}_index"] = df.index
        plot_data[f"{m}_values"] = df.values

    if execution_params['requests'] > 100:
        sampling = int(execution_params['requests'] / 100)
    else:
        sampling = 1
    print(f"Working with sampling rate of {sampling}")

    a4_dims = (11.7, 8.27)
    grid = plt.GridSpec(3, 2, wspace=0.3, hspace=0.5)
    plt.figure(figsize=a4_dims)
    fig1 = plt.subplot(grid[0, 0])
    fig2 = plt.subplot(grid[0, 1])
    fig3 = plt.subplot(grid[1, 0])
    fig4 = plt.subplot(grid[1, 1])
    fig5 = plt.subplot(grid[2, 0:])

    def plot_line(fig, data, color='blue', title=None):
        fig.set_title(title)
        fig.set_ylabel('Time (ms)')
        fig.set_xlabel('Percentage of queries')
        fig.grid()
        plot_points = np.arange(0, 100, 100 / len(data))
        x = plot_points[:len(data):sampling]
        y = data[::sampling]
        fig.plot(x, y, f'tab:{color}')

    # Queue Time
    plot_line(fig1, data=plot_data["waiting_time_values"], color='pink', title='Queue Time')

    # handler Predict Time
    plot_line(fig2, data=plot_data["handler_time_values"], color='orange',
              title='Handler Time(pre & post processing + inference time)')

    # Worker time
    plot_line(fig3, data=plot_data["worker_thread_values"], color='green', title='Worker Thread Time')

    # Predict Time
    plot_line(fig4, data=plot_data["predict_values"], color='red',
              title='Prediction time(handler time+python worker overhead)')

    # Plot in one graph
    plot_line(fig5, data=plot_data["waiting_time_values"], color='pink')
    plot_line(fig5, data=plot_data["handler_time_values"], color='orange')
    plot_line(fig5, data=plot_data["predict_values"], color='red')
    plot_line(fig5, data=plot_data["worker_thread_values"], color='green', title='Combined Graph')
    fig5.grid()
    plt.savefig(f"{TMP_DIR}/benchmark/profile.png", bbox_inches='tight')


def failure_exit(msg):
    import sys
    click.secho(f"{msg}", fg='red')
    click.secho(f"Test suite terminated due to above failure", fg='red')
    sys.exit()


if __name__ == '__main__':
    benchmark()