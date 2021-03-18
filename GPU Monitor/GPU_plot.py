import re
import matplotlib.pyplot as plt
import statistics

power_all = [[] for i in range (0,2)]
util_all = [[]for i in range (0,2)]
power_format = re.compile(r'[0-9]+[.][0-9]+ W')
util_format = re.compile(r'[0-9]+ %')

with open('gpu.log', 'r') as log:
    line = log.readline()
    while line:
        if(line.startswith('GPU 00000000:03:00.0')):
            line = log.readline()
            power = power_format.findall(line)[0][:-2]
            util = util_format.findall(line)[0][:-2]
            power_all[0].append(float(power))
            util_all[0].append(int(util))
            continue
        if(line.startswith('GPU 00000000:04:00.0')):
            line = log.readline()
            power = power_format.findall(line)[0][:-2]
            util = util_format.findall(line)[0][:-2]
            power_all[1].append(float(power))
            util_all[1].append(int(util))
            continue
        else:
            line = log.readline()



print(power_all)
print(util_all)
print(statistics.mean(power_all[0]))
x = [i for i in range(0,len(power_all[0]))]
y = [i for i in range(0,len(power_all[1]))]
# print(x)
# Draw power plot
plt.subplot(211)
plt.title('GPU 0')
plt.xlabel('Time')
plt.ylabel('Power(Watt)')
plt.tight_layout()
plt.plot(x, power_all[0])

plt.subplot(212)
plt.title('GPU 1')
plt.xlabel('Time')
plt.ylabel('Power(Watt)')
plt.tight_layout()
plt.plot(y, power_all[1])
plt.savefig("power.jpg")

# Draw utilization plot
plt.clf() # Clear the last plot
plt.subplot(211)
plt.title('GPU 0')
plt.xlabel('Time')
plt.ylabel('Utilization(%)')
plt.tight_layout()
plt.plot(x, util_all[0])

plt.subplot(212)
plt.title('GPU 1')
plt.xlabel('Time')
plt.ylabel('Utilization(%)')
plt.tight_layout()
plt.plot(y, util_all[1])
plt.savefig("util.jpg")
