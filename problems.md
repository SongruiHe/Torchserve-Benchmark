## On turing, Torchserve does use the GPU(if it doesn't, rps is ~30), but can't fully utilize the GPU.

**1. Singularity environment problems —>Maybe**

I compared the libs loaded by torchserve on Tui and turing, and found out these libs are not loaded on turing: `libnvidia-ngx.so`  `libnvidia-allocator.so`

 `--nv` flag automatically loads libs: 

 - if `nvidia-comtainer-cli` exists, use this to load libs.  We can't isntall this without sudo.
 - if it doesn't exist, use `etc/singularity/nvbliblist.conf` to load. We can't modify this file without sudo.
I tried to install singularity without sudo under my directory(so I can't modify the file), failed—>can't replace older version

    I installed torchserve via conda(so it will load libs directly from system).  Still low throughput.

**2. cuDNN version or CUDA version —> Not likely**

- In conda env, I don't know exactly what libs are loaded(not like singularity), but cuDNN is loaded as version 7.6.5. 
    If use Singularity, cuDNN is loaded as 8.0.4.
    
- The container itselt includes CUDA-11 and cuDNN libs. It didn't use the host library when it starts running.

**3. Nsight systems profiler**

- Can't profile GPU information on both Yue and turing using Singularity. nsys profile can locate the child process(the worker process doing inferences), but can't collect GPU side information.
    
- Can't use profile tool via conda on turing, becuase turing system is CentOS and the kernel version doesn't support this tool.

**4. Nvidia-container-runtime/toolkit missing —> Maybe**

- Two tools are missing on turing and bender. Both singularity(to load `--nv` libs) and torchserve(to build and run docker containers) suggest to install these.
    
- I uninstalled these two tools on tui. Everything still works fine.
<details>
<summary>Links of these tools</summary>

[https://github.com/NVIDIA/nvidia-container-runtime](https://github.com/NVIDIA/nvidia-container-runtime)

nvidia container runtime  

nvidia-docker2
        
nvidia container toolkit

[https://github.com/NVIDIA/libnvidia-container](https://github.com/NVIDIA/libnvidia-container)

libnvidia-container-tools

libnvidia-container1
</details>

**5. Centos(turing and bender) & Ubuntu(tui and yue) —> Maybe**

- CUDA and cuDNN libs may be different in Centos and Ubuntu. I re-build the docker image based on centos 7. It runs perfectly on tui and yue, but still low throughput on turing and bender.

**6. GPU driver —>Likely**

- GPU version:  tui: 455.32.00 yue: 455.45.01
                    turing4: 455.23.05 bender: 455.23.05

- I re-installed driver on yue to 455.23.05. `nvidia-smi` can display but can't monitor GPU utilization. Torchserve still runs perfectly on this driver.
