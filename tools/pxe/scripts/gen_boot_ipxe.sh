#!/bin/bash
. scripts/umount.sh
. scripts/gen_ipxe.sh $1
BOOTPXE=netboot/boot.ipxe
ConfigDir=netboot/config
MonitorDir=netboot/monitor
cp -rf config/header.ipxe $BOOTPXE
rm -rf .temp.ipxe

if [ ! -f "config/config.json" ];then
  cp config/example_cfg.json config/config.json
fi

ip=$(cat config/config.json | grep DHCP_SERVER_IP | awk -F "\"" '{print $4}')
HTTP_PORT=$(cat config/config.json | grep HTTP_PORT | awk -F ",|:" '{print $2}'  | sed 's/ //g')
MENU_DEFAULT=$(cat config/config.json | grep MENU_DEFAULT | awk -F "\"" '{print $4}')
MENU_TIMEOUT=$(cat config/config.json | grep MENU_TIMEOUT | awk -F "\"" '{print $4}')

ip_to_int() {
  local ip=$1
  IFS='.' read -ra parts <<< "$ip"
  echo $(( (parts[0]<<24) | (parts[1]<<16) | (parts[2]<<8) | parts[3] ))
}

# 将整数转为点分十进制IP
int_to_ip() {
  local num=$1
  echo "$(( (num >> 24) & 0xFF )).$(( (num >> 16) & 0xFF )).$(( (num >> 8) & 0xFF )).$(( num & 0xFF ))"
}

# 计算子网掩码（输入CIDR）
cidr_to_mask() {
  local cidr=$1
  local mask=$(( 0xFFFFFFFF & ((0xFFFFFFFF << (32 - cidr)) & 0xFFFFFFFF) ))
  int_to_ip $mask
}

# 计算网络地址（输入IP和CIDR）
calc_network() {
  local ip=$1
  local cidr=$2
  local ip_num=$(ip_to_int $ip)
  local mask_num=$(ip_to_int $(cidr_to_mask $cidr))
  int_to_ip $(( ip_num & mask_num ))
}

# 计算广播地址（输入网络地址和CIDR）
calc_broadcast() {
  local network=$1
  local cidr=$2
  local network_num=$(ip_to_int $network)
  local host_bits=$(( 32 - cidr ))
  int_to_ip $(( network_num | (0xFFFFFFFF >> (32 - host_bits)) ))
}

# IP地址最后一段加1（自动处理255→0循环）
ip_plus_one() {
  local ip=$1
  IFS='.' read -ra parts <<< "$ip"
  local new_last=$(( (parts[3] + 1) % 256 ))
  echo "${parts[0]}.${parts[1]}.${parts[2]}.$new_last"
}

# IP地址最后一段减1（自动处理0→255循环）
ip_minus_one() {
  local ip=$1
  IFS='.' read -ra parts <<< "$ip"
  local new_last=$(( (parts[3] - 1 + 256) % 256 ))
  echo "${parts[0]}.${parts[1]}.${parts[2]}.$new_last"
}

#更换ip第一次跑，自动识别第一个UP网卡，修改配置并启动服务。
if ! echo $(hostname -I)| grep -q "$ip" ; then
    ethname=$(ip -o link show | awk -F': ' '/state UP/ {print $2}'| head -1)

    ip_info=$(ip -4 addr show dev $ethname | grep 'inet ')
    nip=$(echo "$ip_info" | awk '{print $2}' | cut -d'/' -f1)
    cidr=$(echo "$ip_info" | awk '{print $2}' | cut -d'/' -f2)
    mask=$(cidr_to_mask $cidr)
    broadcast=$(calc_broadcast $nip $cidr)
    startip=$(ip_plus_one $nip)
    endip=$(ip_minus_one $broadcast)
    if [ "misstar""$nip" != "misstar" ] && [ "misstar""$startip" != "misstar" ] && [ "misstar""$endip" != "misstar" ] && [ "misstar""$mask" != "misstar" ] && [ "misstar""$ethname" != "misstar" ] ;then
        sed -i "s/$ip/$nip/g" config/config.json
        sed -i  -E "s/\"DHCP_OFFER_BEGIN\": \"[0-9.]+\"/\"DHCP_OFFER_BEGIN\": \"$startip\"/g"  config/config.json
        sed -i  -E "s/\"DHCP_OFFER_END\": \"[0-9.]+\"/\"DHCP_OFFER_END\": \"$endip\"/g"  config/config.json
        sed -i  -E "s/\"DHCP_SUBNET\": \"[0-9.]+\"/\"DHCP_SUBNET\": \"$mask\"/g"  config/config.json
        sed -i  -E "s/\"DHCP_SERVER_NIC\": \"[a-zA-Z0-9_-]+\"/\"DHCP_SERVER_NIC\": \"$ethname\"/g"  config/config.json
    fi
    ip=$nip
fi

function ReadIni(){
    fid=$1
    section=$2
    option=$3

    test ! -f $fid && echo "不存在文件$fid" && return 2
    if [ $# -eq 3 ] ; then
        local src=$(cat $fid | awk '/\['$section'\]/{f=1;next} /\[*\]/{f=0} f' |  #找出section下的所有内容
        grep $option | # 匹配option的行 
        grep '='     | # 看看是不是存在=
        cut -d'=' -f2| # 获取对应的值
        cut -d'#' -f1| # 去除注释
        cut -d';' -f1| #去除注释
        awk '{gsub(/^\s+|\s+$/, "");print}') #去掉最前面的空格
        echo $src
        test ${#src} -eq 0 && return 2 || return 0  #读取到有效数据 返回状态码0
    else
        return 2
    fi 
}

sed -i '/###MisstarPXE/d'  /etc/exports
echo "/tmp/pxenfsroot *(ro,no_subtree_check,crossmnt,fsid=1024,insecure)  ###MisstarPXE" >> /etc/exports

cat netboot/monitor/monitor.sh.tpl > netboot/monitor/monitor.sh

#anconda
cat netboot/monitor/monitor.cfg.tpl  netboot/monitor/hooks.sh.tpl > netboot/monitor/monitor.cfg
echo "%end"  >> netboot/monitor/monitor.cfg

#preseed
mkdir -p netboot/monitor/hooks/
cat netboot/monitor/hooks.sh.tpl > netboot/monitor/hooks/prepare.sh


sed -i "s#SERVER_IP_ADDRESS#$ip#g"  netboot/monitor/hooks/prepare.sh
sed -i "s#HTTP_PORT#$HTTP_PORT#g"   netboot/monitor/hooks/prepare.sh

ls -rt $ConfigDir | while read ipxename; do
    NfsRootPoint=/tmp/pxenfsroot
    autoinstall=""
    fsid=1025
    isoname=$(ReadIni $ConfigDir/$ipxename/config.ini config isoname)
    if [ ! -f "iso/""$isoname" ]; then
        rm -rf $ConfigDir/$ipxename
        continue
    fi
    if [ -f $ConfigDir/$ipxename"/extfile.ini" ]; then
      extpathname=$(ReadIni $ConfigDir/$ipxename/config.ini config extpathname)
      mkdir -p $NfsRootPoint/$ipxename/$extpathname
      while IFS= read -r line || [[ -n "${line}" ]]; do
        if [ "$line""mpxe" != "mpxe" ];then
          if [ -d $line ]; then
            mkdir -p $NfsRootPoint/$ipxename/$extpathname/$(basename $line)
            echo "$NfsRootPoint/$ipxename/$extpathname/$(basename $line) *(ro,no_subtree_check,crossmnt,insecure,fsid=$fsid,no_root_squash,all_squash,anongid=0,anonuid=0,insecure)  ###MisstarPXE" >> /etc/exports
            fsid=`expr $fsid + 1`
          elif [ -f $line ]; then
            touch $NfsRootPoint/$ipxename/$extpathname/$(basename $line)
          fi
          mount --bind $line $NfsRootPoint/$ipxename/$extpathname/$(basename $line)
        fi
      done < $ConfigDir/$ipxename"/extfile.ini"
      exportfs -r
    fi

    cp $ConfigDir/$ipxename/grub.cfg_tpl $ConfigDir/$ipxename/grub.cfg

    #Kylin_desktop
    mkdir -p $NfsRootPoint/$ipxename/hooks/prepare
    cp -f netboot/monitor/hooks/prepare.sh $NfsRootPoint/$ipxename/hooks/prepare/mpxe_monitor.sh
    chmod +x $NfsRootPoint/$ipxename/hooks/prepare/mpxe_monitor.sh

    #uos-desktop
    if [[ -d "$NfsRootPoint/$ipxename/oem" ]];then
      umount $NfsRootPoint/$ipxename/oem
      rm -r $NfsRootPoint/$ipxename/oem
      mkdir -p $NfsRootPoint/$ipxename/oem/live_hooks
      cp -f netboot/monitor/hooks/prepare.sh $NfsRootPoint/$ipxename/oem/live_hooks/mpxe_monitor.job
      chmod +x $NfsRootPoint/$ipxename/oem/live_hooks/mpxe_monitor.job
    fi

    isautoinstall=$(ReadIni $ConfigDir/$ipxename/config.ini config autoinstall )
    if [ "$isautoinstall" = "true" ];then
        cp -f $ConfigDir/$ipxename/autoinstall.cfg_tpl $ConfigDir/$ipxename/autoinstall.cfg
        installclass=$(ReadIni $ConfigDir/$ipxename/config.ini config class )
        if [ "$installclass" = "Kickstart" ];then
          #在现有的ks文件%pre中加入监控脚本内容
          PRE_EXISTS=$(grep -v '^[[:space:]]*#' $ConfigDir/$ipxename/autoinstall.cfg | grep -q '^[[:space:]]*%pre' && echo "yes" || echo "no")
          if [ "$PRE_EXISTS" = "yes" ]; then
              PRE_START_LINE=$(grep -n -v '^[[:space:]]*#' $ConfigDir/$ipxename/autoinstall.cfg | grep '%pre' | head -1 | cut -d: -f1)
              END_LINE=$(sed -n "${PRE_START_LINE},\$p" $ConfigDir/$ipxename/autoinstall.cfg | grep -n '%end' | head -1 | cut -d: -f1)
              ABS_END_LINE=$((PRE_START_LINE + END_LINE - 1))
              INSERT_CONTENT_ESC=$(cat netboot/monitor/hooks.sh.tpl | sed ':a;N;$!ba;s/\n/\\n/g')
              sed -i "${ABS_END_LINE}i\\${INSERT_CONTENT_ESC}" $ConfigDir/$ipxename/autoinstall.cfg
          else
              echo -e "\n\n%pre --log=/tmp/pre_download.log" >> $ConfigDir/$ipxename/autoinstall.cfg
              cat netboot/monitor/hooks.sh.tpl >> $ConfigDir/$ipxename/autoinstall.cfg
              echo "%end"  >> $ConfigDir/$ipxename/autoinstall.cfg
          fi
        fi
        autoinstall=" [autoinstall]"
    fi
    
    echo "  item a"$ipxename" "$isoname$autoinstall >> $BOOTPXE
    echo ":a"$ipxename >> .temp.ipxe
    echo "chain http://SERVER_IP_ADDRESS:HTTP_PORT/config/$ipxename/grub.efi" >> .temp.ipxe
    echo "  boot || goto retry" >>  .temp.ipxe
    echo "  goto start" >>  .temp.ipxe
    echo " " >>  .temp.ipxe
done




cat config/foot.ipxe >> $BOOTPXE
echo " "  >> $BOOTPXE
cat .temp.ipxe >> $BOOTPXE
sed -i "s#SERVER_IP_ADDRESS#$ip#g"  $BOOTPXE
sed -i "s#HTTP_PORT#$HTTP_PORT#g"  $BOOTPXE
sed -i "s#SERVER_IP_ADDRESS#$ip#g"  $ConfigDir/*/*.cfg
sed -i "s#SERVER_IP_ADDRESS#$ip#g"  $MonitorDir/*.sh $MonitorDir/*/*.sh $MonitorDir/*.cfg
sed -i "s#HTTP_PORT#$HTTP_PORT#g"   $ConfigDir/*/*.cfg
sed -i "s#HTTP_PORT#$HTTP_PORT#g"   $MonitorDir/*.sh $MonitorDir/*/*.sh $MonitorDir/*.cfg

sed -i "s#MENU_DEFAULT#a$MENU_DEFAULT#g"  $BOOTPXE
sed -i "s#MENU_TIMEOUT#$MENU_TIMEOUT""000#g"  $BOOTPXE

rm -rf .temp.ipxe