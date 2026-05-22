#!/bin/bash

cd scripts
PxeMountPoint=$(realpath ../netboot/pxenfsroot)
GrubEfiDir=../netboot/grub_efi/
ConfigDir=../netboot/config/


if [ "$1" == "--rescan" ] ;then
  rm -rf ../netboot/config/
fi
ln -sf $PxeMountPoint /tmp
ls ../iso/*.iso | while read filename; do
  isoname=$(echo -n "$filename" | md5sum | cut -c1-9)
  mkdir -p $PxeMountPoint/$isoname $PxeMountPoint/$isoname"_iso"
  if [ "$1" != "--notremount" ] ;then
      umount -q -l $PxeMountPoint/$isoname
      mount -o ro "$filename" $PxeMountPoint/$isoname"_iso"
      ls -A $PxeMountPoint/$isoname"_iso"/ | while read filename ;
      do
        if [ -d $PxeMountPoint/$isoname"_iso"/$filename ]; then
          mkdir -p $PxeMountPoint/$isoname/$filename
        elif [ -f $PxeMountPoint/$isoname"_iso"/$filename ]; then
          touch $PxeMountPoint/$isoname/$filename
        fi
        mount --bind $PxeMountPoint/$isoname"_iso"/$filename $PxeMountPoint/$isoname/$filename
      done
  fi
  grubfile=$(find $PxeMountPoint/$isoname -name "grub.cfg" | head -1)

  #netboot 引导文件

  if [ "$1" != "--rescan" ] ;then
    [ -f $ConfigDir$isoname"/config.ini" ]  && continue 
  fi
  if [ -f "$PxeMountPoint/$isoname/LICENSE" ]; then
    PLATFORM=$(cat $PxeMountPoint/$isoname/LICENSE | grep PLATFORM | awk -F : '{print $2}')
  elif [ -d "$PxeMountPoint/$isoname/boot/grub/x86_64-efi" ] || [ "$PxeMountPoint/$isoname/EFI/BOOT/BOOTX64.EFI" ]; then
    PLATFORM="x86_64"
  elif [ -d "$PxeMountPoint/$isoname/boot/grub/arm64-efi" ]  || [ "$PxeMountPoint/$isoname/EFI/BOOT/BOOTAA64.EFI" ]; then
    PLATFORM="arm64"
  elif [ -d "$PxeMountPoint/$isoname/boot/grub/loongarch64-efi" ]  || [ "$PxeMountPoint/$isoname/EFI/BOOT/BOOTLOONGARCH64.EFI" ]; then
    PLATFORM="loongarch64"
  else
    PLATFORM=""
    echo "镜像"$filename"不支持，跳过"
    continue
  fi
  mkdir -p $ConfigDir$isoname
  cp -rpf $GrubEfiDir$PLATFORM.efi $ConfigDir$isoname/grub.efi
  cp -rpf $grubfile $ConfigDir$isoname/grub.cfg_tpl

  #kylin desktop
  sed -i "/boot=casper/s#\$# ip=dhcp netboot=nfs nfsroot=SERVER_IP_ADDRESS:/tmp/pxenfsroot/$isoname/#" $ConfigDir$isoname/grub.cfg_tpl
  sed -i "s#/casper/#(http,SERVER_IP_ADDRESS:HTTP_PORT)/pxenfsroot/$isoname/casper/#g" $ConfigDir$isoname/grub.cfg_tpl

  #uos
  sed -i "/boot=live/s#\$# ip=dhcp netboot=nfs nfsroot=SERVER_IP_ADDRESS:/tmp/pxenfsroot/$isoname/#" $ConfigDir$isoname/grub.cfg_tpl
  sed -i "s#/live/#(http,SERVER_IP_ADDRESS:HTTP_PORT)/pxenfsroot/$isoname/live/#g" $ConfigDir$isoname/grub.cfg_tpl
  sed -i "s# /boot/# (http,SERVER_IP_ADDRESS:HTTP_PORT)/pxenfsroot/$isoname/boot/#g" $ConfigDir$isoname/grub.cfg_tpl

  #kylin server
  sed -i -E "s#(inst\.stage2=)[^ ]*#\1nfs:SERVER_IP_ADDRESS:/tmp/pxenfsroot/$isoname/#"  $ConfigDir$isoname/grub.cfg_tpl
  sed -i "/inst.stage2=/s#\$# ip=dhcp inst.repo=nfs:SERVER_IP_ADDRESS:/tmp/pxenfsroot/$isoname/ inst.ks=http://SERVER_IP_ADDRESS:HTTP_PORT/monitor/monitor.cfg#" $ConfigDir$isoname/grub.cfg_tpl
  sed -i "s#/images/#(http,SERVER_IP_ADDRESS:HTTP_PORT)/pxenfsroot/$isoname/images/#g" $ConfigDir$isoname/grub.cfg_tpl
  
  echo "[config]" >  $ConfigDir$isoname"/config.ini"
  echo "isoname="$(basename $filename) >>  $ConfigDir$isoname"/config.ini"
  echo "extpathname=mpxe_extfile" >>  $ConfigDir$isoname"/config.ini"
  GrubKernel=$(cat $grubfile | grep "boot=casper" |head -1)
  if [ "misstar""$GrubKernel" != "misstar" ];then
    if [ -f "$PxeMountPoint/$isoname/ky-installer.cfg" ]; then
      cp $PxeMountPoint/$isoname/ky-installer.cfg $ConfigDir$isoname"/autoinstall.cfg_tpl"
    else
      echo > $ConfigDir$isoname"/autoinstall.cfg_tpl"
    fi
    echo "class=Preseed" >>  $ConfigDir$isoname"/config.ini"
  else
    echo "class=Kickstart" >>  $ConfigDir$isoname"/config.ini"
    echo > $ConfigDir$isoname"/autoinstall.cfg_tpl"
  fi

done
cd - &>/dev/null
