function strAdd(b, P, T) {
	return b.substr(0, b.length - T) / 1 + P / 1 + b.substr(b.length - T)
}
function genTraceId(b) {
			var P = b.operateId,
				T = b.bizId,
				C = b.isServer || 0,
				D = new Date,
				J = new Date("2017/01/01"),
				$ = parseInt((D.getTime() - J.getTime()) / 1e3),
				ee = 1e3 * parseInt(100 * Math.random()) + D.getMilliseconds();
			if (!T || !P) return "";
			P &= 2047, T &= 63;
			var te = 1073741823 & $;
			return ee = (ee &= 32767).toString(2), P = P.toString(2), T = T.toString(2), te = te.toString(2), ee = "000000000000000".substr(0, 15 - ee.length) + ee, P = "00000000000".substr(0, 11 - P.length) + P, T = "000000".substr(0, 6 - T.length) + T,
				function bignumAdd(b, P) {
					for (var T = 0, C = [], D = b.length, J = P.length, $ = Math.max(D, J), ee = 0; ee < $; ee++) {
						var te = (D - ee > 0 ? b.charAt(D - ee - 1) / 1 : 0) + (J - ee > 0 ? P.charAt(J - ee - 1) / 1 : 0) + T;
						te >= 10 ? (T = 1, C.push(te % 10)) : (T = 0, C.push(te))
					}
					return C.reverse().join("")
				}(function getTotal(b, P) {
					for (var T = parseInt(b, 2), C = "0", D = [], J = Math.pow(2, P) + "", $ = J.length - 1; $ > -1; $--) {
						var ee = J[$];
						D.push(T * ee + "")
					}
					for (var te = 0; te < D.length; te++) C = strAdd(C, D[te], te);
					return C
				}("0" + te, 33), parseInt(C + T + P + ee, 2) + "")
		}