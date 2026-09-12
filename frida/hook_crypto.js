// Frida hook: 哆点 App DES 加解密明文实时打印
// 用法: frida -U -f com.dodonew.online -l hook_des.js --no-pause
//       (或 App 已运行: frida -U com.dodonew.online -l hook_des.js)

Java.perform(function () {
    var DesSecurity = Java.use("com.dodonew.online.util.DesSecurity");

    DesSecurity.encrypt64.overload("[B").implementation = function (data) {
        var plain = Java.use("java.lang.String").$new(data, "UTF-8");
        var result = this.encrypt64(data);
        console.log("[加密明文] " + plain);
        console.log("[加密结果] " + result);
        return result;
    };

    DesSecurity.decrypt64.overload("java.lang.String").implementation = function (data) {
        var result = this.decrypt64(data);
        var plain = Java.use("java.lang.String").$new(result, "UTF-8");
        console.log("[解密密文] " + data);
        console.log("[解密明文] " + plain);
        return result;
    };

    // 顺便看签名计算: RequestUtil.paraMap 的入参
    var RequestUtil = Java.use("com.dodonew.online.http.RequestUtil");
    RequestUtil.paraMap.overload("java.util.Map", "java.lang.String", "java.lang.String")
        .implementation = function (addMap, append, sign) {
        console.log("[签名参数] " + addMap + " 盐=" + append);
        return this.paraMap(addMap, append, sign);
    };

    console.log("[*] hook 已就绪, 等待 App 发起请求...");
});
