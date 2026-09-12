# -*- coding: utf-8 -*-
"""
哆点 (com.dodonew.online) 报文加解密 / 签名复现工具
算法来源: jadx 反编译
  - com.dodonew.online.util.DesSecurity  (DES/CBC/PKCS5Padding, key 先 MD5)
  - com.dodonew.online.http.RequestUtil.paraMap  (sign 计算)
  - com.dodonew.online.config.Config  (硬编码密钥)

用法:
  python dodonew_crypto.py dec "抓包得到的base64密文"     # 解密(自动尝试两组密钥)
  python dodonew_crypto.py enc "要加密的明文"
  python dodonew_crypto.py sign {"password":"123456"}    # 计算sign
  python dodonew_crypto.py req {"password":"123456"}     # 生成完整加密请求体
"""
import sys, json, hashlib, base64
from Crypto.Cipher import DES

# ---- 来自 Config.java 的硬编码常量 ----
BASE_DES_KEY = "65102933"   # Config.BASE_DES_KEY
BASE_DES_IV  = "32028092"   # Config.BASE_DES_IV
DES_KEY      = "!A^@#8$%"   # Config.DES_KEY
DES_IV       = "demin!@3"   # Config.DES_IV
BASE_APPEND  = "sdlkjsdljf0j2fsjk"  # Config.BASE_APPEND (签名盐)

KEYPAIRS = [("BASE", BASE_DES_KEY, BASE_DES_IV), ("ALT", DES_KEY, DES_IV)]

def md5hex(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def derive_des_key(key_str: str) -> bytes:
    # Java: SecretKeyFactory(DES).generateSecret(DESKeySpec(md5(key)))
    # DESKeySpec 只取前 8 字节
    return hashlib.md5(key_str.encode("utf-8")).digest()[:8]

def _pad(b: bytes) -> bytes:
    n = 8 - len(b) % 8
    return b + bytes([n]) * n

def _unpad(b: bytes) -> bytes:
    return b[:-b[-1]]

def encrypt64(plain: str, key=BASE_DES_KEY, iv=BASE_DES_IV) -> str:
    c = DES.new(derive_des_key(key), DES.MODE_CBC, iv.encode())
    return base64.b64encode(c.encrypt(_pad(plain.encode("utf-8")))).decode()

def decrypt64(b64: str, key=BASE_DES_KEY, iv=BASE_DES_IV) -> str:
    raw = base64.b64decode(b64.strip().replace("\n", "").replace("\r", ""))
    c = DES.new(derive_des_key(key), DES.MODE_CBC, iv.encode())
    return _unpad(c.decrypt(raw)).decode("utf-8")

def decrypt_auto(b64: str):
    """自动尝试两组密钥"""
    for name, k, iv in KEYPAIRS:
        try:
            return name, decrypt64(b64, k, iv)
        except Exception:
            continue
    return None, None

def make_sign(params: dict) -> str:
    """RequestUtil.paraMap: k=v 排序拼接, 末尾 &key=盐, MD5 大写"""
    items = sorted(f"{k}={v}" for k, v in params.items() if k != "sign")
    s = "&".join(items) + "&key=" + BASE_APPEND
    return md5hex(s).upper()

def build_request(params: dict) -> str:
    """完整流程: 加sign -> 按key排序JSON -> DES加密 -> Base64"""
    params = dict(params)
    params["sign"] = make_sign(params)
    plain = json.dumps({k: params[k] for k in sorted(params)},
                       ensure_ascii=False, separators=(",", ":"))
    return encrypt64(plain)

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        cmd, arg = sys.argv[1], sys.argv[2]
        if cmd == "dec":
            name, plain = decrypt_auto(arg)
            print(f"[密钥组: {name}]\n{plain}" if plain else "两组密钥均解密失败")
        elif cmd == "enc":
            print(encrypt64(arg))
        elif cmd == "sign":
            print(make_sign(json.loads(arg)))
        elif cmd == "req":
            print(build_request(json.loads(arg)))
        else:
            print(__doc__)
    else:
        # 自检: 加密再解密应还原
        demo = '{"password":"test123","schoolId":"31"}'
        ct = encrypt64(demo)
        assert decrypt64(ct) == demo
        print("[自检通过] 加解密往返一致")
        print("示例密文:", ct[:60] + "...")
        print(__doc__)
