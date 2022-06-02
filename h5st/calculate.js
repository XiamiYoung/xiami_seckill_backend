we = function sha256(j) {
			var M = function safeAdd(j, M) {
					var W = (65535 & j) + (65535 & M);
					return(j >> 16) + (M >> 16) + (W >> 16) << 16 | 65535 & W
				},
				W = function S(j, M) {
					return j >>> M | j << 32 - M
				},
				$ = function R(j, M) {
					return j >>> M
				},
				q = function ch(j, M, W) {
					return j & M ^ ~j & W
				},
				X = function maj(j, M, W) {
					return j & M ^ j & W ^ M & W
				},
				Y = function sigma0256(j) {
					return W(j, 2) ^ W(j, 13) ^ W(j, 22)
				},
				Z = function sigma1256(j) {
					return W(j, 6) ^ W(j, 11) ^ W(j, 25)
				},
				ee = function gamma0256(j) {
					return W(j, 7) ^ W(j, 18) ^ $(j, 3)
				},
				ae = function gamma1256(j) {
					return W(j, 17) ^ W(j, 19) ^ $(j, 10)
				},
				ie = function utf8Encode(j) {
					j = j.replace(/\r\n/g, "\n");
					for(var M = "", W = 0; W < j.length; W++) {
						var $ = j.charCodeAt(W);
						$ < 128 ? M += String.fromCharCode($) : $ > 127 && $ < 2048 ? (M += String.fromCharCode($ >> 6 | 192), M += String.fromCharCode(63 & $ | 128)) : (M += String.fromCharCode($ >> 12 | 224), M += String.fromCharCode($ >> 6 & 63 | 128), M += String.fromCharCode(63 & $ | 128))
					}
					return M
				}(j);
			return function binb2hex(j) {
				for(var M = "0123456789abcdef", W = "", $ = 0; $ < 4 * j.length; $++) W += M.charAt(j[$ >> 2] >> 8 * (3 - $ % 4) + 4 & 15) + M.charAt(j[$ >> 2] >> 8 * (3 - $ % 4) & 15);
				return W
			}(function coreSha256(j, W) {
				var $ = [1116352408, 1899447441, 3049323471, 3921009573, 961987163, 1508970993, 2453635748, 2870763221, 3624381080, 310598401, 607225278, 1426881987, 1925078388, 2162078206, 2614888103, 3248222580, 3835390401, 4022224774, 264347078, 604807628, 770255983, 1249150122, 1555081692, 1996064986, 2554220882, 2821834349, 2952996808, 3210313671, 3336571891, 3584528711, 113926993, 338241895, 666307205, 773529912, 1294757372, 1396182291, 1695183700, 1986661051, 2177026350, 2456956037, 2730485921, 2820302411, 3259730800, 3345764771, 3516065817, 3600352804, 4094571909, 275423344, 430227734, 506948616, 659060556, 883997877, 958139571, 1322822218, 1537002063, 1747873779, 1955562222, 2024104815, 2227730452, 2361852424, 2428436474, 2756734187, 3204031479, 3329325298],
					ie = [1779033703, 3144134277, 1013904242, 2773480762, 1359893119, 2600822924, 528734635, 1541459225],
					ce = new Array(64);
				j[W >> 5] |= 128 << 24 - W % 32,
					j[15 + (W + 64 >> 9 << 4)] = W;
				for(var le = 0; le < j.length; le += 16) {
					for(var de = ie[0], fe = ie[1], pe = ie[2], be = ie[3], ye = ie[4], we = ie[5], _e = ie[6], Se = ie[7], Te = 0; Te < 64; Te++) {
						ce[Te] = Te < 16 ? j[Te + le] : M(M(M(ae(ce[Te - 2]), ce[Te - 7]), ee(ce[Te - 15])), ce[Te - 16]);
						var xe = M(M(M(M(Se, Z(ye)), q(ye, we, _e)), $[Te]), ce[Te]),
							Ie = M(Y(de), X(de, fe, pe));
						Se = _e,
							_e = we,
							we = ye,
							ye = M(be, xe),
							be = pe,
							pe = fe,
							fe = de,
							de = M(xe, Ie)
					}
					ie[0] = M(de, ie[0]),
						ie[1] = M(fe, ie[1]),
						ie[2] = M(pe, ie[2]),
						ie[3] = M(be, ie[3]),
						ie[4] = M(ye, ie[4]),
						ie[5] = M(we, ie[5]),
						ie[6] = M(_e, ie[6]),
						ie[7] = M(Se, ie[7])
				}
				return ie
			}(function str2binb(j) {
				for(var M = [], W = 0; W < 8 * j.length; W += 8) M[W >> 5] |= (255 & j.charCodeAt(W / 8)) << 24 - W % 32;
				return M
			}(ie), 8 * ie.length))
		}

var promise = new ParamsSign({
	"appId": 'input_app_id',
	"debug": !1
}).sign({
	"functionId": 'input_function_id',
	"appid": "m_core",
	"client": "Win32",
	"clientVersion": "1.3.0",
	"t": input_time,
	"body":'input_body' && we('input_body')
})

promise.then(function(result){
  console.log("h5st:" + result.h5st)
})