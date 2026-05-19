#!/bin/bash
######################
## power by lsh/lzp ##
######################

# 基本信息
systeminfo(){
	systemid=$(cat /etc/.kyinfo | grep dist_id | awk -F"=| " '{print $2}')
	kylin_serial=$(cat /etc/.kyinfo | grep key= | awk -F"=" '{print $2}')
	#service_data=$(cat /etc/.kyinfo | grep term= | awk -F"=" '{print $2}')
	service_data=$(if [ ! -f "/etc/.kyactivation" ]; then echo -e "\033[33m【系统未激活无技术服务】\033[0m" ; else echo -e "技术服务期到：\033[33m$(cat /etc/.kyinfo | grep term= | awk -F"=" '{print $2}') \033[0m";fi)
	register=$(if [ ! -f "/etc/.kyactivation" ]; then echo 系统未激活; else echo $(cat /etc/.kyactivation);fi)
	sncode=$(sudo dmidecode -s system-serial-number)
	systemtime=$(date -r /var/log/installer)
	cpu_model=$(awk -F: '/model name/ {print $2}' /proc/cpuinfo | uniq)
	read -r _ root_size root_used root_avail used_percent _ <<< $(df -h / | awk 'NR==2')
	echo -e "\e[30;48;5;44m============================================系统基本信息===============================================\e[0m"
	echo -e "\e[1;33;44m 硬件信息 \e[0m ：
 1、主机型号：\033[33m $(sudo dmidecode -s system-manufacturer)-$(sudo dmidecode -s system-product-name)  \033[0m  主机SN码： \033[33m $sncode  \033[0m  
 2、CPU型号【$(cat /proc/cpuinfo | grep "processor" | wc -l)核】：\033[33m【$(top -bn1 | grep "Cpu(s)" | awk '{print "" $2 + $4 "%"}')】$cpu_model \033[0m  
 3、$(free -g | awk 'NR==2{printf "总内存/空闲内存: \033[33m %s GB / %s GB\033[0m\n", $2, $7}')
 4、显卡：\033[33m `lspci | grep -i vga | awk -F ":" '{print $3}'` \033[0m 
 5、系统根目录空间：\033[33m $root_size \033[0m  剩余可用： \033[33m $root_avail \033[0m 
 ------------------------- 
 `lsblk -d -o NAME,SIZE,SERIAL --nodeps | awk 'NR==1 {print "磁盘名称\t磁盘大小\t磁盘SN"; next} {print}' | grep -v loop | column -t` 
 ------------------------- 
`for intf in $(ip -o link show|awk -F': ' '{print $2}'|grep -Ev "lo|vmnet|docker|utun|virbr0"); do mac=$(ip link show "$intf" |grep link/ether |awk '{print $2}'); echo " 网卡($intf): $mac"; done` 
 "  2>&1
	echo -e "\e[1;33;44m 软件信息 \e[0m ："
	echo -e " 1、系统服务序列号：\033[33m $kylin_serial \e[0m  $service_data 
 2、当前系统版本是：\033[33m $systemid \033[0m 
 3、当前内核版本是：\033[33m `uname -r` \033[0m 
 4、系统安装时间是：\033[33m $systemtime \033[0m 
 5、系统build-id是：\033[33m $(cat /etc/kylin-build | grep buildid) \033[0m 
 6、操作系统硬件码：\033[33m $(cat /etc/.kyhwid)  \033[0m 
 7、操作系统注册码：\033[33m $(sudo kylin_gen_register)  \033[0m 
 8、操作系统激活码：\033[33m $register \033[0m 
 "  2>&1

}

systeminfo