# 银河麒麟运维管理工具

[![License](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

专为银河麒麟桌面操作系统 V10 SP1 设计的系统运维管理工具，提供一站式系统管理功能。

---

## 📋 功能特性

### 🖥️ 系统监控

**SystemStatusPage** - 实时系统状态监控
- CPU使用率实时监控与折线图展示
- 内存使用情况监控（含Swap分区）
- 网络流量监控（上传/下载速度）
- 进程管理（当前用户进程、全部进程列表）
- 进程结束功能（单个进程/全部同名进程）

### 👥 用户管理

**UserManagementPage** - 用户信息管理
- 用户列表展示
- 用户详情查看（用户名、UID、GID、家目录、Shell、用户类型、密码状态、所属组）
- 登录历史记录查询（支持按用户筛选）
- 密码重置功能（需管理员权限）

### 🌐 网络管理

**NetworkPage** - 网络配置管理
- 网络接口信息展示
- 网络服务重启功能

### 📦 软件管理

**SoftwarePage** - 软件包管理
- APT源配置查看与编辑
- 已安装软件包列表查看
- 软件包列表导出功能

### 💻 命令终端

**TerminalPage** - 系统命令执行
- 命令输入与执行
- 输出结果实时显示
- 危险命令过滤保护（rm -rf, mkfs, dd if= 等）
- 命令超时控制（30秒）

### 🧹 系统清理

**CleanupPage** - 系统清理工具
- 清理服务状态监控与控制
- 磁盘容量显示与进度条
- 定时任务设置（清理时间、频率、巡检设置）
- 清理目录选择（浏览器缓存、系统垃圾等）
- 快捷操作（服务启停、立即清理、日志查看）
- 清理模式选择与扩展配置

### 🎯 特色工具

**FeatureToolsPage** - 实用工具集合

| 工具名称 | 功能描述 | 对应Dialog |
|---------|---------|-----------|
| **Hosts编辑器** | 自定义本地域名解析文件，支持恢复默认、强制保存 | HostsEditorDialog |
| **系统信息查看** | 硬件信息、软件信息、存储信息、网络信息的详细展示 | SystemInfoDialog |
| **打印机服务修复** | 恢复CUPS默认配置并重启打印服务 | PrinterRepairDialog |
| **KMS脚本生成器** | 可视化定制KMS激活脚本，支持克隆机修复、授权文件部署、网络诊断等功能 | KmsScriptGeneratorDialog |

---

## 🛠️ 技术栈

| 分类 | 技术 | 说明 |
|-----|-----|-----|
| 语言 | Python 3.6+ | 主要开发语言 |
| GUI框架 | PyQt5 | 图形界面开发 |
| 系统监控 | psutil | 系统资源监控 |
| 打包格式 | DEB | Debian/Ubuntu包格式 |
| 样式风格 | macOS Human Interface Guidelines | Apple风格UI设计 |

---

## 📁 项目结构

```
Operation_Tools/
├── core/                    # 核心业务逻辑模块
│   ├── commands.py          # 系统命令实现（25+核心功能）
│   ├── local_client.py      # 本地客户端代理
│   ├── kylin_desktop_system_info.sh  # 系统信息收集脚本
│   └── fix_printer.sh       # 打印机修复脚本
├── ui/                      # 用户界面模块
│   ├── main_window.py       # 主窗口（整合版，包含12个页面/对话框）
│   └── macos_styles.py      # macOS风格样式定义
├── server/                  # 服务端模块（保留兼容）
│   ├── server.py            # 服务端实现
│   └── mock_server.py       # 模拟服务端
├── client/                  # 客户端模块（保留兼容）
│   ├── client.py            # 客户端实现
│   ├── gui.py               # 基础GUI
│   ├── enhanced_gui.py      # 增强版GUI
│   └── apple_ui.py          # macOS风格GUI
├── debian/                  # DEB打包配置
│   └── kylin-system-tools/  # 打包目录结构
├── kylin-cleanup_1.3.9.3_all/  # 系统清理工具集成包
├── kylintools.py            # 整合版主入口
├── build-deb.sh             # 构建脚本（支持amd64/arm64/all）
└── setup.py                 # Python包配置
```

---

## 🔧 核心命令列表

### 系统信息
| 函数名 | 功能 |
|-------|------|
| `get_system_info()` | 获取系统基本信息 |
| `get_cpu_info()` | 获取CPU信息 |
| `get_memory_info()` | 获取内存信息 |
| `get_disk_info()` | 获取磁盘信息 |
| `get_network_info()` | 获取网络信息 |

### 进程管理
| 函数名 | 功能 |
|-------|------|
| `get_process_list(limit)` | 获取进程列表 |
| `get_process_list_by_user(username)` | 获取指定用户进程 |
| `kill_process(pid)` | 结束指定进程 |
| `kill_process_by_name(name)` | 结束所有同名进程 |

### 用户管理
| 函数名 | 功能 |
|-------|------|
| `get_users()` | 获取用户列表 |
| `get_user_info(username)` | 获取用户详情 |
| `get_login_history(username)` | 获取登录历史 |
| `reset_user_password(username, password)` | 重置用户密码 |

### 服务管理
| 函数名 | 功能 |
|-------|------|
| `get_service_list()` | 获取服务列表 |
| `restart_network()` | 重启网络服务 |
| `fix_printer()` | 修复打印机服务 |

### 硬件信息
| 函数名 | 功能 |
|-------|------|
| `get_hardware_info()` | 获取硬件信息 |
| `get_gpu_info()` | 获取显卡信息 |
| `get_detailed_system_info()` | 获取详细系统信息 |

### 系统清理
| 函数名 | 功能 |
|-------|------|
| `get_cleanup_status()` | 获取清理服务状态 |
| `get_cleanup_config()` | 获取清理配置 |
| `save_cleanup_config(config)` | 保存清理配置 |
| `run_cleanup()` | 执行立即清理 |
| `start_cleanup_service()` | 启动清理服务 |
| `stop_cleanup_service()` | 停止清理服务 |

---

## 📦 安装方式

### 方法一：DEB包安装

```bash
# 下载最新版本
wget https://github.com/tubinchun/Operation_Tools/releases/download/v1.1/kylin-system-tools_1.1_amd64.deb

# 安装
sudo dpkg -i kylin-system-tools_1.1_amd64.deb
sudo apt-get install -f
```

### 方法二：源码构建

```bash
# 克隆仓库
git clone https://github.com/tubinchun/Operation_Tools.git
cd Operation_Tools

# 安装依赖
sudo apt-get install python3-pyqt5 python3-psutil

# 构建DEB包
bash build-deb.sh amd64

# 安装
sudo dpkg -i output/kylin-system-tools_1.1_amd64.deb
```

---

## 🚀 使用说明

### 启动方式

```bash
# 命令行启动
kylintools
```

或者通过桌面菜单启动「银河麒麟运维管理工具」。

### 界面布局

应用采用 macOS 风格设计：
- **左侧导航栏**：系统监视器、百宝箱（特色工具）、系统清理
- **右侧主内容区**：功能页面展示
- **顶部菜单栏**：文件、工具、帮助

---

## 🔧 构建说明

```bash
# 构建 amd64 架构
bash build-deb.sh amd64

# 构建 arm64 架构
bash build-deb.sh arm64

# 构建通用包
bash build-deb.sh all
```

---

## 📝 开发说明

### 依赖安装

```bash
sudo apt-get install python3-pyqt5 python3-psutil python3-dev
```

### 运行开发版本

```bash
python kylintools.py
```

---

## 🛡️ 安全特性

| 特性 | 说明 |
|-----|-----|
| ✅ 危险命令过滤 | rm -rf, mkfs, dd if= 等危险命令 |
| ✅ 命令超时控制 | 默认30秒超时 |
| ✅ 管理员权限 | 敏感操作使用 pkexec 获取root权限 |
| ✅ 线程安全 | 防止UI组件访问已销毁对象 |
| ✅ Qt高DPI缩放 | 支持高分辨率显示 |

---

## 📄 许可证

本项目采用 GPL-3.0 许可证，详见 [LICENSE](LICENSE) 文件。

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请提交 Issue。

---

**项目地址**: https://github.com/tubinchun/Operation_Tools  
**适用平台**: 银河麒麟桌面操作系统 V10 SP1  
**版本**: v1.1