# -*- coding: utf-8 -*-
"""
哆点 (com.dodonew.online) 协议客户端 —— 完整版
全链路已实测打通: 登录→城市→网点→在线状态

用法:
  python dodonew_client.py qqlogin <openID> <nickName>     # QQ登录拿 userId
  python dodonew_client.py city                           # 城市列表(domainid)
  python dodonew_client.py netbar <domainId>              # 该域网点列表(netBarId)
  python dodonew_client.py state <domainId> <netBarId> <userId>   # 查在线状态
  python dodonew_client.py login <用户名> <密码>           # 密码登录
"""
import sys, time, json, requests
from protocol_crypto import encrypt64, decrypt64, make_sign

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = "http://api.dodovip.com/api/"
UA = "Dalvik/2.1.0 (Linux; U; Android 12; Pixel 3)"
NO_PROXY = {"http": None, "https": None}  # 国内服务器, 绕过本地代理

def call(path, params, timeout=45):
    p = dict(params)
    p["timeStamp"] = str(int(time.time() * 1000))
    p["sign"] = make_sign(p)
    plain = json.dumps({k: p[k] for k in sorted(p)},
                       ensure_ascii=False, separators=(",", ":"))
    r = requests.post(BASE + path, json={"Encrypt": encrypt64(plain)},
                      headers={"User-Agent": UA}, proxies=NO_PROXY, timeout=timeout)
    try:
        return json.loads(decrypt64(r.text.strip()))
    except Exception:
        return {"http_status": r.status_code, "raw": r.text[:300]}

def qq_login(open_id, nickname="test"):
    return call("user/qqLogin", {
        "equtype": "ANDROID", "loginImei": "Androidnull",
        "icon": "", "nickName": nickname, "openID": open_id,
    })

def cities():
    return call("oth/city", {})

def netbar_list(domain_id):
    return call("oth/netbarList", {"domainId": str(domain_id)})

def online_state(domain_id, netbar_id, user_id):
    # memberId = 登录返回的 userId (已验证), account 会报 code:7
    return call("oth/online/state", {
        "domainId": str(domain_id), "netBarId": str(netbar_id),
        "memberId": str(user_id),
    })

def login(username, password):
    return call("user/login", {
        "username": username, "userPwd": password,
        "equtype": "ANDROID", "loginImei": "Androidnull",
    })

if __name__ == "__main__":
    a = sys.argv
    if len(a) >= 4 and a[1] == "qqlogin":   r = qq_login(a[2], a[3])
    elif len(a) >= 2 and a[1] == "city":    r = cities()
    elif len(a) >= 3 and a[1] == "netbar":  r = netbar_list(a[2])
    elif len(a) >= 5 and a[1] == "state":   r = online_state(a[2], a[3], a[4])
    elif len(a) >= 4 and a[1] == "login":   r = login(a[2], a[3])
    else:
        print(__doc__); sys.exit(0)
    print(json.dumps(r, ensure_ascii=False, indent=2)[:3000])
