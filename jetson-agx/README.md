# NVidia Jetson AGX Setup


## SDK Manager

## Preparation for SDK Manager Docker

On the host:

```sh
sudo pacman -Syu qemu-user-static qemu-user-static-binfmt
sudo systemctl restart systemd-binfmt.service

cat /proc/sys/fs/binfmt_misc/qemu-aarch64
```
