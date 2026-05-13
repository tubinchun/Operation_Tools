# 银河麒麟运维管理工具

[![License](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

专为银河麒麟桌面操作系统 V10 SP1 设计的系统运维管理工具。

## 📋 功能特性

- **系统信息监控** - 实时监控主机名、内核版本、架构等系统信息
- **CPU监控** - 监控CPU核心数、频率、使用率
- **内存监控** - 监控内存总量、使用量、Swap分区
- **磁盘监控** - 监控分区信息、磁盘使用率
- **网络管理** - 网络接口、IP地址、连接数管理
- **进程管理** - 进程列表、CPU/内存占用监控
- **服务管理** - 系统服务状态管理
- **用户管理** - 用户列表、登录历史管理
- **软件管理** - APT源配置、已安装软件包管理
- **日志管理** - 系统日志查看与清理
- **安全设置** - Kysec安全中心控制
- **命令终端** - 系统命令执行（带安全过滤）

## 🛠️ 技术栈

- **语言**: Python 3.6+
- **GUI框架**: PyQt5
- **系统监控**: psutil
- **打包格式**: DEB

## 📦 安装方式

### 方法一：从DEB包安装

```bash
# 下载最新版本
wget https://github.com/tubinchun/Operation_Tools/releases/download/v1.0.0/kylin-system-tools_1.0.0_amd64.deb

# 安装
sudo dpkg -i kylin-system-tools_1.0.0_amd64.deb
sudo apt-get install -f
```

### 方法二：从源码构建

```bash
# 克隆仓库
git clone https://github.com/tubinchun/Operation_Tools.git
cd Operation_Tools

# 安装依赖
sudo apt-get install python3-pyqt5 python3-psutil

# 构建DEB包
bash build-deb.sh amd64

# 安装
sudo dpkg -i output/kylin-system-tools_1.0.0_amd64.deb
```

## 🚀 使用说明

### 启动应用

```bash
# 命令行启动
kylintools
```

或者通过桌面菜单启动"银河麒麟运维管理工具"。

### 功能模块

1. **系统信息** - 系统基本信息概览和实时统计
2. **系统状态** - CPU、内存、进程、服务的详细监控
3. **用户管理** - 用户列表和登录历史
4. **网络设置** - 网络信息和网络服务控制
5. **软件管理** - APT源配置和已安装软件包
6. **日志管理** - 系统日志查看和清理
7. **安全设置** - Kysec安全中心控制
8. **命令终端** - 系统命令执行

## 🏗️ 项目结构

```
Operation_Tools/
├── core/                    # 核心业务逻辑模块
│   ├── __init__.py
│   ├── commands.py          # 系统命令实现
│   └── local_client.py      # 本地客户端代理
├── ui/                      # 用户界面模块
│   ├── __init__.py
│   └── main_window.py       # 整合后的主窗口
├── server/                  # 服务端模块 (保留兼容)
├── client/                  # 客户端模块 (保留兼容)
├── debian/                  # DEB打包配置
├── kylintools.py            # 整合版主入口
├── validate.py              # 功能验证脚本
├── build-deb.sh             # 构建脚本
└── setup.py                 # Python包配置
```

## 🔧 构建说明

```bash
# 构建 amd64 架构包
bash build-deb.sh amd64

# 构建 arm64 架构包
bash build-deb.sh arm64

# 构建通用包
bash build-deb.sh all
```

## 📝 开发说明

### 依赖安装

```bash
sudo apt-get install python3-pyqt5 python3-psutil python3-dev
```

### 运行开发版本

```bash
python kylintools.py
```

## 🛡️ 安全特性

- 危险命令过滤（rm -rf, mkfs, dd if= 等）
- 命令超时控制（30秒）
- 敏感操作需要root权限

## 📄 许可证

本项目采用 GPL-3.0 许可证，详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请提交 Issue。

---

**项目地址**: https://github.com/tubinchun/Operation_Tools  
**适用平台**: 银河麒麟桌面操作系统 V10 SP1  
**版本**: v1.0.0