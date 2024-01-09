搜索js_security xxx. js
查找sign方法 ParamsSign
全局network搜索ParamsSign 找到appid
通过console初始化ParamsSign并测试
例如
window.PSign=new window.ParamsSign({appId:"f961a"})
this.PSign.sign({"gid":""}).then(signedParams => {console.log(signedParams.h5st)});

参考官方说明
https://yd-doc.jdcloud.com/docs/5-hufu/5-2-guanfang/waap.html