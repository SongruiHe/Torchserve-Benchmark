rm -f gpu.log
while true	
do
	for((i=0;i<2;i++));
	do
		gpuutilstats=`nvidia-smi -q -d UTILIZATION -i ${i}| grep -E "Gpu|GPU 0"`
		gpupower=`nvidia-smi -q -d POWER -i ${i}| grep "Power Draw"`
		echo -e "$gpuutilstats   $gpupower" >> gpu.log
	done
	echo -e "\n" >> gpu.log
	sleep 0.5
done

