// v3: 修复响应体打印 + 错误详情改走 ServerError 构造函数
// 用法: adb shell am force-stop com.dodonew.online
//       frida -U -f com.dodonew.online -l hook_des2.js

Java.perform(function () {
    var JString = Java.use("java.lang.String");

    // 工具: 打印响应体(防越界)
    function showBody(tag, bytes) {
        try {
            var s = JString.$new(bytes, "UTF-8");
            var n = s.length();
            console.log(tag + " " + s.substring(0, n > 1500 ? 1500 : n));
        } catch (e) { console.log(tag + " (打印失败: " + e + ")"); }
    }

    // 1. DES 加解密明文
    var DesSecurity = Java.use("com.dodonew.online.util.DesSecurity");
    DesSecurity.encrypt64.overload("[B").implementation = function (data) {
        console.log("[加密明文] " + JString.$new(data, "UTF-8"));
        return this.encrypt64(data);
    };
    DesSecurity.decrypt64.overload("java.lang.String").implementation = function (data) {
        var r = this.decrypt64(data);
        console.log("[解密明文] " + JString.$new(r, "UTF-8"));
        return r;
    };

    // 2. Volley 网络层: URL + 成功响应
    var BasicNetwork = Java.use("com.android.volley.toolbox.BasicNetwork");
    BasicNetwork.performRequest.overload("com.android.volley.Request").implementation = function (request) {
        console.log("\n[请求URL] " + request.getMethod() + " " + request.getUrl());
        var resp = this.performRequest(request);
        console.log("[响应] HTTP " + resp.statusCode.value);
        showBody("[响应体]", resp.data.value);
        return resp;
    };

    // 3. 错误响应: hook ServerError 构造, 拿到 4xx/5xx 的状态码和响应体
    var ServerError = Java.use("com.android.volley.ServerError");
    ServerError.$init.overload("com.android.volley.NetworkResponse").implementation = function (nr) {
        console.log("[错误状态码] HTTP " + nr.statusCode.value);
        showBody("[错误响应体]", nr.data.value);
        return this.$init(nr);
    };

    console.log("[*] 全部 hook 就绪 (v3)");
});
