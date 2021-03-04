On turing, Torchserve does use the GPU(if it doesn't, rps is ~30), but can't fully utilize the GPU.

1. **Singularity environment problems —>Maybe**
I compared the libs loaded by torchserve on Tui and turing, and found out these libs are not loaded on turing: `libnvidia-ngx.so`  `libnvidia-allocator.so`

    `--nv` flag automatically loads libs: 

    - if `nvidia-comtainer-cli` exists, use this to load libs.  We can't isntall this without sudo.
    - if it doesn't exist, use `etc/singularity/nvbliblist.conf` to load. We can't modify this file without sudo.

    I tried to install singularity without sudo under my directory(so I can't modify the file), failed—>can't replace older version

    I installed torchserve via conda(so it will load libs directly from system).  Still low throughput.

2. **cuDNN version or CUDA version —> Most possible reason**
In conda env, I don't know what libs are loaded, but cuDNN is loaded as version 7.6.5. 
If use Singularity, cuDNN is loaded as 8.0.4. 
The images contains cudnn libs.
3. **Nsight systems profiler**
- Can't profile GPU information on both Yue and turing using Singularity. nsys profile can locate the child process(the worker process doing inferences), but can't collect GPU side information.
- Can't use profile tool via conda on turing, becuase turing system is CentOS and the kernel version doesn't support this tool.
