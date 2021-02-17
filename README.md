# Usage

## 1. Directory
Make sure you have these folders in your home directory.
```
/model-server
   /benchmark
      /conf
      /logs
   /model-store
   /tmp
  
/torchserve_benchmark
```
And use `chmod -R 777` to give permissions to these folders.

## 2. Command
* First start the server:

`rm -rf logs/; singularity run --nv -B ~/model-server:/home/model-server torchserve_latest-gpu.sif "torchserve --start --model-store /home/model-server/model-store --ts-config /home/model-server/benchmark/conf/config.properties > /home/model-server/benchmark/logs/model_metrics.log"`

Where ~ stands for you own home directory that contains all folders listed above.

* Start the benchmark client:

`singularity run -B ~:/home torchserve_benchmark.sif`

# Reference
https://github.com/pytorch/serve/blob/master/benchmarks/README.md#benchmarking-with-apache-bench
