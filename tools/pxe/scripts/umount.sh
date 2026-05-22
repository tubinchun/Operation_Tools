#!/bin/bash
PxeMountPoint=$(realpath netboot/pxenfsroot)

mount | grep $PxeMountPoint | awk '{print $3}' | xargs umount -l -q > /dev/null 2>&1
rm -rf netboot/pxenfsroot/* > /dev/null 2>&1