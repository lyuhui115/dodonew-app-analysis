# dodonew-app-analysis

Android 商业 App（上网认证类）协议逆向分析：从 APK 反编译到独立协议客户端的完整实战。

> 📖 完整分析过程见 [writeup（个人博客）](https://lyuhui115.github.io/2026/09/12/android-apk-reverse-engineering/)

> ⚠️ 本项目仅用于安全学习与研究，所有密钥/常量均提取自公开可下载的客户端，测试均针对本人账号。请勿用于任何非法用途。

## 分析链路

```
APK → 信息收集/加固检测(无壳) → jadx 反编译 → 静态提取密钥与签名算法
    → Frida 动态验证(双向明文) → 算法离线复现(逐字节一致)
    → 独立 Python 客户端(登录/网点/在线状态 全链路 code:1)
```

## 核心发现

| 项目 | 结果 |
|---|---|
| 传输加密 | DES/CBC/PKCS5Padding，key 先 MD5 取前 8 字节，结果 Base64 |
| 密钥管理 | Key/IV/签名盐全部硬编码于客户端 `Config.java`（形同虚设）|
| 请求封装 | `{"Encrypt": "<密文>"}`，业务参数 + timeStamp + sign |
| 签名算法 | 参数 k=v 字典序排序拼接 + 固定盐 → MD5 大写 |
| 响应格式 | 同样 DES 加密，`{"code":1,...}` 为成功 |
| 传输层 | 明文 HTTP |

## 目录结构

```
crypto/protocol_crypto.py   加解密与签名算法复现（pycryptodome）
frida/hook_crypto.js        hook 加解密函数，实时打印明文
frida/hook_network.js       增强版：网络层 URL/响应/错误详情全量捕获
client/protocol_client.py   独立协议客户端（qqlogin/city/netbar/state/login）
```

## 快速使用

**1. 算法自检**（加解密往返一致 + 签名示例）：

```bash
pip install pycryptodome requests
python crypto/protocol_crypto.py
```

**2. 动态验证**（需 root 设备 + frida-server）：

```bash
adb shell am force-stop <目标包名>
frida -U -f <目标包名> -l frida/hook_network.js
```

**3. 独立客户端**：

```bash
python client/protocol_client.py qqlogin <openID> <nick>
python client/protocol_client.py city
python client/protocol_client.py netbar <domainId>
python client/protocol_client.py state <domainId> <netBarId> <userId>
```

## 踩坑记录

1. 本地代理劫持导致超时 → requests 传 `proxies={"http": None, "https": None}`
2. Windows 控制台 GBK 打印中文报错 → `sys.stdout.reconfigure(encoding="utf-8")`
3. 服务器报错即文档：缺参数直接返回「缺少必须参数:xxx」，参数试错快于读代码
4. 该后端对无效登录返回 404 HTML 页（不要误判为接口不存在）
5. hook 打印响应体注意长度越界（`substring` 前先取 `length()`）

## 相关仓库

- [bagua-crypto](https://github.com/lyuhui115/bagua-crypto) —— 自创编码方案的 CTF 出题与官方题解

## License

MIT（仅供学习交流）
