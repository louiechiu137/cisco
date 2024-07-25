项目

这个项目旨在通过自动化的方式简化和加速网络设备的配置和部署过程。

## 目录

- [介绍](#介绍)
- [功能](#功能)
- [安装](#安装)
- [使用](#使用)
- [贡献](#贡献)
- [许可证](#许可证)
- [联系我们](#联系我们)

## 介绍

**ZTP (Zero-Touch Provisioning)** 项目旨在为网络管理员提供一个高效的自动化解决方案，以简化网络设备的配置和部署。通过 ZTP，网络设备可以在开箱即用的情况下自动获取并应用配置，从而显著减少手动配置的时间和错误。

## 功能

- **自动化设备配置**：设备开机后自动获取配置文件并应用。
- **CSV 文件上传**：支持通过 CSV 文件批量上传设备配置。
- **JSON 配置管理**：管理和更新设备配置的 JSON 文件。
- **设备图像上传**：支持设备固件或操作系统的上传和管理。
- **文件下载模板**：提供 CSV 模板下载，便于批量配置。

## 安装

按照以下步骤安装和设置项目：

1. 克隆此仓库到你的本地机器：

    ```sh
    https://github.com/louiechiu137/cisco.git
    ```

2. 进入项目目录：

    ```sh
    cd ./cisco/ZTP
    ```

3. 使用 Docker Compose 启动项目：

    ```sh
    docker-compose up -d
    ```

## 使用

在成功安装和启动项目后，你可以按照以下步骤使用：

1. 访问本地服务器：

    打开浏览器并访问 `http://localhost:80`。

2. 上传 CSV 文件：

    - 在“Upload CSV File”部分选择一个 CSV 文件并点击“Upload CSV”按钮。
    - 系统会自动解析 CSV 文件并更新设备配置。

3. 下载 CSV 模板：

    - 点击“Download CSV Template”按钮下载模板文件。
    - 使用模板文件创建新的设备配置并上传。

4. 上传设备图像：

    - 在“Upload Device Image”部分选择一个设备图像文件并点击“Upload Image”按钮。
    - 系统会显示上传进度并完成上传。

5. 查看和管理设备配置：

    - 在“Generate and Submit JSON”部分生成并提交设备配置的 JSON 文件。

## 贡献

我们欢迎所有对网络自动化和配置管理有兴趣的人贡献他们的力量。请遵循以下步骤来贡献：

1. Fork 此仓库
2. 创建一个新的分支：

    ```sh
    git checkout -b feature/your-feature-name
    ```

3. 提交你的更改：

    ```sh
    git commit -m "Add some feature"
    ```

4. 推送到分支：

    ```sh
    git push origin feature/your-feature-name
    ```

5. 创建一个 Pull Request

请确保你的代码遵循我们的代码规范，并提供详细的提交信息。

## 许可证

本项目基于 MIT 许可证进行发布。详情请参阅 [LICENSE](LICENSE) 文件。

## 联系我


如果你有任何问题或建议，请通过以下方式联系我：

- Email: zhaolingyun@seinfor.com.cn
- GitHub Issues: [提交问题](https://github.com/louiechiu137/cisco/issues)

!!!!!mkpp greatagain!!!!!
